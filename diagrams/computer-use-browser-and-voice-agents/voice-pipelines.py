# Two ways to build a voice agent: a cascade of three models, or one speech-to-speech model.
SPEC = {
    "title": "Cascaded vs speech-to-speech voice agents",
    "accent": "amber",
    "width": 1100, "height": 640,
    "bands": [
        {"y": 85, "h": 250, "label": "Cascaded", "color": "blue"},
        {"y": 355, "h": 250, "label": "Speech\nto speech", "color": "amber"},
    ],
    "nodes": {
        "mic1": {"x": 150, "y": 160, "w": 110, "h": 90, "icon": "🎙️", "label": "Caller", "color": "gray"},
        "vad": {"x": 290, "y": 160, "w": 130, "h": 90, "icon": "🔊", "label": "VAD", "sub": "speech or\nsilence?", "color": "blue"},
        "stt": {"x": 450, "y": 160, "w": 140, "h": 90, "icon": "📝", "label": "Speech-to-text", "sub": "audio → words", "color": "blue"},
        "llm": {"x": 620, "y": 160, "w": 140, "h": 90, "icon": "🧠", "label": "LLM", "sub": "words → reply\n+ tool calls", "color": "blue"},
        "tts": {"x": 790, "y": 160, "w": 140, "h": 90, "icon": "🗣️", "label": "Text-to-speech", "sub": "words → audio", "color": "blue"},
        "spk1": {"x": 960, "y": 160, "w": 110, "h": 90, "icon": "🎧", "label": "Caller", "color": "gray"},
        "mic2": {"x": 150, "y": 430, "w": 110, "h": 90, "icon": "🎙️", "label": "Caller", "color": "gray"},
        "s2s": {"x": 350, "y": 405, "w": 520, "h": 140, "icon": "🧠", "label": "One realtime model",
                 "sub": "hears audio, speaks audio, calls tools;\nturn detection and interruption built in;\ntranscripts arrive alongside", "color": "amber"},
        "spk2": {"x": 960, "y": 430, "w": 110, "h": 90, "icon": "🎧", "label": "Caller", "color": "gray"},
    },
    "edges": [
        {"from": "mic1", "to": "vad"},
        {"from": "vad", "to": "stt"},
        {"from": "stt", "to": "llm", "label": "text"},
        {"from": "llm", "to": "tts", "label": "text"},
        {"from": "tts", "to": "spk1"},
        {"from": "mic2", "to": "s2s", "label": "audio"},
        {"from": "s2s", "to": "spk2", "label": "audio"},
    ],
    "notes": [
        {"x": 610, "y": 295, "text": "✅ pick each part, inspect text, any LLM     ⚠️ latencies add up, tone of voice is lost", "size": 14},
        {"x": 610, "y": 580, "text": "✅ fastest, natural prosody and interruptions     ⚠️ fewer models, harder to inspect and control", "size": 14},
    ],
}
