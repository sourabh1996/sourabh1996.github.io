# Architecture of an orchestrator (lead agent) with parallel subagents.
SPEC = {
    "title": "Orchestrator and subagents",
    "accent": "purple",
    "width": 1100, "height": 800,
    "groups": [
        {"x": 300, "y": 300, "w": 500, "h": 250, "label": "Subagents: fresh window each, run in parallel", "color": "blue"},
    ],
    "nodes": {
        "user": {"x": 40, "y": 110, "w": 170, "h": 110, "icon": "🙋", "label": "User", "sub": "\"Compare 3 EV makers\"", "color": "gray"},
        "lead": {"x": 380, "y": 95, "w": 340, "h": 140, "icon": "🧭", "label": "Lead agent",
                 "sub": "plans, writes task briefs,\nmerges results, decides when done", "color": "purple"},
        "plan": {"x": 830, "y": 90, "w": 230, "h": 70, "label": "🗒️ Plan saved to memory", "color": "gray", "size": 15},
        "budget": {"x": 830, "y": 175, "w": 230, "h": 70, "label": "⏱️ Effort budget", "sub": "how many agents, how many calls", "color": "gray", "size": 15},
        "s1": {"x": 320, "y": 335, "w": 145, "h": 190, "icon": "🔎", "label": "Subagent A", "sub": "brief: Tata EV\ntools: web search\n8 calls", "color": "blue"},
        "s2": {"x": 478, "y": 335, "w": 145, "h": 190, "icon": "🔎", "label": "Subagent B", "sub": "brief: Mahindra EV\ntools: web search\n8 calls", "color": "blue"},
        "s3": {"x": 636, "y": 335, "w": 145, "h": 190, "icon": "🔎", "label": "Subagent C", "sub": "brief: MG EV\ntools: web search\n8 calls", "color": "blue"},
        "tools": {"x": 40, "y": 370, "w": 200, "h": 120, "icon": "🧰", "label": "Tools", "sub": "search, fetch page,\nread files", "color": "gray"},
        "store": {"x": 860, "y": 370, "w": 200, "h": 120, "icon": "🗄️", "label": "Shared store", "sub": "full notes saved here;\nonly references go back", "color": "teal"},
        "verify": {"x": 380, "y": 620, "w": 340, "h": 120, "icon": "✅", "label": "Verify and cite",
                   "sub": "check claims against sources,\nremove duplicates", "color": "green"},
        "answer": {"x": 830, "y": 630, "w": 230, "h": 100, "icon": "📄", "label": "Final report", "color": "green"},
    },
    "edges": [
        {"from": "user", "to": "lead", "label": "question"},
        {"from": "lead", "to": "plan", "from_side": "right", "to_side": "left", "via": [(775, 125)]},
        {"from": "lead", "to": "budget", "from_side": "right", "to_side": "left", "via": [(775, 210)]},
        {"from": "lead", "to": "s2", "label": "task briefs (fan out)", "from_side": "bottom", "to_side": "top"},
        {"from": "tools", "to": "s1", "both": True, "to_side": "left", "from_side": "right"},
        {"from": "s3", "to": "store", "label": "notes", "from_side": "right", "to_side": "left"},
        {"from": "s2", "to": "verify", "label": "short summaries + refs", "from_side": "bottom", "to_side": "top"},
        {"from": "verify", "to": "answer", "from_side": "right", "to_side": "left"},
    ],
    "notes": [
        {"x": 550, "y": 775, "text": "Each subagent may read 50,000 tokens; the lead only sees about 1,000 back from each.", "size": 14, "weight": 600, "color": "#1f2328"},
    ],
}
