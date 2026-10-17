# Architecture of the Chat with a PDF lab: ingest a PDF once, then answer questions with page citations.
SPEC = {
    "title": "Chat with a PDF: the system you build in the lab",
    "accent": "blue",
    "width": 1100, "height": 600,
    "bands": [
        {"y": 80, "h": 220, "label": "Ingest", "color": "blue"},
        {"y": 320, "h": 260, "label": "Ask", "color": "green"},
    ],
    "nodes": {
        "pdf": {"x": 160, "y": 110, "w": 140, "h": 160, "icon": "📄", "label": "PDF", "sub": "mediclaim\npolicy,\n5 pages", "color": "gray"},
        "pages": {"x": 330, "y": 110, "w": 160, "h": 160, "icon": "📑", "label": "Pages", "sub": "one Document\nper page,\npage number kept", "color": "blue"},
        "clean": {"x": 520, "y": 110, "w": 160, "h": 160, "icon": "🧹", "label": "Clean", "sub": "drop footers,\nre-join hyphens", "color": "blue"},
        "chunk": {"x": 710, "y": 110, "w": 160, "h": 160, "icon": "✂️", "label": "Chunk", "sub": "by section +\nheading path,\nstart page", "color": "blue"},
        "index": {"x": 900, "y": 110, "w": 170, "h": 160, "icon": "🗄️", "label": "Two indexes", "sub": "vectors\n+ BM25", "color": "blue"},
        "q": {"x": 160, "y": 380, "w": 140, "h": 140, "icon": "❓", "label": "Question", "sub": "\"room rent\nlimit?\"", "color": "gray"},
        "hybrid": {"x": 330, "y": 380, "w": 160, "h": 140, "icon": "🔀", "label": "Hybrid search", "sub": "RRF fusion,\ntop 6", "color": "green"},
        "rerank": {"x": 520, "y": 380, "w": 160, "h": 140, "icon": "🏅", "label": "Rerank", "sub": "keep 2,\nrefuse if weak", "color": "green"},
        "llm": {"x": 710, "y": 380, "w": 160, "h": 140, "icon": "🧠", "label": "LLM", "sub": "answer only\nfrom context", "color": "green"},
        "ans": {"x": 900, "y": 380, "w": 170, "h": 140, "icon": "💬", "label": "Answer", "sub": "with (p. 2)\ncitations", "color": "green"},
    },
    "edges": [
        {"from": "pdf", "to": "pages"},
        {"from": "pages", "to": "clean"},
        {"from": "clean", "to": "chunk"},
        {"from": "chunk", "to": "index"},
        {"from": "q", "to": "hybrid"},
        {"from": "index", "to": "hybrid", "from_side": "bottom", "to_side": "top", "via": [(985, 300), (410, 300)]},
        {"from": "hybrid", "to": "rerank"},
        {"from": "rerank", "to": "llm"},
        {"from": "llm", "to": "ans"},
    ],
}
