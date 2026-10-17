# Defence in depth for A2A: five layers between a client agent and a remote agent.
SPEC = {
    "title": "Five layers of A2A security",
    "accent": "blue",
    "width": 1100, "height": 740,
    "groups": [{"x": 315, "y": 80, "w": 470, "h": 615, "label": "Every request passes all five", "color": "gray"}],
    "nodes": {
        "client": {"x": 30, "y": 300, "w": 190, "h": 140, "icon": "🧭", "label": "Client agent", "sub": "acts for a user", "color": "purple"},
        "remote": {"x": 880, "y": 300, "w": 190, "h": 140, "icon": "🚆", "label": "Remote agent", "sub": "another owner", "color": "teal"},
        "l1": {"x": 330, "y": 110, "w": 440, "h": 100, "icon": "🔒", "label": "1. Transport", "sub": "HTTPS / TLS 1.3, certificate checks, optional mTLS", "color": "blue", "size": 17},
        "l2": {"x": 330, "y": 225, "w": 440, "h": 100, "icon": "🪪", "label": "2. Identity", "sub": "signed Agent Card, OAuth 2.0 / OIDC tokens, API keys", "color": "purple", "size": 17},
        "l3": {"x": 330, "y": 340, "w": 440, "h": 100, "icon": "🚦", "label": "3. Authorisation", "sub": "scopes per skill, tasks visible only to their owner", "color": "amber", "size": 17},
        "l4": {"x": 330, "y": 455, "w": 440, "h": 100, "icon": "🧪", "label": "4. Content", "sub": "validate parts, treat remote text as untrusted, no SSRF", "color": "coral", "size": 17},
        "l5": {"x": 330, "y": 570, "w": 440, "h": 100, "icon": "📈", "label": "5. Operations", "sub": "rate limits, audit logs without secrets, key rotation", "color": "green", "size": 17},
    },
    "edges": [
        {"from": "client", "to": "l3", "from_side": "right", "to_side": "left"},
        {"from": "l3", "to": "remote", "from_side": "right", "to_side": "left"},
    ],
}
