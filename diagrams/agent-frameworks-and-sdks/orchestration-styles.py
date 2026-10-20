# Five orchestration frameworks, five different core ideas.
SPEC = {
    "title": "Five frameworks, five core ideas",
    "accent": "green",
    "width": 1100, "height": 600,
    "nodes": {
        "deep": {"x": 30, "y": 90, "w": 196, "h": 260, "icon": "🧠", "label": "Deep Agents", "sub": "a ready-made harness:\nfiles, subagents,\nsummaries, skills,\napprovals", "color": "green"},
        "crew": {"x": 241, "y": 90, "w": 196, "h": 260, "icon": "👥", "label": "CrewAI", "sub": "agents with roles\ndo tasks as a crew;\nflows add code-driven\nsteps and state", "color": "teal"},
        "llama": {"x": 452, "y": 90, "w": 196, "h": 260, "icon": "🦙", "label": "LlamaIndex", "sub": "steps react to\ntyped events;\nagents over\nyour documents", "color": "blue"},
        "smol": {"x": 663, "y": 90, "w": 196, "h": 260, "icon": "🐍", "label": "smolagents", "sub": "the model writes\nPython as its action;\nan executor runs it", "color": "amber"},
        "ts": {"x": 874, "y": 90, "w": 196, "h": 260, "icon": "📘", "label": "Mastra +\nAI SDK", "sub": "TypeScript agents,\nZod-typed tools,\nworkflows, UI\nstreaming", "color": "purple"},
        "k1": {"x": 30, "y": 370, "w": 196, "h": 60, "label": "Unit: a long task", "color": "gray", "size": 14},
        "k2": {"x": 241, "y": 370, "w": 196, "h": 60, "label": "Unit: a role", "color": "gray", "size": 14},
        "k3": {"x": 452, "y": 370, "w": 196, "h": 60, "label": "Unit: an event", "color": "gray", "size": 14},
        "k4": {"x": 663, "y": 370, "w": 196, "h": 60, "label": "Unit: a code snippet", "color": "gray", "size": 14},
        "k5": {"x": 874, "y": 370, "w": 196, "h": 60, "label": "Unit: a typed step", "color": "gray", "size": 14},
        "model": {"x": 30, "y": 470, "w": 330, "h": 90, "icon": "🎲", "label": "Model decides more", "sub": "Deep Agents, crews, code agents", "color": "coral"},
        "code": {"x": 740, "y": 470, "w": 330, "h": 90, "icon": "📏", "label": "Your code decides more", "sub": "flows, event workflows, TS workflows", "color": "blue"},
    },
    "edges": [
        {"from": "model", "to": "code", "label": "every framework offers both ends"},
    ],
}
