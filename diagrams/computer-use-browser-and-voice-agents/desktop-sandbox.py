# Production layout for a computer-use agent: brains and secrets outside, a disposable desktop inside.
SPEC = {
    "title": "A safe home for a desktop agent",
    "accent": "coral",
    "width": 1100, "height": 760,
    "groups": [
        {"x": 30, "y": 95, "w": 330, "h": 620, "label": "Control plane (trusted)", "color": "purple"},
        {"x": 420, "y": 95, "w": 400, "h": 620, "label": "Disposable VM (untrusted)", "color": "teal"},
        {"x": 860, "y": 95, "w": 210, "h": 620, "label": "Outside world", "color": "gray"},
    ],
    "nodes": {
        "loop": {"x": 55, "y": 130, "w": 280, "h": 100, "icon": "🔁", "label": "Agent loop", "sub": "API key lives here,\nnot in the VM", "color": "purple"},
        "policy": {"x": 55, "y": 255, "w": 280, "h": 100, "icon": "🙋", "label": "Policy + approvals", "sub": "per-action checks,\nhuman says yes or no", "color": "coral"},
        "secrets": {"x": 55, "y": 380, "w": 280, "h": 95, "icon": "🔐", "label": "Secret store", "sub": "short-lived, scoped creds", "color": "purple"},
        "logs": {"x": 55, "y": 500, "w": 280, "h": 95, "icon": "🎞️", "label": "Recording + audit", "sub": "every screenshot and action", "color": "purple"},
        "kill": {"x": 55, "y": 620, "w": 280, "h": 70, "label": "🛑 Limits and kill switch", "color": "coral", "size": 15},
        "exec": {"x": 450, "y": 130, "w": 340, "h": 100, "icon": "🖱️", "label": "Executor daemon", "sub": "screenshots, xdotool clicks and keys", "color": "teal"},
        "display": {"x": 450, "y": 255, "w": 340, "h": 100, "icon": "🖥️", "label": "Virtual display", "sub": "Xvfb + window manager", "color": "teal"},
        "apps": {"x": 450, "y": 380, "w": 340, "h": 95, "icon": "📂", "label": "Apps and test data", "sub": "browser, office suite, seeded files", "color": "teal"},
        "snap": {"x": 450, "y": 500, "w": 340, "h": 95, "icon": "♻️", "label": "Fresh snapshot per task", "sub": "destroyed afterwards", "color": "teal"},
        "vnc": {"x": 450, "y": 620, "w": 340, "h": 70, "label": "👀 Live view for a human", "color": "teal", "size": 15},
        "proxy": {"x": 880, "y": 255, "w": 170, "h": 110, "icon": "🚧", "label": "Egress proxy", "sub": "allowlisted\ndomains only", "color": "coral"},
        "web": {"x": 880, "y": 430, "w": 170, "h": 100, "icon": "🌐", "label": "Allowed sites", "sub": "still untrusted", "color": "gray"},
    },
    "edges": [
        {"from": "loop", "to": "exec", "both": True, "label": "actions\nscreenshots", "label_at": (392, 150)},
        {"from": "apps", "to": "proxy", "from_side": "right", "to_side": "left", "via": [(840, 427), (840, 310)]},
        {"from": "proxy", "to": "web"},
    ],
}
