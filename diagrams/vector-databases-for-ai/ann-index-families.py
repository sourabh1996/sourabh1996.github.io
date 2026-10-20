# The four families of vector index: flat, IVF, HNSW and PQ, with their knob and trade-off.
SPEC = {
    "title": "Four ways to find nearest neighbours",
    "accent": "purple",
    "width": 1100, "height": 760,
    "groups": [
        {"x": 30, "y": 100, "w": 505, "h": 300, "label": "Flat: compare with everything", "color": "gray"},
        {"x": 565, "y": 100, "w": 505, "h": 300, "label": "IVF: search the nearest clusters", "color": "blue"},
        {"x": 30, "y": 440, "w": 505, "h": 300, "label": "HNSW: walk a layered graph", "color": "green"},
        {"x": 565, "y": 440, "w": 505, "h": 300, "label": "PQ: compress, then re-rank", "color": "amber"},
    ],
    "nodes": {
        "fq": {"x": 55, "y": 135, "w": 130, "h": 80, "icon": "🎯", "label": "Query", "color": "gray"},
        "fall": {"x": 225, "y": 135, "w": 285, "h": 80, "label": "Score all N vectors", "sub": "one matrix multiply", "color": "gray"},
        "fres": {"x": 55, "y": 245, "w": 455, "h": 130, "label": "Exact top k",
                 "sub": "recall 1.0, work grows with N\nbest under ~100,000 vectors\nor as ground truth for testing", "color": "gray"},

        "iq": {"x": 590, "y": 135, "w": 130, "h": 80, "icon": "🎯", "label": "Query", "color": "blue"},
        "ic": {"x": 760, "y": 135, "w": 285, "h": 80, "label": "Compare with nlist centroids", "sub": "k-means cluster centres", "color": "blue"},
        "il": {"x": 590, "y": 245, "w": 210, "h": 130, "label": "Scan nprobe lists",
               "sub": "only vectors in the\nclosest clusters", "color": "blue"},
        "ik": {"x": 835, "y": 245, "w": 210, "h": 130, "label": "Knob: nprobe",
               "sub": "more lists = higher recall\nmisses sit near borders\nneeds training data", "color": "blue", "size": 15},

        "h2": {"x": 55, "y": 475, "w": 230, "h": 66, "label": "Top layer", "sub": "few nodes, long hops", "color": "green", "size": 15},
        "h1": {"x": 55, "y": 565, "w": 230, "h": 66, "label": "Middle layer", "sub": "more nodes", "color": "green", "size": 15},
        "h0": {"x": 55, "y": 655, "w": 230, "h": 66, "label": "Layer 0", "sub": "every vector, near links", "color": "green", "size": 15},
        "hk": {"x": 310, "y": 475, "w": 200, "h": 246, "label": "Knobs",
               "sub": "M: links per node\n\nef_construction:\nbuild quality\n\nef_search:\nspeed vs recall\n\nfast, RAM-hungry", "color": "green", "size": 15},

        "pv": {"x": 590, "y": 475, "w": 210, "h": 80, "label": "32 floats", "sub": "128 bytes", "color": "amber"},
        "pc": {"x": 835, "y": 475, "w": 210, "h": 80, "label": "8 one-byte codes", "sub": "[17, 203, 31, ... 64]", "color": "amber"},
        "pt": {"x": 590, "y": 590, "w": 210, "h": 130, "label": "Lookup tables",
               "sub": "approximate score =\nsum of 8 table lookups", "color": "amber"},
        "pr": {"x": 835, "y": 590, "w": 210, "h": 130, "label": "Re-rank shortlist",
               "sub": "exact scores for the\ntop 50 restore recall", "color": "amber"},
    },
    "edges": [
        {"from": "fq", "to": "fall", "solid": True},
        {"from": "fall", "to": "fres", "from_side": "bottom", "to_side": "top", "solid": True, "via": [(367, 230), (282, 230)]},
        {"from": "iq", "to": "ic", "solid": True},
        {"from": "ic", "to": "il", "from_side": "bottom", "to_side": "top", "solid": True, "via": [(902, 230), (695, 230)]},
        {"from": "h2", "to": "h1", "solid": True},
        {"from": "h1", "to": "h0", "solid": True},
        {"from": "pv", "to": "pc", "solid": True},
        {"from": "pc", "to": "pr", "from_side": "bottom", "to_side": "top", "solid": True},
        {"from": "pt", "to": "pr", "solid": True},
    ],
}
