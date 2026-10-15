# What happens inside an LLM for one step of generation: text in, one new token out, repeat.
SPEC = {
    "title": "Inside an LLM: from your words to the next token",
    "accent": "blue",
    "width": 1100, "height": 800,
    "groups": [
        {"x": 40, "y": 265, "w": 1020, "h": 235, "label": "Transformer blocks", "color": "purple"},
    ],
    "nodes": {
        # Row 1: text to vectors
        "text": {"x": 40, "y": 95, "w": 200, "h": 110, "icon": "💬", "label": "Your text", "sub": "\"Ek cutting chai\nand one\"", "color": "blue"},
        "tok": {"x": 300, "y": 95, "w": 200, "h": 110, "icon": "✂️", "label": "Tokenizer", "sub": "splits text into\ncommon pieces", "color": "blue"},
        "ids": {"x": 560, "y": 95, "w": 200, "h": 110, "icon": "🔢", "label": "Token IDs", "sub": "[36, 2081, 9437,\n1081, 323, 832]", "color": "blue"},
        "emb": {"x": 820, "y": 95, "w": 240, "h": 110, "icon": "📍", "label": "Embeddings", "sub": "each ID becomes a vector\nof thousands of numbers\n+ its position", "color": "blue"},
        # Row 2: transformer block
        "attn": {"x": 90, "y": 305, "w": 280, "h": 165, "icon": "👀", "label": "Attention", "sub": "every token looks back at\nthe earlier tokens and pulls in\nwhat matters (\"one\" checks\nwhat is being counted)", "color": "purple"},
        "ffn": {"x": 420, "y": 305, "w": 280, "h": 165, "icon": "📚", "label": "Feed-forward layer", "sub": "applies patterns stored\nin the weights to each\ntoken's vector", "color": "purple"},
        "out_vec": {"x": 790, "y": 305, "w": 240, "h": 165, "icon": "🧭", "label": "Final vector", "sub": "for the last position:\na summary of \"what\nshould come next\"", "color": "purple"},
        # Row 3: vector to token
        "next": {"x": 40, "y": 585, "w": 210, "h": 120, "icon": "➕", "label": "Next token", "sub": "\"samosa\"\nappended to the text", "color": "green"},
        "sample": {"x": 290, "y": 585, "w": 210, "h": 120, "icon": "🎲", "label": "Sampler", "sub": "temperature, top-p\npick one token", "color": "amber"},
        "probs": {"x": 545, "y": 585, "w": 210, "h": 120, "icon": "📊", "label": "Probabilities", "sub": "softmax of the scores:\nsamosa 36% · vada 24% · ...", "color": "amber"},
        "logits": {"x": 800, "y": 585, "w": 220, "h": 120, "icon": "🎯", "label": "Scores (logits)", "sub": "one score for every\ntoken in the vocabulary", "color": "amber"},
    },
    "edges": [
        {"from": "text", "to": "tok"},
        {"from": "tok", "to": "ids"},
        {"from": "ids", "to": "emb"},
        {"from": "emb", "to": "attn", "from_side": "bottom", "to_side": "top", "via": [(940, 235), (230, 235)], "label": "vectors in", "label_at": (585, 238)},
        {"from": "attn", "to": "ffn"},
        {"from": "ffn", "to": "out_vec", "label": "× dozens\nof blocks", "label_at": (745, 365)},
        {"from": "out_vec", "to": "logits", "from_side": "bottom", "to_side": "top"},
        {"from": "logits", "to": "probs"},
        {"from": "probs", "to": "sample"},
        {"from": "sample", "to": "next"},
        {"from": "next", "to": "text", "from_side": "left", "to_side": "left", "via": [(22, 645), (22, 150)], "label": "repeat until done", "label_at": (110, 540)},
    ],
    "notes": [
        {"x": 550, "y": 750, "text": "One pass through this pipeline produces exactly one token. A 300-token reply means 300 passes.", "weight": 700, "color": "#2f5fb3", "size": 15},
        {"x": 550, "y": 775, "text": "The weights (billions of numbers) are fixed after training; only the text changes between passes.", "size": 13},
    ],
}
