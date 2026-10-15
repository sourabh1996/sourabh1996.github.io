# Qdrant's building blocks: clients, API, collection, shards, segments, points with payload.
SPEC = {
    "title": "Inside a Qdrant deployment",
    "accent": "coral",
    "width": 1100, "height": 690,
    "groups": [
        {"x": 30, "y": 95, "w": 250, "h": 470, "label": "Clients", "color": "blue"},
        {"x": 310, "y": 95, "w": 760, "h": 470, "label": "Qdrant server or cluster", "color": "coral"},
    ],
    "nodes": {
        "py": {"x": 55, "y": 130, "w": 200, "h": 90, "icon": "🐍", "label": "Python client", "sub": "qdrant-client", "color": "blue"},
        "rest": {"x": 55, "y": 245, "w": 200, "h": 90, "icon": "🌐", "label": "REST :6333", "sub": "JSON over HTTP", "color": "blue"},
        "grpc": {"x": 55, "y": 360, "w": 200, "h": 90, "icon": "⚡", "label": "gRPC :6334", "sub": "faster, binary", "color": "blue"},
        "local": {"x": 55, "y": 465, "w": 200, "h": 80, "label": "Local mode", "sub": "same API, no server", "color": "gray", "size": 15},
        "coll": {"x": 335, "y": 130, "w": 330, "h": 110, "icon": "📁", "label": "Collection: help_centre",
                 "sub": "vector size 384, distance Cosine\nHNSW m=16, payload indexes", "color": "coral"},
        "wal": {"x": 700, "y": 130, "w": 345, "h": 110, "icon": "📜", "label": "Write-ahead log",
                "sub": "every upsert lands here first", "color": "gray"},
        "sh1": {"x": 335, "y": 270, "w": 330, "h": 120, "icon": "🧩", "label": "Shard 1 (+ replica)",
                "sub": "segments: vectors + HNSW\n+ payload index", "color": "amber"},
        "sh2": {"x": 700, "y": 270, "w": 345, "h": 120, "icon": "🧩", "label": "Shard 2 (+ replica)",
                "sub": "segments: vectors + HNSW\n+ payload index", "color": "amber"},
        "pt": {"x": 335, "y": 420, "w": 710, "h": 120, "icon": "📍", "label": "A point",
               "sub": "id: 7c9e...-uuid   vector: [0.98, 0.0, 0.19, ...]\npayload: {\"topic\": \"payments\", \"lang\": \"en\", \"text\": \"UPI payment failed...\"}", "color": "teal"},
    },
    "edges": [
        {"from": "py", "to": "rest", "solid": True},
        {"from": "rest", "to": "coll", "solid": True},
        {"from": "grpc", "to": "coll", "from_side": "right", "to_side": "left", "via": [(295, 405), (295, 185)]},
        {"from": "coll", "to": "wal", "solid": True},
        {"from": "coll", "to": "sh1", "solid": True},
        {"from": "coll", "to": "sh2", "from_side": "bottom", "to_side": "top", "via": [(500, 255), (872, 255)]},
        {"from": "sh1", "to": "pt"},
    ],
    "notes": [
        {"x": 550, "y": 610, "text": "A query fans out to every shard, filters on the payload while walking HNSW, and merges the top k.", "size": 14, "weight": 600, "color": "#1f2328"},
        {"x": 550, "y": 640, "text": "Scores come back as similarities for Cosine and Dot: higher is better.", "size": 13},
    ],
}
