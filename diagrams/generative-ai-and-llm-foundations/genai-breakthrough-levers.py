# The six levers behind GenAI breakthroughs since 2022, each with an example and what it changed for builders.
SPEC = {
    "title": "Six levers behind GenAI breakthroughs",
    "accent": "purple",
    "width": 1100, "height": 640,
    "nodes": {
        "hub": {"x": 400, "y": 270, "w": 300, "h": 95, "icon": "🚀", "label": "Better GenAI", "sub": "more capable, cheaper,\nable to act", "color": "gray"},
        "scale": {"x": 40, "y": 80, "w": 320, "h": 150, "icon": "📚", "label": "Scale and data", "sub": "cleaner data, synthetic data,\nsmall models trained longer\n\nsmaller new models beat\nbigger old ones", "color": "blue"},
        "post": {"x": 390, "y": 80, "w": 320, "h": 150, "icon": "🤝", "label": "Post-training", "sub": "SFT, RLHF, RLAIF, DPO\n\nGPT-3 became ChatGPT:\nhelpful, follows instructions", "color": "teal"},
        "think": {"x": 740, "y": 80, "w": 320, "h": 150, "icon": "🧠", "label": "Thinking at answer time", "sub": "reasoning models (o1, R1)\n\nan effort dial: buy accuracy\nwith tokens and time", "color": "coral"},
        "multi": {"x": 40, "y": 410, "w": 320, "h": 150, "icon": "🖼️", "label": "Multimodality", "sub": "images, voice, video,\nscreenshots in and out\n\nread invoices, talk,\ngenerate creatives", "color": "amber"},
        "eff": {"x": 390, "y": 410, "w": 320, "h": 150, "icon": "⚡", "label": "Long context, low cost", "sub": "1M tokens, MoE, quantization,\ndistillation, caching\n\nwhole documents affordable;\nmodels on laptops", "color": "green"},
        "tools": {"x": 740, "y": 410, "w": 320, "h": 150, "icon": "🛠️", "label": "Tools and agents", "sub": "function calling, computer use,\nMCP, coding agents\n\nmodels that act,\nnot just talk", "color": "purple"},
    },
    "edges": [
        {"from": "scale", "to": "hub", "from_side": "bottom", "to_side": "left"},
        {"from": "post", "to": "hub"},
        {"from": "think", "to": "hub", "from_side": "bottom", "to_side": "right"},
        {"from": "multi", "to": "hub", "from_side": "top", "to_side": "left"},
        {"from": "eff", "to": "hub"},
        {"from": "tools", "to": "hub", "from_side": "top", "to_side": "right"},
    ],
    "notes": [{"x": 550, "y": 605, "text": "Ask of every headline: which lever, measured how, at what cost?"}],
}
