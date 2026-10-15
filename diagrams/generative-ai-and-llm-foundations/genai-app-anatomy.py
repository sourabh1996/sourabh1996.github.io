# The shape most industry GenAI applications share: channel, backend, context, model, checks, human review, systems, logs.
SPEC = {
    "title": "Inside a typical industry GenAI application",
    "accent": "blue",
    "width": 1100, "height": 660,
    "groups": [
        {"x": 225, "y": 75, "w": 640, "h": 430, "label": "Your application", "color": "purple"},
    ],
    "nodes": {
        "channel": {"x": 25, "y": 200, "w": 165, "h": 150, "icon": "📱", "label": "Channel", "sub": "WhatsApp, app,\nwebsite, phone,\ninternal tool", "color": "blue"},
        "backend": {"x": 245, "y": 210, "w": 165, "h": 130, "icon": "⚙️", "label": "Backend", "sub": "who is the user?\nwhat may they see?\nbuild the prompt", "color": "purple"},
        "context": {"x": 245, "y": 105, "w": 400, "h": 80, "icon": "📂", "label": "Company context", "sub": "policy PDFs, catalogue, customer account", "color": "amber"},
        "model": {"x": 470, "y": 210, "w": 165, "h": 130, "icon": "🧠", "label": "Foundation model", "sub": "API or\nself-hosted", "color": "teal"},
        "checks": {"x": 690, "y": 210, "w": 150, "h": 130, "icon": "🛡️", "label": "Checks", "sub": "schema, business\nrules, safety", "color": "coral"},
        "human": {"x": 690, "y": 375, "w": 150, "h": 110, "icon": "🧑‍💼", "label": "Human review", "sub": "risky or unsure\ncases", "color": "pink"},
        "systems": {"x": 915, "y": 200, "w": 165, "h": 150, "icon": "🏦", "label": "Answer or act", "sub": "reply to user;\nCRM, core banking,\nhospital records", "color": "green"},
        "logs": {"x": 245, "y": 375, "w": 390, "h": 110, "icon": "📊", "label": "Logs and evaluation", "sub": "every request recorded: quality,\ncost, new failure patterns", "color": "gray"},
    },
    "edges": [
        {"from": "channel", "to": "backend", "label": "request"},
        {"from": "context", "to": "backend", "from_side": "bottom", "to_side": "top"},
        {"from": "backend", "to": "model", "label": "prompt", "label_at": (440, 258)},
        {"from": "model", "to": "checks"},
        {"from": "checks", "to": "human", "label": "flagged"},
        {"from": "checks", "to": "systems", "label": "ok", "label_at": (890, 258)},
        {"from": "human", "to": "systems", "from_side": "right", "to_side": "bottom"},
        {"from": "model", "to": "logs", "from_side": "bottom", "to_side": "top"},
    ],
    "notes": [{"x": 550, "y": 560, "text": "The model is one box. The boxes around it make the application safe in a real industry."},
              {"x": 550, "y": 595, "text": "Industries differ in the context, the checks and who reviews, far more than in the model."}],
}
