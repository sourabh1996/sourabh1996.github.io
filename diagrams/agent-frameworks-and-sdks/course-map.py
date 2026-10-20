# The agent framework landscape this course walks through, as four layers.
SPEC = {
    "title": "The agent framework landscape, layer by layer",
    "accent": "purple",
    "width": 1100, "height": 760,
    "bands": [
        {"y": 80, "h": 150, "label": "Vendor\nSDKs", "color": "blue"},
        {"y": 245, "h": 150, "label": "Frame-\nworks", "color": "green"},
        {"y": 410, "h": 150, "label": "Typed\nlayer", "color": "amber"},
        {"y": 575, "h": 160, "label": "Choosing", "color": "purple"},
    ],
    "nodes": {
        "claude": {"x": 170, "y": 100, "w": 165, "h": 110, "icon": "🟠", "label": "Claude\nAgent SDK", "sub": "Claude Code as a library", "color": "blue"},
        "openai": {"x": 350, "y": 100, "w": 165, "h": 110, "icon": "🟢", "label": "OpenAI\nAgents SDK", "sub": "handoffs, guardrails", "color": "blue"},
        "adk": {"x": 530, "y": 100, "w": 165, "h": 110, "icon": "🔵", "label": "Google ADK", "sub": "agents + graph workflows", "color": "blue"},
        "maf": {"x": 710, "y": 100, "w": 165, "h": 110, "icon": "🟦", "label": "Microsoft\nAgent Framework", "sub": "AutoGen + SK, merged", "color": "blue"},
        "aws": {"x": 890, "y": 100, "w": 180, "h": 110, "icon": "🟧", "label": "Strands +\nAgentCore", "sub": "agent + managed runtime", "color": "blue"},
        "deep": {"x": 170, "y": 265, "w": 165, "h": 110, "icon": "🧠", "label": "Deep Agents", "sub": "ready-made harness", "color": "green"},
        "crew": {"x": 350, "y": 265, "w": 165, "h": 110, "icon": "👥", "label": "CrewAI", "sub": "roles, tasks, flows", "color": "green"},
        "llama": {"x": 530, "y": 265, "w": 165, "h": 110, "icon": "🦙", "label": "LlamaIndex", "sub": "agents over your data", "color": "green"},
        "smol": {"x": 710, "y": 265, "w": 165, "h": 110, "icon": "🐍", "label": "smolagents", "sub": "act by writing code", "color": "green"},
        "ts": {"x": 890, "y": 265, "w": 180, "h": 110, "icon": "📘", "label": "Mastra +\nAI SDK", "sub": "agents in TypeScript", "color": "green"},
        "why": {"x": 170, "y": 430, "w": 165, "h": 110, "icon": "🛡️", "label": "Why types", "sub": "text in, objects out", "color": "amber"},
        "pyd": {"x": 350, "y": 430, "w": 165, "h": 110, "icon": "🧩", "label": "Pydantic AI", "sub": "typed agents", "color": "amber"},
        "inst": {"x": 530, "y": 430, "w": 165, "h": 110, "icon": "📐", "label": "Instructor", "sub": "validate + retry", "color": "amber"},
        "jev": {"x": 710, "y": 430, "w": 165, "h": 110, "icon": "🎯", "label": "Decision\nmodels (Jev)", "sub": "answers with odds", "color": "amber"},
        "dspy": {"x": 890, "y": 430, "w": 180, "h": 110, "icon": "⚙️", "label": "DSPy", "sub": "optimise, don't hand-tune", "color": "amber"},
        "compare": {"x": 170, "y": 600, "w": 260, "h": 110, "icon": "⚖️", "label": "Same task,\nmany frameworks", "sub": "compare on one job", "color": "purple"},
        "port": {"x": 470, "y": 600, "w": 260, "h": 110, "icon": "🔓", "label": "Avoid lock-in", "sub": "MCP, A2A, OpenTelemetry", "color": "purple"},
        "lab": {"x": 770, "y": 600, "w": 300, "h": 110, "icon": "🧪", "label": "Lab: one agent,\nthree frameworks", "sub": "shared tests prove it", "color": "purple"},
    },
    "edges": [
        {"from": "compare", "to": "port"},
        {"from": "port", "to": "lab"},
    ],
    "notes": [
        {"x": 620, "y": 752, "text": "Underneath every box is the same loop you built by hand: model, tools, state, stop rules.", "size": 13},
    ],
}
