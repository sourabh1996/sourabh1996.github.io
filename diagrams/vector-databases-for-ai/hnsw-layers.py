# HNSW: sparse upper layers for long hops, dense layer 0 for the final careful search.
_L2, _L1, _L0 = 115, 245, 375   # node top y per layer
_X = {"A": 200, "B": 300, "C": 400, "D": 480, "E": 580, "F": 680, "G": 770, "H": 860, "J": 950}

def _n(name, y, color="gray"):
    return {"x": _X[name], "y": y, "w": 52, "h": 40, "label": name, "color": color, "size": 15}

SPEC = {
    "title": "HNSW: fast trains on top, slow trains below",
    "accent": "green",
    "width": 1100, "height": 600,
    "bands": [
        {"y": 85, "h": 100, "label": "Layer 2", "color": "purple"},
        {"y": 215, "h": 100, "label": "Layer 1", "color": "blue"},
        {"y": 345, "h": 100, "label": "Layer 0", "color": "green"},
    ],
    "nodes": {
        "A2": _n("A", _L2, "amber"), "H2": _n("H", _L2, "amber"),
        "A1": _n("A", _L1), "D1": _n("D", _L1), "H1": _n("H", _L1, "amber"), "J1": _n("J", _L1),
        "A0": _n("A", _L0), "B0": _n("B", _L0), "C0": _n("C", _L0), "D0": _n("D", _L0), "E0": _n("E", _L0, "teal"),
        "F0": _n("F", _L0, "teal"), "G0": _n("G", _L0, "amber"), "H0": _n("H", _L0, "amber"), "J0": _n("J", _L0),
        "q": {"x": 655, "y": 465, "w": 110, "h": 40, "label": "🎯 query", "color": "coral", "size": 14},
    },
    "edges": [
        {"from": "A2", "to": "H2", "label": "one long hop", "solid": True},
        {"from": "A1", "to": "D1", "both": True}, {"from": "D1", "to": "H1", "both": True}, {"from": "H1", "to": "J1", "both": True},
        {"from": "A0", "to": "B0", "both": True}, {"from": "B0", "to": "C0", "both": True}, {"from": "C0", "to": "D0", "both": True}, {"from": "D0", "to": "E0", "both": True},
        {"from": "E0", "to": "F0", "both": True}, {"from": "F0", "to": "G0"}, {"from": "G0", "to": "H0", "both": True, "solid": True},
        {"from": "H0", "to": "J0", "both": True},
        {"from": "q", "to": "F0", "from_side": "top", "to_side": "bottom"},
        {"from": "H2", "to": "H1", "label": "drop down", "solid": True},
        {"from": "H1", "to": "H0", "label": "drop down", "solid": True},
        {"from": "G0", "to": "F0", "solid": True},
    ],
    "notes": [
        {"x": 226, "y": 108, "text": "entry point", "weight": 700, "color": "#9a6412"},
        {"x": 550, "y": 540, "text": "Links are two-way neighbour links. Path: A → H on layer 2, drop to H, no closer neighbour on layer 1, drop to H on layer 0, then H → G → F.", "size": 14, "weight": 600, "color": "#1f2328"},
        {"x": 550, "y": 565, "text": "Layer 0 search keeps the ef best candidates (here F, E, G in teal and amber) and returns the top k.", "size": 13},
    ],
}
