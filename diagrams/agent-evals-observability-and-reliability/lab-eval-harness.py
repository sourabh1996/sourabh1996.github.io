# The eval harness built in the Module 2 lab.
SPEC = {
    "title": "The lab's eval harness",
    "accent": "green",
    "width": 1100, "height": 640,
    "groups": [
        {"x": 300, "y": 85, "w": 470, "h": 330, "label": "Repeated k times per task", "color": "amber"},
        {"x": 800, "y": 85, "w": 275, "h": 330, "label": "Graders", "color": "green"},
    ],
    "nodes": {
        "tasks": {"x": 30, "y": 120, "w": 230, "h": 120, "icon": "📋", "label": "8 tasks", "sub": "message, expected refunds,\nescalation, tags, faults", "color": "blue"},
        "versions": {"x": 30, "y": 270, "w": 230, "h": 110, "icon": "🔀", "label": "Agent under test", "sub": "v1 or v2", "color": "blue"},
        "world": {"x": 325, "y": 120, "w": 190, "h": 120, "icon": "🧼", "label": "Fresh World", "sub": "orders, refunds,\nescalations", "color": "amber"},
        "agent": {"x": 555, "y": 120, "w": 190, "h": 120, "icon": "🤖", "label": "run_agent", "sub": "random mistakes,\nlike a real model", "color": "amber"},
        "status": {"x": 325, "y": 270, "w": 190, "h": 125, "icon": "🚦", "label": "Trial status", "sub": "pass · fail\nor error (infra)", "color": "amber"},
        "outcome": {"x": 820, "y": 120, "w": 235, "h": 80, "icon": "📦", "label": "Outcome", "sub": "refunds, escalation", "color": "green"},
        "path": {"x": 820, "y": 215, "w": 235, "h": 80, "icon": "🧭", "label": "Path", "sub": "policy before refund", "color": "green"},
        "honesty": {"x": 820, "y": 310, "w": 235, "h": 85, "icon": "🤝", "label": "Honesty", "sub": "claims match the world", "color": "green"},
        "r1": {"x": 30, "y": 470, "w": 245, "h": 120, "icon": "📈", "label": "pass@1 ± CI", "sub": "bootstrap over tasks", "color": "teal"},
        "r2": {"x": 300, "y": 470, "w": 245, "h": 120, "icon": "🔁", "label": "pass^3 per task", "sub": "consistency", "color": "teal"},
        "r3": {"x": 570, "y": 470, "w": 245, "h": 120, "icon": "🧾", "label": "Failing checks", "sub": "where to work next", "color": "teal"},
        "r4": {"x": 840, "y": 470, "w": 235, "h": 120, "icon": "⚖️", "label": "v1 vs v2", "sub": "paired comparison,\nthen read transcripts", "color": "teal"},
    },
    "edges": [
        {"from": "tasks", "to": "world", "from_side": "right", "to_side": "left"},
        {"from": "versions", "to": "agent", "from_side": "top", "to_side": "bottom", "via": [(145, 255), (650, 255)], "label": "version", "label_at": (290, 248)},
        {"from": "path", "to": "status", "from_side": "left", "to_side": "right", "label": "verdicts", "label_at": (600, 350)},
        {"from": "world", "to": "agent", "both": True, "label": "tools"},
        {"from": "agent", "to": "outcome", "from_side": "right", "to_side": "left"},
        {"from": "agent", "to": "path", "from_side": "right", "to_side": "left"},
        {"from": "agent", "to": "honesty", "from_side": "right", "to_side": "left"},
    ],
    "notes": [
        {"x": 550, "y": 445, "text": "Report", "weight": 700, "color": "#1f766d", "size": 15},
    ],
}
