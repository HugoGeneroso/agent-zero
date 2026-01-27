"""
UAZAPI Webhook Endpoint for Agent Zero.

This API endpoint receives WhatsApp webhooks from UAZAPI and routes them
to Agent Zero's monologue loop for processing.

UAZAPI Webhook Format (real):
{
    "EventType": "messages",
    "message": {
        "chatid": "5517991317923@s.whatsapp.net",
        "text": "Hello",
        "content": "Hello",
        "fromMe": false,
        "sender": "5517991317923@s.whatsapp.net",
        "senderName": "Hugo Generoso",
        ...
    },
    "chat": {
        "phone": "+55 17 99131-7923",
        "name": "Hugo Generoso",
        ...
    },
    ...
}
"""

from agent import AgentContext, UserMessage, AgentContextType
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.print_style import PrintStyle
from initialize import initialize_agent
import logging
import re

logger = logging.getLogger(__name__)


class UazapiWebhook(ApiHandler):
    """
    Handle incoming UAZAPI webhooks.
    
    This is a native Agent Zero endpoint - no external adapter needed.
    Receives WhatsApp messages and routes them to the Catarina agent profile.
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return False  # Webhook endpoint - no web auth

    @classmethod
    def requires_csrf(cls) -> bool:
        return False  # Webhook endpoint - no CSRF

    @classmethod
    def requires_api_key(cls) -> bool:
        return False  # UAZAPI sends its own token, we trust the webhook URL

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        """Process incoming UAZAPI webhook."""
        
        # UAZAPI uses "EventType" (capitalized)
        event_type = input.get("EventType", "") or input.get("event", "")
        
        # Only process incoming messages
        if event_type not in ["messages", "messages.upsert"]:
            return {"ok": True, "ignored": True, "reason": f"Event type: {event_type}"}
        
        # Extract message data - UAZAPI puts it directly in "message" field
        message_data = input.get("message", {})
        chat_data = input.get("chat", {})
        
        if not message_data:
            # Fallback: try old format
            message_data = input.get("data", {}).get("message", {})
        
        # Check if message is from self (outgoing) - ignore FIRST
        from_me = message_data.get("fromMe", False)
        if from_me:
            return {"ok": True, "ignored": True, "reason": "From self"}
        
        # Get phone number from UAZAPI format
        # UAZAPI provides: chatid = "5517991317923@s.whatsapp.net"
        # or sender = "5517991317923@s.whatsapp.net"
        phone_raw = (
            message_data.get("chatid", "") or 
            message_data.get("sender", "") or
            message_data.get("from", "") or
            chat_data.get("wa_chatid", "")
        )
        
        # Clean phone number - remove @s.whatsapp.net, @c.us, @g.us
        phone = re.sub(r'@(s\.whatsapp\.net|c\.us|g\.us)$', '', phone_raw)
        
        if not phone:
            logger.warning("Webhook received without phone number")
            return {"ok": True, "ignored": True, "reason": "No phone"}
        
        # Get message text - UAZAPI uses both "text" and "content"
        text = (
            message_data.get("text", "") or
            message_data.get("content", "") or
            message_data.get("body", "") or
            message_data.get("conversation", "")
        )
        
        # Ensure text is a string (sometimes UAZAPI sends dict/object)
        if not isinstance(text, str):
            text = str(text) if text else ""
        
        # Handle button/list interactive responses
        if not text:
            button_id = message_data.get("buttonOrListid", "")
            if button_id:
                text = str(button_id)
        
        if not text:
            logger.info(f"No text in message from {phone[:6]}...")
            return {"ok": True, "ignored": True, "reason": "No text content"}
        
        # Get sender name for context
        sender_name = (
            message_data.get("senderName", "") or
            chat_data.get("name", "") or
            chat_data.get("wa_name", "") or
            "Unknown"
        )
        
        # Log incoming message
        PrintStyle(
            background_color="#25D366", font_color="white", bold=True, padding=True
        ).print(f"📱 WhatsApp: {sender_name} ({phone[-4:]})")
        PrintStyle(font_color="white", padding=False).print(f"> {str(text)[:100]}")
        
        try:
            # Get or create context for this phone number
            # Each WhatsApp user gets their own persistent context
            context = AgentContext.get(phone)
            
            if not context:
                # Create new context with Catarina profile
                config = initialize_agent()
                # Override profile to use Catarina
                config.profile = "catarina"
                
                context = AgentContext(
                    config=config,
                    id=phone,
                    name=f"WhatsApp: {sender_name}",
                    type=AgentContextType.USER,
                    set_current=True
                )
                PrintStyle().print(f"✨ Created new context for {sender_name}")
            else:
                AgentContext.set_current(phone)
            
            # Store phone in context data for whatsapp_send tool
            context.set_data("current_phone", phone)
            
            # Store sender name for personalization
            context.set_data("sender_name", sender_name)
            
            # Store original message data for reference
            context.set_data("last_message_data", message_data)
            
            # Log the message in context
            context.log.log(
                type="user",
                heading=f"WhatsApp: {sender_name}",
                content=text,
            )
            
            # Send message to agent's monologue loop
            user_msg = UserMessage(message=text)
            task = context.communicate(user_msg)
            
            # Wait for agent response
            result = await task.result()
            
            PrintStyle(
                background_color="#25D366", font_color="white", bold=True, padding=True
            ).print(f"✅ Response sent to {sender_name}")
            
            return {
                "ok": True,
                "context_id": phone,
                "sender_name": sender_name,
                "message_received": text[:50],
                "response": result
            }
            
        except Exception as e:
            logger.exception(f"Error processing message from {phone[:6]}...")
            PrintStyle.error(f"Webhook error: {str(e)}")
            return Response(
                f'{{"ok": false, "error": "{str(e)}"}}',
                status=500,
                mimetype="application/json"
            )
