### contact_lookup:
Look up patient information by CPF or phone number.

Use this tool when you need to find existing patient records.

#### Arguments:
* "cpf" (string, optional): Patient's CPF (11 digits, formatting will be removed)
* "phone" (string, optional): Patient's phone number

At least one of `cpf` or `phone` must be provided.

#### Usage Examples:

##### 1: Look up by CPF
```json
{
    "thoughts": [
        "Patient provided their CPF for identification.",
        "Let me look up their record."
    ],
    "tool_name": "contact_lookup",
    "tool_args": {
        "cpf": "123.456.789-00"
    }
}
```

##### 2: Look up by phone
```json
{
    "thoughts": [
        "I have the patient's phone number.",
        "Let me check if they are already registered."
    ],
    "tool_name": "contact_lookup",
    "tool_args": {
        "phone": "11999998888"
    }
}
```

#### Response Format:
If found, returns:
- Patient name
- Phone number
- Email (if available)

If not found, indicates this is likely a new patient.
