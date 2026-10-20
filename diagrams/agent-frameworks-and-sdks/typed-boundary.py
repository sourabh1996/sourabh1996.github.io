# Module 4 central idea: put a typed boundary between the model and your code.
SPEC = {
    "title": "A typed boundary between the model and your code",
    "accent": "purple",
    "width": 1100, "height": 640,
    "bands": [
        {"y": 70, "h": 170, "label": "Untyped", "color": "coral"},
        {"y": 260, "h": 350, "label": "Typed", "color": "green"},
    ],
    "nodes": {
        "m1": {"x": 170, "y": 100, "w": 200, "h": 110, "icon": "🧠", "label": "LLM", "sub": "free text out", "color": "gray"},
        "s1": {"x": 450, "y": 100, "w": 220, "h": 110, "icon": "📝", "label": "\"approx ₹1,500,\nmaybe urgent?\"", "sub": "", "color": "coral"},
        "c1": {"x": 760, "y": 100, "w": 290, "h": 110, "icon": "💥", "label": "Your code guesses", "sub": "regex, string checks,\nsilent bugs later", "color": "coral"},
        "m2": {"x": 170, "y": 290, "w": 200, "h": 110, "icon": "🧠", "label": "LLM or\ndecision model", "sub": "", "color": "gray"},
        "v": {"x": 450, "y": 290, "w": 220, "h": 110, "icon": "🛂", "label": "Schema check", "sub": "Pydantic / Zod", "color": "purple"},
        "c2": {"x": 760, "y": 290, "w": 290, "h": 110, "icon": "✅", "label": "Typed object", "sub": "amount: int = 1500\nurgent: bool = True", "color": "green"},
        "retry": {"x": 450, "y": 460, "w": 220, "h": 110, "icon": "🔁", "label": "Retry with\nthe error", "sub": "", "color": "amber"},
        "tools": {"x": 760, "y": 460, "w": 290, "h": 110, "icon": "🧰", "label": "Tools in this module", "sub": "Pydantic AI, Instructor,\nJev, DSPy signatures", "color": "blue"},
    },
    "edges": [
        {"from": "m1", "to": "s1"},
        {"from": "s1", "to": "c1"},
        {"from": "m2", "to": "v", "label": "output"},
        {"from": "v", "to": "c2", "label": "valid"},
        {"from": "v", "to": "retry", "label": "invalid", "from_side": "bottom", "to_side": "top"},
        {"from": "retry", "to": "m2", "from_side": "left", "to_side": "bottom", "via": [(270, 515)]},
    ],
}
