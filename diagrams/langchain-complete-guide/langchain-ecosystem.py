# How the LangChain family of packages fits around your app.
SPEC = {
    "title": "The LangChain ecosystem in one picture",
    "accent": "teal",
    "width": 1100, "height": 760,
    "bands": [
        {"y": 85, "h": 130, "label": "Your\napp", "color": "gray"},
        {"y": 230, "h": 150, "label": "Build", "color": "teal"},
        {"y": 395, "h": 150, "label": "Connect", "color": "blue"},
        {"y": 560, "h": 175, "label": "Run and\nwatch", "color": "purple"},
    ],
    "nodes": {
        "app": {"x": 160, "y": 105, "w": 360, "h": 90, "icon": "🛍️", "label": "Saree-shop support bot", "sub": "your code: routes, UI, business rules", "color": "gray"},
        "user": {"x": 780, "y": 105, "w": 280, "h": 90, "icon": "🙋", "label": "Customers", "sub": "web, WhatsApp, app", "color": "gray"},
        "core": {"x": 160, "y": 250, "w": 250, "h": 110, "icon": "🧩", "label": "langchain-core", "sub": "messages, prompts, parsers,\nrunnables, tool interface", "color": "teal"},
        "lc": {"x": 490, "y": 250, "w": 250, "h": 110, "icon": "🔗", "label": "langchain", "sub": "init_chat_model, create_agent,\nmiddleware", "color": "teal"},
        "classic": {"x": 770, "y": 250, "w": 290, "h": 110, "icon": "📦", "label": "langchain-classic", "sub": "legacy chains and memory\nfrom before 1.0", "color": "gray"},
        "prov": {"x": 160, "y": 415, "w": 300, "h": 110, "icon": "🔌", "label": "Provider packages", "sub": "langchain-anthropic, -openai,\n-huggingface, -ollama", "color": "blue"},
        "comm": {"x": 485, "y": 415, "w": 280, "h": 110, "icon": "🗃️", "label": "langchain-community", "sub": "hundreds of loaders,\ntools, vector stores", "color": "blue"},
        "models": {"x": 790, "y": 415, "w": 270, "h": 110, "icon": "🧠", "label": "Models and services", "sub": "Claude, GPT, Llama,\nsearch APIs, databases", "color": "blue"},
        "lg": {"x": 160, "y": 580, "w": 270, "h": 130, "icon": "🕸️", "label": "LangGraph", "sub": "loops, state, pauses,\nmemory for agents", "color": "purple"},
        "ls": {"x": 455, "y": 580, "w": 270, "h": 130, "icon": "🔭", "label": "LangSmith", "sub": "traces, datasets,\nevaluations, prompts", "color": "purple"},
        "dep": {"x": 750, "y": 580, "w": 310, "h": 130, "icon": "🚀", "label": "Serving", "sub": "your FastAPI app, LangSmith\nDeployment (old: LangServe)", "color": "purple"},
    },
    "edges": [
        {"from": "user", "to": "app", "label": "questions"},
        {"from": "app", "to": "core", "to_side": "top", "from_side": "bottom"},
        {"from": "lc", "to": "core", "label": "built\non", "label_at": (450, 295)},
        {"from": "prov", "to": "core", "from_side": "top", "to_side": "bottom", "label": "implement"},
        {"from": "prov", "to": "models", "from_side": "bottom", "to_side": "bottom", "via": [(310, 548), (925, 548)], "label": "API calls", "label_at": (620, 548)},
    ],
}
