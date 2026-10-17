# How a Claude Agent SDK app is wired: your Python, the bundled Claude Code runtime, tools and the API.
SPEC = {
    "title": "Inside a Claude Agent SDK app",
    "accent": "amber",
    "width": 1100, "height": 640,
    "groups": [
        {"x": 30, "y": 85, "w": 300, "h": 520, "label": "Your Python program", "color": "blue"},
        {"x": 365, "y": 85, "w": 400, "h": 520, "label": "Claude Code runtime (bundled CLI)", "color": "amber"},
        {"x": 800, "y": 85, "w": 270, "h": 520, "label": "Outside world", "color": "green"},
    ],
    "nodes": {
        "query": {"x": 55, "y": 120, "w": 250, "h": 85, "icon": "📨", "label": "query() or\nClaudeSDKClient", "color": "blue"},
        "opts": {"x": 55, "y": 222, "w": 250, "h": 98, "icon": "⚙️", "label": "ClaudeAgentOptions", "sub": "tools, permission_mode,\nmax_turns, budget", "color": "blue"},
        "mytools": {"x": 55, "y": 335, "w": 250, "h": 80, "icon": "🧩", "label": "@tool functions", "sub": "in-process MCP server", "color": "blue"},
        "hooks": {"x": 55, "y": 435, "w": 250, "h": 70, "icon": "🪝", "label": "Hooks + can_use_tool", "color": "blue", "size": 15},
        "msgs": {"x": 55, "y": 515, "w": 250, "h": 75, "icon": "📬", "label": "Message stream", "sub": "assistant, tool, result", "color": "blue"},
        "loop": {"x": 400, "y": 120, "w": 330, "h": 110, "icon": "🔁", "label": "Agent loop", "sub": "ask Claude, run tool,\nfeed result back, repeat", "color": "amber"},
        "builtin": {"x": 400, "y": 248, "w": 160, "h": 106, "icon": "🧰", "label": "Built-in tools", "sub": "Read, Edit, Bash,\nGrep, WebFetch", "color": "amber"},
        "sub": {"x": 570, "y": 250, "w": 160, "h": 100, "icon": "👥", "label": "Subagents", "sub": "fresh context each", "color": "amber"},
        "perm": {"x": 400, "y": 368, "w": 330, "h": 82, "icon": "🛡️", "label": "Permission check", "sub": "allow, ask, or deny every tool call", "color": "amber"},
        "ctx": {"x": 400, "y": 465, "w": 330, "h": 120, "icon": "🗂️", "label": "Context management", "sub": "sessions (resume, fork),\nskills, CLAUDE.md, compaction", "color": "amber"},
        "api": {"x": 830, "y": 120, "w": 210, "h": 100, "icon": "🧠", "label": "Claude API", "sub": "claude-opus-5-5", "color": "green"},
        "mcp": {"x": 830, "y": 250, "w": 210, "h": 100, "icon": "🔌", "label": "MCP servers", "sub": "stdio or HTTP", "color": "green"},
        "fs": {"x": 830, "y": 380, "w": 210, "h": 100, "icon": "💻", "label": "Files + shell", "sub": "in cwd or a sandbox", "color": "green"},
    },
    "edges": [
        {"from": "query", "to": "loop", "label": "prompt"},
        {"from": "loop", "to": "api", "label": "messages"},
        {"from": "builtin", "to": "fs", "from_side": "bottom", "to_side": "left", "via": [(480, 362), (790, 362), (790, 430)]},
        {"from": "loop", "to": "mcp", "from_side": "right", "to_side": "left", "via": [(780, 175), (780, 300)]},
        {"from": "loop", "to": "msgs", "from_side": "left", "to_side": "right", "via": [(350, 200), (350, 552)]},
    ],
}
