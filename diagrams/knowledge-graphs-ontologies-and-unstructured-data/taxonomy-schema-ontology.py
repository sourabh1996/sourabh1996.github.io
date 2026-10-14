# Taxonomy vs schema vs ontology, each shown on the same tea-shop data.
SPEC = {
    "title": "Taxonomy vs schema vs ontology",
    "accent": "purple",
    "width": 1100, "height": 800,
    "groups": [
        {"x": 30, "y": 100, "w": 330, "h": 450, "label": "Taxonomy", "color": "green"},
        {"x": 385, "y": 100, "w": 330, "h": 450, "label": "Schema", "color": "blue"},
        {"x": 740, "y": 100, "w": 330, "h": 450, "label": "Ontology", "color": "purple"},
    ],
    "nodes": {
        # taxonomy tree
        "t0": {"x": 125, "y": 130, "w": 140, "h": 44, "label": "Products", "color": "green", "size": 14},
        "t1": {"x": 125, "y": 200, "w": 140, "h": 44, "label": "Beverages", "color": "green", "size": 14},
        "t2": {"x": 50, "y": 270, "w": 120, "h": 44, "label": "Tea", "color": "green", "size": 14},
        "t3": {"x": 215, "y": 270, "w": 120, "h": 44, "label": "Coffee", "color": "green", "size": 14},
        "t4": {"x": 50, "y": 340, "w": 120, "h": 44, "label": "Black Tea", "color": "green", "size": 14},
        "t5": {"x": 50, "y": 410, "w": 120, "h": 44, "label": "Assam", "color": "green", "size": 14},
        "tq": {"x": 185, "y": 340, "w": 160, "h": 190, "style": "plain", "label": "One relation:", "sub": "\"is a kind of\"\n\nAnswers:\nWhat kind of\nthing is this?\nWhat's under\nTea?", "color": "green", "size": 14},
        # schema
        "s1": {"x": 405, "y": 135, "w": 290, "h": 150, "icon": "🗄️", "label": "products table", "sub": "id TEXT PRIMARY KEY\nname TEXT NOT NULL\nprice_inr INTEGER\nseller_id TEXT -> sellers.id", "color": "blue", "size": 15},
        "sq": {"x": 405, "y": 310, "w": 290, "h": 220, "style": "plain", "label": "Describes storage:", "sub": "which fields, which types,\nwhich are required,\nwhich keys point where\n\nAnswers:\nIs this record valid\nfor this database?", "color": "blue", "size": 14},
        # ontology
        "o1": {"x": 760, "y": 135, "w": 290, "h": 150, "icon": "📐", "label": "Classes + relations + rules", "sub": "Tea subClassOf Product\nOrder placedBy exactly 1 Customer\nTea disjointWith SpiceMix\nsoldBy: Product -> Seller", "color": "purple", "size": 15},
        "oq": {"x": 760, "y": 310, "w": 290, "h": 220, "style": "plain", "label": "Describes meaning:", "sub": "what things are, how they\nrelate, what must be true\n\nAnswers:\nWhat can we conclude?\nDoes this fact make sense?", "color": "purple", "size": 14},
        # ladder
        "l1": {"x": 40, "y": 625, "w": 185, "h": 70, "label": "Controlled vocabulary", "sub": "agreed list of terms", "color": "gray", "size": 14},
        "l2": {"x": 250, "y": 625, "w": 185, "h": 70, "label": "Taxonomy", "sub": "terms in a hierarchy", "color": "green", "size": 14},
        "l3": {"x": 460, "y": 625, "w": 185, "h": 70, "label": "Thesaurus", "sub": "+ synonyms, related", "color": "teal", "size": 14},
        "l4": {"x": 670, "y": 625, "w": 185, "h": 70, "label": "Ontology", "sub": "+ relations, rules", "color": "purple", "size": 14},
        "l5": {"x": 880, "y": 625, "w": 185, "h": 70, "label": "Knowledge graph", "sub": "ontology + real facts", "color": "blue", "size": 14},
    },
    "edges": [
        {"from": "t0", "to": "t1", "solid": True},
        {"from": "t1", "to": "t2", "solid": True},
        {"from": "t1", "to": "t3", "solid": True},
        {"from": "t2", "to": "t4", "solid": True},
        {"from": "t4", "to": "t5", "solid": True},
        {"from": "l1", "to": "l2", "solid": True},
        {"from": "l2", "to": "l3", "solid": True},
        {"from": "l3", "to": "l4", "solid": True},
        {"from": "l4", "to": "l5", "solid": True},
    ],
    "notes": [
        {"x": 550, "y": 600, "text": "More meaning, more effort to build and maintain  →", "weight": 700, "color": "#5b3fa0", "size": 15},
        {"x": 550, "y": 740, "text": "A schema can sit beside any of these: it says how the data is stored, not what it means.", "size": 14},
        {"x": 550, "y": 765, "text": "Pick the lightest one that answers your questions.", "weight": 700, "size": 14, "color": "#1f2328"},
    ],
}
