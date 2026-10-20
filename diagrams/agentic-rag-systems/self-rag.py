# Self-RAG as a LangGraph: four reflection checks and the loops they trigger.
SPEC = {
    "title": "Self-RAG: the model checks itself at every step",
    "accent": "green",
    "width": 1100, "height": 560,
    "nodes": {
        "q": {"x": 30, "y": 95, "w": 130, "h": 100, "icon": "🙋", "label": "Question", "color": "gray"},
        "r": {"x": 190, "y": 90, "w": 180, "h": 110, "icon": "❓", "label": "Retrieve?", "sub": "no: generate without\ndocuments", "color": "purple"},
        "ret": {"x": 410, "y": 95, "w": 150, "h": 100, "icon": "🔎", "label": "Retrieve", "color": "gray"},
        "rel": {"x": 600, "y": 90, "w": 190, "h": 110, "icon": "🎯", "label": "Relevant?", "sub": "grade each doc,\nkeep the good ones", "color": "teal"},
        "gen": {"x": 840, "y": 95, "w": 170, "h": 100, "icon": "✍️", "label": "Generate", "color": "blue"},
        "sup": {"x": 830, "y": 330, "w": 190, "h": 110, "icon": "🔗", "label": "Supported?", "sub": "every claim backed\nby the docs?", "color": "amber"},
        "use": {"x": 590, "y": 330, "w": 190, "h": 110, "icon": "👍", "label": "Useful?", "sub": "does it answer\nthe question?", "color": "green"},
        "ans": {"x": 330, "y": 340, "w": 170, "h": 90, "icon": "💬", "label": "Answer", "color": "green"},
        "rw": {"x": 410, "y": 225, "w": 150, "h": 70, "label": "🔁 Rewrite query", "color": "coral", "size": 15},
    },
    "edges": [
        {"from": "q", "to": "r", "solid": True},
        {"from": "r", "to": "ret", "label": "yes", "solid": True},
        {"from": "ret", "to": "rel", "solid": True},
        {"from": "rel", "to": "gen", "solid": True},
        {"from": "gen", "to": "sup", "solid": True, "from_side": "bottom", "to_side": "top"},
        {"from": "sup", "to": "gen", "from_side": "right", "to_side": "right", "via": [(1060, 385), (1060, 145)]},
        {"from": "sup", "to": "use", "label": "yes", "solid": True},
        {"from": "use", "to": "ans", "label": "yes", "solid": True},
        {"from": "use", "to": "rw", "label": "no", "from_side": "top", "to_side": "right", "via": [(685, 260)]},
        {"from": "rw", "to": "ret", "from_side": "top", "to_side": "bottom"},
    ],
    "notes": [
        {"x": 993, "y": 262, "text": "no:\nregenerate", "size": 13},
        {"x": 550, "y": 510, "text": "Every loop has a cap: after N tries the graph answers with what it has, or says it doesn't know.", "size": 14},
    ],
}
