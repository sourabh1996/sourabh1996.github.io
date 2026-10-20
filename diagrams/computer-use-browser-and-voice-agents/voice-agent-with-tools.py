# A production voice agent: calls come in, a voice server runs the conversation, tools sit behind a policy layer.
SPEC = {
    "title": "A voice agent that can act",
    "accent": "amber",
    "width": 1100, "height": 720,
    "groups": [
        {"x": 300, "y": 95, "w": 420, "h": 590, "label": "Your voice server", "color": "amber"},
        {"x": 760, "y": 95, "w": 310, "h": 590, "label": "Tools behind a policy layer", "color": "coral"},
    ],
    "nodes": {
        "phone": {"x": 40, "y": 150, "w": 220, "h": 95, "icon": "📞", "label": "Phone caller", "sub": "SIP via a telephony provider", "color": "gray"},
        "app": {"x": 40, "y": 285, "w": 220, "h": 95, "icon": "📱", "label": "App or browser", "sub": "WebRTC, ephemeral token", "color": "gray"},
        "human": {"x": 40, "y": 520, "w": 220, "h": 110, "icon": "🧑‍💼", "label": "Human agent", "sub": "warm transfer with\na summary", "color": "green"},
        "turn": {"x": 330, "y": 130, "w": 360, "h": 95, "icon": "👂", "label": "Turn-taking", "sub": "VAD, turn detection, barge-in, truncation", "color": "amber"},
        "brain": {"x": 330, "y": 250, "w": 360, "h": 120, "icon": "🧠", "label": "Realtime model or cascade", "sub": "decides what to say\nand which tool to call", "color": "amber"},
        "voice": {"x": 330, "y": 395, "w": 360, "h": 95, "icon": "🗣️", "label": "Fillers while tools run", "sub": "\"Let me check that for you\"", "color": "amber"},
        "log": {"x": 330, "y": 515, "w": 360, "h": 140, "icon": "🗒️", "label": "Transcripts, timings, consent", "sub": "every turn and tool call,\nrecorded with the caller's consent", "color": "amber"},
        "read": {"x": 785, "y": 130, "w": 260, "h": 120, "icon": "🔎", "label": "Read tools", "sub": "train status, order lookup\nrun at once, time out fast", "color": "teal"},
        "confirm": {"x": 785, "y": 275, "w": 260, "h": 120, "icon": "✋", "label": "Spoken confirmation", "sub": "read back details,\ncode hears a clear yes", "color": "coral"},
        "write": {"x": 785, "y": 445, "w": 260, "h": 100, "icon": "✍️", "label": "Write tools", "sub": "cancel, refund, book\nidempotency keys", "color": "coral"},
        "verify": {"x": 785, "y": 565, "w": 260, "h": 95, "icon": "🔐", "label": "Identity check", "sub": "OTP to registered number,\nnever 'trust the voice'", "color": "coral"},
    },
    "edges": [
        {"from": "phone", "to": "turn", "both": True},
        {"from": "app", "to": "brain", "both": True, "to_side": "left"},
        {"from": "brain", "to": "read", "label": "lookup", "to_side": "left", "from_side": "right"},
        {"from": "brain", "to": "confirm", "label": "change", "to_side": "left", "from_side": "right"},
        {"from": "confirm", "to": "write", "label": "yes", "label_at": (945, 420)},
        {"from": "brain", "to": "human", "label": "handoff", "from_side": "left", "to_side": "right", "via": [(300, 330), (285, 575)], "label_at": (283, 470)},
    ],
}
