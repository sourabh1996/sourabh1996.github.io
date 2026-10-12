# How prompt caching sees a request: one long prefix in a fixed order, with breakpoints.
SPEC = {
    "title": "Prompt caching is a prefix match",
    "accent": "purple",
    "width": 1100, "height": 640,
    "bands": [
        {"y": 85, "h": 170, "label": "Turn 1", "color": "blue"},
        {"y": 275, "h": 170, "label": "Turn 2", "color": "purple"},
    ],
    "nodes": {
        "t1": {"x": 145, "y": 110, "w": 190, "h": 80, "icon": "🧰", "label": "tools", "sub": "3,400 tokens", "color": "blue"},
        "s1": {"x": 345, "y": 110, "w": 220, "h": 80, "label": "📜 system", "sub": "system prompt + examples\n3,370 tokens", "color": "blue"},
        "m1": {"x": 575, "y": 110, "w": 300, "h": 80, "icon": "💬", "label": "messages", "sub": "turn 1: 1,500 tokens", "color": "amber"},
        "o1": {"x": 895, "y": 110, "w": 175, "h": 80, "label": "✍️ reply", "sub": "output", "color": "gray"},
        "t2": {"x": 145, "y": 300, "w": 190, "h": 80, "icon": "📗", "label": "tools", "sub": "read from cache", "color": "green"},
        "s2": {"x": 345, "y": 300, "w": 220, "h": 80, "icon": "📗", "label": "system", "sub": "read from cache", "color": "green"},
        "m2a": {"x": 575, "y": 300, "w": 150, "h": 80, "icon": "📗", "label": "turn 1", "sub": "read from cache", "color": "green"},
        "m2b": {"x": 735, "y": 300, "w": 140, "h": 80, "icon": "✏️", "label": "turn 2", "sub": "new: written", "color": "amber"},
        "o2": {"x": 895, "y": 300, "w": 175, "h": 80, "label": "✍️ reply", "sub": "output", "color": "gray"},
        "bad1": {"x": 40, "y": 490, "w": 245, "h": 82, "label": "🕒 Timestamp in system", "sub": "changes every call:\nnothing after it caches", "color": "coral", "size": 14},
        "bad2": {"x": 300, "y": 490, "w": 245, "h": 82, "label": "🔀 Tool list changes", "sub": "added, removed or reordered:\neverything is rewritten", "color": "coral", "size": 14},
        "bad3": {"x": 560, "y": 490, "w": 245, "h": 82, "label": "🧾 Unsorted JSON", "sub": "same data, different bytes:\nsilent miss", "color": "coral", "size": 14},
        "bad4": {"x": 820, "y": 490, "w": 245, "h": 82, "label": "✂️ Edited old turns", "sub": "trimming or rewriting history\nbreaks the cache from there", "color": "coral", "size": 14},
    },
    "edges": [],
    "notes": [
        {"x": 565, "y": 212, "text": "▲ breakpoint", "size": 13, "weight": 700, "color": "#5b3fa0"},
        {"x": 875, "y": 212, "text": "▲ breakpoint", "size": 13, "weight": 700, "color": "#5b3fa0"},
        {"x": 145, "y": 240, "text": "Order is always tools → system → messages. A breakpoint caches everything before it.", "anchor": "start", "size": 13},
        {"x": 145, "y": 425, "text": "Cached reads on Claude Opus 5.5 cost $0.20 per million tokens instead of $4.00 (writes cost 1.25×).", "anchor": "start", "size": 13},
        {"x": 550, "y": 470, "text": "Silent cache breakers: any changed byte invalidates everything after it", "weight": 700, "color": "#b2442f", "size": 15},
        {"x": 550, "y": 610, "text": "Stable first, volatile last. Append, don't edit.", "weight": 700, "color": "#1f2328", "size": 16},
    ],
}
