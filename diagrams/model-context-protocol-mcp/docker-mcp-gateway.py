# Docker MCP Gateway: hosts have one config entry; the gateway runs each server of a profile in its own container.
SPEC = {
    "title": "Docker MCP Gateway: one server in front of many containers",
    "accent": "blue",
    "width": 1100, "height": 640,
    "groups": [
        {"x": 30, "y": 80, "w": 230, "h": 400, "label": "Hosts", "color": "purple"},
        {"x": 330, "y": 80, "w": 260, "h": 400, "label": "MCP Gateway", "color": "blue"},
        {"x": 660, "y": 80, "w": 410, "h": 400, "label": "Profile web-dev: one container each", "color": "teal"},
    ],
    "nodes": {
        "claude": {"x": 55, "y": 120, "w": 180, "h": 85, "icon": "💬", "label": "Claude Desktop", "sub": "one config entry", "color": "purple"},
        "cursor": {"x": 55, "y": 240, "w": 180, "h": 85, "icon": "🧑‍💻", "label": "Cursor", "sub": "one config entry", "color": "purple"},
        "vscode": {"x": 55, "y": 360, "w": 180, "h": 85, "icon": "📝", "label": "VS Code", "sub": "client connect", "color": "purple"},
        "merge": {"x": 360, "y": 120, "w": 200, "h": 85, "icon": "📋", "label": "Merge tools", "sub": "reads the profile", "color": "blue"},
        "check": {"x": 360, "y": 240, "w": 200, "h": 85, "icon": "🛡️", "label": "Check calls", "sub": "block secrets, log", "color": "blue"},
        "route": {"x": 360, "y": 360, "w": 200, "h": 85, "icon": "🔀", "label": "Route", "sub": "start containers", "color": "blue"},
        "gh": {"x": 690, "y": 120, "w": 350, "h": 85, "icon": "🐙", "label": "github-official", "sub": "1 CPU, 2 GB, token injected", "color": "teal"},
        "pw": {"x": 690, "y": 240, "w": 350, "h": 85, "icon": "🎭", "label": "playwright", "sub": "1 CPU, 2 GB, network on", "color": "teal"},
        "own": {"x": 690, "y": 360, "w": 350, "h": 85, "icon": "📦", "label": "internal-api", "sub": "no host files unless mounted", "color": "teal"},
        "cat": {"x": 360, "y": 520, "w": 200, "h": 80, "icon": "🗂️", "label": "Catalogs", "sub": "Docker's + your company's", "color": "gray"},
        "hub": {"x": 690, "y": 520, "w": 350, "h": 80, "icon": "✍️", "label": "Signed images + SBOM", "sub": "mcp namespace on Docker Hub", "color": "gray"},
    },
    "edges": [
        {"from": "claude", "to": "merge", "from_side": "right", "to_side": "left"},
        {"from": "cursor", "to": "check", "from_side": "right", "to_side": "left"},
        {"from": "vscode", "to": "route", "from_side": "right", "to_side": "left"},
        {"from": "merge", "to": "check", "from_side": "bottom", "to_side": "top", "solid": True},
        {"from": "check", "to": "route", "from_side": "bottom", "to_side": "top", "solid": True},
        {"from": "route", "to": "gh", "from_side": "right", "to_side": "left"},
        {"from": "route", "to": "pw", "from_side": "right", "to_side": "left"},
        {"from": "route", "to": "own", "from_side": "right", "to_side": "left"},
        {"from": "cat", "to": "hub", "from_side": "right", "to_side": "left", "label": "lists"},
    ],
    "notes": [
        {"x": 180, "y": 560, "text": "docker mcp gateway run", "size": 14, "weight": 600, "color": "#2b5fb0"},
        {"x": 180, "y": 582, "text": "--profile web-dev", "size": 14, "weight": 600, "color": "#2b5fb0"},
    ],
}
