# What every vendor agent SDK packages, and the name each SDK gives it.
SPEC = {
    "title": "One anatomy, five vendor SDKs",
    "accent": "blue",
    "width": 1100, "height": 700,
    "groups": [
        {"x": 30, "y": 85, "w": 1040, "h": 300, "label": "What every SDK gives you around the model", "color": "blue"},
        {"x": 30, "y": 410, "w": 1040, "h": 270, "label": "What each vendor adds on top", "color": "gray"},
    ],
    "nodes": {
        "agent": {"x": 420, "y": 165, "w": 260, "h": 140, "icon": "🤖", "label": "Agent", "sub": "model + instructions\n+ tools + output type", "color": "blue"},
        "runner": {"x": 60, "y": 120, "w": 250, "h": 80, "icon": "🔁", "label": "Runner / loop", "sub": "calls model, runs tools, stops", "color": "blue"},
        "tools": {"x": 60, "y": 212, "w": 250, "h": 80, "icon": "🧰", "label": "Tools + MCP", "sub": "functions and servers", "color": "blue"},
        "guard": {"x": 60, "y": 303, "w": 250, "h": 70, "icon": "🛡️", "label": "Guardrails, permissions", "color": "blue", "size": 15},
        "session": {"x": 790, "y": 120, "w": 250, "h": 80, "icon": "🗂️", "label": "Sessions / memory", "sub": "history across turns", "color": "blue"},
        "multi": {"x": 790, "y": 212, "w": 250, "h": 80, "icon": "👥", "label": "Multi-agent", "sub": "handoffs, subagents, graphs", "color": "blue"},
        "trace": {"x": 790, "y": 303, "w": 250, "h": 70, "icon": "📈", "label": "Tracing and evals", "color": "blue", "size": 15},
        "c": {"x": 55, "y": 450, "w": 190, "h": 205, "icon": "🟠", "label": "Claude\nAgent SDK", "sub": "built-in file, shell\nand web tools;\nhooks; skills;\nsubagents", "color": "amber"},
        "o": {"x": 260, "y": 450, "w": 190, "h": 205, "icon": "🟢", "label": "OpenAI\nAgents SDK", "sub": "handoffs;\ntripwire guardrails;\nsandbox agents;\nvoice", "color": "green"},
        "g": {"x": 465, "y": 450, "w": 190, "h": 205, "icon": "🔵", "label": "Google\nADK", "sub": "graph Workflow;\nadk web dev UI;\nbuilt-in evals;\nAgent Engine", "color": "blue"},
        "m": {"x": 670, "y": 450, "w": 190, "h": 205, "icon": "🟦", "label": "Microsoft\nAgent Framework", "sub": "typed workflows;\nMagentic, group chat;\n.NET + Python;\nFoundry", "color": "purple"},
        "a": {"x": 875, "y": 450, "w": 175, "h": 205, "icon": "🟧", "label": "Strands +\nAgentCore", "sub": "model-driven loop;\nmanaged runtime,\nmemory, gateway,\nidentity", "color": "coral"},
    },
    "edges": [
        {"from": "runner", "to": "agent", "to_side": "left"},
        {"from": "tools", "to": "agent", "to_side": "left"},
        {"from": "guard", "to": "agent", "to_side": "left"},
        {"from": "session", "to": "agent", "to_side": "right"},
        {"from": "multi", "to": "agent", "to_side": "right"},
        {"from": "trace", "to": "agent", "to_side": "right"},
    ],
    "notes": [
        {"x": 550, "y": 345, "text": "Same loop as your hand-built agent", "weight": 700, "color": "#2f5fb3", "size": 14},
    ],
}
