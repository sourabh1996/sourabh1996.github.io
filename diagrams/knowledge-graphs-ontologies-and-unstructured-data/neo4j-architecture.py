# How Neo4j fits together: clients talk Bolt or HTTP to the DBMS, which plans Cypher and walks stored graph records.
SPEC = {
    "title": "Inside Neo4j: from a Cypher query to stored graph records",
    "accent": "blue",
    "width": 1080, "height": 750,
    "bands": [
        {"y": 80, "h": 130, "label": "Clients", "color": "blue"},
        {"y": 240, "h": 315, "label": "Neo4j\nDBMS", "color": "purple"},
        {"y": 585, "h": 120, "label": "Run it\non", "color": "teal"},
    ],
    "nodes": {
        "browser": {"x": 150, "y": 100, "w": 190, "h": 90, "icon": "🖥️", "label": "Neo4j Browser", "sub": "type Cypher, see graphs", "color": "blue"},
        "driver": {"x": 360, "y": 100, "w": 190, "h": 90, "icon": "🐍", "label": "Python driver", "sub": "your application", "color": "blue"},
        "agent": {"x": 570, "y": 100, "w": 190, "h": 90, "icon": "🤖", "label": "LLM agent", "sub": "text-to-Cypher tool", "color": "blue"},
        "bloom": {"x": 780, "y": 100, "w": 190, "h": 90, "icon": "🔭", "label": "Explore / BI tools", "sub": "visual search", "color": "blue"},
        "proto": {"x": 150, "y": 262, "w": 820, "h": 46, "label": "Bolt protocol (port 7687)  ·  HTTP API (port 7474)", "color": "gray", "size": 15},
        "parse": {"x": 150, "y": 330, "w": 180, "h": 80, "icon": "📝", "label": "Parse", "sub": "Cypher text to a tree", "color": "purple"},
        "plan": {"x": 360, "y": 330, "w": 180, "h": 80, "icon": "🧭", "label": "Plan", "sub": "pick indexes and order", "color": "purple"},
        "run": {"x": 570, "y": 330, "w": 180, "h": 80, "icon": "⚙️", "label": "Run", "sub": "expand along relationships", "color": "purple"},
        "tx": {"x": 780, "y": 330, "w": 190, "h": 80, "icon": "🔒", "label": "Transactions", "sub": "ACID, write-ahead log", "color": "purple"},
        "store": {"x": 150, "y": 458, "w": 390, "h": 80, "icon": "🗄️", "label": "Graph storage", "sub": "nodes · relationships · properties, neighbours linked directly", "color": "amber"},
        "index": {"x": 570, "y": 458, "w": 180, "h": 80, "icon": "🔎", "label": "Indexes", "sub": "range, text, full-text, vector", "color": "amber"},
        "plugins": {"x": 780, "y": 458, "w": 190, "h": 80, "icon": "🧩", "label": "Plugins", "sub": "APOC, Graph Data Science", "color": "amber"},
        "desktop": {"x": 150, "y": 605, "w": 190, "h": 80, "icon": "💻", "label": "Neo4j Desktop", "sub": "on your laptop", "color": "teal"},
        "docker": {"x": 360, "y": 605, "w": 190, "h": 80, "icon": "🐳", "label": "Docker image", "sub": "one command", "color": "teal"},
        "aura": {"x": 570, "y": 605, "w": 190, "h": 80, "icon": "☁️", "label": "AuraDB", "sub": "managed cloud, free tier", "color": "teal"},
        "cluster": {"x": 780, "y": 605, "w": 190, "h": 80, "icon": "🏢", "label": "Self-managed cluster", "sub": "Enterprise Edition", "color": "teal"},
    },
    "edges": [
        {"from": "parse", "to": "plan", "solid": True},
        {"from": "plan", "to": "run", "solid": True},
        {"from": "run", "to": "index", "label": "find start", "solid": True, "from_side": "bottom", "to_side": "top", "label_at": (710, 440)},
        {"from": "run", "to": "store", "label": "hop along", "solid": True, "from_side": "bottom", "to_side": "top", "via": [(660, 434), (345, 434)], "label_at": (450, 434)},
    ],
    "notes": [
        {"x": 540, "y": 732, "text": "Every client sends Cypher over Bolt. The planner chooses a starting point (often an index), then the runtime hops from node to node.", "size": 13.5},
    ],
}
