# The training stages that turn random weights into a helpful assistant (and a reasoning model).
SPEC = {
    "title": "How an LLM is trained: four stages",
    "accent": "green",
    "width": 1100, "height": 930,
    "bands": [
        {"y": 80, "h": 190, "label": "Stage 1\nPretrain", "color": "blue"},
        {"y": 285, "h": 175, "label": "Stage 2\nSFT", "color": "teal"},
        {"y": 475, "h": 235, "label": "Stage 3\nRLHF /\nRLAIF", "color": "purple"},
        {"y": 725, "h": 190, "label": "Stage 4\nRLVR", "color": "coral"},
    ],
    "nodes": {
        # Stage 1
        "p_data": {"x": 160, "y": 105, "w": 230, "h": 140, "icon": "🌐", "label": "Huge raw text", "sub": "web pages, books, code,\npapers: trillions of tokens\n(filtered and cleaned)", "color": "blue"},
        "p_task": {"x": 440, "y": 105, "w": 250, "h": 140, "icon": "🔮", "label": "Predict the next token", "sub": "\"ek cutting ___\"\nloss = surprise at the real\nnext token; months on\nhuge GPU clusters", "color": "blue"},
        "p_out": {"x": 740, "y": 105, "w": 320, "h": 140, "icon": "📖", "label": "Base model", "sub": "knows language, facts, code\nbut only continues text:\nasked a question, it may\nwrite more questions", "color": "gray"},
        # Stage 2
        "s_data": {"x": 160, "y": 305, "w": 230, "h": 135, "icon": "✍️", "label": "Ideal answers", "sub": "thousands to millions of\ninstruction → ideal reply\nexamples, by experts", "color": "teal"},
        "s_task": {"x": 440, "y": 305, "w": 250, "h": 135, "icon": "🎓", "label": "Supervised fine-tuning", "sub": "same next-token loss,\nbut only on the replies", "color": "teal"},
        "s_out": {"x": 740, "y": 305, "w": 320, "h": 135, "icon": "💬", "label": "Instruction-following model", "sub": "answers in the assistant\nformat, follows requests", "color": "gray"},
        # Stage 3
        "r_cmp": {"x": 160, "y": 495, "w": 230, "h": 195, "icon": "⚖️", "label": "Which reply is better?", "sub": "two answers to one prompt;\na judge picks the better\n\nRLHF: human judges\nRLAIF: an AI judge guided\nby written principles", "color": "purple"},
        "r_rm": {"x": 440, "y": 495, "w": 250, "h": 85, "icon": "🏅", "label": "Reward model", "sub": "learns to score replies", "color": "purple"},
        "r_rl": {"x": 440, "y": 605, "w": 250, "h": 85, "icon": "🔁", "label": "RL: write, get scored, adjust", "color": "purple", "size": 14},
        "r_out": {"x": 740, "y": 495, "w": 320, "h": 195, "icon": "🤝", "label": "Assistant model", "sub": "more helpful, more honest,\nrefuses harmful requests\n\n(DPO skips the reward model\nand learns from the pairs\ndirectly)", "color": "gray"},
        # Stage 4
        "x_data": {"x": 160, "y": 750, "w": 230, "h": 140, "icon": "🧮", "label": "Checkable problems", "sub": "maths with known answers,\ncode with unit tests,\nlogic puzzles", "color": "coral"},
        "x_task": {"x": 440, "y": 750, "w": 250, "h": 140, "icon": "🧠", "label": "Think, answer, verify", "sub": "reward when the final\nanswer is checked correct;\nlonger useful thinking\ngets reinforced", "color": "coral"},
        "x_out": {"x": 740, "y": 750, "w": 320, "h": 140, "icon": "💡", "label": "Reasoning model", "sub": "thinks step by step before\nanswering; spend more\nthinking for harder problems", "color": "gray"},
    },
    "edges": [
        {"from": "p_data", "to": "p_task"},
        {"from": "p_task", "to": "p_out"},
        {"from": "s_data", "to": "s_task"},
        {"from": "s_task", "to": "s_out"},
        {"from": "r_cmp", "to": "r_rm", "to_side": "left"},
        {"from": "r_rm", "to": "r_rl"},
        {"from": "r_rl", "to": "r_out", "to_side": "left"},
        {"from": "x_data", "to": "x_task"},
        {"from": "x_task", "to": "x_out"},
        {"from": "p_out", "to": "s_out", "label": "starting point", "label_at": (965, 280)},
        {"from": "s_out", "to": "r_out", "label": "starting point", "label_at": (965, 470)},
        {"from": "r_out", "to": "x_out", "label": "starting point", "label_at": (965, 720)},
    ],
}
