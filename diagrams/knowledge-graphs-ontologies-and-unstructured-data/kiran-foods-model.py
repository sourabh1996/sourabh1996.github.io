# The Kiran Foods company knowledge graph: three CSV exports are cleaned and loaded into one Neo4j model.
SPEC = {
    "title": "Kiran Foods company graph: from CSV exports to a Neo4j model",
    "accent": "teal",
    "width": 1180, "height": 690,
    "groups": [
        {"x": 30, "y": 250, "w": 1120, "h": 340, "label": "Inside Neo4j: the graph model", "color": "teal"},
    ],
    "nodes": {
        "csv": {"x": 60, "y": 90, "w": 300, "h": 100, "icon": "📄", "label": "Three CSV exports", "sub": "employees · suppliers · projects\nfrom HR, procurement, project tracker", "color": "gray"},
        "loader": {"x": 440, "y": 90, "w": 320, "h": 100, "icon": "🐍", "label": "Python loader", "sub": "clean and validate with Pydantic\nsend UNWIND + MERGE batches", "color": "blue"},
        "db": {"x": 840, "y": 90, "w": 300, "h": 100, "icon": "🗄️", "label": "Neo4j database", "sub": "constraints first, then data\nsafe to reload any time", "color": "purple"},
        "dept": {"x": 60, "y": 300, "w": 190, "h": 76, "icon": "🏢", "label": "Department", "color": "blue"},
        "emp": {"x": 360, "y": 300, "w": 190, "h": 76, "icon": "👤", "label": "Employee", "sub": "↻ REPORTS_TO Employee", "color": "blue"},
        "state": {"x": 960, "y": 300, "w": 170, "h": 76, "icon": "🗺️", "label": "State", "color": "teal"},
        "proj": {"x": 360, "y": 480, "w": 190, "h": 76, "icon": "🎯", "label": "Project", "sub": "budgetLakh · status", "color": "purple"},
        "sup": {"x": 660, "y": 480, "w": 190, "h": 76, "icon": "🏭", "label": "Supplier", "sub": "name · gstin", "color": "amber"},
        "city": {"x": 960, "y": 480, "w": 170, "h": 76, "icon": "🏙️", "label": "City", "color": "teal"},
    },
    "edges": [
        {"from": "csv", "to": "loader", "solid": True},
        {"from": "loader", "to": "db", "solid": True},
        {"from": "emp", "to": "dept", "label": "WORKS_IN", "solid": True},
        {"from": "emp", "to": "proj", "label": "LEADS · WORKS_ON {role}", "solid": True, "label_at": (455, 437)},
        {"from": "emp", "to": "sup", "label": "MANAGES_ACCOUNT {since}", "solid": True, "from_side": "right", "to_side": "top",
         "via": [(755, 338)], "label_at": (672, 338)},
        {"from": "proj", "to": "sup", "label": "SOURCES_FROM\n{item}", "solid": True, "label_at": (605, 500)},
        {"from": "sup", "to": "city", "label": "LOCATED_IN", "solid": True, "label_at": (905, 500)},
        {"from": "city", "to": "state", "label": "IN_STATE", "solid": True, "label_at": (1045, 437)},
    ],
    "notes": [
        {"x": 590, "y": 630, "text": "Every label has a uniqueness constraint on its key (Employee.id, Supplier.id, Project.id, Department.name, City.name, State.name).", "size": 13.5},
        {"x": 590, "y": 656, "text": "Relationship properties in braces: who manages an account since when, what a project buys from each supplier.", "size": 13.5},
    ],
}
