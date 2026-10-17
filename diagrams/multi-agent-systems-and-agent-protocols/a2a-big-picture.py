# The A2A protocol at a glance: discovery, a task-based exchange, and opaque agents on both sides.
SPEC = {
    "title": "A2A: how two independent agents work together",
    "accent": "blue",
    "width": 1100, "height": 820,
    "groups": [
        {"x": 30, "y": 95, "w": 300, "h": 560, "label": "Client agent (your team)", "color": "purple"},
        {"x": 770, "y": 95, "w": 300, "h": 560, "label": "Remote agent (their team)", "color": "teal"},
    ],
    "nodes": {
        "user": {"x": 70, "y": 130, "w": 220, "h": 95, "icon": "🙋", "label": "User", "sub": "\"Plan my Pune trip\"", "color": "gray"},
        "client": {"x": 70, "y": 260, "w": 220, "h": 140, "icon": "🧭", "label": "Trip planner", "sub": "built with LangGraph\nacts as A2A client", "color": "purple"},
        "ctools": {"x": 70, "y": 440, "w": 220, "h": 85, "label": "🧰 Its own tools (MCP)", "color": "gray", "size": 15},
        "cnote": {"x": 70, "y": 555, "w": 220, "h": 80, "label": "Sees only the card,\ntasks and artifacts", "color": "gray", "size": 14},
        "card": {"x": 395, "y": 105, "w": 310, "h": 120, "icon": "🪪", "label": "Step 1: read the Agent Card",
                 "sub": "GET /.well-known/agent-card.json\nname, skills, URL, auth", "color": "blue"},
        "send": {"x": 395, "y": 270, "w": 310, "h": 90, "label": "Step 2: SendMessage", "sub": "message with parts (text, file, data)", "color": "blue", "size": 17},
        "task": {"x": 395, "y": 385, "w": 310, "h": 90, "label": "Step 3: track the Task", "sub": "id, contextId, state: WORKING ...", "color": "blue", "size": 17},
        "art": {"x": 395, "y": 500, "w": 310, "h": 90, "label": "Step 4: receive Artifacts", "sub": "results, streamed, polled or pushed", "color": "blue", "size": 17},
        "remote": {"x": 810, "y": 260, "w": 220, "h": 140, "icon": "🚆", "label": "Rail booking agent", "sub": "built with Google ADK\nacts as A2A server", "color": "teal"},
        "rtools": {"x": 810, "y": 440, "w": 220, "h": 85, "label": "🧰 Its own tools (MCP)", "color": "gray", "size": 15},
        "rnote": {"x": 810, "y": 555, "w": 220, "h": 80, "label": "Prompts, memory and\ntools stay private", "color": "gray", "size": 14},
        "bind": {"x": 230, "y": 690, "w": 640, "h": 90, "icon": "🔌", "label": "Same messages over JSON-RPC, gRPC or HTTP+JSON",
                 "sub": "HTTPS + auth declared in the card (OAuth 2.0, API key, mTLS ...)", "color": "amber"},
    },
    "edges": [
        {"from": "user", "to": "client"},
        {"from": "client", "to": "send", "both": True, "label": "A2A", "from_side": "right", "to_side": "left"},
        {"from": "send", "to": "remote", "both": True, "label": "A2A", "from_side": "right", "to_side": "left"},
        {"from": "client", "to": "ctools", "both": True},
        {"from": "remote", "to": "rtools", "both": True},
    ],
}
