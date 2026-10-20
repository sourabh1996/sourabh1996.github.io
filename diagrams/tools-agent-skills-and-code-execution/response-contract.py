# Module 2, lesson 2: the response contract every tool result is checked against.
SPEC = {
    "title": "The response contract: return just enough",
    "accent": "teal",
    "width": 1100, "height": 620,
    "groups": [
        {"x": 360, "y": 120, "w": 380, "h": 330, "label": "One tool result", "color": "teal"},
    ],
    "nodes": {
        "answer": {"x": 385, "y": 150, "w": 330, "h": 60, "label": "📌 Answer: facts in human units", "color": "teal", "size": 15},
        "handles": {"x": 385, "y": 222, "w": 330, "h": 60, "label": "🔗 Handles: IDs, cursors", "color": "teal", "size": 15},
        "state": {"x": 385, "y": 294, "w": 330, "h": 60, "label": "📊 State: 3 of 41, pending", "color": "teal", "size": 15},
        "guide": {"x": 385, "y": 366, "w": 330, "h": 60, "label": "🧭 Guidance: what to call next", "color": "teal", "size": 15},

        "sem": {"x": 40, "y": 120, "w": 270, "h": 100, "icon": "🏷️", "label": "Readable handles",
                "sub": "MM-48213, rider_ravi_k\nnot 36-char UUIDs", "color": "blue"},
        "fmt": {"x": 40, "y": 240, "w": 270, "h": 100, "icon": "📏", "label": "Measured format",
                "sub": "table or lines for lists,\nJSON when code parses", "color": "blue"},
        "rf": {"x": 40, "y": 360, "w": 270, "h": 100, "icon": "🎚️", "label": "response_format",
               "sub": "concise by default,\ndetailed on request", "color": "blue"},
        "cur": {"x": 790, "y": 120, "w": 270, "h": 100, "icon": "➡️", "label": "Cursor pagination",
                "sub": "continue after an item,\nsafe on live data", "color": "purple"},
        "sum": {"x": 790, "y": 240, "w": 270, "h": 100, "icon": "🧮", "label": "Summary first",
                "sub": "totals + outliers +\npointer to detail tool", "color": "purple"},
        "rcpt": {"x": 790, "y": 360, "w": 270, "h": 100, "icon": "🧾", "label": "Receipts for writes",
                 "sub": "what changed, new ID,\nidempotent retries", "color": "purple"},
        "budget": {"x": 360, "y": 495, "w": 380, "h": 80, "icon": "⚖️", "label": "Per-tool output budget",
                   "sub": "falls back to concise, then cuts with guidance", "color": "amber"},
    },
    "edges": [
        {"from": "sem", "to": "handles", "from_side": "right", "to_side": "left", "via": [(335, 165), (335, 252)]},
        {"from": "fmt", "to": "answer", "from_side": "right", "to_side": "left", "via": [(345, 285), (345, 180)]},
        {"from": "rf", "to": "state", "from_side": "right", "to_side": "left", "via": [(335, 405), (335, 324)]},
        {"from": "cur", "to": "handles", "from_side": "left", "to_side": "right", "via": [(765, 165), (765, 252)]},
        {"from": "sum", "to": "guide", "from_side": "left", "to_side": "right", "via": [(755, 285), (755, 396)]},
        {"from": "rcpt", "to": "state", "from_side": "left", "to_side": "right", "via": [(770, 405), (770, 324)]},
        {"from": "budget", "to": "guide", "from_side": "top", "to_side": "bottom"},
    ],
}
