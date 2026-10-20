# The three capabilities that together let an injected agent leak data, and how to break each leg.
SPEC = {
    "title": "The lethal trifecta, and three ways to break it",
    "accent": "coral",
    "width": 1100, "height": 700,
    "groups": [
        {"x": 30, "y": 90, "w": 640, "h": 450, "label": "All three in one session = data can be stolen", "color": "coral"},
        {"x": 700, "y": 90, "w": 370, "h": 450, "label": "Remove any one leg", "color": "green"},
    ],
    "nodes": {
        "private": {"x": 60, "y": 140, "w": 260, "h": 110, "icon": "🔒", "label": "Private data", "sub": "inbox, files, CRM,\nprivate repos", "color": "amber"},
        "untrusted": {"x": 380, "y": 140, "w": 260, "h": 110, "icon": "📨", "label": "Untrusted content", "sub": "emails, web pages,\nissues, documents", "color": "coral"},
        "exfil": {"x": 220, "y": 400, "w": 260, "h": 110, "icon": "📤", "label": "A way to send out", "sub": "email, URL fetch,\nimage link, public post", "color": "purple"},
        "core": {"x": 255, "y": 285, "w": 190, "h": 66, "label": "⚠️ Model in the middle", "color": "gray", "size": 15},
        "fix1": {"x": 725, "y": 140, "w": 320, "h": 110, "icon": "🧹", "label": "No private data", "sub": "a reader agent with\nno access to secrets", "color": "green"},
        "fix2": {"x": 725, "y": 270, "w": 320, "h": 110, "icon": "🚫", "label": "No untrusted input", "sub": "only content you or\nthe user wrote", "color": "green"},
        "fix3": {"x": 725, "y": 400, "w": 320, "h": 110, "icon": "🧱", "label": "No way out", "sub": "egress blocked, links not\nauto-loaded, sends gated", "color": "green"},
        "rule": {"x": 30, "y": 575, "w": 1040, "h": 90, "icon": "✌️", "label": "Rule of Two (Meta, 2025)", "sub": "in one session, at most two of: untrusted input · sensitive access · changing state or talking outside", "color": "blue"},
    },
    "edges": [
        {"from": "untrusted", "to": "core", "label": "instructions in"},
        {"from": "private", "to": "core", "label": "secrets in"},
        {"from": "core", "to": "exfil", "label": "data out"},
    ],
}
