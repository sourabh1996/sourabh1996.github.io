# Lab architecture: an agent loop with a budget manager between every tool result and the next model call.
SPEC = {
    "title": "Lab: a 200-step agent with a budget manager",
    "accent": "amber",
    "width": 1100, "height": 680,
    "groups": [
        {"x": 30, "y": 100, "w": 400, "h": 300, "label": "Agent loop", "color": "blue"},
        {"x": 470, "y": 100, "w": 600, "h": 420, "label": "Budget manager (your harness code)", "color": "amber"},
    ],
    "nodes": {
        "model": {"x": 60, "y": 135, "w": 160, "h": 100, "icon": "🧠", "label": "Model", "sub": "records the last finding,\ncalls the next tool", "color": "blue"},
        "tool": {"x": 245, "y": 135, "w": 160, "h": 100, "icon": "🎫", "label": "get_ticket", "sub": "helpdesk API,\n200 tickets", "color": "blue"},
        "ctx": {"x": 60, "y": 270, "w": 345, "h": 105, "icon": "🪟", "label": "Context window", "sub": "budget 16,000 = 14,000 usable + 2,000 reserve\nprefix, history, results", "color": "gray"},
        "shape": {"x": 500, "y": 140, "w": 260, "h": 100, "icon": "✂️", "label": "Shape at source", "sub": "concise result + truncated\ntranscript with a pointer", "color": "teal"},
        "clear": {"x": 790, "y": 140, "w": 255, "h": 100, "icon": "🧹", "label": "Clear old results", "sub": "above 70%: keep last 3,\nonly if 4,000+ tokens freed", "color": "amber"},
        "notes": {"x": 500, "y": 280, "w": 260, "h": 100, "icon": "🗒️", "label": "Notes file", "sub": "one line per finding,\nNOTES.md on disk", "color": "purple"},
        "compact": {"x": 790, "y": 280, "w": 255, "h": 100, "icon": "🗜️", "label": "Compact", "sub": "above 80%: summary that\npoints to NOTES.md + last turn", "color": "amber"},
        "answer": {"x": 500, "y": 410, "w": 545, "h": 80, "icon": "", "label": "✅ Final answer computed from NOTES.md, checked against ground truth", "color": "green", "size": 15},
    },
    "edges": [
        {"from": "model", "to": "tool", "solid": True},
        {"from": "tool", "to": "shape", "label": "raw result", "from_side": "right", "to_side": "left", "via": [(440, 185), (470, 190)]},
        {"from": "shape", "to": "clear", "solid": True},
        {"from": "clear", "to": "compact", "from_side": "bottom", "to_side": "top", "solid": True},
        {"from": "compact", "to": "ctx", "label": "fits the budget", "from_side": "right", "to_side": "bottom", "via": [(1082, 330), (1082, 560), (232, 560)]},
        {"from": "ctx", "to": "model", "from_side": "top", "to_side": "bottom", "solid": True},
        {"from": "model", "to": "notes", "label": "append finding", "from_side": "bottom", "to_side": "left", "via": [(140, 255), (450, 255), (450, 330)]},
        {"from": "notes", "to": "answer", "from_side": "bottom", "to_side": "top", "solid": True},
    ],
    "notes": [
        {"x": 550, "y": 610, "text": "Naive: 13 steps.  Clearing: 82.  Shape + clear: 116.  Add compaction: all 200, but the wrong total.",
         "size": 13},
        {"x": 550, "y": 638, "text": "All four layers: 200 tickets, peak 11,142 of 14,000, correct total, only 2 history rewrites.",
         "weight": 700, "size": 15, "color": "#2e7d4f"},
    ],
}
