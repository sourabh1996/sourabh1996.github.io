# Module 7's central idea: three ways to make images retrievable, and a vision model to answer from them.
SPEC = {
    "title": "Multimodal RAG: three ways to retrieve images",
    "accent": "purple",
    "width": 1100, "height": 700,
    "bands": [
        {"y": 80, "h": 180, "label": "A. To text", "color": "blue"},
        {"y": 280, "h": 180, "label": "B. Shared\nspace", "color": "purple"},
        {"y": 480, "h": 180, "label": "C. Page\nimages", "color": "teal"},
    ],
    "nodes": {
        "a1": {"x": 180, "y": 105, "w": 170, "h": 130, "icon": "🖼️", "label": "Chart, photo", "sub": "or scanned page", "color": "gray"},
        "a2": {"x": 400, "y": 105, "w": 190, "h": 130, "icon": "📝", "label": "Caption + OCR", "sub": "vision model writes\na text description", "color": "blue"},
        "a3": {"x": 640, "y": 105, "w": 190, "h": 130, "icon": "🔤", "label": "Text index", "sub": "caption embedded,\nimage path in metadata", "color": "blue"},
        "b1": {"x": 180, "y": 305, "w": 170, "h": 130, "icon": "🖼️", "label": "Images", "sub": "and text chunks", "color": "gray"},
        "b2": {"x": 400, "y": 305, "w": 190, "h": 130, "icon": "🧬", "label": "Multimodal\nembedding", "sub": "one vector space\nfor both", "color": "purple"},
        "b3": {"x": 640, "y": 305, "w": 190, "h": 130, "icon": "🗄️", "label": "Mixed index", "sub": "text query finds\nimages directly", "color": "purple"},
        "c1": {"x": 180, "y": 505, "w": 170, "h": 130, "icon": "📄", "label": "PDF pages", "sub": "rendered as\nscreenshots", "color": "gray"},
        "c2": {"x": 400, "y": 505, "w": 190, "h": 130, "icon": "🔬", "label": "Page embeddings", "sub": "ColPali-style,\nno parsing", "color": "teal"},
        "c3": {"x": 640, "y": 505, "w": 190, "h": 130, "icon": "🗄️", "label": "Page index", "sub": "returns whole\npage images", "color": "teal"},
        "vlm": {"x": 875, "y": 295, "w": 195, "h": 150, "icon": "👁️", "label": "Vision LLM", "sub": "reads question,\ntext and images;\nanswers with sources", "color": "green"},
    },
    "edges": [
        {"from": "a1", "to": "a2"}, {"from": "a2", "to": "a3"},
        {"from": "b1", "to": "b2"}, {"from": "b2", "to": "b3"},
        {"from": "c1", "to": "c2"}, {"from": "c2", "to": "c3"},
        {"from": "a3", "to": "vlm"}, {"from": "b3", "to": "vlm"}, {"from": "c3", "to": "vlm"},
    ],
}
