# The three kinds of model interface in LangChain, with what goes in and what comes out.
SPEC = {
    "title": "Three kinds of model, one family of interfaces",
    "accent": "blue",
    "width": 1100, "height": 700,
    "bands": [
        {"y": 85, "h": 175, "label": "Chat\nmodel", "color": "blue", "tile": 135},
        {"y": 275, "h": 175, "label": "LLM\n(text)", "color": "gray", "tile": 135},
        {"y": 465, "h": 175, "label": "Embedding\nmodel", "color": "green", "tile": 135},
    ],
    "nodes": {
        "cin": {"x": 180, "y": 105, "w": 250, "h": 135, "icon": "💬", "label": "List of messages", "sub": "System: you are a TTE helper\nHuman: is 12951 on time?", "color": "blue"},
        "cm": {"x": 540, "y": 115, "w": 200, "h": 115, "icon": "🧠", "label": "ChatAnthropic", "sub": "ChatOpenAI, ChatOllama…", "color": "blue"},
        "cout": {"x": 800, "y": 105, "w": 260, "h": 135, "icon": "📨", "label": "AIMessage", "sub": "text, tool calls,\ntoken usage, metadata", "color": "blue"},
        "lin": {"x": 180, "y": 295, "w": 250, "h": 135, "icon": "📝", "label": "One string", "sub": "\"The capital of\nKerala is\"", "color": "gray"},
        "lm": {"x": 540, "y": 305, "w": 200, "h": 115, "icon": "⚙️", "label": "LLM class", "sub": "older completion style", "color": "gray"},
        "lout": {"x": 800, "y": 295, "w": 260, "h": 135, "icon": "📝", "label": "One string", "sub": "\" Thiruvananthapuram.\"", "color": "gray"},
        "ein": {"x": 180, "y": 485, "w": 250, "h": 135, "icon": "🔤", "label": "Text", "sub": "\"refund for a late train\"", "color": "green"},
        "em": {"x": 540, "y": 495, "w": 200, "h": 115, "icon": "📐", "label": "Embeddings", "sub": "Voyage, OpenAI, HF", "color": "green"},
        "eout": {"x": 800, "y": 485, "w": 260, "h": 135, "icon": "🔢", "label": "Vector of numbers", "sub": "[0.12, -0.48, 0.31, …]\nsimilar meaning, nearby", "color": "green"},
    },
    "edges": [
        {"from": "cin", "to": "cm", "label": "invoke"},
        {"from": "cm", "to": "cout"},
        {"from": "lin", "to": "lm", "label": "invoke"},
        {"from": "lm", "to": "lout"},
        {"from": "ein", "to": "em", "label": "embed"},
        {"from": "em", "to": "eout"},
    ],
    "notes": [
        {"x": 610, "y": 668, "text": "Use chat models for generating text; embeddings for search; LLM classes mostly in older code.", "size": 15, "weight": 600, "color": "#2f5fb3"},
    ],
}
