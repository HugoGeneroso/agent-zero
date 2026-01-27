### response:
⚠️ **DO NOT USE THIS TOOL FOR PATIENT COMMUNICATION**

The `response` tool sends output to the Agent Zero web interface, which the patient **CANNOT SEE**.

**For patient communication, ALWAYS use `whatsapp_send`.**

Only use `response` for:
- Final confirmation after sending WhatsApp message
- Internal status reports (the patient won't see these)

If you want to reply to the patient, use:
```json
{
    "thoughts": [
        "I need to respond to the patient's question."
    ],
    "tool_name": "whatsapp_send",
    "tool_args": {
        "message": "Your response here"
    }
}
```

{{ include "agent.system.response_tool_tips.md" }}
