# Module 7 central idea: the model asks for a tool, your code runs it, the result goes back to the model.
SPEC = {
    "title": "The tool-calling loop",
    "accent": "teal",
    "width": 1100, "height": 790,
    "bands": [
        {"y": 85, "h": 190, "label": "Define", "color": "blue", "tile": 130},
        {"y": 295, "h": 300, "label": "Call", "color": "teal", "tile": 130},
        {"y": 615, "h": 120, "label": "Answer", "color": "green", "tile": 130},
    ],
    "nodes": {
        "fn": {"x": 175, "y": 115, "w": 250, "h": 130, "icon": "🐍", "label": "Python function", "sub": "type hints + docstring\n@tool, StructuredTool\nor BaseTool", "color": "blue"},
        "schema": {"x": 470, "y": 115, "w": 250, "h": 130, "icon": "📐", "label": "Tool schema", "sub": "name, description,\nJSON Schema of the args", "color": "blue"},
        "bind": {"x": 765, "y": 115, "w": 295, "h": 130, "icon": "🔗", "label": "model.bind_tools([...])", "sub": "schemas sent with\nevery request", "color": "blue"},
        "user": {"x": 175, "y": 330, "w": 250, "h": 110, "icon": "🙋", "label": "HumanMessage", "sub": "\"Fare from Pune\nto Nagpur?\"", "color": "teal"},
        "model": {"x": 470, "y": 330, "w": 250, "h": 110, "icon": "🧠", "label": "Model decides", "sub": "answer directly, or\nrequest one or more tools", "color": "teal"},
        "call": {"x": 765, "y": 330, "w": 295, "h": 110, "icon": "📨", "label": "AIMessage.tool_calls", "sub": "[{name, args, id}]\nthe model never runs code", "color": "teal"},
        "run": {"x": 765, "y": 465, "w": 295, "h": 110, "icon": "⚙️", "label": "Your code runs the tool", "sub": "tool.invoke(tool_call)\nvalidates args first", "color": "amber"},
        "result": {"x": 470, "y": 465, "w": 250, "h": 110, "icon": "📬", "label": "ToolMessage", "sub": "result + matching\ntool_call_id", "color": "teal"},
        "final": {"x": 175, "y": 633, "w": 885, "h": 84, "icon": "✅", "label": "Final AIMessage: a grounded answer", "sub": "when the model needs no more tools, the loop ends", "color": "green"},
    },
    "edges": [
        {"from": "fn", "to": "schema"},
        {"from": "schema", "to": "bind"},
        {"from": "user", "to": "model"},
        {"from": "model", "to": "call"},
        {"from": "call", "to": "run"},
        {"from": "run", "to": "result"},
        {"from": "result", "to": "model"},
    ],
    "notes": [
        {"x": 618, "y": 765, "text": "ToolMessage goes back to the model, which may call more tools. Agents automate this loop.", "size": 15, "weight": 600, "color": "#1f7a70"},
    ],
}
