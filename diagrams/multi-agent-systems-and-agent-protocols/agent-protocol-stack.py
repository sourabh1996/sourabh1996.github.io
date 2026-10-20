# The open agent standards around one agent: who each one connects, and who stewards it.
SPEC = {
    "title": "The open standards map: one agent, many connections",
    "accent": "blue",
    "width": 1100, "height": 780,
    "groups": [
        {"x": 25, "y": 85, "w": 1050, "h": 175, "label": "Facing people", "color": "purple"},
        {"x": 25, "y": 290, "w": 1050, "h": 190, "label": "The agent and its peers", "color": "teal"},
        {"x": 25, "y": 510, "w": 1050, "h": 175, "label": "Facing tools, data and code", "color": "amber"},
    ],
    "nodes": {
        "agui": {"x": 55, "y": 120, "w": 310, "h": 115, "label": "AG-UI", "sub": "agent ↔ app frontend\nevent stream · CopilotKit-led", "color": "purple", "size": 17},
        "acp": {"x": 395, "y": 120, "w": 310, "h": 115, "label": "ACP (Agent Client Protocol)", "sub": "coding agent ↔ editor\nJSON-RPC on stdio · Zed-led", "color": "purple", "size": 17},
        "genui": {"x": 735, "y": 120, "w": 310, "h": 115, "label": "A2UI · MCP Apps", "sub": "what the UI looks like\nGoogle-led · MCP extension", "color": "purple", "size": 17},
        "agent": {"x": 395, "y": 325, "w": 310, "h": 130, "icon": "🤖", "label": "Your agent", "sub": "model + loop + memory", "color": "gray", "size": 18},
        "a2a": {"x": 55, "y": 325, "w": 310, "h": 130, "label": "A2A", "sub": "agent ↔ agent, across teams\nand companies\nLinux Foundation project", "color": "teal", "size": 17},
        "peer": {"x": 735, "y": 325, "w": 310, "h": 130, "icon": "🤝", "label": "Other agents", "sub": "found through Agent Cards", "color": "teal", "size": 17},
        "mcp": {"x": 55, "y": 545, "w": 470, "h": 115, "label": "MCP (+ MCP Apps extension)", "sub": "agent ↔ tools, data and prompts\nAgentic AI Foundation (AAIF)", "color": "amber", "size": 17},
        "agentsmd": {"x": 575, "y": 545, "w": 470, "h": 115, "label": "AGENTS.md", "sub": "repository ↔ coding agent: how to build,\ntest and behave · AAIF", "color": "amber", "size": 17},
    },
    "edges": [
        {"from": "a2a", "to": "agent", "from_side": "right", "to_side": "left"},
        {"from": "agent", "to": "peer", "from_side": "right", "to_side": "left"},
    ],
    "notes": [
        {"x": 550, "y": 720, "text": "AAIF (Linux Foundation, Dec 2025) launched with MCP, goose and AGENTS.md. A2A is a separate Linux Foundation project.",
         "size": 14, "weight": 600, "color": "#1f2328"},
        {"x": 550, "y": 748, "text": "None of these replace each other: a real product often uses four or five of them at once.", "size": 13},
    ],
}
