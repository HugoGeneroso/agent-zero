### knowledge_search:
Search the clinic's knowledge base for procedures, prices, and information.

Use this tool when:
- Patient asks about a specific procedure
- Patient describes an aesthetic concern (recommend appropriate treatment)
- Patient asks about prices
- You need accurate information about the clinic

#### Arguments:
* "query" (string, required): What to search for (procedure name, concern, or question)

#### Usage Examples:

##### 1: Search for a procedure
```json
{
    "thoughts": [
        "Patient asked about lip filler.",
        "I need to find information about this procedure."
    ],
    "tool_name": "knowledge_search",
    "tool_args": {
        "query": "preenchimento labial"
    }
}
```

##### 2: Find treatment for a concern
```json
{
    "thoughts": [
        "Patient mentioned sagging skin on their face.",
        "I should search for treatments that address this concern."
    ],
    "tool_name": "knowledge_search",
    "tool_args": {
        "query": "flacidez facial tratamento"
    }
}
```

##### 3: Price inquiry
```json
{
    "thoughts": [
        "Patient wants to know botox pricing.",
        "Let me search for this information."
    ],
    "tool_name": "knowledge_search",
    "tool_args": {
        "query": "botox preço valor"
    }
}
```

#### Response Format:
Returns relevant documents with:
- Title
- Content (procedure description, pricing, etc.)

Use this information to craft a helpful response via `whatsapp_send`.
