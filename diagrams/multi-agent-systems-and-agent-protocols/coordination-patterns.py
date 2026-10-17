# Three peer coordination patterns: handoff, group chat and Magentic orchestration.
SPEC = {
    "title": "Handoff, group chat and Magentic orchestration",
    "accent": "amber",
    "width": 1100, "height": 900,
    "bands": [
        {"y": 80, "h": 230, "label": "Handoff", "color": "blue"},
        {"y": 325, "h": 260, "label": "Group\nchat", "color": "green"},
        {"y": 600, "h": 280, "label": "Magentic", "color": "purple"},
    ],
    "nodes": {
        # Handoff
        "hu": {"x": 160, "y": 140, "w": 130, "h": 100, "icon": "🙋", "label": "Customer", "color": "gray"},
        "tri": {"x": 350, "y": 130, "w": 170, "h": 120, "icon": "🧭", "label": "Triage agent", "sub": "holds the baton first", "color": "blue"},
        "ref": {"x": 610, "y": 100, "w": 190, "h": 90, "icon": "💸", "label": "Refunds agent", "color": "blue"},
        "bil": {"x": 610, "y": 205, "w": 190, "h": 90, "icon": "🧾", "label": "Billing agent", "color": "blue"},
        "hnote": {"x": 840, "y": 120, "w": 230, "h": 150, "label": "Control moves", "sub": "a handoff is a tool call:\ntransfer_to_refunds\n\nthe new agent talks\nto the customer", "color": "gray", "size": 15},
        # Group chat
        "mgr": {"x": 160, "y": 380, "w": 190, "h": 150, "icon": "🎙️", "label": "Chat manager", "sub": "picks who speaks next,\ndecides when to stop", "color": "green"},
        "thread": {"x": 420, "y": 395, "w": 230, "h": 120, "icon": "💬", "label": "One shared thread", "sub": "every message goes\nto every agent", "color": "teal"},
        "w": {"x": 720, "y": 345, "w": 150, "h": 70, "label": "✍️ Writer", "color": "green"},
        "c": {"x": 720, "y": 425, "w": 150, "h": 70, "label": "🧐 Critic", "color": "green"},
        "f": {"x": 720, "y": 505, "w": 150, "h": 70, "label": "🔍 Fact-checker", "color": "green", "size": 15},
        "gnote": {"x": 900, "y": 390, "w": 170, "h": 130, "label": "Watch the cost", "sub": "each turn re-reads\nthe whole thread", "color": "gray", "size": 15},
        # Magentic
        "mm": {"x": 160, "y": 640, "w": 200, "h": 160, "icon": "🧠", "label": "Manager", "sub": "plans, picks next agent,\nwrites an instruction", "color": "purple"},
        "tl": {"x": 400, "y": 625, "w": 250, "h": 100, "icon": "📒", "label": "Task ledger", "sub": "facts, guesses, plan", "color": "purple", "size": 15},
        "pl": {"x": 400, "y": 740, "w": 250, "h": 120, "icon": "📈", "label": "Progress ledger", "sub": "done? looping? progressing?\nnext speaker + instruction", "color": "purple", "size": 15},
        "agents": {"x": 700, "y": 640, "w": 170, "h": 160, "icon": "🧑‍🤝‍🧑", "label": "Specialists", "sub": "web surfer\ncoder\nfile reader", "color": "purple"},
        "stall": {"x": 900, "y": 655, "w": 170, "h": 130, "icon": "🔁", "label": "Stalled?", "sub": "too many rounds\nwith no progress:\nreplan", "color": "coral"},
    },
    "edges": [
        {"from": "hu", "to": "tri"},
        {"from": "tri", "to": "ref", "label": "handoff", "from_side": "right", "to_side": "left"},
        {"from": "tri", "to": "bil", "from_side": "right", "to_side": "left"},
        {"from": "mgr", "to": "thread", "both": True},
        {"from": "thread", "to": "w", "both": True, "from_side": "right", "to_side": "left"},
        {"from": "thread", "to": "c", "both": True, "from_side": "right", "to_side": "left"},
        {"from": "thread", "to": "f", "both": True, "from_side": "right", "to_side": "left"},
        {"from": "mm", "to": "tl", "from_side": "right", "to_side": "left"},
        {"from": "mm", "to": "pl", "from_side": "right", "to_side": "left"},
        {"from": "pl", "to": "agents", "from_side": "right", "to_side": "left"},
        {"from": "agents", "to": "stall", "from_side": "right", "to_side": "left"},
    ],
}
