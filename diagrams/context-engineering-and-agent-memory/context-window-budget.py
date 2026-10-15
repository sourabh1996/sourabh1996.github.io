# One real-looking agent request, item by item, laid out against a 40,000-token operating budget.
# Bar widths are proportional to tokens: 1,020 px = 40,000 tokens.
X0, W = 40, 1020


SEGS = [("Stable prefix", 6770, "blue"), ("RAG", 2600, "teal"), ("History", 5900, "amber"),
        ("Tool results", 9800, "amber"), ("", 70, "coral"), ("Answer reserve", 8000, "gray"),
        ("Headroom", 6860, "green")]
nodes, x = {}, X0
for i, (label, tokens, color) in enumerate(SEGS):
    w = max(14, round(tokens / 40000 * W)) if i < len(SEGS) - 1 else X0 + W - x
    nodes[f"bar{i}"] = {"x": x, "y": 120, "w": w, "h": 64, "label": label, "sub": f"{tokens:,}" if label else "",
                        "color": color, "size": 14}
    x += w

CARD_W, CARD_H = 228, 62


def card(x, y, label, sub, color):
    return {"x": x, "y": y, "w": CARD_W, "h": CARD_H, "label": label, "sub": sub, "color": color, "size": 15}


cols = [40, 300, 560, 820]
nodes.update({
    "sys": card(cols[0] + 6, 300, "📜 System prompt", "1,850 tokens", "blue"),
    "tools": card(cols[0] + 6, 375, "🧰 Tool definitions (12)", "3,400 tokens", "blue"),
    "mem": card(cols[0] + 6, 450, "🧠 User memory", "420 tokens", "blue"),
    "ex": card(cols[0] + 6, 525, "🧪 Examples (3)", "1,100 tokens", "blue"),
    "rag": card(cols[1] + 6, 300, "📚 Policy chunks (4)", "2,600 tokens", "teal"),
    "rag2": {"x": cols[1] + 6, "y": 375, "w": CARD_W, "h": 120, "style": "plain", "color": "teal", "size": 13,
             "label": "Chosen for THIS question,", "sub": "dropped next turn if\nno longer relevant"},
    "hist": card(cols[2] + 6, 300, "💬 Conversation (8 turns)", "5,900 tokens", "amber"),
    "res": card(cols[2] + 6, 375, "🛠️ Tool results so far", "9,800 tokens", "amber"),
    "msg": card(cols[2] + 6, 450, "🙋 New user message", "70 tokens", "coral"),
    "out": card(cols[3] + 6, 300, "✍️ Reserved for answer", "max_tokens = 8,000", "gray"),
    "free": card(cols[3] + 6, 375, "🌿 Headroom", "6,860 tokens", "green"),
})

SPEC = {
    "title": "The context window as a budget: one request, item by item",
    "accent": "blue",
    "width": 1100, "height": 720,
    "groups": [
        {"x": cols[0] - 4, "y": 270, "w": 248, "h": 340, "label": "Stable prefix: cache it", "color": "blue"},
        {"x": cols[1] - 4, "y": 270, "w": 248, "h": 340, "label": "Fetched just in time", "color": "teal"},
        {"x": cols[2] - 4, "y": 270, "w": 248, "h": 340, "label": "Grows every turn", "color": "amber"},
        {"x": cols[3] - 4, "y": 270, "w": 248, "h": 340, "label": "Kept free on purpose", "color": "green"},
    ],
    "nodes": nodes,
    "edges": [],
    "notes": [
        {"x": 40, "y": 105, "text": "Turn 9 of a RailSathi refund chat. The bar is our 40,000-token operating budget (the model's window is 1,000,000).",
         "anchor": "start", "size": 14},
        {"x": 40, "y": 210, "text": "Input sent this turn: 25,140 tokens  ·  plus 8,000 reserved for the reply  ·  6,860 left before we must trim",
         "anchor": "start", "weight": 700, "color": "#2f5fb3", "size": 15},
        {"x": 40, "y": 236, "text": "The tiny red sliver is the user's actual question: 70 tokens out of 25,140.",
         "anchor": "start", "size": 13},
        {"x": 550, "y": 660, "text": "Context engineering = deciding, every turn, which tokens earn a place in this bar.",
         "weight": 700, "color": "#1f2328", "size": 16},
        {"x": 550, "y": 688, "text": "Fixed items go first and stay byte-identical (cheap with caching). Growing items get trimmed, cleared, compacted or offloaded.",
         "size": 13},
    ],
}
