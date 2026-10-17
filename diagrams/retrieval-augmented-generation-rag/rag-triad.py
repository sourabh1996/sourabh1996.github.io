# Module 9's central idea: three checks between question, retrieved context and answer, plus reference-based checks.
SPEC = {
    "title": "The RAG triad: three checks, one for each pair",
    "accent": "amber",
    "width": 1100, "height": 640,
    "groups": [
        {"x": 40, "y": 80, "w": 690, "h": 540, "label": "The triad: no reference needed", "color": "amber"},
        {"x": 760, "y": 80, "w": 320, "h": 540, "label": "With a reference answer", "color": "purple"},
    ],
    "nodes": {
        "q": {"x": 180, "y": 120, "w": 170, "h": 120, "icon": "❓", "label": "Question", "sub": "what the user\nasked", "color": "gray"},
        "c": {"x": 500, "y": 120, "w": 190, "h": 120, "icon": "📚", "label": "Retrieved context", "sub": "chunks the\nretriever returned", "color": "blue"},
        "a": {"x": 340, "y": 440, "w": 190, "h": 120, "icon": "💬", "label": "Answer", "sub": "what the model\nwrote", "color": "green"},
        "r": {"x": 840, "y": 300, "w": 180, "h": 130, "icon": "✅", "label": "Reference", "sub": "the answer a\nhuman expects", "color": "purple"},
    },
    "edges": [
        {"from": "q", "to": "c", "label": "1. Context relevance\nis it on topic?", "both": True},
        {"from": "c", "to": "a", "label": "2. Groundedness\nis every claim\nin the context?", "both": True},
        {"from": "q", "to": "a", "label": "3. Answer relevance\ndoes it answer?", "both": True},
        {"from": "r", "to": "c", "label": "context recall\nand precision", "both": True},
        {"from": "r", "to": "a", "label": "answer\ncorrectness", "both": True},
    ],
}
