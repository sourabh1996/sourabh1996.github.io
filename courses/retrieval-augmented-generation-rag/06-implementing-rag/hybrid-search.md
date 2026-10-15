---
title: "Hybrid Search"
course: "Retrieval-Augmented Generation (RAG)"
module: "6. Implementing RAG"
type: Article
level: Intermediate
reading_time: 30 min
---

# Hybrid Search: The Complete Guide

> 📚 **Before you start**
>
> - [Retrieval Methods](retrieval-methods.md), for BM25, dense retrieval and where each one fails.
> - [Retrievers](../05-rag-building-blocks-in-langchain/retrievers.md), for writing a `BaseRetriever` subclass.

## Introduction

Two friends are helping you find a lost wallet in a crowded mela. One has a sharp memory for **exact details**: "brown leather, Tata Capital card, a photo of a beagle". The other is good at **the gist**: "it was near the chaat stall, around when the band started". Alone, each misses things. Together, compare notes: whatever *both* of them think is likely goes to the top of the list, and you search there first.

**Hybrid search** runs a keyword search (BM25) and a vector search side by side, then **fuses** the two ranked lists into one. Keyword search catches exact terms (error codes, product names, section numbers) that embeddings blur; vector search catches paraphrases that keywords miss. In the last lesson you saw each fail on questions the other handled easily. Hybrid search is the standard fix, and it's one of the most reliable improvements you can make to a RAG system.

By the end of this lesson you'll be able to fuse result lists with **Reciprocal Rank Fusion** and with **normalised score blending**, explain why rank-based fusion is usually the safer default, measure the improvement on a mixed test set, and set up hybrid retrieval in LangChain and in vector databases that support it natively.

![Hybrid search and reranking stack. In the recall band, a question goes to a BM25 keyword search for exact terms and a dense vector search for meaning; the two ranked lists are fused with Reciprocal Rank Fusion into a pool of 20 to 100 candidates. In the precision band, a cross-encoder rescores each candidate together with the question, the best 3 to 5 above a threshold are kept, and the LLM writes a grounded answer with citations](/img/diagrams/retrieval-augmented-generation-rag/rag-hybrid-rerank.svg)
*The retrieval stack most production RAG systems converge on. This lesson builds the top band; [Reranking](reranking.md) builds the bottom one.*

> 💡 **Key Insight**
>
> Keyword and vector scores live on different scales and can't be added directly. **Fuse by rank, not by raw score**: Reciprocal Rank Fusion gives each document `1 / (60 + rank)` from every list it appears in and sorts by the sum. Documents that both methods like rise to the top, and you never have to calibrate one score against the other.

---

## Core Explanation

### 1. Setup: two retrievers over the same documents

The handbook and the IT knowledge base from the last lesson, a dense store and a BM25 index.

```python
import re, zlib
import numpy as np
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore

STOP = {"a", "an", "the", "is", "are", "of", "to", "in", "on", "for", "and", "or", "i", "my", "can",
        "do", "how", "many", "much", "what", "be", "it", "by", "with", "per", "up", "get", "if"}
CONCEPTS = {"vacation": "leave", "pto": "leave", "food": "meal", "lunch": "meal", "dinner": "meal",
            "budget": "allowance", "trip": "travel", "visit": "travel", "customer": "travel", "client": "travel",
            "notebook": "laptop", "computer": "laptop", "stolen": "lost", "resign": "notice", "quit": "notice",
            "expense": "claim", "reimbursement": "claim", "refund": "claim", "bill": "claim", "hotel": "stay",
            "room": "stay", "lodging": "stay", "baby": "parental", "maternity": "parental",
            "paternity": "parental", "doctor": "medical", "insurance": "medical", "hospital": "medical"}

def normalise(w):
    if w.endswith("ied"):
        return w[:-3] + "y"
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w

def words(text):
    return {normalise(w) for w in re.findall(r"[a-z0-9]+", text.lower())} - STOP

class ToyEmbeddings(Embeddings):
    def __init__(self, dim=256):
        self.dim = dim
    def _embed(self, text):
        vec = np.zeros(self.dim)
        for w in words(text):
            vec[zlib.crc32(CONCEPTS.get(w, w).encode()) % self.dim] += 1.0
        norm = np.linalg.norm(vec)
        return [round(float(x), 6) for x in (vec / norm if norm else vec)]
    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]
    def embed_query(self, text):
        return self._embed(text)

SECTIONS = [
    ("2.1", "Annual leave", 3, "Every employee gets 24 days of paid leave per calendar year. Up to 8 unused days can be carried forward to the next year."),
    ("2.2", "Sick leave", 3, "Employees get 10 days of sick leave per year. A doctor's note is required for more than 2 sick days in a row."),
    ("2.3", "Parental leave", 4, "Mothers get 26 weeks of paid maternity leave. Fathers get 2 weeks of paid paternity leave within 6 months of the birth."),
    ("3.1", "Work from home", 5, "Employees may work from home up to 2 days a week with their manager's approval."),
    ("4.1", "Health insurance", 6, "Medical insurance covers the employee, spouse and two children up to Rs 5 lakh a year."),
    ("5.1", "Travel claims", 8, "Submit bills on the Kharcha portal within 30 days of the trip. Approved claims are reimbursed within 15 days."),
    ("5.2", "Meal allowance", 8, "On client travel the daily meal allowance is Rs 1,200 in metro cities and Rs 800 in other cities."),
    ("5.3", "Hotel stay", 9, "Hotel stays are covered up to Rs 6,000 a night in metro cities and Rs 3,500 a night elsewhere."),
    ("6.1", "Laptops", 11, "A lost or stolen laptop must be reported to IT within 24 hours. The employee pays 10% of the replacement cost."),
    ("7.1", "Public holidays", 12, "The office is closed on 10 public holidays, including Diwali, Holi and Independence Day."),
    ("8.1", "Notice period", 14, "The notice period is 60 days. It can be shortened by paying basic salary for the remaining days."),
]

def handbook_docs():
    return [Document(page_content=f"{sec} {title}: {body}", id=f"handbook-{sec}",
                     metadata={"source": "hr/handbook-2026.pdf", "page": page, "section": sec})
            for sec, title, page, body in SECTIONS]

emb = ToyEmbeddings()
store = InMemoryVectorStore.from_documents(handbook_docs(), embedding=emb)
print(len(handbook_docs()), "chunks indexed")
```

Output:

```
11 chunks indexed
```

```python
import math
from collections import Counter

IT_KB = [
    ("it-1", "VPN error 809: the office firewall is blocking the connection. Switch to the Tarang-Secure Wi-Fi and reconnect."),
    ("it-2", "VPN error 720: your VPN client is out of date. Install version 6.2 from the Software Centre."),
    ("it-3", "Outlook error 0x800CCC0E: the mail server cannot be reached. Check that you are on the VPN."),
    ("it-4", "Forgot your password? Reset it at passwords.tarang.in using the OTP sent to your registered mobile."),
]
it_docs = [Document(page_content=t, id=i, metadata={"source": "it/kb.md", "page": 1, "section": i}) for i, t in IT_KB]
all_docs = handbook_docs() + it_docs
store.add_documents(it_docs)

def tokens(text):
    return [normalise(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]

class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.tfs = [Counter(tokens(d.page_content)) for d in docs]
        self.lengths = [sum(tf.values()) for tf in self.tfs]
        self.avg_length = sum(self.lengths) / len(self.lengths)
        df = Counter(term for tf in self.tfs for term in tf)
        self.idf = {t: math.log(1 + (len(docs) - n + 0.5) / (n + 0.5)) for t, n in df.items()}

    def score(self, query, i):
        tf, length, total = self.tfs[i], self.lengths[i], 0.0
        for term in tokens(query):
            if term in tf:
                f = tf[term]
                total += self.idf[term] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * length / self.avg_length))
        return total

    def search(self, query, k=10):
        scored = [(self.docs[i], self.score(query, i)) for i in range(len(self.docs))]
        return [pair for pair in sorted(scored, key=lambda p: -p[1]) if pair[1] > 0][:k]

bm25 = BM25(all_docs)

def keyword_ranking(q, k=10):
    return [d.metadata["section"] for d, _ in bm25.search(q, k)]

def vector_ranking(q, k=10):
    return [d.metadata["section"] for d, s in store.similarity_search_with_score(q, k=k) if s > 0]

q = "error 809 when connecting"
print("keyword:", keyword_ranking(q)[:4])
print("vector: ", vector_ranking(q)[:4])
```

Output:

```
keyword: ['it-1', 'it-3', 'it-2']
vector:  ['8.1', 'it-1', 'it-4', 'it-3']
```

Two ranked lists that disagree about first place. (Both helpers drop documents with a zero score: they matched nothing and shouldn't vote.) How do we combine them?

### 2. Fusion method 1: Reciprocal Rank Fusion (RRF)

**RRF** (Cormack, Clarke and Büttcher, 2009) ignores raw scores entirely and uses only **positions**:

```
RRF(doc) = Σ over lists of  1 / (k + rank of doc in that list)        with k = 60 by convention
```

A document ranked 1st in one list gets 1/61 ≈ 0.0164 from it; 2nd gets 1/62; 10th gets 1/70. A document that appears in **both** lists collects two contributions and usually beats one that's top of only one list. The constant 60 damps the difference between ranks, so a single list's opinion about first versus second place doesn't dominate.

```python
def rrf(rankings, k=60, weights=None):
    weights = weights or [1.0] * len(rankings)
    scores = {}
    for weight, ranking in zip(weights, rankings):
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + weight / (k + rank)
    return sorted(scores.items(), key=lambda pair: -pair[1])

for doc_id, score in rrf([keyword_ranking(q), vector_ranking(q)])[:4]:
    print(f"{doc_id:<5} {score:.4f}")
```

Output:

```
it-1  0.0325
it-3  0.0318
it-2  0.0313
8.1   0.0164
```

`it-1` is first in the keyword list and second in the vector list, so its two contributions add up to the highest total. Section 8.1, which only the vector list liked (thanks to a hash collision on "809"), falls behind. Notice what RRF **didn't** need: any idea whether a BM25 score of 4.26 is "better" than a cosine of 0.30.

### 3. Fusion method 2: normalise scores, then blend

The other common approach keeps the scores but rescales them first, then takes a weighted sum:

```
hybrid(doc) = α × norm(vector score) + (1 − α) × norm(keyword score)
```

**Min-max normalisation** maps each list's scores onto 0 to 1 (best = 1, worst = 0). α (alpha) sets the balance: 1 means pure vector, 0 pure keyword.

```python
def minmax(pairs):
    if not pairs:
        return {}
    lo, hi = min(s for _, s in pairs), max(s for _, s in pairs)
    return {d: (s - lo) / (hi - lo) if hi > lo else 1.0 for d, s in pairs}

def blend(q, alpha=0.5, k=10):
    kw = minmax([(d.metadata["section"], s) for d, s in bm25.search(q, k)])
    vec = minmax([(d.metadata["section"], s) for d, s in store.similarity_search_with_score(q, k=k) if s > 0])
    ids = set(kw) | set(vec)
    combined = {i: alpha * vec.get(i, 0) + (1 - alpha) * kw.get(i, 0) for i in ids}
    return sorted(combined.items(), key=lambda pair: -pair[1])

for alpha in (0.2, 0.5, 0.95):
    print(alpha, [(i, round(s, 2)) for i, s in blend(q, alpha)[:3]])
```

Output:

```
0.2 [('it-1', 0.97), ('8.1', 0.2), ('it-3', 0.1)]
0.5 [('it-1', 0.93), ('8.1', 0.5), ('it-3', 0.13)]
0.95 [('8.1', 0.95), ('it-1', 0.88), ('it-3', 0.17)]
```

At a low α the keyword side dominates and `it-1` wins comfortably. As α rises, the vector side's mistake (8.1) climbs, and at α = 0.95 it takes first place. The ranking depends on a knob you have to get right. Score blending can work well **once tuned**, and it uses more information than ranks (a runaway winner stays far ahead). But it has pitfalls:

| Issue | Why it matters |
|---|---|
| **Scale and distribution differ** | BM25 scores are unbounded and depend on query length; cosine scores cluster in a narrow band. Min-max stretches whatever range each query happens to produce. |
| **Outliers** | One very high score squashes everyone else towards 0 after min-max. |
| **α needs tuning** | And the best α can differ by query type (codes vs paraphrases). |

That's why **RRF is the usual default**: no tuning, robust to scale. Weaviate's hybrid search, for example, offers both a ranked fusion and a relative-score fusion; Elasticsearch, OpenSearch, Qdrant, Milvus and others offer RRF.

### 4. Does it help? Measure on a mixed test set

A realistic test set mixes question types: error codes and portal names (keyword territory) and paraphrased policy questions (vector territory).

```python
TESTS = [
    ("VPN error 720", "it-2"), ("error 809 when connecting", "it-1"), ("0x800CCC0E in Outlook", "it-3"),
    ("reset password with OTP", "it-4"), ("What food budget do I get when I visit customers?", "5.2"),
    ("My notebook was stolen", "6.1"), ("How many vacation days carry over?", "2.1"),
    ("Leave for new fathers?", "2.3"), ("Hotel budget in Mumbai?", "5.3"), ("If I quit, how long must I stay?", "8.1"),
    ("Is the office closed on Holi?", "7.1"), ("Who is covered by medical insurance?", "4.1"),
    ("Doctor's note for sick days?", "2.2"), ("Kharcha portal deadline", "5.1"),
]

def measure(name, rank_fn, k=3):
    hit1 = hitk = rr = 0
    for question, gold in TESTS:
        top = rank_fn(question)[:k]
        if gold in top:
            pos = top.index(gold)
            hitk, rr, hit1 = hitk + 1, rr + 1 / (pos + 1), hit1 + (pos == 0)
    n = len(TESTS)
    print(f"{name:<16} recall@1 {hit1/n:.2f}   recall@{k} {hitk/n:.2f}   MRR {rr/n:.2f}")

measure("keyword (BM25)", keyword_ranking)
measure("vector", vector_ranking)
measure("hybrid (RRF)", lambda q: [i for i, _ in rrf([keyword_ranking(q), vector_ranking(q)])])
measure("hybrid (blend)", lambda q: [i for i, _ in blend(q, 0.5)])
```

Output:

```
keyword (BM25)   recall@1 0.86   recall@3 0.86   MRR 0.86
vector           recall@1 0.86   recall@3 1.00   MRR 0.93
hybrid (RRF)     recall@1 0.93   recall@3 1.00   MRR 0.95
hybrid (blend)   recall@1 0.93   recall@3 1.00   MRR 0.96
```

The pattern you'll see on most real datasets: each single method has blind spots; hybrid search gets the best recall@1 and MRR, because it rescues the questions where one method stumbled and the other was right. Let's look at which question each method gets wrong at rank 1:

```python
for question, gold in TESTS:
    kw, vec = keyword_ranking(question)[:1], vector_ranking(question)[:1]
    hy = [i for i, _ in rrf([keyword_ranking(question), vector_ranking(question)])][:1]
    if kw != [gold] or vec != [gold] or hy != [gold]:
        print(f"{question:<50} gold={gold:<5} keyword={kw} vector={vec} hybrid={hy}")
```

Output:

```
error 809 when connecting                          gold=it-1  keyword=['it-1'] vector=['8.1'] hybrid=['it-1']
What food budget do I get when I visit customers?  gold=5.2   keyword=[] vector=['5.2'] hybrid=['5.2']
If I quit, how long must I stay?                   gold=8.1   keyword=['5.3'] vector=['5.3'] hybrid=['5.3']
```

- "error 809": keyword is right, vector is fooled; hybrid follows the list with the stronger agreement.
- "food budget": keyword finds **nothing** (no shared words), so hybrid simply uses the vector list. RRF degrades gracefully when one list is empty.
- "If I quit, how long must I stay?" is still wrong everywhere: the word "stay" pulls both methods to the **hotel stay** section. Neither retriever reads the question as a whole; a **reranker** does, which is the next lesson.

### 5. Weighting the lists

Sometimes you know one retriever deserves more trust (say, your users mostly paste error codes). Weighted RRF multiplies each list's contribution:

```python
q2 = "How many vacation days carry over?"
print("keyword:", keyword_ranking(q2)[:3], " vector:", vector_ranking(q2)[:3])
for w in ([1.0, 1.0], [2.0, 1.0], [1.0, 2.0]):
    fused = rrf([keyword_ranking(q2), vector_ranking(q2)], weights=w)
    print(f"weights keyword:vector = {w[0]:.0f}:{w[1]:.0f} -> {[i for i, _ in fused[:3]]}")
```

Output:

```
keyword: ['2.1', '8.1', '5.1']  vector: ['2.1', '7.1', '3.1']
weights keyword:vector = 1:1 -> ['2.1', '8.1', '7.1']
weights keyword:vector = 2:1 -> ['2.1', '8.1', '7.1']
weights keyword:vector = 1:2 -> ['2.1', '7.1', '8.1']
```

Both lists agree on first place, so the winner doesn't move; second place follows whichever list you weight more. Tune weights on your test set, not by intuition, and re-check them when your traffic changes.

### 6. A hybrid retriever for LangChain

Wrap the fusion in a `BaseRetriever` and it drops into any chain from [RAG with LangChain and a Vector DB](rag-with-langchain-and-a-vector-db.md):

```python
from langchain_core.retrievers import BaseRetriever

class HybridRetriever(BaseRetriever):
    """BM25 + vector search fused with Reciprocal Rank Fusion."""
    vectorstore: object
    keyword_index: object
    k: int = 3
    fetch_k: int = 10
    weights: tuple = (1.0, 1.0)

    def _get_relevant_documents(self, query, *, run_manager):
        kw = [d for d, _ in self.keyword_index.search(query, self.fetch_k)]
        vec = [d for d, s in self.vectorstore.similarity_search_with_score(query, k=self.fetch_k) if s > 0]
        by_id = {d.metadata["section"]: d for d in kw + vec}
        fused = rrf([[d.metadata["section"] for d in kw], [d.metadata["section"] for d in vec]], weights=list(self.weights))
        return [by_id[i].model_copy(update={"metadata": {**by_id[i].metadata, "rrf": round(s, 4)}})
                for i, s in fused[: self.k]]

hybrid = HybridRetriever(vectorstore=store, keyword_index=bm25)
for d in hybrid.invoke("VPN error 720 after the update"):
    print(d.metadata["section"], d.metadata["rrf"], d.page_content[:45])
```

Output:

```
it-2 0.0328 VPN error 720: your VPN client is out of date
it-3 0.0323 Outlook error 0x800CCC0E: the mail server can
it-1 0.0317 VPN error 809: the office firewall is blockin
```

LangChain's ready-made equivalent is `EnsembleRetriever`, which fuses any number of retrievers with weighted RRF:

```python
# not-run: needs langchain-classic, langchain-community and rank-bm25
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

bm25_retriever = BM25Retriever.from_documents(all_docs, k=10)
vector_retriever = store.as_retriever(search_kwargs={"k": 10})
hybrid = EnsembleRetriever(retrievers=[bm25_retriever, vector_retriever], weights=[0.5, 0.5])
hybrid.invoke("VPN error 720 after the update")
```

### 7. Hybrid search inside the database

For large collections you don't want to keep a BM25 index in Python memory. Many search engines and vector databases run both searches and the fusion server-side, in one query:

| System | How hybrid works there |
|---|---|
| **Elasticsearch / OpenSearch** | BM25 is native; add a dense vector field and combine with RRF or score normalisation in one request |
| **Qdrant** | Store a dense and a sparse (BM25-style or SPLADE) vector per point; the Query API prefetches from both and fuses with RRF |
| **Weaviate** | A `hybrid` query with an `alpha` between keyword and vector, using ranked or relative-score fusion |
| **Milvus, Pinecone, MongoDB Atlas, Azure AI Search, PostgreSQL** | Each supports sparse or full-text search alongside vectors, with a fusion step (in PostgreSQL you combine `tsvector` full-text search with pgvector yourself, often using RRF in SQL) |

With LangChain's Qdrant integration, hybrid is a constructor option:

```python
# not-run: needs langchain-qdrant and fastembed
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode

store = QdrantVectorStore.from_documents(
    all_docs, embedding=dense_embeddings, sparse_embedding=FastEmbedSparse(model_name="Qdrant/bm25"),
    location=":memory:", collection_name="tarang-kb", retrieval_mode=RetrievalMode.HYBRID)
store.similarity_search("VPN error 720 after the update", k=3)
```

### 8. Practical tips

- **Tokenisation matters for BM25.** Error codes like `0x800CCC0E`, versions like `6.2` and Hindi or mixed-script text need a tokenizer that keeps them intact. Test with your real identifiers.
- **Fetch wider than you keep.** Fuse the top 20 to 50 from each list, then keep a few (or hand them to a reranker).
- **Contextual chunks help both sides.** Heading paths and contextual-retrieval lines (from [Chunking Strategies](chunking-strategies.md)) add useful keywords for BM25 as well as meaning for embeddings.
- **Log both lists.** When a question fails, seeing the keyword and vector rankings side by side tells you which side to fix.

---

## Try It Yourself

1. **RRF by hand.** A document is 3rd in the keyword list and 1st in the vector list. Another is 1st in the keyword list and absent from the vector list. Which wins with k=60? Check with `rrf`.
2. **The k constant.** Re-run `measure` for hybrid RRF with `k=1` and `k=60`. Does the constant change the results on this small test set? What does a small k do in general?
3. **Alpha sweep.** Measure `blend` at α = 0.2, 0.5 and 0.8. Which α is best here, and would you trust that choice on a different test set?

<details>
<summary>Show answers</summary>

**1.**

```python
print([(d, round(s, 4)) for d, s in rrf([["x", "y", "A"], ["A", "z"]])])
print([(d, round(s, 4)) for d, s in rrf([["B", "x"], ["y", "z"]])])
```

Output:

```
[('A', 0.0323), ('x', 0.0164), ('y', 0.0161), ('z', 0.0161)]
[('B', 0.0164), ('y', 0.0164), ('x', 0.0161), ('z', 0.0161)]
```

A gets 1/63 + 1/61 ≈ 0.0323; B gets only 1/61 ≈ 0.0164. Agreement between the lists beats a single first place.

**2.**

```python
for k in (1, 60):
    measure(f"RRF k={k}", lambda q, k=k: [i for i, _ in rrf([keyword_ranking(q), vector_ranking(q)], k=k)])
```

Output:

```
RRF k=1          recall@1 0.93   recall@3 1.00   MRR 0.95
RRF k=60         recall@1 0.93   recall@3 1.00   MRR 0.95
```

On this small set the results don't change at all. In general, a small k makes the top positions count much more (1/2 vs 1/3 is a big gap; 1/61 vs 1/62 is not), so a single list's first place can dominate. k = 60 is a robust default from the original paper.

**3.**

```python
for alpha in (0.2, 0.5, 0.8):
    measure(f"blend a={alpha}", lambda q, a=alpha: [i for i, _ in blend(q, a)])
```

Output:

```
blend a=0.2      recall@1 0.93   recall@3 1.00   MRR 0.96
blend a=0.5      recall@1 0.93   recall@3 1.00   MRR 0.96
blend a=0.8      recall@1 0.93   recall@3 1.00   MRR 0.96
```

With only 14 questions, small differences are noise. Choose α on a larger, representative test set, and prefer RRF when you can't tune.

</details>

---

## Real-World Examples

- **Developer documentation assistants** rely on hybrid search because users paste exact error messages and API names as often as they ask "how do I..." questions.
- **E-commerce search** combines keyword matching on brands, model numbers and sizes with semantic matching on descriptions.
- **Enterprise search products** built on Elasticsearch or OpenSearch typically add a dense vector field to an existing BM25 index and fuse with RRF, rather than replacing keyword search.
- **Anthropic's contextual retrieval** results combined contextual embeddings with contextual BM25, and the hybrid did clearly better than embeddings alone.

---

## Common Misconceptions

### "Just add the two scores together"

BM25 and cosine scores are on different scales; adding them raw lets one method dominate unpredictably. Normalise and weight them, or fuse by rank.

### "Hybrid search is only for keyword-heavy domains"

Even in plain-language domains, names, numbers and rare terms show up. Hybrid rarely hurts and often helps; measure to be sure.

### "RRF throws away useful information"

It ignores score magnitudes on purpose, trading a little information for a lot of robustness. When you can tune on good data, score blending can edge ahead.

### "Hybrid search fixes everything"

It improves recall. It doesn't understand the question as a whole, which is why "If I quit, how long must I stay?" still fails. That's the reranker's job.

---

## Interview Relevance

*"What is hybrid search and why use it?"* Combine sparse (BM25) and dense retrieval because they fail on different queries; explain fusion by RRF (`1/(k + rank)`, k = 60) vs normalised weighted sum (alpha), with pros and cons; mention native support in Elasticsearch/OpenSearch, Qdrant, Weaviate and others, and LangChain's `EnsembleRetriever`.

*"Your RAG system misses queries with product codes. What do you do?"* Add a BM25 or sparse index with a code-friendly tokenizer, fuse with RRF, verify with a test set that includes code queries.

---

## Key Takeaways

- **Keyword and vector search fail on different questions**, so running both and fusing the lists improves recall and ranking.
- **Reciprocal Rank Fusion** (`Σ 1/(60 + rank)`) needs no score calibration and is the safe default.
- **Score blending** (min-max plus alpha) can work once tuned, but is sensitive to scales and outliers.
- **LangChain** offers `EnsembleRetriever`; many databases run hybrid queries natively.
- **Hybrid search widens recall; a reranker then fixes precision.**

---

**Up next:** [Reranking](reranking.md)
