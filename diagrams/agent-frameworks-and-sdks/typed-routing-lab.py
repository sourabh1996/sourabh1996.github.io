# Architecture of the Module 4 lab: a typed routing layer in front of an agent.
SPEC = {
    "title": "Lab: a typed routing layer in front of an agent",
    "accent": "purple",
    "width": 1100, "height": 520,
    "groups": [
        {"x": 230, "y": 75, "w": 620, "h": 360, "label": "LangGraph StateGraph", "color": "purple"},
    ],
    "nodes": {
        "ticket": {"x": 30, "y": 120, "w": 170, "h": 110, "icon": "🎫", "label": "Ticket", "sub": "customer message", "color": "blue"},
        "decide": {"x": 260, "y": 120, "w": 190, "h": 110, "icon": "⚡", "label": "decide", "sub": "decision model;\nanswers checked\nby Pydantic", "color": "teal"},
        "gate": {"x": 480, "y": 120, "w": 160, "h": 110, "icon": "🚦", "label": "gate", "sub": "confidence\nbands", "color": "amber"},
        "act": {"x": 670, "y": 120, "w": 160, "h": 110, "icon": "✅", "label": "act", "sub": "typed Route", "color": "green"},
        "human": {"x": 275, "y": 300, "w": 160, "h": 110, "icon": "🙋", "label": "human", "sub": "review queue", "color": "coral"},
        "llm": {"x": 480, "y": 300, "w": 160, "h": 110, "icon": "🧠", "label": "llm_check", "sub": "LLM + schema\n+ retry", "color": "gray"},
        "team": {"x": 885, "y": 120, "w": 190, "h": 110, "icon": "👥", "label": "Team agent", "sub": "billing / delivery /\naccount", "color": "blue"},
    },
    "edges": [
        {"from": "ticket", "to": "decide"},
        {"from": "decide", "to": "gate"},
        {"from": "gate", "to": "act", "label": "sure"},
        {"from": "gate", "to": "human", "label": "low", "from_side": "bottom", "to_side": "top", "via": [(560, 262), (355, 262)]},
        {"from": "gate", "to": "llm", "label": "middle", "from_side": "bottom", "to_side": "top"},
        {"from": "llm", "to": "act", "label": "valid", "from_side": "right", "to_side": "bottom", "via": [(750, 355)]},
        {"from": "llm", "to": "human", "label": "unsure", "from_side": "left", "to_side": "right"},
        {"from": "act", "to": "team"},
    ],
    "notes": [
        {"x": 550, "y": 480, "text": "Thresholds come from measuring accuracy per confidence band on labelled tickets (Step 6).", "size": 13},
    ],
}
