# MCP authorization: four parties; the MCP server is a resource server that points to the AS and checks tokens.
SPEC = {
    "title": "MCP authorization with OAuth 2.1",
    "accent": "amber",
    "width": 1100, "height": 600,
    "nodes": {
        "user": {"x": 30, "y": 230, "w": 180, "h": 110, "icon": "🧑", "label": "User + browser", "sub": "logs in, approves\nscopes", "color": "purple"},
        "client": {"x": 300, "y": 230, "w": 200, "h": 110, "icon": "💬", "label": "MCP client", "sub": "in Claude, VS Code,\nyour agent", "color": "blue"},
        "server": {"x": 620, "y": 80, "w": 230, "h": 120, "icon": "🚪", "label": "MCP server", "sub": "resource server:\nmetadata + token checks", "color": "teal"},
        "as": {"x": 620, "y": 380, "w": 230, "h": 120, "icon": "🛂", "label": "Authorization server", "sub": "Entra ID, Okta, Auth0,\nKeycloak, Google", "color": "amber"},
        "checks": {"x": 900, "y": 80, "w": 170, "h": 120, "icon": "✅", "label": "Every request", "sub": "signature, issuer,\nexpiry, audience, scope", "color": "green"},
        "pkce": {"x": 900, "y": 380, "w": 170, "h": 120, "icon": "🔐", "label": "Login safety", "sub": "PKCE S256, resource,\nstate, iss", "color": "coral"},
    },
    "edges": [
        {"from": "client", "to": "server", "label": "metadata, then Bearer token"},
        {"from": "client", "to": "as", "label": "AS metadata, token"},
        {"from": "user", "to": "client", "label": "uses", "from_side": "right", "to_side": "left"},
        {"from": "user", "to": "as", "label": "log in", "via": [(120, 440)], "to_side": "left"},
        {"from": "server", "to": "as", "label": "authorization_servers", "from_side": "bottom", "to_side": "top"},
        {"from": "server", "to": "checks", "from_side": "right", "to_side": "left", "solid": True},
        {"from": "as", "to": "pkce", "from_side": "right", "to_side": "left", "solid": True},
    ],
    "notes": [
        {"x": 550, "y": 560, "text": "The MCP server never sees passwords. It names its authorization server and checks the tokens clients bring.", "size": 14, "weight": 600, "color": "#9a5b00"},
    ],
}
