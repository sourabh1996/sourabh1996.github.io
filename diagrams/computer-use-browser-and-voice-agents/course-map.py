# Three kinds of agents that act through human interfaces, sharing one loop and one safety layer.
SPEC = {
    "title": "Agents that use human interfaces",
    "accent": "teal",
    "width": 1100, "height": 700,
    "groups": [
        {"x": 30, "y": 95, "w": 1040, "h": 250, "label": "What the agent perceives and how it acts", "color": "blue"},
        {"x": 30, "y": 385, "w": 1040, "h": 150, "label": "The loop all three share", "color": "teal"},
        {"x": 30, "y": 570, "w": 1040, "h": 110, "label": "Your harness keeps it safe", "color": "coral"},
    ],
    "nodes": {
        "web": {"x": 60, "y": 130, "w": 300, "h": 190, "icon": "🌐", "label": "Browser agent",
                 "sub": "sees: page structure,\naccessibility tree, screenshot\nacts: click, fill, navigate\nModule 2", "color": "blue"},
        "cu": {"x": 400, "y": 130, "w": 300, "h": 190, "icon": "🖥️", "label": "Computer-use agent",
                "sub": "sees: screenshots of a desktop\nacts: mouse and keyboard\nat pixel coordinates\nModule 3", "color": "purple"},
        "voice": {"x": 740, "y": 130, "w": 300, "h": 190, "icon": "🎙️", "label": "Voice agent",
                   "sub": "hears: a live audio stream\nacts: speaks, calls tools,\nyields when interrupted\nModule 4", "color": "amber"},
        "obs": {"x": 70, "y": 425, "w": 200, "h": 85, "icon": "👀", "label": "Observe", "sub": "page, screen or speech", "color": "teal"},
        "dec": {"x": 330, "y": 425, "w": 200, "h": 85, "icon": "🧠", "label": "Decide", "sub": "model picks one step", "color": "teal"},
        "act": {"x": 590, "y": 425, "w": 200, "h": 85, "icon": "🛠️", "label": "Act", "sub": "your code executes it", "color": "teal"},
        "ver": {"x": 850, "y": 425, "w": 190, "h": 85, "icon": "✅", "label": "Verify", "sub": "did it really work?", "color": "teal"},
        "iso": {"x": 60, "y": 605, "w": 225, "h": 55, "label": "📦 Isolated browser or VM", "color": "coral", "size": 15},
        "allow": {"x": 310, "y": 605, "w": 225, "h": 55, "label": "🚧 Allowlisted sites", "color": "coral", "size": 15},
        "human": {"x": 560, "y": 605, "w": 225, "h": 55, "label": "🙋 Human approves risky steps", "color": "coral", "size": 14},
        "untrust": {"x": 810, "y": 605, "w": 230, "h": 55, "label": "⚠️ Screen text is untrusted", "color": "coral", "size": 14},
    },
    "edges": [
        {"from": "obs", "to": "dec"},
        {"from": "dec", "to": "act"},
        {"from": "act", "to": "ver"},
        {"from": "ver", "to": "obs", "label": "next turn", "from_side": "bottom", "to_side": "bottom",
         "via": [(945, 528), (170, 528)], "label_at": (560, 528)},
    ],
}
