# Local Self-RAG deployment: everything runs on machines you control.
SPEC = {
    "title": "Self-RAG deployed locally",
    "accent": "green",
    "width": 1100, "height": 620,
    "groups": [
        {"x": 250, "y": 85, "w": 820, "h": 400, "label": "Your server (or laptop): nothing leaves it", "color": "green"},
    ],
    "nodes": {
        "user": {"x": 30, "y": 200, "w": 180, "h": 110, "icon": "🧑‍💼", "label": "Staff app", "sub": "POST /ask", "color": "gray"},
        "api": {"x": 280, "y": 180, "w": 210, "h": 150, "icon": "🚪", "label": "FastAPI service",
                "sub": "validates input,\ntimeout, logs,\nreturns verdicts", "color": "blue"},
        "graph": {"x": 530, "y": 180, "w": 210, "h": 150, "icon": "🕸️", "label": "Self-RAG graph",
                  "sub": "retrieve, grade,\ngenerate, check,\ncapped loops", "color": "green"},
        "ollama": {"x": 800, "y": 120, "w": 240, "h": 110, "icon": "🦙", "label": "Ollama",
                   "sub": "small model: graders\nlarger model: answers", "color": "purple"},
        "chroma": {"x": 800, "y": 270, "w": 240, "h": 110, "icon": "🗄️", "label": "Chroma (persistent)",
                   "sub": "chunks + metadata\n./chroma_saathirail", "color": "teal"},
        "index": {"x": 530, "y": 390, "w": 210, "h": 80, "icon": "🔄", "label": "Indexing job", "sub": "upsert, delete stale", "color": "amber"},
        "logs": {"x": 280, "y": 390, "w": 210, "h": 80, "icon": "📒", "label": "Logs", "sub": "path, verdicts, latency", "color": "gray"},
        "docs": {"x": 800, "y": 520, "w": 240, "h": 80, "icon": "📄", "label": "Help-centre pages", "sub": "internal source of truth", "color": "gray"},
    },
    "edges": [
        {"from": "user", "to": "api", "solid": True},
        {"from": "api", "to": "graph", "solid": True},
        {"from": "graph", "to": "ollama", "from_side": "right", "to_side": "left"},
        {"from": "graph", "to": "chroma", "from_side": "right", "to_side": "left"},
        {"from": "api", "to": "logs", "from_side": "bottom", "to_side": "top"},
        {"from": "docs", "to": "index", "from_side": "left", "to_side": "bottom", "via": [(635, 560)]},
        {"from": "index", "to": "chroma", "from_side": "right", "to_side": "bottom", "via": [(920, 430)]},
    ],
    "notes": [
        {"x": 135, "y": 360, "text": "answer + sources\n+ support verdict", "size": 13},
    ],
}
