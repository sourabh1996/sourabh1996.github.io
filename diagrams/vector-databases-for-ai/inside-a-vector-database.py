# Write path and read path inside a typical vector database: WAL, buffer, immutable segments, fan-out search.
SPEC = {
    "title": "Inside a vector database",
    "accent": "teal",
    "width": 1100, "height": 640,
    "groups": [
        {"x": 30, "y": 95, "w": 300, "h": 420, "label": "Write path", "color": "blue"},
        {"x": 360, "y": 95, "w": 380, "h": 420, "label": "Storage: segments", "color": "teal"},
        {"x": 770, "y": 95, "w": 300, "h": 420, "label": "Read path", "color": "green"},
    ],
    "nodes": {
        "w": {"x": 55, "y": 125, "w": 250, "h": 80, "icon": "✍️", "label": "Upsert / delete", "sub": "id, vector, metadata, text", "color": "blue"},
        "wal": {"x": 55, "y": 240, "w": 250, "h": 95, "icon": "📜", "label": "Write-ahead log", "sub": "appended to disk first,\nreplayed after a crash", "color": "blue"},
        "buf": {"x": 55, "y": 370, "w": 250, "h": 120, "icon": "🧺", "label": "Fresh buffer", "sub": "newest vectors, searched\nby brute force until\nsealed into a segment", "color": "blue"},
        "s1": {"x": 385, "y": 125, "w": 330, "h": 95, "label": "Segment 1 (immutable)", "sub": "vectors + HNSW or IVF index\npayload index for filters", "color": "teal", "size": 15},
        "s2": {"x": 385, "y": 240, "w": 330, "h": 95, "label": "Segment 2 (immutable)", "sub": "vectors + index + payload index\ntombstones: id 4471 deleted", "color": "teal", "size": 15},
        "s3": {"x": 385, "y": 355, "w": 330, "h": 135, "icon": "🧹", "label": "Background jobs", "sub": "build indexes for sealed segments\nmerge small segments (compaction)\ndrop deleted items for real", "color": "gray", "size": 15},
        "q": {"x": 795, "y": 125, "w": 250, "h": 80, "icon": "🎯", "label": "Query + filter", "sub": "vector, k, lang = 'hi'", "color": "green"},
        "fan": {"x": 795, "y": 240, "w": 250, "h": 95, "label": "Fan out", "sub": "search buffer and every\nsegment, filter-aware,\nskip tombstones", "color": "green", "size": 15},
        "merge": {"x": 795, "y": 370, "w": 250, "h": 120, "icon": "🏆", "label": "Merge to top k", "sub": "best k across segments,\nwith ids, scores,\nmetadata and text", "color": "green"},
    },
    "edges": [
        {"from": "w", "to": "wal", "solid": True},
        {"from": "wal", "to": "buf", "solid": True},
        {"from": "buf", "to": "s2", "label": "seal", "from_side": "right", "to_side": "left", "solid": True, "via": [(345, 430), (345, 287)]},
        {"from": "q", "to": "fan", "solid": True},
        {"from": "fan", "to": "merge", "solid": True},
        {"from": "fan", "to": "s1", "from_side": "left", "to_side": "right", "via": [(760, 287), (760, 172)]},
        {"from": "fan", "to": "s2", "from_side": "left", "to_side": "right"},
    ],
    "notes": [
        {"x": 550, "y": 560, "text": "Writes are durable as soon as they reach the log; they are searchable as soon as they reach the buffer.", "size": 14, "weight": 600, "color": "#1f2328"},
        {"x": 550, "y": 588, "text": "Updates are a delete plus an insert. Metadata lives beside the vectors, with its own index, so filters stay fast.", "size": 13},
    ],
}
