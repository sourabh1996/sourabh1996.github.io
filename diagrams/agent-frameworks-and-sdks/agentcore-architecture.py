# A Strands agent deployed on Amazon Bedrock AgentCore, with the managed services around it.
SPEC = {
    "title": "A Strands agent running on Bedrock AgentCore",
    "accent": "coral",
    "width": 1100, "height": 660,
    "groups": [
        {"x": 300, "y": 85, "w": 480, "h": 300, "label": "AgentCore Runtime (isolated session)", "color": "coral"},
        {"x": 30, "y": 420, "w": 1040, "h": 215, "label": "AgentCore managed services", "color": "gray"},
    ],
    "nodes": {
        "user": {"x": 40, "y": 160, "w": 200, "h": 110, "icon": "🙋", "label": "User or app", "sub": "POST /invocations", "color": "blue"},
        "entry": {"x": 320, "y": 125, "w": 200, "h": 100, "icon": "🚪", "label": "@app.entrypoint", "sub": "BedrockAgentCoreApp", "color": "coral"},
        "agent": {"x": 555, "y": 125, "w": 200, "h": 100, "icon": "🧵", "label": "Strands Agent", "sub": "model-driven loop", "color": "coral"},
        "tools": {"x": 320, "y": 250, "w": 200, "h": 110, "icon": "🧰", "label": "@tool functions", "sub": "plus MCP tools", "color": "coral"},
        "model": {"x": 555, "y": 250, "w": 200, "h": 110, "icon": "🧠", "label": "Model provider", "sub": "Bedrock, Anthropic,\nOpenAI, Ollama", "color": "coral"},
        "obs": {"x": 840, "y": 160, "w": 220, "h": 110, "icon": "📈", "label": "Observability", "sub": "OpenTelemetry traces", "color": "green"},
        "mem": {"x": 55, "y": 465, "w": 180, "h": 145, "icon": "🧠", "label": "Memory", "sub": "short-term turns,\nlong-term facts", "color": "purple"},
        "gw": {"x": 255, "y": 465, "w": 180, "h": 145, "icon": "🔗", "label": "Gateway", "sub": "APIs and Lambdas\nturned into\nMCP tools", "color": "purple"},
        "id": {"x": 455, "y": 465, "w": 180, "h": 145, "icon": "🔐", "label": "Identity", "sub": "who the agent acts\nfor; OAuth to\nother services", "color": "purple"},
        "code": {"x": 655, "y": 465, "w": 180, "h": 145, "icon": "🐍", "label": "Code\nInterpreter", "sub": "sandboxed code", "color": "purple"},
        "browser": {"x": 855, "y": 465, "w": 195, "h": 145, "icon": "🌐", "label": "Browser", "sub": "cloud web\nautomation", "color": "purple"},
    },
    "edges": [
        {"from": "user", "to": "entry", "label": "prompt"},
        {"from": "entry", "to": "agent"},
        {"from": "agent", "to": "model", "from_side": "bottom", "to_side": "top"},
        {"from": "agent", "to": "tools", "from_side": "left", "to_side": "right", "via": [(543, 175), (543, 305)]},
        {"from": "agent", "to": "obs", "label": "spans"},
        {"from": "tools", "to": "gw", "from_side": "bottom", "to_side": "top", "via": [(430, 395), (345, 395)]},
    ],
    "notes": [
        {"x": 550, "y": 650, "text": "Any framework can run inside the Runtime: Strands, LangGraph, CrewAI or your own loop.", "size": 13},
    ],
}
