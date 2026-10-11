# What goes into one decision of an agent, who makes it, and what can happen next.
SPEC = {
    "title": "How an agent decides its next step",
    "accent": "amber",
    "width": 1100, "height": 720,
    "groups": [
        {"x": 30, "y": 95, "w": 280, "h": 440, "label": "What the model sees", "color": "blue"},
        {"x": 770, "y": 95, "w": 300, "h": 440, "label": "What it can choose", "color": "green"},
        {"x": 30, "y": 575, "w": 1040, "h": 120, "label": "What the harness (your code) checks before anything runs", "color": "amber"},
    ],
    "nodes": {
        "sys": {"x": 55, "y": 125, "w": 230, "h": 90, "icon": "📜", "label": "Instructions", "sub": "role, rules, when to stop", "color": "blue"},
        "tools": {"x": 55, "y": 235, "w": 230, "h": 90, "icon": "🧰", "label": "Tool menu", "sub": "name + description + inputs", "color": "blue"},
        "hist": {"x": 55, "y": 345, "w": 230, "h": 90, "icon": "🗒️", "label": "History so far", "sub": "goal, past actions, results", "color": "blue"},
        "ctx": {"x": 55, "y": 455, "w": 230, "h": 62, "label": "➕ Retrieved facts, memory", "color": "gray", "size": 14},
        "model": {"x": 400, "y": 230, "w": 270, "h": 200, "icon": "🧠", "label": "The model", "sub": "reads everything, then writes\nthe most likely good next step:\neither words or a tool call", "color": "amber"},
        "call": {"x": 795, "y": 125, "w": 250, "h": 90, "icon": "🛠️", "label": "Call a tool", "sub": "search_books(title=\"Godan\")", "color": "green"},
        "ask": {"x": 795, "y": 235, "w": 250, "h": 90, "icon": "🙋", "label": "Ask the user", "sub": "\"Which branch, Andheri or Thane?\"", "color": "green"},
        "plan": {"x": 795, "y": 345, "w": 250, "h": 80, "icon": "🗺️", "label": "Write or update a plan", "color": "green"},
        "stop": {"x": 795, "y": 445, "w": 250, "h": 72, "label": "✅ Answer and stop", "color": "green"},
        "allowed": {"x": 60, "y": 610, "w": 220, "h": 66, "label": "🛡️ Is this tool allowed?", "color": "amber", "size": 15},
        "approve": {"x": 310, "y": 610, "w": 230, "h": 66, "label": "🙋 Needs human approval?", "color": "amber", "size": 15},
        "budget": {"x": 570, "y": 610, "w": 230, "h": 66, "label": "⏱️ Steps or money left?", "color": "amber", "size": 15},
        "valid": {"x": 830, "y": 610, "w": 215, "h": 66, "label": "🔍 Inputs valid?", "color": "amber", "size": 15},
    },
    "edges": [
        {"from": "sys", "to": "model", "to_side": "left"},
        {"from": "tools", "to": "model", "to_side": "left"},
        {"from": "hist", "to": "model", "to_side": "left"},
        {"from": "model", "to": "call", "from_side": "right", "to_side": "left"},
        {"from": "model", "to": "ask", "from_side": "right", "to_side": "left"},
        {"from": "model", "to": "plan", "from_side": "right", "to_side": "left"},
        {"from": "model", "to": "stop", "from_side": "right", "to_side": "left"},
    ],
    "notes": [
        {"x": 535, "y": 470, "text": "The model decides WHAT to do.", "weight": 700, "color": "#9a6412", "size": 15},
        {"x": 535, "y": 492, "text": "Your loop decides WHEN to ask it and WHETHER it may run.", "size": 13},
    ],
}
