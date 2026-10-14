# The MCP lifecycle in both eras: the stateless 2026-07-28 model and the older initialize handshake.
SPEC = {
    "title": "The MCP lifecycle: agree, operate, stop",
    "accent": "teal",
    "width": 1100, "height": 600,
    "bands": [
        {"y": 85, "h": 230, "label": "Modern\n(2026)", "color": "teal", "tile": 130},
        {"y": 335, "h": 230, "label": "Legacy\n(2025 and\nearlier)", "color": "gray", "tile": 130},
    ],
    "nodes": {
        "disc": {"x": 175, "y": 110, "w": 200, "h": 105, "icon": "🔎", "label": "server/discover", "sub": "optional: versions,\ncapabilities, instructions", "color": "teal"},
        "req": {"x": 415, "y": 110, "w": 230, "h": 105, "icon": "📨", "label": "Any request", "sub": "carries version and\ncapabilities in _meta", "color": "teal"},
        "op": {"x": 685, "y": 110, "w": 190, "h": 105, "icon": "⚙️", "label": "Operate", "sub": "each request\nstands alone", "color": "teal"},
        "stop": {"x": 915, "y": 110, "w": 160, "h": 105, "icon": "🔚", "label": "Stop", "sub": "close stdin, or\njust stop POSTing", "color": "teal"},
        "err": {"x": 300, "y": 235, "w": 460, "h": 62, "label": "↩️ -32022 Unsupported version: pick one from data.supported, retry", "color": "amber", "size": 14},
        "init": {"x": 175, "y": 360, "w": 200, "h": 105, "icon": "🤝", "label": "initialize", "sub": "propose version,\nexchange capabilities", "color": "gray"},
        "ack": {"x": 415, "y": 360, "w": 230, "h": 105, "icon": "✅", "label": "notifications/\ninitialized", "sub": "client is ready", "color": "gray"},
        "sess": {"x": 685, "y": 360, "w": 190, "h": 105, "icon": "🧷", "label": "Session", "sub": "server remembers\nversion + capabilities", "color": "gray"},
        "close": {"x": 915, "y": 360, "w": 160, "h": 105, "icon": "🔚", "label": "Close", "sub": "close stdin, or\nHTTP DELETE", "color": "gray"},
    },
    "edges": [
        {"from": "disc", "to": "req", "solid": True},
        {"from": "req", "to": "op", "solid": True},
        {"from": "op", "to": "stop", "solid": True},
        {"from": "req", "to": "err", "from_side": "bottom", "to_side": "top", "both": True},
        {"from": "init", "to": "ack", "solid": True},
        {"from": "ack", "to": "sess", "solid": True},
        {"from": "sess", "to": "close", "solid": True},
    ],
    "notes": [
        {"x": 625, "y": 492, "text": "Dual-era clients probe with server/discover first; any non-modern error means: fall back to initialize.", "size": 13},
        {"x": 625, "y": 515, "text": "Dual-era servers answer both: _meta on a request means modern, an initialize request means legacy.", "size": 13},
        {"x": 625, "y": 548, "text": "Same messages for tools, resources and prompts in both eras. Only how they agree differs.", "size": 14, "weight": 700, "color": "#1f766d"},
    ],
}
