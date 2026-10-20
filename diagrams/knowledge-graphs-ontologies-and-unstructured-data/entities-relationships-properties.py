# The three building blocks of every knowledge graph, shown on one tiny shop graph.
SPEC = {
    "title": "Entities, relationships and properties",
    "accent": "blue",
    "width": 1100, "height": 760,
    "nodes": {
        # legend row
        "ent": {"x": 40, "y": 85, "w": 320, "h": 110, "icon": "🟦", "label": "Entity (a node)", "sub": "a thing you can point at and name\nPriya · Order 1001 · Assam CTC Tea", "color": "blue"},
        "rel": {"x": 390, "y": 85, "w": 320, "h": 110, "icon": "➡️", "label": "Relationship (an edge)", "sub": "how two things are connected\nPLACED · CONTAINS · LIVES_IN", "color": "amber"},
        "prop": {"x": 740, "y": 85, "w": 320, "h": 110, "icon": "🏷️", "label": "Property (a key: value)", "sub": "a detail about one thing\nprice: ₹240 · city: Pune", "color": "green"},
        # graph
        "priya": {"x": 60, "y": 300, "w": 210, "h": 90, "icon": "👩", "label": "Priya", "sub": "label: Customer", "color": "blue"},
        "order": {"x": 445, "y": 300, "w": 210, "h": 90, "icon": "📦", "label": "Order 1001", "sub": "label: Order", "color": "blue"},
        "tea": {"x": 830, "y": 300, "w": 210, "h": 90, "icon": "🍵", "label": "Assam CTC Tea", "sub": "label: Product", "color": "blue"},
        "pune": {"x": 60, "y": 545, "w": 210, "h": 80, "icon": "🏙️", "label": "Pune", "sub": "label: City", "color": "blue"},
        "seller": {"x": 830, "y": 545, "w": 210, "h": 80, "icon": "🏪", "label": "Brahmaputra Tea Co.", "sub": "label: Seller", "color": "blue"},
        # properties
        "p1": {"x": 285, "y": 410, "w": 150, "h": 62, "label": "email: priya@…", "sub": "joined: 2023", "color": "green", "size": 13},
        "p2": {"x": 470, "y": 410, "w": 160, "h": 62, "label": "date: 2026-09-14", "sub": "total: ₹480", "color": "green", "size": 13},
        "p3": {"x": 660, "y": 410, "w": 150, "h": 62, "label": "price: ₹240", "sub": "weight: 250 g", "color": "green", "size": 13},
    },
    "edges": [
        {"from": "priya", "to": "order", "label": "PLACED", "solid": True},
        {"from": "order", "to": "tea", "label": "CONTAINS {qty: 2}", "solid": True},
        {"from": "priya", "to": "pune", "label": "LIVES_IN", "solid": True, "from_side": "left", "to_side": "left",
         "via": [(32, 345), (32, 585)], "label_at": (82, 475)},
        {"from": "tea", "to": "seller", "label": "SOLD_BY", "solid": True},
        {"from": "p1", "to": "priya", "from_side": "left", "to_side": "bottom", "via": [(165, 441)]},
        {"from": "p2", "to": "order", "to_side": "bottom", "from_side": "top"},
        {"from": "p3", "to": "tea", "from_side": "right", "to_side": "bottom", "via": [(935, 441)]},
    ],
    "notes": [
        {"x": 550, "y": 250, "text": "The same ideas on a real graph:", "weight": 700, "color": "#2f5fb3", "size": 16},
        {"x": 550, "y": 520, "text": "Read any edge as a sentence:", "weight": 700, "color": "#9a6412", "size": 15},
        {"x": 550, "y": 545, "text": "Priya PLACED Order 1001.", "size": 14},
        {"x": 550, "y": 568, "text": "Order 1001 CONTAINS Assam CTC Tea (2 packs).", "size": 14},
        {"x": 550, "y": 591, "text": "Assam CTC Tea is SOLD_BY Brahmaputra Tea Co.", "size": 14},
        {"x": 550, "y": 680, "text": "Nouns become entities, verbs become relationships, adjectives and numbers become properties.", "weight": 700, "color": "#1f2328", "size": 15},
        {"x": 550, "y": 708, "text": "Relationships can carry properties too: qty: 2 lives on the CONTAINS edge, not on the tea.", "size": 13.5},
    ],
}
