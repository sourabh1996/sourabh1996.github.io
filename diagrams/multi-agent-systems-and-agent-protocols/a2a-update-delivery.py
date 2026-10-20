# The three ways an A2A client learns about task progress: polling, streaming and push notifications.
SPEC = {
    "title": "Three ways to follow a long A2A task",
    "accent": "blue",
    "width": 1100, "height": 700,
    "groups": [
        {"x": 25, "y": 90, "w": 340, "h": 580, "label": "Polling", "color": "gray"},
        {"x": 380, "y": 90, "w": 340, "h": 580, "label": "Streaming (SSE)", "color": "blue"},
        {"x": 735, "y": 90, "w": 340, "h": 580, "label": "Push notifications", "color": "green"},
    ],
    "nodes": {
        "pc": {"x": 65, "y": 130, "w": 260, "h": 80, "icon": "🧭", "label": "Client", "color": "purple", "size": 17},
        "pa": {"x": 65, "y": 330, "w": 260, "h": 80, "icon": "🚆", "label": "Remote agent", "color": "teal", "size": 17},
        "pn": {"x": 65, "y": 450, "w": 260, "h": 190, "label": "SendMessage, then\nGetTask every few seconds",
               "sub": "simplest, works everywhere\nwasted calls, slower to notice\nfine behind strict firewalls", "color": "gray", "size": 15},
        "sc": {"x": 420, "y": 130, "w": 260, "h": 80, "icon": "🧭", "label": "Client", "color": "purple", "size": 17},
        "sa": {"x": 420, "y": 330, "w": 260, "h": 80, "icon": "🚆", "label": "Remote agent", "color": "teal", "size": 17},
        "sn": {"x": 420, "y": 450, "w": 260, "h": 190, "label": "SendStreamingMessage\nkeeps one connection open",
               "sub": "events arrive instantly, in order\nartifacts in chunks\nreconnect with SubscribeToTask", "color": "blue", "size": 15},
        "uc": {"x": 775, "y": 130, "w": 260, "h": 80, "icon": "🧭", "label": "Client webhook", "color": "purple", "size": 17},
        "ua": {"x": 775, "y": 330, "w": 260, "h": 80, "icon": "🚆", "label": "Remote agent", "color": "teal", "size": 17},
        "un": {"x": 775, "y": 450, "w": 260, "h": 190, "label": "Agent POSTs to your URL\nwhen the task changes",
               "sub": "no open connection, hours-long jobs\nat-least-once: dedupe events\ncheck auth, block SSRF", "color": "green", "size": 15},
    },
    "edges": [
        {"from": "pc", "to": "pa", "label": "GetTask? GetTask?"},
        {"from": "sa", "to": "sc", "label": "event, event, event"},
        {"from": "ua", "to": "uc", "label": "HTTP POST on change"},
    ],
}
