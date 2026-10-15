# The six parts of a good prompt, flowing into the model and out as a checkable reply.
SPEC = {
    "title": "Anatomy of a good prompt",
    "accent": "teal",
    "width": 1100, "height": 720,
    "groups": [
        {"x": 40, "y": 100, "w": 640, "h": 520, "label": "The prompt: everything the model reads", "color": "teal"},
    ],
    "nodes": {
        "role": {"x": 70, "y": 135, "w": 280, "h": 135, "icon": "🧑‍💼", "label": "Role and audience", "sub": "who writes, for whom\n\"support team of a food app;\nreaders are upset, on phones\"", "color": "blue"},
        "task": {"x": 370, "y": 135, "w": 280, "h": 135, "icon": "🎯", "label": "Task", "sub": "one clear thing to produce\n\"write a reply to the\ncomplaint below\"", "color": "blue"},
        "data": {"x": 70, "y": 290, "w": 280, "h": 135, "icon": "📎", "label": "Context and data", "sub": "facts it must not guess\norder #88213, ₹320, policy;\ncomplaint inside <tags>", "color": "purple"},
        "rules": {"x": 370, "y": 290, "w": 280, "h": 135, "icon": "📏", "label": "Rules, with reasons", "sub": "\"refund only if policy allows;\nnever promise a time,\nbecause riders vary\"", "color": "purple"},
        "format": {"x": 70, "y": 445, "w": 280, "h": 145, "icon": "🧾", "label": "Output format", "sub": "a shape code or a reader\ncan use: \"max 3 sentences\",\n\"answer in <answer> tags\",\nor a JSON schema", "color": "amber"},
        "examples": {"x": 370, "y": 445, "w": 280, "h": 145, "icon": "🧩", "label": "Examples", "sub": "1 to 5 diverse samples\nof input → ideal output;\nthe model copies the pattern", "color": "amber"},
        "llm": {"x": 750, "y": 290, "w": 150, "h": 135, "icon": "🤖", "label": "LLM", "sub": "fills any gap\nwith a guess", "color": "gray"},
        "reply": {"x": 930, "y": 290, "w": 140, "h": 135, "icon": "✅", "label": "Reply", "sub": "checked by\ncode or an\neval set", "color": "green"},
    },
    "edges": [
        {"from": "rules", "to": "llm", "label": "reads", "label_at": (715, 340)},
        {"from": "llm", "to": "reply"},
    ],
    "notes": [
        {"x": 550, "y": 660, "text": "Newcomer test: could a smart colleague with no background do the task from this text alone?", "weight": 700, "color": "#1f766d", "size": 15},
        {"x": 550, "y": 688, "text": "Not every prompt needs all six parts; every weak prompt is missing at least one.", "size": 13},
    ],
}
