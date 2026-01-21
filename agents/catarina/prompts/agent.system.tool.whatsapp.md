### whatsapp_send:
Send a WhatsApp message to the current patient.

**IMPORTANT**: This is the ONLY way to respond to the patient. Your thoughts and tool results are NOT visible to them. You MUST use this tool to send your response.

#### Arguments:
* "message" (string, required): The text message to send to the patient
* "type" (string, optional): Message type - "text" (default) or "menu"
* "menu" (object, optional): Menu configuration when type is "menu"
  * "choices" (array): List of menu options in format "Title|id" or "Title|id|Description"
  * "menu_type" (string): "list" or "button"
  * "button_text" (string): Text for the menu button (e.g., "Ver opções")

#### Usage Examples:

##### 1: Simple text response
```json
{
    "thoughts": [
        "The patient asked about botox.",
        "I found information about the procedure.",
        "I need to send a helpful response."
    ],
    "tool_name": "whatsapp_send",
    "tool_args": {
        "message": "Olá! O Botox (Dysport) é excelente para suavizar rugas de expressão. A Dra. Thais utiliza produtos de alta qualidade para resultados naturais. Gostaria de agendar uma avaliação? 💆‍♀️"
    }
}
```

##### 2: Greeting response
```json
{
    "thoughts": [
        "This is a new patient greeting me.",
        "I should welcome them and ask how I can help."
    ],
    "tool_name": "whatsapp_send",
    "tool_args": {
        "message": "Olá! Bem-vindo(a) à clínica da Dra. Thais Tiberio! 😊 Sou a Catarina, como posso ajudar você hoje?"
    }
}
```

##### 3: Offering appointment options (menu)
```json
{
    "thoughts": [
        "I found available slots.",
        "I should present them as a menu for easy selection."
    ],
    "tool_name": "whatsapp_send",
    "tool_args": {
        "message": "Encontrei esses horários disponíveis para sua avaliação:",
        "type": "menu",
        "menu": {
            "menu_type": "list",
            "button_text": "Ver horários",
            "choices": [
                "Segunda 10/02 às 10:00|slot_1",
                "Terça 11/02 às 14:30|slot_2",
                "Quarta 12/02 às 09:00|slot_3"
            ]
        }
    }
}
```
