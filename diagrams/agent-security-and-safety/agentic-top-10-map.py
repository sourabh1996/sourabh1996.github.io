# Where each OWASP Agentic Top 10 (2026) risk lives in an agent system.
SPEC = {
    "title": "OWASP Agentic Top 10: where each risk lives",
    "accent": "purple",
    "width": 1100, "height": 710,
    "groups": [
        {"x": 30, "y": 90, "w": 1040, "h": 150, "label": "What the agent reads", "color": "blue"},
        {"x": 30, "y": 270, "w": 1040, "h": 150, "label": "What the agent is and holds", "color": "purple"},
        {"x": 30, "y": 450, "w": 1040, "h": 230, "label": "What the agent does, and what follows", "color": "coral"},
    ],
    "nodes": {
        "a01": {"x": 60, "y": 130, "w": 310, "h": 84, "label": "ASI01 Goal hijack", "sub": "outside text redirects its goal", "color": "blue"},
        "a06": {"x": 395, "y": 130, "w": 310, "h": 84, "label": "ASI06 Memory poisoning", "sub": "bad facts saved for later", "color": "blue"},
        "a07": {"x": 730, "y": 130, "w": 310, "h": 84, "label": "ASI07 Inter-agent comms", "sub": "spoofed or tampered messages", "color": "blue"},
        "a03": {"x": 60, "y": 310, "w": 310, "h": 84, "label": "ASI03 Identity and privilege", "sub": "borrowed, broad, long-lived keys", "color": "purple"},
        "a04": {"x": 395, "y": 310, "w": 310, "h": 84, "label": "ASI04 Supply chain", "sub": "MCP servers, skills, packages", "color": "purple"},
        "a10": {"x": 730, "y": 310, "w": 310, "h": 84, "label": "ASI10 Rogue agents", "sub": "acting outside policy, unseen", "color": "purple"},
        "a02": {"x": 60, "y": 490, "w": 230, "h": 84, "label": "ASI02 Tool misuse", "sub": "right tool, wrong outcome", "color": "coral"},
        "a05": {"x": 315, "y": 490, "w": 230, "h": 84, "label": "ASI05 Code execution", "sub": "words become running code", "color": "coral"},
        "a08": {"x": 570, "y": 490, "w": 230, "h": 84, "label": "ASI08 Cascading failures", "sub": "one error spreads", "color": "coral"},
        "a09": {"x": 825, "y": 490, "w": 215, "h": 84, "label": "ASI09 Trust exploitation", "sub": "humans approve bad acts", "color": "coral"},
        "least": {"x": 250, "y": 600, "w": 600, "h": 62, "label": "🧭 Least agency: only the autonomy, tools and access the task needs", "color": "gray", "size": 15},
    },
    "edges": [],
}
