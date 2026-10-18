# The course map: three places an agent can step into a RAG pipeline.
SPEC = {
    "title": "Three places an agent can step into RAG",
    "accent": "teal",
    "width": 1100, "height": 550,
    "groups": [
        {"x": 30, "y": 300, "w": 330, "h": 220, "label": "Module 2: Adaptive RAG", "color": "blue"},
        {"x": 385, "y": 300, "w": 330, "h": 220, "label": "Module 3: Corrective RAG", "color": "amber"},
        {"x": 740, "y": 300, "w": 330, "h": 220, "label": "Module 4: Self-RAG", "color": "green"},
    ],
    "nodes": {
        "q": {"x": 30, "y": 100, "w": 150, "h": 90, "icon": "🙋", "label": "Question", "color": "gray"},
        "route": {"x": 215, "y": 100, "w": 170, "h": 90, "icon": "🧭", "label": "Route", "sub": "before retrieving", "color": "blue"},
        "ret": {"x": 420, "y": 100, "w": 150, "h": 90, "icon": "🔎", "label": "Retrieve", "color": "gray"},
        "grade": {"x": 605, "y": 100, "w": 170, "h": 90, "icon": "🧪", "label": "Check docs", "sub": "after retrieving", "color": "amber"},
        "gen": {"x": 810, "y": 100, "w": 120, "h": 90, "icon": "✍️", "label": "Write", "color": "gray"},
        "crit": {"x": 960, "y": 100, "w": 120, "h": 90, "icon": "✅", "label": "Check", "sub": "the answer", "color": "green"},
        "m2": {"x": 55, "y": 340, "w": 280, "h": 150, "label": "How hard is it?",
               "sub": "no search, one search,\nor many searches;\nhelp centre or web", "color": "blue"},
        "m3": {"x": 410, "y": 340, "w": 280, "h": 150, "label": "Are these docs any good?",
               "sub": "keep, refine, or throw away\nand search the web", "color": "amber"},
        "m4": {"x": 765, "y": 340, "w": 280, "h": 150, "label": "Is my answer supported?",
               "sub": "search only when needed,\ngrade relevance, support\nand usefulness", "color": "green"},
    },
    "edges": [
        {"from": "q", "to": "route", "solid": True},
        {"from": "route", "to": "ret", "solid": True},
        {"from": "ret", "to": "grade", "solid": True},
        {"from": "grade", "to": "gen", "solid": True},
        {"from": "gen", "to": "crit", "solid": True},
    ],
    "notes": [
        {"x": 550, "y": 245, "text": "A fixed pipeline runs only the grey boxes, every time. Agentic RAG adds the coloured decisions.\nEach module of this course teaches one of them.", "size": 14},
    ],
}
