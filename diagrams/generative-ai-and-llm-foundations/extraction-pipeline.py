# The reliable extraction pipeline from the lab: prompt, model, parse, three layers of checks, repair loop, review queue.
SPEC = {
    "title": "A reliable extraction pipeline",
    "accent": "purple",
    "width": 1100, "height": 760,
    "groups": [
        {"x": 470, "y": 110, "w": 300, "h": 470, "label": "Three layers of checks", "color": "purple"},
    ],
    "nodes": {
        "sms": {"x": 40, "y": 130, "w": 180, "h": 120, "icon": "📩", "label": "Raw SMS", "sub": "\"Rs.450.00 debited\nfrom A/c XX4821...\"", "color": "blue"},
        "prompt": {"x": 40, "y": 300, "w": 180, "h": 130, "icon": "📝", "label": "Prompt", "sub": "system rules\n+ schema + example\n+ SMS in <sms> tags", "color": "blue"},
        "llm": {"x": 260, "y": 300, "w": 170, "h": 130, "icon": "🤖", "label": "LLM", "sub": "proposes JSON", "color": "gray"},
        "parse": {"x": 260, "y": 130, "w": 170, "h": 120, "icon": "🧹", "label": "Parse", "sub": "strip ```fences\nand preambles", "color": "teal"},
        "schema": {"x": 500, "y": 145, "w": 240, "h": 115, "icon": "📐", "label": "Schema", "sub": "types, enums, required\n(Pydantic)", "color": "purple"},
        "rules": {"x": 500, "y": 285, "w": 240, "h": 115, "icon": "📏", "label": "Business rules", "sub": "₹0 < amount ≤ ₹10 lakh,\n12-digit ref, no future date", "color": "purple"},
        "ground": {"x": 500, "y": 425, "w": 240, "h": 125, "icon": "🔍", "label": "Grounding", "sub": "is each amount, ref and\naccount number really\nin the SMS?", "color": "purple"},
        "ok": {"x": 850, "y": 130, "w": 210, "h": 120, "icon": "✅", "label": "Clean record", "sub": "saved to the database", "color": "green"},
        "repair": {"x": 850, "y": 300, "w": 210, "h": 150, "icon": "🔧", "label": "Repair message", "sub": "\"upi_ref 630012457789\ndoes not appear in\nthe SMS. Reply with\ncorrected JSON.\"", "color": "amber"},
        "review": {"x": 850, "y": 500, "w": 210, "h": 120, "icon": "🧑‍💻", "label": "Human review", "sub": "after 2 failed attempts,\nwith error history", "color": "coral"},
    },
    "edges": [
        {"from": "sms", "to": "prompt"},
        {"from": "prompt", "to": "llm"},
        {"from": "llm", "to": "parse"},
        {"from": "parse", "to": "schema", "to_side": "left"},
        {"from": "schema", "to": "ok", "label": "all pass", "label_at": (800, 175)},
        {"from": "rules", "to": "repair", "label": "fail", "label_at": (800, 345)},
        {"from": "ground", "to": "review", "from_side": "right", "to_side": "left", "via": [(800, 487), (800, 560)], "label": "fail twice", "label_at": (800, 525)},
        {"from": "repair", "to": "llm", "from_side": "right", "to_side": "bottom", "via": [(1080, 375), (1080, 655), (345, 655)], "label": "retry with errors", "label_at": (580, 640)},
    ],
    "notes": [
        {"x": 550, "y": 705, "text": "The model is allowed to be wrong; the pipeline is not allowed to pass it on.", "weight": 700, "color": "#5b3fa0", "size": 15},
        {"x": 550, "y": 732, "text": "Constrained decoding removes shape errors; grounding, rules and review still catch wrong values.", "size": 13},
    ],
}
