from python.helpers.tool import Tool, Response
import httpx
import os
import logging

logger = logging.getLogger(__name__)


class ContactLookupTool(Tool):
    """
    Look up patient contact information by CPF.
    
    Searches Supabase for patient records to retrieve stored information.
    """

    async def execute(self, **kwargs):
        cpf = self.args.get("cpf", "")
        phone = self.args.get("phone", "")
        
        if not cpf and not phone:
            return Response(
                message="Erro: Forneça CPF ou telefone para buscar o paciente.",
                break_loop=False
            )
        
        # Clean CPF (remove formatting)
        if cpf:
            cpf_clean = "".join(c for c in cpf if c.isdigit())
            if len(cpf_clean) != 11:
                return Response(
                    message=f"CPF inválido: deve ter 11 dígitos.",
                    break_loop=False
                )
        else:
            cpf_clean = None
        
        # Clean phone
        if phone:
            phone_clean = "".join(c for c in phone if c.isdigit())
        else:
            phone_clean = None
        
        # Get Supabase credentials
        supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        
        if not all([supabase_url, supabase_key]):
            return Response(
                message="Erro: Supabase não configurado.",
                break_loop=False
            )
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Search in contacts table
                params = {"limit": 1}
                
                if cpf_clean:
                    params["cpf"] = f"eq.{cpf_clean}"
                elif phone_clean:
                    params["phone"] = f"eq.{phone_clean}"
                
                resp = await client.get(
                    f"{supabase_url}/rest/v1/contacts",
                    headers={
                        "apikey": supabase_key,
                        "Authorization": f"Bearer {supabase_key}",
                    },
                    params=params
                )
                
                if resp.status_code != 200:
                    # Try google_contacts_cache table
                    resp = await client.get(
                        f"{supabase_url}/rest/v1/google_contacts_cache",
                        headers={
                            "apikey": supabase_key,
                            "Authorization": f"Bearer {supabase_key}",
                        },
                        params=params
                    )
                
                if resp.status_code != 200:
                    return Response(
                        message="Erro ao buscar contato no banco de dados.",
                        break_loop=False
                    )
                
                contacts = resp.json()
                
                if not contacts:
                    search_term = cpf_clean if cpf_clean else phone_clean
                    return Response(
                        message=f"Paciente não encontrado com '{search_term}'. Pode ser um novo paciente.",
                        break_loop=False
                    )
                
                contact = contacts[0]
                
                # Format contact info
                name = contact.get("name", contact.get("full_name", "Nome não informado"))
                email = contact.get("email", "Não informado")
                phone_found = contact.get("phone", contact.get("phone_number", "Não informado"))
                
                return Response(
                    message=f"Paciente encontrado:\n- Nome: {name}\n- Telefone: {phone_found}\n- Email: {email}",
                    break_loop=False
                )
                
        except Exception as e:
            logger.error(f"Contact lookup error: {str(e)}")
            return Response(
                message=f"Erro ao buscar contato: {str(e)}",
                break_loop=False
            )

    async def before_execution(self, **kwargs):
        cpf = self.args.get("cpf", "")
        self.log = self.agent.context.log.log(
            type="tool",
            heading=f"👤 Buscando paciente...",
            content=f"CPF: {cpf[:3]}***" if cpf else ""
        )

    async def after_execution(self, response, **kwargs):
        if self.log:
            self.log.update(finished=True)
