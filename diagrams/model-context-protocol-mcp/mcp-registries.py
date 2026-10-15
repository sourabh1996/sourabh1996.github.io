# Where MCP servers are found: code at the bottom, the official registry's metadata in the middle, curation on top.
SPEC = {
    "title": "Finding MCP servers: code, metadata, curation",
    "accent": "blue",
    "width": 1100, "height": 640,
    "bands": [
        {"y": 80, "h": 150, "label": "Curate", "color": "purple", "tile": 120},
        {"y": 250, "h": 150, "label": "Describe", "color": "blue", "tile": 120},
        {"y": 420, "h": 150, "label": "Store\ncode", "color": "green", "tile": 120},
    ],
    "nodes": {
        "smithery": {"x": 165, "y": 100, "w": 190, "h": 110, "icon": "🛠️", "label": "Smithery", "sub": "search, hosted\nconnections, CLI", "color": "purple"},
        "ghreg": {"x": 375, "y": 100, "w": 190, "h": 110, "icon": "🧩", "label": "GitHub MCP\nRegistry", "sub": "inside VS Code", "color": "purple"},
        "docker": {"x": 585, "y": 100, "w": 190, "h": 110, "icon": "🐳", "label": "Docker MCP\nCatalog", "sub": "signed images", "color": "purple"},
        "private": {"x": 795, "y": 100, "w": 270, "h": 110, "icon": "🏢", "label": "Company registry", "sub": "approved servers only,\nsame OpenAPI", "color": "purple"},
        "official": {"x": 300, "y": 270, "w": 500, "h": 110, "icon": "📇", "label": "Official MCP Registry", "sub": "server.json metadata, verified namespaces\nio.github.user/...  or  in.example/...", "color": "blue"},
        "hosts": {"x": 855, "y": 270, "w": 210, "h": 110, "icon": "💻", "label": "Hosts", "sub": "read curated lists,\nwrite mcpServers config", "color": "amber"},
        "npm": {"x": 165, "y": 440, "w": 160, "h": 110, "icon": "📦", "label": "npm", "sub": "npx -y pkg@1.2.0", "color": "green"},
        "pypi": {"x": 345, "y": 440, "w": 160, "h": 110, "icon": "🐍", "label": "PyPI", "sub": "uvx pkg==1.2.0", "color": "green"},
        "oci": {"x": 525, "y": 440, "w": 180, "h": 110, "icon": "🐳", "label": "Docker Hub", "sub": "docker run -i --rm", "color": "green"},
        "remote": {"x": 725, "y": 440, "w": 340, "h": 110, "icon": "🌐", "label": "Remote endpoints", "sub": "https://mcp.vendor.com/mcp\n(no install, maybe OAuth)", "color": "green"},
    },
    "edges": [
        {"from": "official", "to": "smithery", "from_side": "top", "to_side": "bottom", "via": [(400, 240), (260, 240)]},
        {"from": "official", "to": "ghreg", "from_side": "top", "to_side": "bottom", "via": [(470, 240)]},
        {"from": "official", "to": "npm", "from_side": "bottom", "to_side": "top", "label": "points to", "via": [(400, 410), (245, 410)], "label_at": (300, 405)},
        {"from": "official", "to": "pypi", "from_side": "bottom", "to_side": "top", "via": [(450, 410), (425, 410)]},
        {"from": "official", "to": "oci", "from_side": "bottom", "to_side": "top", "via": [(615, 410)]},
        {"from": "official", "to": "remote", "from_side": "bottom", "to_side": "top", "via": [(750, 410), (895, 410)]},
        {"from": "private", "to": "hosts", "from_side": "bottom", "to_side": "top"},
    ],
    "notes": [
        {"x": 615, "y": 600, "text": "The registry verifies who published an entry. It does not check what the code does: review before you install.", "size": 14, "weight": 600, "color": "#2f5fb3"},
    ],
}
