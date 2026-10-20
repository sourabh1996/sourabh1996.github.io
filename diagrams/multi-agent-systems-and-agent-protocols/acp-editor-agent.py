# Agent Client Protocol: the editor launches a coding agent as a subprocess and both sides call each other over JSON-RPC on stdio.
SPEC = {
    "title": "ACP: any coding agent inside any editor",
    "accent": "blue",
    "width": 1100, "height": 760,
    "groups": [
        {"x": 25, "y": 90, "w": 360, "h": 640, "label": "Client: the editor", "color": "purple"},
        {"x": 715, "y": 90, "w": 360, "h": 640, "label": "Agent: a subprocess", "color": "teal"},
    ],
    "nodes": {
        "editor": {"x": 60, "y": 130, "w": 290, "h": 110, "icon": "📝", "label": "Zed, JetBrains, Neovim ...", "sub": "owns the files, the UI\nand the user's consent", "color": "purple"},
        "fs": {"x": 60, "y": 280, "w": 290, "h": 95, "label": "fs/read_text_file\nfs/write_text_file", "sub": "sees unsaved buffers", "color": "gray", "size": 15},
        "term": {"x": 60, "y": 410, "w": 290, "h": 95, "label": "terminal/create, output,\nwait_for_exit, kill", "color": "gray", "size": 15},
        "perm": {"x": 60, "y": 540, "w": 290, "h": 95, "label": "session/request_permission", "sub": "allow once / always, reject", "color": "pink", "size": 15},
        "pipe": {"x": 425, "y": 230, "w": 250, "h": 300, "icon": "🔌", "label": "stdio", "sub": "JSON-RPC 2.0\none message per line\n\nstdin: editor → agent\nstdout: agent → editor\nstderr: logs only", "color": "amber"},
        "agent": {"x": 750, "y": 130, "w": 290, "h": 110, "icon": "🤖", "label": "Gemini CLI, Claude Agent,\nCodex CLI, Goose ...", "sub": "owns the model and the loop", "color": "teal"},
        "methods": {"x": 750, "y": 280, "w": 290, "h": 150, "label": "initialize\nsession/new · session/prompt\nsession/cancel", "sub": "called by the editor", "color": "teal", "size": 15},
        "updates": {"x": 750, "y": 470, "w": 290, "h": 165, "label": "session/update", "sub": "agent_message_chunk\ntool_call · tool_call_update\nplan · diffs\nthen stopReason: end_turn", "color": "blue", "size": 16},
    },
    "edges": [
        {"from": "editor", "to": "pipe", "label": "spawns", "from_side": "right", "to_side": "top"},
        {"from": "pipe", "to": "methods", "from_side": "right", "to_side": "left"},
        {"from": "updates", "to": "pipe", "from_side": "left", "to_side": "bottom"},
        {"from": "pipe", "to": "perm", "from_side": "left", "to_side": "right"},
    ],
}
