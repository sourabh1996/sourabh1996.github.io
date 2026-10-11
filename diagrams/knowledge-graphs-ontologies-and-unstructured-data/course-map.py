# The journey of this course: messy documents become a knowledge graph that agents can use.
SPEC = {
    "title": "From messy documents to a graph your agent can think with",
    "accent": "teal",
    "width": 1100, "height": 600,
    "groups": [
        {"x": 30, "y": 110, "w": 300, "h": 330, "label": "Module 5: digitise", "color": "coral"},
        {"x": 365, "y": 110, "w": 370, "h": 330, "label": "Modules 2 to 4: model and store", "color": "blue"},
        {"x": 770, "y": 110, "w": 300, "h": 330, "label": "Module 6: use it", "color": "green"},
    ],
    "nodes": {
        "docs": {"x": 55, "y": 140, "w": 250, "h": 80, "icon": "🧾", "label": "Messy documents", "sub": "invoices, PDFs, emails, scans", "color": "coral"},
        "extract": {"x": 55, "y": 245, "w": 250, "h": 80, "icon": "🔍", "label": "Extract", "sub": "OCR, layout, LLM + Pydantic", "color": "coral"},
        "resolve": {"x": 55, "y": 350, "w": 250, "h": 72, "icon": "🧩", "label": "Resolve duplicates", "sub": "\"A. Sharma\" = \"Anita Sharma\"", "color": "coral"},
        "onto": {"x": 390, "y": 140, "w": 320, "h": 80, "icon": "📐", "label": "Ontology: the rulebook", "sub": "classes, relationships, constraints", "color": "purple"},
        "kg": {"x": 390, "y": 245, "w": 320, "h": 105, "icon": "🕸️", "label": "Knowledge graph", "sub": "(Priya)-[:PLACED]->(Order 1001)\n-[:CONTAINS]->(Assam Tea)", "color": "blue"},
        "store": {"x": 390, "y": 368, "w": 320, "h": 56, "label": "🗄️ Neo4j (Cypher) or RDF store (SPARQL)", "color": "gray", "size": 14},
        "graphrag": {"x": 795, "y": 140, "w": 250, "h": 80, "icon": "🧠", "label": "GraphRAG", "sub": "answers that follow connections", "color": "green"},
        "cypher": {"x": 795, "y": 245, "w": 250, "h": 80, "icon": "🤖", "label": "Text-to-Cypher agent", "sub": "questions become graph queries", "color": "green"},
        "grounded": {"x": 795, "y": 350, "w": 250, "h": 72, "icon": "🛡️", "label": "Ontology-grounded agent", "sub": "checks facts against the rules", "color": "green"},
    },
    "edges": [
        {"from": "docs", "to": "extract"},
        {"from": "extract", "to": "resolve"},
        {"from": "resolve", "to": "kg", "from_side": "right", "to_side": "left", "via": [(345, 386), (345, 297)]},
        {"from": "onto", "to": "kg"},
        {"from": "kg", "to": "graphrag", "from_side": "right", "to_side": "left"},
        {"from": "kg", "to": "cypher", "from_side": "right", "to_side": "left"},
        {"from": "kg", "to": "grounded", "from_side": "right", "to_side": "left"},
    ],
    "notes": [
        {"x": 550, "y": 490, "text": "Each module adds one layer. By the end you can build every box on this page.", "weight": 700, "color": "#1f766d", "size": 16},
        {"x": 550, "y": 520, "text": "Running examples: an online tea shop, a company graph and a pile of supplier invoices.", "size": 14},
        {"x": 550, "y": 548, "text": "Runnable code uses plain Python, sqlite3 and Pydantic. Neo4j and LLM calls are shown with real syntax.", "size": 13},
    ],
}
