# Where vectors live: library, embedded database, self-hosted server, managed cloud.
SPEC = {
    "title": "Where your vectors live",
    "accent": "teal",
    "width": 1100, "height": 600,
    "groups": [
        {"x": 30, "y": 95, "w": 500, "h": 380, "label": "Inside your Python process", "color": "blue"},
        {"x": 570, "y": 95, "w": 500, "h": 380, "label": "Over the network", "color": "purple"},
    ],
    "nodes": {
        "lib": {"x": 55, "y": 130, "w": 200, "h": 150, "icon": "📚", "label": "Library",
                "sub": "vectors in RAM\nyou save files yourself\nFAISS, hnswlib", "color": "blue"},
        "emb": {"x": 305, "y": 130, "w": 200, "h": 150, "icon": "🗄️", "label": "Embedded DB",
                "sub": "local files, auto-saved\none process owns it\nChroma, LanceDB", "color": "teal"},
        "srv": {"x": 595, "y": 130, "w": 200, "h": 150, "icon": "🖥️", "label": "Self-hosted server",
                "sub": "your machines, Docker\nmany clients share it\nQdrant, Milvus, pgvector", "color": "purple"},
        "cld": {"x": 845, "y": 130, "w": 200, "h": 150, "icon": "☁️", "label": "Managed cloud",
                "sub": "provider runs it\nAPI key + endpoint\nPinecone, Qdrant Cloud", "color": "amber"},
        "you1": {"x": 55, "y": 320, "w": 450, "h": 125, "icon": "🧑‍💻", "label": "You run nothing extra",
                 "sub": "fastest calls, no network hop\nlimited to one machine and one owner", "color": "gray"},
        "you2": {"x": 595, "y": 320, "w": 450, "h": 125, "icon": "🌐", "label": "A service answers queries",
                 "sub": "shared by many apps, scales out\nyou (or a provider) operate it", "color": "gray"},
    },
    "edges": [
        {"from": "lib", "to": "emb", "solid": True},
        {"from": "emb", "to": "srv", "label": "grow", "solid": True},
        {"from": "srv", "to": "cld", "solid": True},
    ],
    "notes": [
        {"x": 550, "y": 520, "text": "Moving right adds scale and sharing, and removes work you do yourself.", "size": 14, "weight": 600, "color": "#1f2328"},
        {"x": 550, "y": 548, "text": "The price: a network hop on every query, and a bill or an on-call rota.", "size": 13},
    ],
}
