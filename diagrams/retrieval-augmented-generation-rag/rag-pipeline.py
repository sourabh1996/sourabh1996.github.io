# The full RAG pipeline: offline indexing, online answering, and the evaluation loop around both.
SPEC = {
    "title": "A production RAG pipeline, end to end",
    "accent": "green",
    "width": 1100, "height": 800,
    "bands": [
        {"y": 80, "h": 200, "label": "Index\n(offline)", "color": "blue"},
        {"y": 300, "h": 280, "label": "Answer\n(online)", "color": "green"},
        {"y": 600, "h": 180, "label": "Evaluate", "color": "purple"},
    ],
    "nodes": {
        # Indexing
        "sources": {"x": 160, "y": 110, "w": 150, "h": 130, "icon": "📂", "label": "Sources", "sub": "PDFs · web pages\nCSV · wikis · tickets", "color": "gray"},
        "ingest": {"x": 350, "y": 110, "w": 150, "h": 130, "icon": "📥", "label": "Ingest", "sub": "load, clean,\nadd metadata", "color": "blue"},
        "chunk": {"x": 540, "y": 110, "w": 150, "h": 130, "icon": "✂️", "label": "Chunk", "sub": "split into\n200-800 token pieces", "color": "blue"},
        "embed": {"x": 730, "y": 110, "w": 150, "h": 130, "icon": "🔢", "label": "Embed", "sub": "text to vector\n[0.12, -0.40, ...]", "color": "blue"},
        "index": {"x": 920, "y": 110, "w": 150, "h": 130, "icon": "🗄️", "label": "Index", "sub": "vector store\n+ keyword (BM25)", "color": "blue"},
        # Answering, row 1
        "question": {"x": 160, "y": 330, "w": 150, "h": 100, "icon": "❓", "label": "Question", "sub": "from the user", "color": "green"},
        "rewrite": {"x": 350, "y": 330, "w": 150, "h": 100, "icon": "📝", "label": "Rewrite query", "sub": "optional", "color": "green"},
        "retrieve": {"x": 540, "y": 330, "w": 150, "h": 100, "icon": "🔎", "label": "Retrieve", "sub": "hybrid: top 50", "color": "green"},
        "rerank": {"x": 730, "y": 330, "w": 150, "h": 100, "icon": "🏅", "label": "Rerank", "sub": "keep best 5", "color": "green"},
        # Answering, row 2 (flows right to left)
        "prompt": {"x": 730, "y": 460, "w": 150, "h": 100, "icon": "🧩", "label": "Build prompt", "sub": "rules + chunks\n+ question", "color": "green"},
        "llm": {"x": 540, "y": 460, "w": 150, "h": 100, "icon": "🧠", "label": "Generate", "sub": "LLM writes answer", "color": "green"},
        "answer": {"x": 350, "y": 460, "w": 150, "h": 100, "icon": "📚", "label": "Answer", "sub": "with citations", "color": "green"},
        "guard": {"x": 920, "y": 330, "w": 150, "h": 100, "icon": "🛡️", "label": "Guardrails", "sub": "too weak? say\n'not found'", "color": "coral"},
        # Evaluation
        "evalset": {"x": 160, "y": 630, "w": 170, "h": 120, "icon": "🧪", "label": "Test questions", "sub": "with expected\nsources and answers", "color": "purple"},
        "retmetrics": {"x": 380, "y": 630, "w": 190, "h": 120, "icon": "🎯", "label": "Retrieval metrics", "sub": "recall@k · MRR\ncontext precision", "color": "purple"},
        "ansmetrics": {"x": 620, "y": 630, "w": 190, "h": 120, "icon": "✅", "label": "Answer metrics", "sub": "faithfulness\nrelevance · citations", "color": "purple"},
        "improve": {"x": 860, "y": 630, "w": 210, "h": 120, "icon": "🔁", "label": "Tune and re-run", "sub": "chunk size · k · model\nprompt · reranker", "color": "purple"},
    },
    "edges": [
        {"from": "sources", "to": "ingest"},
        {"from": "ingest", "to": "chunk"},
        {"from": "chunk", "to": "embed"},
        {"from": "embed", "to": "index"},
        {"from": "question", "to": "rewrite"},
        {"from": "rewrite", "to": "retrieve"},
        {"from": "index", "to": "retrieve", "from_side": "bottom", "to_side": "top", "via": [(995, 290), (615, 290)], "label": "search the index", "label_at": (805, 290)},
        {"from": "retrieve", "to": "rerank"},
        {"from": "rerank", "to": "guard"},
        {"from": "guard", "to": "prompt", "from_side": "bottom", "to_side": "right", "via": [(995, 510)], "label": "good chunks", "label_at": (995, 470)},
        {"from": "prompt", "to": "llm"},
        {"from": "llm", "to": "answer"},
        {"from": "evalset", "to": "retmetrics"},
        {"from": "retmetrics", "to": "ansmetrics"},
        {"from": "ansmetrics", "to": "improve"},
        {"from": "answer", "to": "ansmetrics", "from_side": "bottom", "to_side": "top", "via": [(425, 595), (715, 595)], "label": "traces", "label_at": (570, 595)},
    ],
}
