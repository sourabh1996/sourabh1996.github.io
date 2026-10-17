# Module 5 central idea: lock-in lives in layers, and each layer has a portable escape hatch.
SPEC = {
    "title": "Where agent lock-in lives, layer by layer",
    "accent": "blue",
    "width": 1100, "height": 660,
    "bands": [
        {"y": 70, "h": 95, "label": "Runtime", "color": "coral"},
        {"y": 175, "h": 95, "label": "State", "color": "coral"},
        {"y": 280, "h": 95, "label": "Loop", "color": "amber"},
        {"y": 385, "h": 95, "label": "Tools", "color": "green"},
        {"y": 490, "h": 95, "label": "Model", "color": "green"},
    ],
    "nodes": {
        "r1": {"x": 170, "y": 82, "w": 400, "h": 72, "label": "Hosted runtimes, managed memory,\nprovider-hosted tools", "color": "coral", "size": 14},
        "r2": {"x": 620, "y": 82, "w": 450, "h": 72, "label": "Escape hatch: containers you can move;\nkeep your own copy of data", "color": "gray", "size": 14},
        "s1": {"x": 170, "y": 187, "w": 400, "h": 72, "label": "Sessions, checkpoints and memory\nin a framework's own format", "color": "coral", "size": 14},
        "s2": {"x": 620, "y": 187, "w": 450, "h": 72, "label": "Escape hatch: store plain messages\nand your own typed state", "color": "gray", "size": 14},
        "l1": {"x": 170, "y": 292, "w": 400, "h": 72, "label": "Agent loop, handoffs, graphs,\nguardrail and hook APIs", "color": "amber", "size": 14},
        "l2": {"x": 620, "y": 292, "w": 450, "h": 72, "label": "Escape hatch: thin adapter around\nyour own business logic", "color": "gray", "size": 14},
        "t1": {"x": 170, "y": 397, "w": 400, "h": 72, "label": "Tool definitions and schemas", "color": "green", "size": 14},
        "t2": {"x": 620, "y": 397, "w": 450, "h": 72, "label": "Escape hatch: plain functions,\nJSON Schema, MCP servers", "color": "gray", "size": 14},
        "m1": {"x": 170, "y": 502, "w": 400, "h": 72, "label": "Model provider and message format", "color": "green", "size": 14},
        "m2": {"x": 620, "y": 502, "w": 450, "h": 72, "label": "Escape hatch: model strings, gateways,\nLiteLLM-style adapters", "color": "gray", "size": 14},
    },
    "edges": [],
    "notes": [
        {"x": 550, "y": 615, "text": "Top layers are sticky (hard to move); bottom layers are already portable if you use open formats.", "size": 13},
        {"x": 550, "y": 640, "text": "Traces: export with OpenTelemetry so observability survives a framework change.", "size": 13},
    ],
}
