---
title: "Deploying Self-RAG Locally"
course: Agentic RAG Systems
module: "4. Self-RAG"
type: Article
level: Advanced
reading_time: 35 min
---

# Deploying Self-RAG Locally: The Complete Guide

> 📚 **Before you start**
>
> - [Self-RAG with a Vector DB](self-rag-with-a-vector-db.md), for the indexed store, filters and verdict cache.
> - [Running Adaptive RAG Locally](../02-adaptive-rag/running-adaptive-rag-locally.md), for Ollama, local model settings and making small models' decisions robust.
> - [Deploying and Running LangGraph Apps](../../langgraph-complete-guide/10-deployment-and-observability/deploying-and-running-langgraph-apps.md), for wrapping a graph in FastAPI and testing it with `TestClient`.

## Introduction

A district hospital's IT team has built a Self-RAG assistant over the hospital's standard operating procedures. On a developer's laptop it works beautifully. Now it has to run on the server in the records room, answer forty nurses during a shift change, survive a power cut and a reboot, never send a word outside the building, and, crucially, never show a nurse an answer its own support check failed.

That gap, from "works in a notebook" to "runs as a service people rely on", is what this lesson closes. Nothing about Self-RAG's logic changes. What's added is the engineering around it: a clear API, persistence, startup checks, timeouts, honest responses when a check fails, logs you can debug from, and a way to update the knowledge without downtime.

By the end of this lesson you will be able to:

- lay out a fully local Self-RAG deployment: FastAPI, the graph, Ollama, and a persistent Chroma store;
- build the graph from injected components, so the same code runs with stand-ins in tests and real models in production;
- design a response that carries the answer, its sources and its verdicts, and falls back safely when a check fails;
- add timeouts, health checks and structured logs;
- test the whole service end to end with `TestClient`, and run it with Docker Compose.

> 💡 **Key Insight**
>
> A deployed Self-RAG service must **expose its verdicts, not hide them**. The graph already knows whether the answer is supported and useful; the API should return that, and should replace any answer that failed its checks with an honest fallback. Everything else (timeouts, health checks, logs) exists so that you find out when it goes wrong before the users do.

---

## Core Explanation

### 1. The deployment at a glance

![A staff app calls POST /ask on a FastAPI service inside your server. The service validates input, applies a timeout, logs, and returns verdicts. It runs the Self-RAG graph, which calls Ollama (a small model for graders and a larger one for answers) and a persistent Chroma store holding chunks and metadata. A separate indexing job reads the internal help-centre pages and upserts into Chroma, deleting stale chunks. Logs record path, verdicts and latency. Nothing leaves the server.](/img/diagrams/agentic-rag-systems/local-self-rag-deployment.svg)
*Every box runs on hardware you control. The indexing job and the question-answering service share only the Chroma folder.*

| Component | Runs as | Notes |
|---|---|---|
| **FastAPI service** | A Python process (`uvicorn`) | Stateless apart from loaded objects; can run several copies |
| **Self-RAG graph** | Inside the service | Built once at startup, reused for every request |
| **Ollama** | Its own process or container, port 11434 | Holds the models in memory; the slowest component |
| **Chroma** | Embedded in the service, persisting to a folder | One process should own the folder; use a Chroma server if several services need it |
| **Indexing job** | A separate script, run on a schedule or when pages change | Never runs inside a request |

The split between the indexing job and the service matters. Indexing is slow and occasionally fails halfway; answering questions must be fast and always available. Keeping them separate means a bad indexing run can't take the assistant down.

### 2. Build the graph from injected parts

The single most useful structural decision: **write one function that builds the graph from its parts** (store, filter, models), instead of creating models at import time. Tests pass stand-ins; production passes Ollama and Chroma. The graph code is identical in both.

First the shared setup (help centre and stand-ins, as in the last two lessons, condensed):

```python
import json, math, re, time
from typing import Callable, Literal, TypedDict
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

class KeywordEmbeddings(Embeddings):
    """Toy embedding: one dimension per keyword stem, plus a small constant. Offline stand-in only."""
    def __init__(self, stems):
        self.stems = stems

    def _embed(self, text):
        words = re.findall(r"[a-z]+", text.lower())
        vector = [float(sum(w.startswith(s) for w in words)) for s in self.stems]
        vector.append(0.1)
        norm = math.sqrt(sum(x * x for x in vector))
        return [x / norm for x in vector]

    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]

    def embed_query(self, text):
        return self._embed(text)

STEMS = ["cancel", "refund", "fee", "fare", "tatkal", "upi", "wallet", "card", "payment",
         "method", "bag", "luggage", "kg", "pet", "dog", "railway"]

PAGES = [
    ("refunds-1", "refunds.md §1", "Cancelling a confirmed ticket more than 48 hours before departure costs a flat "
     "fee of ₹60 per passenger. Between 48 and 12 hours before departure, 25% of the fare is deducted."),
    ("refunds-3", "refunds.md §3", "If the railway cancels a train, every ticket on it is refunded in full "
     "automatically. The money goes back to the original payment method; payments.md lists how long each takes."),
    ("payments-2", "payments.md §2", "Refund timelines by payment method: SaathiRail Wallet is instant, UPI takes "
     "1 to 3 working days, and credit or debit cards take 5 to 7 working days."),
    ("pets-1", "pets.md §1", "Pets such as dogs and cats travel only in a fully booked first class cabin."),
]

class StandInModel(BaseChatModel):
    """A chat model whose replies come from a Python function. For offline lessons only."""
    respond: Callable

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return ChatResult(generations=[ChatGeneration(message=self.respond(messages))])

    @property
    def _llm_type(self):
        return "stand-in"

    def bind_tools(self, tools, **kwargs):
        return self

def structured_reply(schema_name, **fields):
    return AIMessage("", tool_calls=[{"name": schema_name, "args": fields, "id": "call_1"}])

class IsRelevant(BaseModel):
    """Is this document relevant to the question?"""
    relevant: Literal["yes", "no"]

class IsSupported(BaseModel):
    """Is every factual claim in the answer supported by the documents?"""
    support: Literal["fully", "partially", "no"]
    unsupported_claims: list[str] = Field(default_factory=list)

def relevance_rules(messages):
    question, document = messages[-1].content.lower().split("document:")
    wanted = {t for t in STEMS if t in question}
    covered = len(wanted & {t for t in STEMS if t in document}) / len(wanted) if wanted else 0
    return structured_reply("IsRelevant", relevant="yes" if covered > 0.5 else "no")

def support_rules(messages):
    docs, answer = messages[-1].content.split("Answer:")
    answer = re.sub(r"\[[^\]]*\]", "", answer)
    missing = [c for c in re.findall(r"₹?\d+%?(?: to \d+)?", answer) if c not in docs]
    return structured_reply("IsSupported", support="fully" if not missing else "partially", unsupported_claims=missing)

def generator_rules(messages):
    prompt = messages[-1].content
    if "payments.md §2" in prompt:
        return AIMessage("UPI refunds take 1 to 3 working days and cards 5 to 7 [payments.md §2].")
    if "refunds.md §1" in prompt:
        return AIMessage("More than 48 hours ahead, it's ₹60 per passenger plus a ₹20 service charge [refunds.md §1]."
                         if "unsupported" not in prompt else
                         "More than 48 hours ahead, it's a flat ₹60 per passenger [refunds.md §1].")
    return AIMessage("I couldn't find this in the help centre.")
```

Now the builder. It takes every external dependency as an argument and returns a compiled graph. The graph is the Self-RAG core from the previous lessons: retrieve (filtered and thresholded), grade, generate, check support, regenerate with feedback up to a cap.

```python
MAX_GENERATIONS = 2

class ServiceState(TypedDict):
    question: str
    docs: list
    answer: str
    support: str
    feedback: str
    generations: int
    path: list

def build_self_rag(store, search_filter, relevance_grader, support_grader, generator, k=4, min_score=0.3):
    def retrieve(state: ServiceState):
        hits = store.similarity_search_with_score(state["question"], k=k, filter=search_filter)
        return {"docs": [d for d, s in hits if s >= min_score], "path": state["path"] + ["retrieve"]}

    def grade(state: ServiceState):
        kept = [d for d in state["docs"] if relevance_grader.invoke(
            f"Question: {state['question']}\nDocument: {d.page_content}").relevant == "yes"]
        return {"docs": kept, "path": state["path"] + ["grade"]}

    def generate(state: ServiceState):
        context = "\n".join(f"[{d.metadata['source']}] {d.page_content}" for d in state["docs"])
        prompt = f"{state['feedback']}\nDocuments:\n{context}\n\nQuestion: {state['question']}"
        return {"answer": generator.invoke(prompt).content, "generations": state["generations"] + 1,
                "path": state["path"] + ["generate"]}

    def check_support(state: ServiceState):
        context = "\n".join(d.page_content for d in state["docs"])
        verdict = support_grader.invoke(f"{context}\nAnswer: {state['answer']}")
        feedback = f"Your previous answer had unsupported claims: {verdict.unsupported_claims}." \
            if verdict.support != "fully" else ""
        return {"support": verdict.support, "feedback": feedback, "path": state["path"] + ["check_support"]}

    def after_support(state: ServiceState) -> Literal["generate", "__end__"]:
        return "generate" if state["support"] != "fully" and state["generations"] < MAX_GENERATIONS else END

    g = StateGraph(ServiceState)
    for name, fn in [("retrieve", retrieve), ("grade", grade), ("generate", generate), ("check_support", check_support)]:
        g.add_node(name, fn)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "grade")
    g.add_edge("grade", "generate")
    g.add_edge("generate", "check_support")
    g.add_conditional_edges("check_support", after_support)
    return g.compile()

store = InMemoryVectorStore(KeywordEmbeddings(STEMS))
store.add_documents([Document(text, id=pid, metadata={"source": src, "status": "current"})
                     for pid, src, text in PAGES], ids=[p[0] for p in PAGES])

graph = build_self_rag(
    store=store,
    search_filter=lambda d: d.metadata["status"] == "current",
    relevance_grader=StandInModel(respond=relevance_rules).with_structured_output(IsRelevant),
    support_grader=StandInModel(respond=support_rules).with_structured_output(IsSupported),
    generator=StandInModel(respond=generator_rules),
)
out = graph.invoke({"question": "What is the fee to cancel 3 days before departure?",
                    "feedback": "", "generations": 0, "path": []})
print(out["path"])
print(out["support"], "->", out["answer"])
```

Output:

```
['retrieve', 'grade', 'generate', 'check_support', 'generate', 'check_support']
fully -> More than 48 hours ahead, it's a flat ₹60 per passenger [refunds.md §1].
```

The production call to the same builder, run once at startup:

```python
# not-run: needs Ollama with these models pulled, plus langchain-ollama and langchain-chroma
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings

OLLAMA = "http://localhost:11434"           # in Docker Compose: http://ollama:11434
small = ChatOllama(model="llama3.1:8b", temperature=0, num_ctx=8192, keep_alive="30m", base_url=OLLAMA)
large = ChatOllama(model="gpt-oss:20b", temperature=0, num_ctx=8192, keep_alive="30m", base_url=OLLAMA)

graph = build_self_rag(
    store=Chroma(collection_name="saathirail_help", persist_directory="./chroma_saathirail",
                 embedding_function=OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA)),
    search_filter={"status": "current"},
    relevance_grader=small.with_structured_output(IsRelevant),
    support_grader=small.with_structured_output(IsSupported),
    generator=large,
    min_score=0.0,      # re-tune for this store: Chroma's similarity_search_with_score returns distances
)
```

Two details in that block are deployment lessons in themselves. The store's score semantics differ (Chroma returns distances), so the threshold logic must be re-tuned, ideally by switching the retrieve node to `similarity_search_with_relevance_scores`. And the graders run on the **small** model while answers run on the **large** one; graders are narrow decisions called several times per request, so they dominate the call count.

### 3. A response that tells the truth

What should `POST /ask` return? Not just a string. The caller (a web app, a chat widget) needs enough to display the answer responsibly:

```json
{
  "answer": "More than 48 hours ahead, it's a flat ₹60 per passenger [refunds.md §1].",
  "verified": true,
  "support": "fully",
  "sources": ["refunds.md §1"],
  "path": ["retrieve", "grade", "generate", "check_support", "generate", "check_support"],
  "request_id": "req-0001"
}
```

The rule that makes the deployment safe: **if the answer didn't pass its support check, don't return it as the answer**. Replace it with a fallback that says what happened and points to the sources, and set `verified` to false so the UI can style it differently. Here is the service:

```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from fastapi import FastAPI, HTTPException

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)

class AskResponse(BaseModel):
    answer: str
    verified: bool
    support: str
    sources: list[str]
    path: list[str]
    request_id: str

FALLBACK = ("I found related help-centre pages but couldn't verify every detail of an answer. "
            "Please check the sources listed, or contact support.")
NOT_FOUND = "I couldn't find this in the help centre. Please contact support."

def create_app(graph, timeout_s=20.0, log=print):
    app = FastAPI(title="SaathiRail Self-RAG")
    pool = ThreadPoolExecutor(max_workers=4)
    counter = {"n": 0}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/ask", response_model=AskResponse)
    def ask(req: AskRequest):
        counter["n"] += 1
        request_id = f"req-{counter['n']:04d}"
        start = time.perf_counter()
        future = pool.submit(graph.invoke, {"question": req.question, "feedback": "", "generations": 0, "path": []},
                             {"recursion_limit": 20})
        try:
            out = future.result(timeout=timeout_s)
        except FutureTimeout:
            log(json.dumps({"request_id": request_id, "event": "timeout", "timeout_s": timeout_s}))
            raise HTTPException(status_code=504, detail="The assistant took too long. Please try again.")
        verified = out["support"] == "fully" and "couldn't find" not in out["answer"]
        sources = sorted({d.metadata["source"] for d in out["docs"]})
        log(json.dumps({"request_id": request_id, "path": out["path"], "support": out["support"],
                        "verified": verified, "sources": sources,
                        "slow": time.perf_counter() - start > timeout_s / 2}, ensure_ascii=False))
        answer = out["answer"] if verified else (FALLBACK if out["docs"] else NOT_FOUND)
        return AskResponse(answer=answer, verified=verified,
                           support=out["support"], sources=sources, path=out["path"], request_id=request_id)

    return app
```

A few design choices worth naming:

- **Input validation** with Pydantic (`min_length`, `max_length`) rejects empty and absurdly long questions before any model runs. A 50,000-character "question" would blow the local model's context window and tie up the server.
- **A per-request timeout.** Local models can be slow, especially when several requests queue for one model. The graph runs in a worker thread and the request waits at most `timeout_s`. One caveat: Python can't kill the thread, so a timed-out graph keeps running in the background until it finishes; the recursion limit and loop caps keep that bounded.
- **A recursion limit** passed per request as a last line of defence against a loop you didn't cap.
- **One structured log line per request**, JSON so it can be searched: request id, path, verdicts, sources and a slow-request flag. That line is what you'll read when someone reports a wrong answer.

### 4. Testing the service end to end

FastAPI's `TestClient` calls the app in-process, no server needed. With stand-ins injected, these tests run in seconds and can run in CI on every change:

```python
from fastapi.testclient import TestClient

logs = []
client = TestClient(create_app(graph, log=logs.append))

r = client.post("/ask", json={"question": "What is the fee to cancel 3 days before departure?"})
print(r.status_code, json.dumps(r.json(), ensure_ascii=False, indent=1))
print("log:", logs[-1])
```

Output:

```
200 {
 "answer": "More than 48 hours ahead, it's a flat ₹60 per passenger [refunds.md §1].",
 "verified": true,
 "support": "fully",
 "sources": [
  "refunds.md §1"
 ],
 "path": [
  "retrieve",
  "grade",
  "generate",
  "check_support",
  "generate",
  "check_support"
 ],
 "request_id": "req-0001"
}
log: {"request_id": "req-0001", "path": ["retrieve", "grade", "generate", "check_support", "generate", "check_support"], "support": "fully", "verified": true, "sources": ["refunds.md §1"], "slow": false}
```

The generator's first attempt invented a ₹20 service charge; the support check caught it; the second attempt passed, so `verified` is true and the user sees the clean answer. The `path` and the log line both show the retry, which is exactly what you'd want to see when investigating "why was this answer slow?".

Now the cases that must *not* produce a confident answer:

```python
r = client.post("/ask", json={"question": "Can I bring my parrot?"})
print(r.status_code, r.json()["verified"], "|", r.json()["answer"][:60], "|", r.json()["sources"])

r = client.post("/ask", json={"question": "?"})
print(r.status_code, r.json()["detail"][0]["type"])

print(client.get("/health").json())
```

Output:

```
200 False | I couldn't find this in the help centre. Please contact supp | []
422 string_too_short
{'status': 'ok'}
```

The parrot question found nothing relevant (the pets page says dogs and cats, and our relevance rule has no "parrot"), so the user gets an honest "not found" rather than a guess. (When pages *were* found but the answer failed its support check, the other fallback, `FALLBACK`, is used instead and the sources are listed.) The one-character question is rejected by validation with a 422 before any model call.

Finally, the timeout. A deliberately slow graph shows the 504 path:

```python
class SlowGraph:
    def invoke(self, state, config=None):
        time.sleep(0.5)
        return graph.invoke(state, config)

slow_client = TestClient(create_app(SlowGraph(), timeout_s=0.1, log=logs.append))
r = slow_client.post("/ask", json={"question": "What is the fee to cancel?"})
print(r.status_code, r.json()["detail"])
print("log:", logs[-1])
```

Output:

```
504 The assistant took too long. Please try again.
log: {"request_id": "req-0001", "event": "timeout", "timeout_s": 0.1}
```

### 5. Startup: warm up and fail fast

At startup, before accepting traffic, the service should check that its dependencies work and **warm them up**: loading a model into Ollama's memory can take many seconds, and the first user shouldn't pay for it. FastAPI runs startup code through a **lifespan** function:

```python
# not-run: production startup for the service in section 2 (needs Ollama and Chroma)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    small.invoke("Reply with OK.")                   # loads the grader model into memory
    large.invoke("Reply with OK.")                   # loads the answer model
    if not store.similarity_search("refund", k=1):  # the index exists and isn't empty
        raise RuntimeError("Chroma collection is empty: run the indexing job first")
    yield                                            # the app serves requests here

app = FastAPI(title="SaathiRail Self-RAG", lifespan=lifespan)
```

If a check fails, the service refuses to start, and your process manager or container platform reports it, rather than the service starting "healthy" and failing every request. Make `/health` meaningful the same way: a cheap check that the store answers and Ollama is reachable, so a load balancer can stop sending traffic to a broken instance.

### 6. Running it with Docker Compose

A two-container setup: Ollama with a volume so models survive restarts, and the API with a volume for the Chroma folder.

```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama
    volumes:
      - ollama_models:/root/.ollama     # pulled models survive container restarts
    ports:
      - "11434:11434"
  api:
    build: .
    command: uvicorn app:app --host 0.0.0.0 --port 8000
    environment:
      - OLLAMA_URL=http://ollama:11434
    volumes:
      - ./chroma_saathirail:/app/chroma_saathirail
    ports:
      - "8000:8000"
    depends_on:
      - ollama
volumes:
  ollama_models:
```

```bash
docker compose up -d
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull gpt-oss:20b
docker compose exec ollama ollama pull nomic-embed-text
docker compose run --rm api python index.py        # the indexing job, once and then on a schedule
curl -s -X POST localhost:8000/ask -H 'content-type: application/json' \
     -d '{"question": "What is the fee to cancel 3 days before departure?"}'
```

Example output:

```
{"answer":"More than 48 hours ahead, it's a flat ₹60 per passenger [refunds.md §1].","verified":true,"support":"fully","sources":["refunds.md §1"],"path":["retrieve","grade","generate","check_support"],"request_id":"req-0001"}
```

For a GPU, Ollama's container needs the GPU passed through (with the NVIDIA container toolkit on Linux); without one, everything still works on CPU, just more slowly, so size models to the hardware. Ollama also reads environment variables such as `OLLAMA_KEEP_ALIVE` (how long models stay loaded) and `OLLAMA_NUM_PARALLEL` (how many requests one model serves at once); check Ollama's documentation for the current list before tuning them.

### 7. Capacity: where the time goes

Every Self-RAG request makes several model calls, so on local hardware the model server is the bottleneck. Estimate before you launch:

```python
calls = {"relevance grades (k=4)": 4, "generate": 1, "support check": 1}
retry_rate = 0.2                      # share of questions needing a second generation + check
seconds = {"relevance grades (k=4)": 0.4, "generate": 3.0, "support check": 0.6}   # per call, measured on your box

per_request = sum(calls[c] * seconds[c] for c in calls) + retry_rate * (seconds["generate"] + seconds["support check"])
print(f"average time per question: {per_request:.1f} s")
print(f"questions per minute with one model worker: {60 / per_request:.0f}")
```

Output:

```
average time per question: 5.9 s
questions per minute with one model worker: 10
```

With these (made-up but typical-shaped) timings, one model worker serves about ten questions a minute. Forty nurses at shift change won't wait patiently for that. The levers, in the order teams usually pull them:

| Lever | Effect |
|---|---|
| Pre-filter by score and metadata (previous lesson) | Fewer relevance grades per request |
| Batch the relevance grades into one call ("grade these 4 documents") | 4 calls become 1 |
| Smaller grader model, larger answer model | Graders get much faster |
| Cache answers for repeated questions, keyed by normalised question and index version | Repeat questions cost nothing |
| Stream the answer to the UI | Same total time, but the user sees progress |
| More GPU memory, or a second machine | Real parallelism |

Answer caching needs one care point: invalidate the cache when the index changes (key it on an index version that the indexing job bumps), or the cache will serve answers based on yesterday's policy.

### 8. Updating knowledge without downtime

The indexing job from [Self-RAG with a Vector DB](self-rag-with-a-vector-db.md) runs separately: it upserts changed chunks by stable id and deletes stale ones. Two operational rules keep it safe alongside a live service:

- **Single writer.** Only the indexing job writes to the store. An embedded Chroma folder should be owned by one process at a time; if the service and the indexer must both open it, run Chroma as a server instead.
- **Build, then switch, for big changes.** For a full re-index (a new embedding model, say), build a new collection alongside the old one, run your evaluation set against it, then point the service at the new collection name. Never re-index in place a collection that's serving traffic with a different embedding model: queries embedded by the new model against vectors from the old one return nonsense.

---

## Try It Yourself

1. **Return the reason.** Add a `reason` field to `AskResponse` that is `"verified"`, `"unsupported"`, `"not_found"` or `"timeout"`, and set it correctly in `ask`. (Timeouts return 504, so `"timeout"` only appears in logs.)
2. **A cache with versioning.** Write `cached_ask(question, index_version, run)` that stores results in a dict keyed by the lower-cased, whitespace-collapsed question plus the index version, and only calls `run(question)` on a miss.
3. **Capacity.** Using the section 7 numbers, how many questions per minute would you serve if the four relevance grades were batched into one call that takes 0.6 s?

<details>
<summary>Show answers</summary>

**1.** Compute it next to `verified`:

```python
def reason_for(out):
    if "couldn't find" in out["answer"] or not out["docs"]:
        return "not_found"
    return "verified" if out["support"] == "fully" else "unsupported"

print(reason_for({"answer": "x", "docs": [1], "support": "fully"}),
      reason_for({"answer": "x", "docs": [1], "support": "partially"}),
      reason_for({"answer": "I couldn't find this.", "docs": [], "support": "fully"}))
```

Output:

```
verified unsupported not_found
```

Add `reason: str` to `AskResponse` and `reason=reason_for(out)` to the constructor call; log `"timeout"` in the 504 branch.

**2.**

```python
answer_cache = {}

def cached_ask(question, index_version, run):
    key = (" ".join(question.lower().split()), index_version)
    if key not in answer_cache:
        answer_cache[key] = run(question)
    return answer_cache[key]

calls = []
run = lambda q: calls.append(q) or f"answer to {q!r}"
cached_ask("Fee to cancel?", "v7", run)
cached_ask("  fee to   CANCEL? ", "v7", run)
cached_ask("Fee to cancel?", "v8", run)
print(len(calls), "graph runs for 3 requests")
```

Output:

```
2 graph runs for 3 requests
```

The second request hit the cache despite different spacing and case; the third missed because the index version changed, which is exactly when the old answer might be wrong.

**3.**

```python
batched = 0.6 + 3.0 + 0.6 + retry_rate * (3.0 + 0.6)
print(f"{batched:.1f} s per question, {60 / batched:.0f} per minute")
```

Output:

```
4.9 s per question, 12 per minute
```

Batching the grades saves a full second per question (about a sixth). The generation call still dominates, which is why streaming and a well-sized answer model matter most.

</details>

---

## Real-World Examples

- **Hospitals and labs** run Self-RAG over SOPs on an on-premises server with a local model, returning a "verified" flag that the nurse-facing UI shows as a green tick next to the cited SOP section.
- **Government departments** deploy local assistants over circulars and acts on servers inside their own network, with nightly indexing jobs and answer caches keyed by circular version.
- **Factories** put small local RAG services on edge servers next to the production line, so maintenance staff can query equipment manuals even when the internet link is down.

---

## Common Misconceptions

### "Deployment means putting the notebook behind an endpoint"

The notebook has no timeouts, no input limits, no warm-up, no logs and no fallback. Those are most of the work, and most of what users experience.

### "If the support check fails, return the answer with a warning"

Users skim past warnings. If the answer failed its check, return a fallback and the sources, and let a person decide; don't put unverified claims in the answer slot.

### "One Chroma folder can be shared by every service"

An embedded store's folder should have one owner. For several writers or several services, run the database as a server.

### "Local means slow, so it can't serve a team"

It's slower per call, but with pre-filtering, batched grading, small graders, caching and streaming, a single well-sized machine serves a department comfortably. Measure, then size.

---

## Interview Relevance

*"How would you deploy a RAG system that must run on-premises?"* FastAPI service with the graph built once at startup via dependency injection; Ollama (or another local server) for models with warm-up and keep-alive; a persistent vector store with a separate indexing job; input validation, timeouts, recursion limits; structured logs; health checks; Docker Compose with volumes for models and data.

*"How do you make sure users don't see hallucinated answers?"* Run the support check in the graph, return the verdict in the API, replace unverified answers with a fallback plus sources, and log every verdict for review.

*"How do you scale it?"* Measure per-call latency; reduce calls (pre-filter, batch grading), use small graders, cache answers keyed by index version, stream output, then add hardware.

---

## Key Takeaways

- **Build the graph from injected parts**: stand-ins in tests, Ollama and Chroma in production, identical graph code.
- **Return the verdicts**: answer, sources, support and a `verified` flag; replace unverified answers with an honest fallback.
- **Guard every request** with validation, a timeout and a recursion limit, and log one structured line per request.
- **Warm up and fail fast at startup**, and keep `/health` meaningful.
- **Keep indexing separate** from serving, with one writer, and switch collections for big re-indexes.

---

**Up next:** [Lab: Build Self-RAG](lab-build-self-rag.md)
