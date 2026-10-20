# Module 4 map: the vector tools this module teaches, placed on the deployment spectrum.
SPEC = {
    "title": "The vector tools in this module",
    "accent": "teal",
    "width": 1100, "height": 660,
    "bands": [
        {"y": 80, "h": 150, "label": "Library", "color": "blue"},
        {"y": 245, "h": 150, "label": "Dedicated", "color": "teal"},
        {"y": 410, "h": 150, "label": "Built-in", "color": "purple"},
    ],
    "nodes": {
        "faiss": {"x": 200, "y": 100, "w": 400, "h": 110, "icon": "⚡", "label": "FAISS",
                  "sub": "index types you assemble yourself\nin your process, no server", "color": "blue"},
        "use1": {"x": 640, "y": 100, "w": 420, "h": 110, "label": "Use for",
                 "sub": "batch jobs, research, huge offline indexes,\nthe engine inside your own service", "color": "gray", "size": 15},
        "chroma": {"x": 200, "y": 265, "w": 200, "h": 110, "icon": "🧪", "label": "Chroma",
                   "sub": "embedded or server\nembeds text for you", "color": "teal"},
        "lance": {"x": 420, "y": 265, "w": 200, "h": 110, "icon": "🗂️", "label": "LanceDB",
                  "sub": "tables in files\nversioned, columnar", "color": "teal"},
        "qdrant": {"x": 640, "y": 265, "w": 200, "h": 110, "icon": "🎯", "label": "Qdrant",
                   "sub": "server or local mode\nrich payload filters", "color": "teal"},
        "pine": {"x": 860, "y": 265, "w": 200, "h": 110, "icon": "☁️", "label": "Pinecone",
                 "sub": "managed only\nserverless, namespaces", "color": "amber"},
        "mongo": {"x": 200, "y": 430, "w": 400, "h": 110, "icon": "🍃", "label": "MongoDB",
                  "sub": "$vectorSearch stage in an\naggregation pipeline", "color": "purple"},
        "cass": {"x": 640, "y": 430, "w": 420, "h": 110, "icon": "💠", "label": "Cassandra 5",
                 "sub": "VECTOR column + SAI index\nORDER BY ... ANN OF in CQL", "color": "purple"},
    },
    "edges": [],
    "notes": [
        {"x": 550, "y": 598, "text": "Same idea everywhere: store id + vector + metadata, then ask for the k nearest with a filter.", "size": 14, "weight": 600, "color": "#1f2328"},
        {"x": 550, "y": 626, "text": "What differs: who runs it, how filters are written, and how scores are reported.", "size": 13},
    ],
}
