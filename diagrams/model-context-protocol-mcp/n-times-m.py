# The fragmentation problem: N apps x M tools custom connectors, versus N + M with one shared protocol.
SPEC = {
    "title": "From N x M connectors to N + M",
    "accent": "coral",
    "width": 1100, "height": 600,
    "groups": [
        {"x": 30, "y": 100, "w": 500, "h": 440, "label": "Before: every pair needs its own glue", "color": "coral"},
        {"x": 570, "y": 100, "w": 500, "h": 440, "label": "After: everyone speaks MCP", "color": "green"},
    ],
    "nodes": {
        "a1": {"x": 55, "y": 140, "w": 140, "h": 60, "label": "💬 Chat app", "color": "blue", "size": 14},
        "a2": {"x": 55, "y": 260, "w": 140, "h": 60, "label": "🧑‍💻 Code editor", "color": "blue", "size": 14},
        "a3": {"x": 55, "y": 380, "w": 140, "h": 60, "label": "🤖 Your agent", "color": "blue", "size": 14},
        "t1": {"x": 365, "y": 125, "w": 140, "h": 56, "label": "🐙 GitHub", "color": "gray", "size": 14},
        "t2": {"x": 365, "y": 215, "w": 140, "h": 56, "label": "🗄️ Postgres", "color": "gray", "size": 14},
        "t3": {"x": 365, "y": 305, "w": 140, "h": 56, "label": "📅 Calendar", "color": "gray", "size": 14},
        "t4": {"x": 365, "y": 395, "w": 140, "h": 56, "label": "💳 Payments", "color": "gray", "size": 14},
        "b1": {"x": 595, "y": 140, "w": 140, "h": 60, "label": "💬 Chat app", "color": "blue", "size": 14},
        "b2": {"x": 595, "y": 260, "w": 140, "h": 60, "label": "🧑‍💻 Code editor", "color": "blue", "size": 14},
        "b3": {"x": 595, "y": 380, "w": 140, "h": 60, "label": "🤖 Your agent", "color": "blue", "size": 14},
        "hub": {"x": 770, "y": 230, "w": 110, "h": 120, "icon": "🔌", "label": "MCP", "sub": "one protocol", "color": "green"},
        "u1": {"x": 915, "y": 125, "w": 140, "h": 56, "label": "🐙 GitHub", "color": "gray", "size": 14},
        "u2": {"x": 915, "y": 215, "w": 140, "h": 56, "label": "🗄️ Postgres", "color": "gray", "size": 14},
        "u3": {"x": 915, "y": 305, "w": 140, "h": 56, "label": "📅 Calendar", "color": "gray", "size": 14},
        "u4": {"x": 915, "y": 395, "w": 140, "h": 56, "label": "💳 Payments", "color": "gray", "size": 14},
    },
    "edges": [
        {"from": a, "to": t, "from_side": "right", "to_side": "left", "solid": True}
        for a in ("a1", "a2", "a3") for t in ("t1", "t2", "t3", "t4")
    ] + [
        {"from": b, "to": "hub", "from_side": "right", "to_side": "left", "solid": True} for b in ("b1", "b2", "b3")
    ] + [
        {"from": "hub", "to": u, "from_side": "right", "to_side": "left", "solid": True} for u in ("u1", "u2", "u3", "u4")
    ],
    "notes": [
        {"x": 280, "y": 500, "text": "3 apps x 4 tools = 12 integrations", "size": 16, "weight": 700, "color": "#b2442f"},
        {"x": 820, "y": 500, "text": "3 clients + 4 servers = 7 pieces", "size": 16, "weight": 700, "color": "#2e7d4f"},
        {"x": 550, "y": 575, "text": "Add a 5th tool: 3 new connectors on the left, 1 new server on the right.", "size": 14},
    ],
}
