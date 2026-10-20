# A LanceDB table: columns, fragments, versions and indexes, stored as files locally or in object storage.
SPEC = {
    "title": "A LanceDB table is a folder of files",
    "accent": "green",
    "width": 1100, "height": 680,
    "groups": [
        {"x": 30, "y": 95, "w": 640, "h": 470, "label": "help_centre.lance", "color": "green"},
        {"x": 700, "y": 95, "w": 370, "h": 470, "label": "Where the folder lives", "color": "gray"},
    ],
    "nodes": {
        "cols": {"x": 55, "y": 130, "w": 590, "h": 105, "icon": "🧱", "label": "Columns, stored separately",
                 "sub": "id | text | topic | lang | views | vector[384]\nread only the columns a query needs", "color": "green"},
        "frag": {"x": 55, "y": 260, "w": 285, "h": 125, "icon": "📦", "label": "Data fragments",
                 "sub": "each add() writes new files;\nold files are never edited", "color": "teal"},
        "ver": {"x": 360, "y": 260, "w": 285, "h": 125, "icon": "🕰️", "label": "Versions",
                "sub": "v1: 8 rows, v2: +2 rows\nv3: 1 row deleted\ncheckout any version", "color": "purple"},
        "idx": {"x": 55, "y": 410, "w": 590, "h": 125, "icon": "🗂️", "label": "Indexes",
                "sub": "vector: IVF_PQ or IVF_HNSW_SQ\nfull text: words in the text column\nscalar: lang, topic (fast where filters)", "color": "blue"},
        "local": {"x": 725, "y": 130, "w": 320, "h": 105, "icon": "💻", "label": "Local disk",
                  "sub": "lancedb.connect(\"./data\")\nembedded in your process", "color": "gray"},
        "s3": {"x": 725, "y": 260, "w": 320, "h": 125, "icon": "🪣", "label": "Object storage",
               "sub": "connect(\"s3://bucket/path\")\nmany readers, cheap storage", "color": "amber"},
        "cloud": {"x": 725, "y": 410, "w": 320, "h": 125, "icon": "☁️", "label": "LanceDB Cloud",
                  "sub": "connect(\"db://...\")\nmanaged service", "color": "coral"},
    },
    "edges": [
        {"from": "cols", "to": "frag", "solid": True},
        {"from": "frag", "to": "ver", "solid": True},
        {"from": "cols", "to": "local", "solid": True},
    ],
    "notes": [
        {"x": 550, "y": 610, "text": "Search = vector index + SQL-style where filter over the other columns, in one query.", "size": 14, "weight": 600, "color": "#1f2328"},
        {"x": 550, "y": 640, "text": "Append-only files make versions free and let many processes read the same table safely.", "size": 13},
    ],
}
