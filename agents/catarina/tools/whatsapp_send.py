from python.helpers.tool import Tool, Response
import httpx
import os
import logging

logger = logging.getLogger(__name__)


class WhatsAppSendTool(Tool):
    """
    Send a WhatsApp message to the current user via UAZAPI.
    
    This tool is used to send responses back to WhatsApp users.
    The phone number is retrieved from the agent context.
    """

    async def execute(self, **kwargs):
        # Get phone from context (set by webhook)
        phone = self.agent.context.get_data("current_phone")
        message = self.args.get("message", "")
        msg_type = self.args.get("type", "text")  # text, menu, media
        
        if not phone:
            return Response(
                message="Erro: Número de telefone não encontrado no contexto.",
                break_loop=False
            )
        
        if not message:
            return Response(
                message="Erro: Mensagem vazia.",
                break_loop=False
            )
        
        # Get credentials from environment
        base_url = os.environ.get("UAZAPI_BASE_URL", "").rstrip("/")
        token = os.environ.get("UAZAPI_INSTANCE_TOKEN", "")
        
        if not base_url or not token:
            return Response(
                message="Erro: UAZAPI não configurado (UAZAPI_BASE_URL ou UAZAPI_INSTANCE_TOKEN ausente).",
                break_loop=False
            )
        
        headers = {
            "token": token,
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if msg_type == "text":
                    # Simple text message
                    resp = await client.post(
                        f"{base_url}/send/text",
                        headers=headers,
                        json={
                            "number": phone,
                            "text": message,
                            "delay": 2000,  # 2s typing indicator
                            "readchat": True,
                        }
                    )
                elif msg_type == "menu":
                    # Interactive menu (list or buttons)
                    menu_data = self.args.get("menu", {})
                    choices = menu_data.get("choices", [])
                    menu_type = menu_data.get("menu_type", "list")
                    
                    resp = await client.post(
                        f"{base_url}/send/menu",
                        headers=headers,
                        json={
                            "number": phone,
                            "type": menu_type,
                            "text": message,
                            "listButton": menu_data.get("button_text", "Ver opções"),
                            "choices": choices,
                            "delay": 2000,
                            "readchat": True,
                        }
                    )
                else:
                    # Fallback to text
                    resp = await client.post(
                        f"{base_url}/send/text",
                        headers=headers,
                        json={
                            "number": phone,
                            "text": message,
                            "delay": 2000,
                            "readchat": True,
                        }
                    )
                
                resp.raise_for_status()
                
                logger.info(f"WhatsApp message sent to {phone[:6]}...")
                return Response(
                    message=f"✅ Mensagem enviada para o paciente.",
                    break_loop=True  # End loop after sending response
                )
                
        except httpx.HTTPStatusError as e:
            logger.error(f"UAZAPI HTTP error: {e.response.status_code} - {e.response.text[:200]}")
            return Response(
                message=f"Erro ao enviar mensagem: HTTP {e.response.status_code}",
                break_loop=False
            )
        except Exception as e:
            logger.error(f"UAZAPI error: {str(e)}")
            return Response(
                message=f"Erro ao enviar mensagem: {str(e)}",
                break_loop=False
            )

    async def before_execution(self, **kwargs):
        """Log before sending."""
        phone = self.agent.context.get_data("current_phone")
        msg_preview = self.args.get("message", "")[:50]
        self.log = self.agent.context.log.log(
            type="tool",
            heading=f"📱 WhatsApp: Enviando para {phone[:6] if phone else '?'}...",
            content=msg_preview
        )

    async def after_execution(self, response, **kwargs):
        """Update log after sending."""
        if self.log:
            self.log.update(finished=True)
