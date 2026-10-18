# The computer-use loop: the model sees resized screenshots and answers with actions in that image's coordinates.
SPEC = {
    "title": "The screenshot-action loop",
    "accent": "purple",
    "width": 1100, "height": 700,
    "groups": [
        {"x": 30, "y": 95, "w": 330, "h": 560, "label": "Model (API)", "color": "purple"},
        {"x": 400, "y": 95, "w": 670, "h": 560, "label": "Your executor, inside a VM", "color": "teal"},
    ],
    "nodes": {
        "model": {"x": 60, "y": 260, "w": 270, "h": 190, "icon": "🧠", "label": "Model",
                   "sub": "looks at the screenshot,\nwrites one or more actions:\nleft_click [512, 342]\ntype \"Chai at 5\"\nkey ctrl+s", "color": "purple"},
        "capture": {"x": 430, "y": 130, "w": 280, "h": 100, "icon": "📸", "label": "Capture screen", "sub": "real pixels, e.g. 2560x1600", "color": "teal"},
        "resize": {"x": 760, "y": 130, "w": 280, "h": 100, "icon": "📐", "label": "Resize to fit limits", "sub": "remember the scale factor", "color": "teal"},
        "scale": {"x": 430, "y": 470, "w": 280, "h": 100, "icon": "🎯", "label": "Map coordinates back", "sub": "screen = image ÷ scale", "color": "teal"},
        "gate": {"x": 760, "y": 470, "w": 280, "h": 100, "icon": "🙋", "label": "Policy and approval", "sub": "each action, one by one", "color": "coral"},
        "do": {"x": 760, "y": 300, "w": 280, "h": 100, "icon": "🖱️", "label": "Move mouse, press keys", "sub": "xdotool, PyAutoGUI, Playwright", "color": "teal"},
        "wait": {"x": 430, "y": 300, "w": 280, "h": 100, "icon": "⏳", "label": "Let the screen settle", "sub": "then capture again", "color": "teal"},
    },
    "edges": [
        {"from": "capture", "to": "resize"},
        {"from": "resize", "to": "model", "label": "screenshot (image)", "from_side": "top", "to_side": "top", "via": [(900, 112), (195, 112)], "label_at": (560, 112)},
        {"from": "model", "to": "scale", "label": "tool_use: actions", "from_side": "bottom", "to_side": "bottom", "via": [(195, 625), (570, 625)], "label_at": (380, 625)},
        {"from": "scale", "to": "gate"},
        {"from": "gate", "to": "do"},
        {"from": "do", "to": "wait"},
        {"from": "wait", "to": "capture", "label": "next turn"},
    ],
}
