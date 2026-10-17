# How A2A and MCP fit together: A2A connects agents to each other, MCP connects each agent to its own tools.
SPEC = {
    "title": "A2A across, MCP down",
    "accent": "blue",
    "width": 1100, "height": 790,
    "nodes": {
        "user": {"x": 420, "y": 90, "w": 260, "h": 80, "icon": "🙋", "label": "Traveller", "sub": "in the trip app", "color": "gray", "size": 17},
        "planner": {"x": 400, "y": 230, "w": 300, "h": 120, "icon": "🧭", "label": "Trip planner agent", "sub": "your team, A2A client", "color": "purple"},
        "maps": {"x": 800, "y": 245, "w": 260, "h": 90, "label": "🗺️ Maps MCP server", "sub": "a tool the planner controls", "color": "gray", "size": 15},
        "rail": {"x": 60, "y": 440, "w": 300, "h": 120, "icon": "🚆", "label": "Rail agent", "sub": "rail company, A2A server", "color": "teal"},
        "hotel": {"x": 740, "y": 440, "w": 300, "h": 120, "icon": "🏨", "label": "Hotel agent", "sub": "hotel chain, A2A server", "color": "teal"},
        "seat": {"x": 30, "y": 650, "w": 165, "h": 90, "label": "Seat DB", "sub": "MCP tool", "color": "gray", "size": 15},
        "fare": {"x": 220, "y": 650, "w": 165, "h": 90, "label": "Fare API", "sub": "MCP tool", "color": "gray", "size": 15},
        "rooms": {"x": 715, "y": 650, "w": 165, "h": 90, "label": "Rooms DB", "sub": "MCP tool", "color": "gray", "size": 15},
        "pay": {"x": 905, "y": 650, "w": 165, "h": 90, "label": "Payments", "sub": "MCP tool", "color": "gray", "size": 15},
        "legend": {"x": 420, "y": 440, "w": 260, "h": 300, "icon": "🧩", "label": "Rule of thumb",
                   "sub": "A2A (across):\ndelegate a goal to\nan agent you don't control\n\nMCP (down):\ncall a tool or read data\nyour agent controls", "color": "amber", "size": 17},
    },
    "edges": [
        {"from": "user", "to": "planner", "label": "app UI"},
        {"from": "planner", "to": "maps", "label": "MCP", "from_side": "right", "to_side": "left"},
        {"from": "planner", "to": "rail", "label": "A2A", "both": True, "from_side": "left", "to_side": "top"},
        {"from": "planner", "to": "hotel", "label": "A2A", "both": True, "from_side": "bottom", "to_side": "top"},
        {"from": "rail", "to": "seat", "label": "MCP"},
        {"from": "rail", "to": "fare", "label": "MCP"},
        {"from": "hotel", "to": "rooms", "label": "MCP"},
        {"from": "hotel", "to": "pay", "label": "MCP"},
    ],
}
