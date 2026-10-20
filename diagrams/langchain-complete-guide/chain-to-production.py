# Module 8 architecture: serve a chain over HTTP and watch it with LangSmith.
SPEC = {
    "title": "From chain to production: serve it, watch it",
    "accent": "purple",
    "width": 1100, "height": 760,
    "bands": [
        {"y": 85, "h": 170, "label": "Clients", "color": "gray", "tile": 130},
        {"y": 275, "h": 230, "label": "Serve", "color": "blue", "tile": 130},
        {"y": 525, "h": 190, "label": "Watch", "color": "purple", "tile": 130},
    ],
    "nodes": {
        "web": {"x": 175, "y": 115, "w": 250, "h": 110, "icon": "📱", "label": "Web and mobile apps", "sub": "POST /invoke, /stream", "color": "gray"},
        "remote": {"x": 470, "y": 115, "w": 250, "h": 110, "icon": "🐍", "label": "Python services", "sub": "RemoteRunnable or\nhttpx / LangGraph SDK", "color": "gray"},
        "ops": {"x": 765, "y": 115, "w": 295, "h": 110, "icon": "🧑‍💻", "label": "Developers", "sub": "playground, Studio,\ntrace viewer", "color": "gray"},
        "api": {"x": 175, "y": 305, "w": 250, "h": 170, "icon": "🚪", "label": "HTTP layer", "sub": "LangServe add_routes (legacy)\nor your FastAPI routes\nor the Agent Server", "color": "blue"},
        "chain": {"x": 470, "y": 305, "w": 250, "h": 170, "icon": "⛓️", "label": "Your runnable", "sub": "prompt | model | parser\nor a LangGraph graph\nsame code as in dev", "color": "blue"},
        "infra": {"x": 765, "y": 305, "w": 295, "h": 170, "icon": "🏗️", "label": "Around it", "sub": "keys in env vars, auth,\nrate limits, timeouts,\ncheckpointer DB, Docker", "color": "blue"},
        "trace": {"x": 470, "y": 555, "w": 250, "h": 130, "icon": "🔭", "label": "Traces", "sub": "every step: inputs, outputs,\nlatency, tokens, errors", "color": "purple"},
        "monitor": {"x": 765, "y": 555, "w": 295, "h": 130, "icon": "📈", "label": "Monitoring", "sub": "dashboards, alerts,\nfeedback, cost", "color": "purple"},
        "eval": {"x": 175, "y": 555, "w": 250, "h": 130, "icon": "🧪", "label": "Datasets and evals", "sub": "replay real cases after\nevery change; prompt versions", "color": "purple"},
    },
    "edges": [
        {"from": "web", "to": "api"},
        {"from": "api", "to": "chain"},
        {"from": "chain", "to": "infra"},
        {"from": "chain", "to": "trace", "label": "LANGSMITH_TRACING"},
        {"from": "trace", "to": "monitor"},
        {"from": "trace", "to": "eval"},
    ],
    "notes": [
        {"x": 618, "y": 738, "text": "The chain itself doesn't change: serving and tracing are layers around the same runnable.", "size": 15, "weight": 600, "color": "#5b3fa0"},
    ],
}
