# Four ways to get JSON from an LLM, from least to most reliable, with value validation beside every step.
SPEC = {
    "title": "Getting JSON from an LLM: the reliability ladder",
    "accent": "amber",
    "width": 1100, "height": 700,
    "nodes": {
        "r1": {"x": 40, "y": 400, "w": 240, "h": 150, "icon": "🙏", "label": "Step 1: Ask", "sub": "\"reply with only JSON\"\nguarantees: nothing\nfails: preamble, ```fences,\nmissing fields", "color": "coral"},
        "r2": {"x": 300, "y": 320, "w": 240, "h": 150, "icon": "🔁", "label": "Step 2: Validate + retry", "sub": "examples, parse, Pydantic,\nre-ask with the errors\ncatches failures,\ncosts extra calls", "color": "amber"},
        "r3": {"x": 560, "y": 240, "w": 240, "h": 150, "icon": "🧱", "label": "Step 3: JSON mode", "sub": "API setting\nguarantees: valid syntax\nfails: wrong fields\nor wrong types", "color": "blue"},
        "r4": {"x": 820, "y": 160, "w": 240, "h": 150, "icon": "🔒", "label": "Step 4: Constrained", "sub": "API takes your schema;\ninvalid tokens masked\nguarantees: the shape\n(not the values)", "color": "green"},
        "val": {"x": 40, "y": 590, "w": 1020, "h": 70, "icon": "", "label": "Always, at every step: check stop reason · business rules · values found in the source · human review when stakes are high", "color": "purple", "size": 15},
    },
    "edges": [
        {"from": "r1", "to": "r2", "from_side": "top", "to_side": "left", "via": [(160, 395)]},
        {"from": "r2", "to": "r3", "from_side": "top", "to_side": "left", "via": [(420, 315)]},
        {"from": "r3", "to": "r4", "from_side": "top", "to_side": "left", "via": [(680, 235)]},
    ],
    "notes": [
        {"x": 40, "y": 110, "text": "more reliable →", "anchor": "start", "weight": 700, "color": "#2e7d4f", "size": 16},
        {"x": 40, "y": 135, "text": "Steps 1-2 work with any model.", "anchor": "start", "size": 13},
        {"x": 40, "y": 155, "text": "Steps 3-4 need API support.", "anchor": "start", "size": 13},
    ],
}
