# Module 8's central idea: index a document as a tree of sections, then let an LLM navigate it like a human expert.
SPEC = {
    "title": "Vectorless RAG: build a tree once, then reason your way down it",
    "accent": "teal",
    "width": 1100, "height": 640,
    "bands": [
        {"y": 80, "h": 220, "label": "Index", "color": "teal"},
        {"y": 320, "h": 300, "label": "Search", "color": "green"},
    ],
    "nodes": {
        "pdf": {"x": 160, "y": 110, "w": 150, "h": 160, "icon": "📄", "label": "Long PDF", "sub": "annual report,\nfiling, manual", "color": "gray"},
        "toc": {"x": 340, "y": 110, "w": 170, "h": 160, "icon": "🧭", "label": "Find structure", "sub": "contents page\nor headings;\nverify page starts", "color": "teal"},
        "seg": {"x": 540, "y": 110, "w": 170, "h": 160, "icon": "📚", "label": "Sections", "sub": "natural units,\nno fixed chunks;\nsplit only if huge", "color": "teal"},
        "tree": {"x": 740, "y": 110, "w": 330, "h": 160, "icon": "🌳", "label": "Document tree", "sub": "node_id, title, summary,\nstart and end page,\nchild nodes", "color": "teal"},
        "q": {"x": 160, "y": 400, "w": 150, "h": 140, "icon": "❓", "label": "Question", "sub": "\"tax disputes\nat stake?\"", "color": "gray"},
        "pick": {"x": 340, "y": 400, "w": 170, "h": 140, "icon": "🧠", "label": "LLM reads tree", "sub": "titles + summaries,\npicks node ids", "color": "green"},
        "fetch": {"x": 540, "y": 400, "w": 170, "h": 140, "icon": "📖", "label": "Fetch pages", "sub": "full text of\nthe node's pages", "color": "green"},
        "judge": {"x": 740, "y": 400, "w": 150, "h": 140, "icon": "⚖️", "label": "Enough?", "sub": "no: follow a\nreference, pick\nanother node", "color": "purple"},
        "ans": {"x": 920, "y": 400, "w": 150, "h": 140, "icon": "📌", "label": "Answer", "sub": "with exact\npage numbers", "color": "green"},
    },
    "edges": [
        {"from": "pdf", "to": "toc"},
        {"from": "toc", "to": "seg"},
        {"from": "seg", "to": "tree"},
        {"from": "q", "to": "pick"},
        {"from": "tree", "to": "pick", "from_side": "bottom", "to_side": "top", "via": [(905, 315), (425, 315)]},
        {"from": "pick", "to": "fetch"},
        {"from": "fetch", "to": "judge"},
        {"from": "judge", "to": "ans"},
        {"from": "judge", "to": "pick", "from_side": "bottom", "to_side": "bottom", "via": [(815, 580), (425, 580)], "label": "loop"},
    ],
}
