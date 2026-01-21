"""
UAZAPI Webhook Endpoint for Agent Zero.

This API endpoint receives WhatsApp webhooks from UAZAPI and routes them
to Agent Zero's monologue loop for processing.
"""

from agent import AgentContext, UserMessage, AgentContextType
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.print_style import PrintStyle
from initialize import initialize_agent
import logging

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
        return False  # UAZAPI sends its own signature, we trust the webhook URL

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        """Process incoming UAZAPI webhook."""
        
        # Extract event type
        event_type = input.get("event", "")
        
        # Only process incoming messages
        if event_type != "messages.upsert":
            return {"ok": True, "ignored": True, "reason": f"Event type: {event_type}"}
        
        # Extract message data
        # UAZAPI format: data.message contains the message object
        message_data = input.get("data", {}).get("message", {})
        
        # Get phone number (remove @c.us suffix if present)
        phone_raw = message_data.get("from", "") or message_data.get("key", {}).get("remoteJid", "")
        phone = phone_raw.replace("@c.us", "").replace("@g.us", "")
        
        if not phone:
            logger.warning("Webhook received without phone number")
            return {"ok": True, "ignored": True, "reason": "No phone"}
        
        # Get message text
        # UAZAPI can have text in different places depending on message type
        text = (
            message_data.get("body", "") or
            message_data.get("text", "") or
            message_data.get("conversation", "") or
            message_data.get("message", {}).get("conversation", "") or
            message_data.get("message", {}).get("extendedTextMessage", {}).get("text", "")
        )
        
        # Handle interactive message responses (button/list selections)
        if not text:
            # Check for button response
            button_response = message_data.get("buttonsResponseMessage", {})
            if button_response:
                text = button_response.get("selectedButtonId", "") or button_response.get("selectedDisplayText", "")
            
            # Check for list response
            list_response = message_data.get("listResponseMessage", {})
            if list_response:
                text = list_response.get("singleSelectReply", {}).get("selectedRowId", "") or list_response.get("title", "")
        
        if not text:
            logger.info(f"No text in message from {phone[:6]}...")
            return {"ok": True, "ignored": True, "reason": "No text content"}
        
        # Check if message is from self (outgoing) - ignore
        from_me = message_data.get("key", {}).get("fromMe", False) or message_data.get("fromMe", False)
        if from_me:
            return {"ok": True, "ignored": True, "reason": "From self"}
        
        # Log incoming message
        PrintStyle(
            background_color="#25D366", font_color="white", bold=True, padding=True
        ).print(f"WhatsApp message from {phone[:6]}...")
        PrintStyle(font_color="white", padding=False).print(f"> {text[:100]}")
        
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
                    name=f"WhatsApp: {phone}",
                    type=AgentContextType.USER,
                    set_current=True
                )
                PrintStyle().print(f"Created new context for {phone[:6]}...")
            else:
                AgentContext.set_current(phone)
            
            # Store phone in context data for whatsapp_send tool
            context.set_data("current_phone", phone)
            
            # Store original message data for reference
            context.set_data("last_message_data", message_data)
            
            # Log the message in context
            context.log.log(
                type="user",
                heading="WhatsApp message",
                content=text,
            )
            
            # Send message to agent's monologue loop
            user_msg = UserMessage(message=text)
            task = context.communicate(user_msg)
            
            # Wait for agent response
            result = await task.result()
            
            return {
                "ok": True,
                "context_id": phone,
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
