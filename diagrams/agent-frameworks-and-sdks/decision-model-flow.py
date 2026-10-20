# How a decision model like Jev answers: one request, typed questions answered in parallel, probabilities out.
SPEC = {
    "title": "A decision model answers typed questions, not prompts",
    "accent": "purple",
    "width": 1100, "height": 640,
    "groups": [
        {"x": 300, "y": 80, "w": 470, "h": 400, "label": "One request to the decision model", "color": "purple"},
    ],
    "nodes": {
        "state": {"x": 30, "y": 200, "w": 230, "h": 140, "icon": "📄", "label": "State", "sub": "text, JSON or array;\nevery question reads\nthe same state", "color": "blue"},
        "q1": {"x": 325, "y": 120, "w": 200, "h": 95, "icon": "🔘", "label": "Choice", "sub": "billing / delivery /\naccount / other", "color": "purple"},
        "q2": {"x": 325, "y": 240, "w": 200, "h": 95, "icon": "📶", "label": "Score", "sub": "urgency levels 0..2", "color": "purple"},
        "q3": {"x": 325, "y": 360, "w": 200, "h": 95, "icon": "✔️", "label": "Noul (yes/no)", "sub": "asks for a refund?", "color": "purple"},
        "jev": {"x": 570, "y": 120, "w": 180, "h": 335, "icon": "⚡", "label": "Jev", "sub": "answers all questions\nin parallel, no text\ngenerated", "color": "teal"},
        "ans": {"x": 820, "y": 207, "w": 250, "h": 160, "icon": "🧮", "label": "Typed answers", "sub": "choice + probabilities\n+ confidence;\nscore; P(yes)", "color": "green"},
        "code": {"x": 820, "y": 395, "w": 250, "h": 120, "icon": "🚦", "label": "Your code decides", "sub": "high confidence: act\nmiddle: LLM or review\nlow: a person", "color": "amber"},
        "llm": {"x": 300, "y": 520, "w": 470, "h": 90, "icon": "🧠", "label": "LLM fallback", "sub": "only for the unsure cases, or when text must be written", "color": "gray"},
    },
    "edges": [
        {"from": "state", "to": "q2"},
        {"from": "q1", "to": "jev", "from_side": "right", "to_side": "left", "via": [(548, 167), (548, 287)]},
        {"from": "q2", "to": "jev"},
        {"from": "q3", "to": "jev", "from_side": "right", "to_side": "left", "via": [(548, 407), (548, 287)]},
        {"from": "jev", "to": "ans", "label": "one call"},
        {"from": "ans", "to": "code", "from_side": "bottom", "to_side": "top"},
        {"from": "code", "to": "llm", "from_side": "bottom", "to_side": "right", "via": [(945, 565)], "label": "unsure"},
    ],
}
