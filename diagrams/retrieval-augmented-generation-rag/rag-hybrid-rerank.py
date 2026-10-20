# Module 6's central idea: two retrievers in parallel, fused, then reranked before generation.
SPEC = {
    "title": "Hybrid search + reranking: the production retrieval stack",
    "accent": "green",
    "width": 1100, "height": 620,
    "bands": [
        {"y": 80, "h": 330, "label": "Recall", "color": "blue"},
        {"y": 430, "h": 170, "label": "Precision", "color": "green"},
    ],
    "nodes": {
        "question": {"x": 160, "y": 185, "w": 150, "h": 110, "icon": "❓", "label": "Question", "sub": "\"VPN error 720\nafter the update\"", "color": "gray"},
        "bm25": {"x": 380, "y": 100, "w": 190, "h": 120, "icon": "🔤", "label": "BM25 keyword", "sub": "exact terms, codes,\nnames, numbers", "color": "blue"},
        "dense": {"x": 380, "y": 260, "w": 190, "h": 120, "icon": "🧭", "label": "Dense vectors", "sub": "meaning, synonyms,\nparaphrases", "color": "blue"},
        "fuse": {"x": 650, "y": 175, "w": 180, "h": 130, "icon": "🔀", "label": "Fuse (RRF)", "sub": "sum of 1 / (60 + rank)\nacross both lists", "color": "purple"},
        "pool": {"x": 900, "y": 175, "w": 170, "h": 130, "icon": "📚", "label": "Candidates", "sub": "top 20 to 100", "color": "blue"},
        "rerank": {"x": 900, "y": 455, "w": 170, "h": 120, "icon": "🏅", "label": "Cross-encoder", "sub": "reads question +\neach chunk together", "color": "green"},
        "top": {"x": 650, "y": 455, "w": 180, "h": 120, "icon": "🎯", "label": "Best 3 to 5", "sub": "drop if score\nbelow threshold", "color": "green"},
        "llm": {"x": 380, "y": 455, "w": 190, "h": 120, "icon": "🧠", "label": "LLM answer", "sub": "grounded, with\ncitations", "color": "green"},
    },
    "edges": [
        {"from": "question", "to": "bm25"},
        {"from": "question", "to": "dense"},
        {"from": "bm25", "to": "fuse"},
        {"from": "dense", "to": "fuse"},
        {"from": "fuse", "to": "pool"},
        {"from": "pool", "to": "rerank", "label": "rescore"},
        {"from": "rerank", "to": "top"},
        {"from": "top", "to": "llm"},
    ],
}
