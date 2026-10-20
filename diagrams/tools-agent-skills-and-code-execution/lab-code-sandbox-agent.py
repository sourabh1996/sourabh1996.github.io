# Module 3 lab architecture: agent loop + subprocess sandbox + tool bridge with policy.
SPEC = {
    "title": "Lab: a code-execution agent with a tool bridge",
    "accent": "teal",
    "width": 1100, "height": 600,
    "groups": [
        {"x": 30, "y": 90, "w": 640, "h": 450, "label": "Harness (trusted)", "color": "purple"},
        {"x": 720, "y": 90, "w": 350, "h": 450, "label": "Sandbox process", "color": "coral"},
    ],
    "nodes": {
        "model": {"x": 60, "y": 130, "w": 260, "h": 100, "icon": "🤖", "label": "Pretend model",
                  "sub": "writes a python block", "color": "purple"},
        "loop": {"x": 380, "y": 130, "w": 260, "h": 100, "icon": "🔁", "label": "Agent loop",
                 "sub": "extract code, run,\nreturn capped output", "color": "purple"},
        "bridge": {"x": 380, "y": 280, "w": 260, "h": 120, "icon": "🌉", "label": "Tool bridge",
                   "sub": "allowlist, call budget,\nRs cap, log", "color": "amber"},
        "tools": {"x": 60, "y": 280, "w": 260, "h": 120, "icon": "🧰", "label": "Tools + data",
                  "sub": "orders, coupons ledger", "color": "blue"},
        "secret": {"x": 60, "y": 430, "w": 260, "h": 80, "label": "🔑 Secret stays here", "color": "gray", "size": 14},
        "code": {"x": 750, "y": 130, "w": 290, "h": 100, "icon": "🐍", "label": "main.py",
                 "sub": "model-written code", "color": "coral"},
        "toolsmod": {"x": 750, "y": 280, "w": 290, "h": 120, "icon": "📨", "label": "tools.py",
                     "sub": "tools.call() sends a\nJSON line, waits for reply", "color": "teal"},
        "limits": {"x": 750, "y": 430, "w": 290, "h": 80, "label": "⏱️ CPU, memory, timeout, empty env", "color": "gray", "size": 14},
    },
    "edges": [
        {"from": "model", "to": "loop", "label": "reply"},
        {"from": "loop", "to": "code", "label": "run code"},
        {"from": "code", "to": "toolsmod", "from_side": "bottom", "to_side": "top"},
        {"from": "toolsmod", "to": "bridge", "label": "request / result", "both": True},
        {"from": "bridge", "to": "tools", "label": "if allowed", "from_side": "left", "to_side": "right"},
    ],
    "notes": [{"x": 550, "y": 575, "text": "Sandbox limits the code; the bridge limits what it can do through your tools"}],
}
