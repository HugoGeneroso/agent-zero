### calendar_search:
Search for available appointment slots in Dra. Thais's calendar.

Use this tool when the patient wants to schedule an appointment or asks about availability.

#### Arguments:
* "start_date" (string, optional): Start date in YYYY-MM-DD format, or "today" (default)
* "days" (integer, optional): Number of days to search ahead (default: 14)
* "procedure_type" (string, optional): Type of procedure for context (e.g., "avaliação", "botox")

#### Usage Examples:

##### 1: Find next available slots
```json
{
    "thoughts": [
        "Patient wants to schedule an evaluation.",
        "I need to check the calendar for available times."
    ],
    "tool_name": "calendar_search",
    "tool_args": {
        "procedure_type": "avaliação"
    }
}
```

##### 2: Search specific week
```json
{
    "thoughts": [
        "Patient asked about availability next week.",
        "I should search starting from next Monday."
    ],
    "tool_name": "calendar_search",
    "tool_args": {
        "start_date": "2026-01-27",
        "days": 5,
        "procedure_type": "botox"
    }
}
```

#### Response Format:
The tool returns a list of available slots with:
- Day of week (Segunda, Terça, etc.)
- Date (DD/MM/YYYY)
- Time (HH:MM)
- Formatted string for easy display

After receiving results, use `whatsapp_send` to present the options to the patient.
