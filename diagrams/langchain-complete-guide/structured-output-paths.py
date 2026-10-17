# Two routes from a model's reply to typed data: native structured output vs prompt + parser.
SPEC = {
    "title": "Two roads to structured data",
    "accent": "purple",
    "width": 1100, "height": 720,
    "bands": [
        {"y": 85, "h": 270, "label": "Native\nroute", "color": "purple", "tile": 130},
        {"y": 375, "h": 270, "label": "Parser\nroute", "color": "teal", "tile": 130},
    ],
    "nodes": {
        "schema1": {"x": 175, "y": 110, "w": 210, "h": 110, "icon": "📐", "label": "Schema", "sub": "TypedDict, Pydantic\nor JSON Schema", "color": "purple"},
        "wso": {"x": 430, "y": 110, "w": 250, "h": 110, "icon": "🧩", "label": "with_structured_output", "sub": "schema sent to the API\nas a tool or JSON schema", "color": "purple"},
        "api": {"x": 725, "y": 110, "w": 335, "h": 110, "icon": "🧠", "label": "Model API", "sub": "constrained to the schema\n(tool call or native JSON)", "color": "purple"},
        "out1": {"x": 725, "y": 245, "w": 335, "h": 90, "icon": "✅", "label": "dict or Pydantic object", "sub": "validated by the schema", "color": "green"},
        "raw": {"x": 430, "y": 245, "w": 250, "h": 90, "icon": "🧾", "label": "include_raw=True", "sub": "also returns the raw message\nand any parsing_error", "color": "gray"},
        "schema2": {"x": 175, "y": 400, "w": 210, "h": 110, "icon": "📐", "label": "Schema", "sub": "Pydantic model or\nResponseSchema list", "color": "teal"},
        "fmt": {"x": 430, "y": 400, "w": 250, "h": 110, "icon": "📝", "label": "Format instructions", "sub": "parser.get_format_instructions()\ngo into the prompt", "color": "teal"},
        "any": {"x": 725, "y": 400, "w": 335, "h": 110, "icon": "🤖", "label": "Any model", "sub": "even ones without tool calling\nreplies with text containing JSON", "color": "teal"},
        "parse": {"x": 725, "y": 535, "w": 335, "h": 90, "icon": "🔍", "label": "Output parser", "sub": "find JSON, parse, validate", "color": "teal"},
        "out2": {"x": 430, "y": 535, "w": 250, "h": 90, "icon": "✅", "label": "dict or object", "sub": "or OutputParserException", "color": "green"},
    },
    "edges": [
        {"from": "schema1", "to": "wso"},
        {"from": "wso", "to": "api"},
        {"from": "api", "to": "out1"},
        {"from": "schema2", "to": "fmt"},
        {"from": "fmt", "to": "any"},
        {"from": "any", "to": "parse"},
        {"from": "parse", "to": "out2"},
        {"from": "out1", "to": "raw"},
    ],
    "notes": [
        {"x": 618, "y": 685, "text": "Prefer the native route when the model supports it; use parsers for older or local models, or plain text.", "size": 15, "weight": 600, "color": "#5b3fa0"},
    ],
}
