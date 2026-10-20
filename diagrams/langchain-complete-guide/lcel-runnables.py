# Module 6 central idea: every component is a Runnable, LCEL composes them, and the composite is a Runnable too.
SPEC = {
    "title": "LCEL: build with Runnables, get one interface",
    "accent": "blue",
    "width": 1100, "height": 760,
    "bands": [
        {"y": 85, "h": 180, "label": "Parts", "color": "blue", "tile": 130},
        {"y": 285, "h": 200, "label": "Compose", "color": "purple", "tile": 130},
        {"y": 505, "h": 190, "label": "Get for\nfree", "color": "green", "tile": 130},
    ],
    "nodes": {
        "prompt": {"x": 175, "y": 120, "w": 205, "h": 110, "icon": "📝", "label": "Prompt template", "sub": "dict in\nPromptValue out", "color": "blue"},
        "model": {"x": 400, "y": 120, "w": 205, "h": 110, "icon": "🧠", "label": "Chat model", "sub": "messages in\nAIMessage out", "color": "blue"},
        "parser": {"x": 625, "y": 120, "w": 205, "h": 110, "icon": "🔍", "label": "Output parser", "sub": "message in\nstr, dict or object out", "color": "blue"},
        "fn": {"x": 850, "y": 120, "w": 210, "h": 110, "icon": "🐍", "label": "Your function", "sub": "RunnableLambda\nany Python code", "color": "blue"},
        "seq": {"x": 175, "y": 320, "w": 205, "h": 130, "icon": "➡️", "label": "a | b | c", "sub": "RunnableSequence\nsteps in order", "color": "purple"},
        "par": {"x": 400, "y": 320, "w": 205, "h": 130, "icon": "🔀", "label": "{\"x\": a, \"y\": b}", "sub": "RunnableParallel\nsame input, side by side", "color": "purple"},
        "pass": {"x": 625, "y": 320, "w": 205, "h": 130, "icon": "➕", "label": ".assign(...)", "sub": "RunnablePassthrough\nkeep input, add keys", "color": "purple"},
        "branch": {"x": 850, "y": 320, "w": 210, "h": 130, "icon": "🚦", "label": "RunnableBranch", "sub": "pick a path\nby condition", "color": "purple"},
        "calls": {"x": 175, "y": 540, "w": 205, "h": 120, "icon": "⚡", "label": "invoke · batch · stream", "sub": "plus async twins\nainvoke, abatch, astream", "color": "green"},
        "robust": {"x": 400, "y": 540, "w": 205, "h": 120, "icon": "🛟", "label": "Retries, fallbacks", "sub": "with_retry()\nwith_fallbacks([...])", "color": "green"},
        "config": {"x": 625, "y": 540, "w": 205, "h": 120, "icon": "🏷️", "label": "Config and tracing", "sub": "tags, metadata, callbacks\nseen in LangSmith", "color": "green"},
        "schema": {"x": 850, "y": 540, "w": 210, "h": 120, "icon": "📐", "label": "Schemas and graph", "sub": "input_schema, output_schema\nget_graph()", "color": "green"},
    },
    "edges": [
        {"from": "prompt", "to": "model"},
        {"from": "model", "to": "parser"},
    ],
    "notes": [
        {"x": 618, "y": 728, "text": "A composed chain is itself a Runnable, so it can be a step inside a bigger chain.", "size": 15, "weight": 600, "color": "#2b5fa8"},
    ],
}
