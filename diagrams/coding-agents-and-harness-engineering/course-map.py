# The five teaching modules of the course, grouped into "use agents" and "engineer the harness".
SPEC = {
    "title": "Coding agents and harness engineering: the course map",
    "accent": "teal",
    "width": 1100, "height": 560,
    "groups": [
        {"x": 30, "y": 100, "w": 430, "h": 300, "label": "Use coding agents well", "color": "blue"},
        {"x": 490, "y": 100, "w": 580, "h": 300, "label": "Engineer the harness", "color": "purple"},
    ],
    "nodes": {
        "m2": {"x": 55, "y": 140, "w": 180, "h": 230, "icon": "🧑‍💻", "label": "Module 2", "sub": "Working with\ncoding agents\n\nlandscape · workflow\nspecs · review", "color": "blue"},
        "m3": {"x": 255, "y": 140, "w": 180, "h": 230, "icon": "🐙", "label": "Module 3", "sub": "Coding agents\non GitHub\n\nCopilot · cloud agents\nMCP · Actions", "color": "blue"},
        "m4": {"x": 515, "y": 140, "w": 170, "h": 230, "icon": "🧰", "label": "Module 4", "sub": "What a\nharness is\n\nloop · permissions\nhooks · sandboxes", "color": "purple"},
        "m5": {"x": 700, "y": 140, "w": 170, "h": 230, "icon": "⏳", "label": "Module 5", "sub": "Long-running\nagents\n\nprogress files\nhandoffs · worktrees", "color": "purple"},
        "m6": {"x": 885, "y": 140, "w": 165, "h": 230, "icon": "🏗️", "label": "Module 6", "sub": "Harness for\ncodebases\n\nlinters · tests\ncleanup agents", "color": "purple"},
        "lab1": {"x": 515, "y": 430, "w": 170, "h": 64, "label": "🔧 Lab: build a harness", "color": "amber", "size": 14},
        "lab2": {"x": 885, "y": 430, "w": 165, "h": 64, "label": "🔧 Lab: agent-ready repo", "color": "amber", "size": 13},
    },
    "edges": [
        {"from": "m2", "to": "m3", "solid": True},
        {"from": "m3", "to": "m4", "solid": True},
        {"from": "m4", "to": "m5", "solid": True},
        {"from": "m5", "to": "m6", "solid": True},
        {"from": "m4", "to": "lab1"},
        {"from": "m6", "to": "lab2"},
    ],
    "notes": [
        {"x": 550, "y": 530, "text": "Agent = model + harness. You control the harness.", "weight": 700, "color": "#1f766d", "size": 16},
    ],
}
