# The GenAI project lifecycle as a loop of seven stages with the evaluation set at its centre.
SPEC = {
    "title": "The GenAI project lifecycle",
    "accent": "teal",
    "width": 1100, "height": 700,
    "nodes": {
        "scope": {"x": 60, "y": 90, "w": 230, "h": 130, "icon": "🎯", "label": "Step 1: Scope", "sub": "problem, users, out of scope;\nsuccess criteria as numbers", "color": "blue"},
        "eval": {"x": 435, "y": 90, "w": 230, "h": 130, "icon": "📋", "label": "Step 2: Evaluation set", "sub": "real inputs, hard cases,\na rule for \"correct\"", "color": "amber"},
        "choose": {"x": 810, "y": 90, "w": 230, "h": 130, "icon": "⚖️", "label": "Step 3: Model and approach", "sub": "adaptation ladder;\ncandidates tested on evals", "color": "purple"},
        "proto": {"x": 810, "y": 300, "w": 230, "h": 130, "icon": "🧪", "label": "Step 4: Prototype", "sub": "prompts, retrieval, tools,\nstructured output", "color": "teal"},
        "iterate": {"x": 810, "y": 510, "w": 230, "h": 130, "icon": "🔁", "label": "Step 5: Evaluate, iterate", "sub": "read failures, group by\ncause, fix, re-run all", "color": "coral"},
        "launch": {"x": 435, "y": 510, "w": 230, "h": 130, "icon": "🚦", "label": "Step 6: Harden, launch", "sub": "guardrails, cost budget;\nshadow, canary, rollout", "color": "green"},
        "monitor": {"x": 60, "y": 510, "w": 230, "h": 130, "icon": "📈", "label": "Step 7: Monitor, improve", "sub": "quality, safety, cost,\nlatency; pinned versions", "color": "pink"},
        "gate": {"x": 400, "y": 300, "w": 300, "h": 130, "icon": "🛂", "label": "Release gate", "sub": "scores on the evaluation set:\nquality, safety, speed, cost", "color": "gray"},
    },
    "edges": [
        {"from": "scope", "to": "eval"},
        {"from": "eval", "to": "choose"},
        {"from": "choose", "to": "proto"},
        {"from": "proto", "to": "iterate"},
        {"from": "iterate", "to": "launch", "label": "passes gate"},
        {"from": "launch", "to": "monitor"},
        {"from": "monitor", "to": "eval", "label": "new failures become test cases", "from_side": "top", "to_side": "bottom", "via": [(175, 265), (550, 265)], "label_at": (330, 285)},
        {"from": "gate", "to": "launch", "label": "must pass", "from_side": "bottom", "to_side": "top"},
    ],
    "notes": [{"x": 550, "y": 675, "text": "The evaluation set is the spine: it picks the model, compares versions and gates every release."}],
}
