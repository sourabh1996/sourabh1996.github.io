# AG-UI: one POST of run input in, one ordered stream of typed events out, and how a frontend turns them into UI.
SPEC = {
    "title": "AG-UI: one request in, a stream of events out",
    "accent": "blue",
    "width": 1100, "height": 780,
    "groups": [
        {"x": 25, "y": 90, "w": 320, "h": 660, "label": "Frontend (your app)", "color": "purple"},
        {"x": 755, "y": 90, "w": 320, "h": 660, "label": "Agent backend (any framework)", "color": "teal"},
    ],
    "nodes": {
        "ui": {"x": 55, "y": 130, "w": 260, "h": 120, "icon": "🖥️", "label": "Chat + app UI", "sub": "messages, cards, forms,\nprogress, approvals", "color": "purple"},
        "reducer": {"x": 55, "y": 300, "w": 260, "h": 120, "icon": "🧮", "label": "Event reducer", "sub": "applies each event\nto local UI state", "color": "purple"},
        "ftools": {"x": 55, "y": 470, "w": 260, "h": 120, "icon": "🛠️", "label": "Frontend tools", "sub": "confirm_booking,\nshow_map ...", "color": "purple"},
        "state": {"x": 55, "y": 630, "w": 260, "h": 95, "label": "Shared state", "sub": "snapshot + JSON Patch", "color": "gray", "size": 16},
        "input": {"x": 395, "y": 130, "w": 310, "h": 150, "icon": "📤", "label": "POST RunAgentInput",
                  "sub": "threadId, runId, messages,\ntools, context, state,\nresume", "color": "blue"},
        "events": {"x": 395, "y": 330, "w": 310, "h": 300, "icon": "📡", "label": "SSE event stream",
                   "sub": "RUN_STARTED\nSTEP_STARTED / FINISHED\nTEXT_MESSAGE_START / CONTENT / END\nTOOL_CALL_START / ARGS / END\nTOOL_CALL_RESULT\nSTATE_SNAPSHOT / STATE_DELTA\nRUN_FINISHED (outcome)", "color": "amber"},
        "agent": {"x": 785, "y": 130, "w": 260, "h": 140, "icon": "🤖", "label": "Agent", "sub": "LangGraph, ADK, CrewAI,\nAgent Framework ...", "color": "teal"},
        "adapter": {"x": 785, "y": 330, "w": 260, "h": 120, "icon": "🔁", "label": "AG-UI adapter", "sub": "framework events\n→ AG-UI events", "color": "teal"},
        "btools": {"x": 785, "y": 500, "w": 260, "h": 120, "icon": "🧰", "label": "Backend tools", "sub": "MCP servers, APIs,\nother agents (A2A)", "color": "gray"},
    },
    "edges": [
        {"from": "ui", "to": "input", "from_side": "right", "to_side": "left"},
        {"from": "input", "to": "agent", "from_side": "right", "to_side": "left"},
        {"from": "agent", "to": "adapter"},
        {"from": "agent", "to": "btools", "both": True, "from_side": "right", "to_side": "right", "via": [[1062, 200], [1062, 560]]},
        {"from": "adapter", "to": "events", "from_side": "left", "to_side": "right"},
        {"from": "events", "to": "reducer", "from_side": "left", "to_side": "right"},
        {"from": "reducer", "to": "ui"},
        {"from": "reducer", "to": "ftools"},
        {"from": "ftools", "to": "state"},
    ],
}
