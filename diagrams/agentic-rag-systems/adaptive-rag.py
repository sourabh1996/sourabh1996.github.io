# Module 2's central idea: classify the question, then spend retrieval effort to match.
SPEC = {
    "title": "Adaptive RAG: match the effort to the question",
    "accent": "blue",
    "width": 1100, "height": 620,
    "bands": [
        {"y": 95, "h": 150, "label": "Easy", "color": "green"},
        {"y": 260, "h": 150, "label": "Medium", "color": "amber"},
        {"y": 425, "h": 150, "label": "Hard", "color": "coral"},
    ],
    "nodes": {
        "q": {"x": 160, "y": 285, "w": 160, "h": 100, "icon": "🙋", "label": "Question", "color": "gray"},
        "clf": {"x": 360, "y": 275, "w": 190, "h": 120, "icon": "🧭", "label": "Classifier",
                "sub": "small model or LLM\npicks a level", "color": "blue"},
        "a": {"x": 600, "y": 120, "w": 230, "h": 100, "icon": "💬", "label": "No retrieval",
              "sub": "\"What does PNR stand for?\"", "color": "green"},
        "b": {"x": 600, "y": 285, "w": 230, "h": 100, "icon": "🔎", "label": "One search",
              "sub": "\"Fee to cancel 3 days early?\"", "color": "amber"},
        "c": {"x": 600, "y": 450, "w": 230, "h": 100, "icon": "🔁", "label": "Search, think, repeat",
              "sub": "\"Train cancelled: when is\nmy refund?\"", "color": "coral"},
        "ca": {"x": 870, "y": 135, "w": 200, "h": 70, "label": "1 model call", "sub": "fast, cheap", "color": "green", "size": 15},
        "cb": {"x": 870, "y": 300, "w": 200, "h": 70, "label": "1 search + 1 call", "sub": "the classic pipeline", "color": "amber", "size": 15},
        "cc": {"x": 870, "y": 465, "w": 200, "h": 70, "label": "2 to 4 searches + calls", "sub": "slow, but gets it right", "color": "coral", "size": 15},
    },
    "edges": [
        {"from": "q", "to": "clf", "solid": True},
        {"from": "clf", "to": "a", "from_side": "right", "to_side": "left"},
        {"from": "clf", "to": "b", "from_side": "right", "to_side": "left"},
        {"from": "clf", "to": "c", "from_side": "right", "to_side": "left"},
        {"from": "a", "to": "ca", "solid": True},
        {"from": "b", "to": "cb", "solid": True},
        {"from": "c", "to": "cc", "solid": True},
    ],
    "notes": [
        {"x": 550, "y": 600, "text": "A fixed pipeline treats every question as Medium: it wastes effort on Easy ones and fails Hard ones.", "size": 14},
    ],
}
