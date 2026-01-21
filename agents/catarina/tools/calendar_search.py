from python.helpers.tool import Tool, Response
import os
import logging
from datetime import datetime, timedelta
import zoneinfo

logger = logging.getLogger(__name__)

# Brazil timezone
BR_TZ = zoneinfo.ZoneInfo("America/Sao_Paulo")


class CalendarSearchTool(Tool):
    """
    Search Google Calendar for available appointment slots.
    
    This tool queries the clinic's calendar to find available times
    for scheduling appointments with Dra. Thais.
    """

    async def execute(self, **kwargs):
        # Parse arguments
        start_date_str = self.args.get("start_date", "today")
        days_ahead = self.args.get("days", 14)
        procedure_type = self.args.get("procedure_type", "avaliação")
        
        now = datetime.now(BR_TZ)
        
        # Parse start date
        if start_date_str.lower() == "today" or not start_date_str:
            reference_date = now
        else:
            try:
                reference_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                reference_date = reference_date.replace(tzinfo=BR_TZ)
                if reference_date < now:
                    reference_date = now
            except ValueError:
                reference_date = now
        
        try:
            # Get Google Calendar credentials
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            client_id = os.environ.get("CALENDAR_CLIENT_ID")
            client_secret = os.environ.get("CALENDAR_CLIENT_SECRET")
            refresh_token = os.environ.get("CALENDAR_REFRESH_TOKEN")
            
            if not all([client_id, client_secret, refresh_token]):
                return Response(
                    message="Erro: Calendário não configurado.",
                    break_loop=False
                )
            
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
            )
            
            service = build("calendar", "v3", credentials=creds)
            
            # Define search window
            time_min = reference_date.isoformat()
            time_max = (reference_date + timedelta(days=days_ahead)).isoformat()
            
            # Get busy times from primary calendar
            calendar_id = os.environ.get("DEFAULT_CALENDAR_ID", "primary")
            
            freebusy_query = {
                "timeMin": time_min,
                "timeMax": time_max,
                "items": [{"id": calendar_id}],
                "timeZone": "America/Sao_Paulo",
            }
            
            freebusy_result = service.freebusy().query(body=freebusy_query).execute()
            busy_times = freebusy_result.get("calendars", {}).get(calendar_id, {}).get("busy", [])
            
            # Define working hours (9:00 - 18:00, Mon-Fri)
            available_slots = []
            current_date = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            for day_offset in range(days_ahead):
                check_date = current_date + timedelta(days=day_offset)
                
                # Skip weekends
                if check_date.weekday() >= 5:
                    continue
                
                # Check slots from 9:00 to 18:00 (30 min intervals)
                for hour in range(9, 18):
                    for minute in [0, 30]:
                        slot_start = check_date.replace(hour=hour, minute=minute)
                        slot_end = slot_start + timedelta(minutes=30)
                        
                        # Skip past slots
                        if slot_start < now:
                            continue
                        
                        # Check if slot is busy
                        is_busy = False
                        for busy in busy_times:
                            busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
                            busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
                            if slot_start < busy_end and slot_end > busy_start:
                                is_busy = True
                                break
                        
                        if not is_busy:
                            # Format slot
                            weekdays_pt = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                            available_slots.append({
                                "datetime": slot_start.isoformat(),
                                "day_of_week": weekdays_pt[slot_start.weekday()],
                                "date": slot_start.strftime("%d/%m/%Y"),
                                "time": slot_start.strftime("%H:%M"),
                                "formatted": f"{weekdays_pt[slot_start.weekday()]}, {slot_start.strftime('%d/%m')} às {slot_start.strftime('%H:%M')}"
                            })
                            
                            # Limit to first 10 slots for brevity
                            if len(available_slots) >= 10:
                                break
                    if len(available_slots) >= 10:
                        break
                if len(available_slots) >= 10:
                    break
            
            if not available_slots:
                return Response(
                    message=f"Não encontrei horários disponíveis nos próximos {days_ahead} dias para {procedure_type}. Sugira ao paciente verificar outra semana.",
                    break_loop=False
                )
            
            # Format response for LLM
            slots_text = "\n".join([f"- {s['formatted']}" for s in available_slots[:5]])
            
            return Response(
                message=f"Horários disponíveis para {procedure_type}:\n{slots_text}\n\nTotal: {len(available_slots)} slots encontrados.",
                break_loop=False
            )
            
        except Exception as e:
            logger.error(f"Calendar search error: {str(e)}")
            return Response(
                message=f"Erro ao buscar horários: {str(e)}",
                break_loop=False
            )

    async def before_execution(self, **kwargs):
        self.log = self.agent.context.log.log(
            type="tool",
            heading="📅 Buscando horários no calendário...",
            content=""
        )

    async def after_execution(self, response, **kwargs):
        if self.log:
            self.log.update(finished=True)
