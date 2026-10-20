---
title: "Running Adaptive RAG Locally"
course: Agentic RAG Systems
module: "2. Adaptive RAG"
type: Article
level: Advanced
reading_time: 32 min
---

# Running Adaptive RAG Locally: The Complete Guide

> 📚 **Before you start**
>
> - [What is Adaptive RAG?](what-is-adaptive-rag.md), for the complexity classifier and the three strategies.
> - [Adaptive RAG with Cohere](adaptive-rag-with-cohere.md), for source routing, reranking and the idea that providers are plug-ins.
> - [LangChain Complete Guide › Models](../../langchain-complete-guide/course.md#m3), for open-source models, and [Structured Output and Output Parsers](../../langchain-complete-guide/course.md#m5).

## Introduction

A cooperative bank in Pune wants an assistant for its staff that answers questions from its circulars and loan rules. The board has one non-negotiable condition: **no customer data and no internal document leaves the bank's own machines**. No hosted API, however good, is allowed. Many hospitals, government offices and law firms are in the same position, and India's Digital Personal Data Protection Act makes teams think carefully before sending personal data to outside services.

The answer is to run the whole adaptive RAG system **locally**: the embedding model, the vector store, the router and the generator all on hardware you control. The graph you built in the last two lessons doesn't change. What changes is the models, and that turns out to matter a lot, because a model small enough to run on a laptop or a single office server is much worse at exactly the thing adaptive RAG depends on: making small, precise, structured decisions.

By the end of this lesson you will be able to:

- set up a local stack with Ollama, local embeddings and a local vector store;
- choose which models to run for routing and for answering;
- make a small model's structured decisions reliable with schemas, validation, repair and fallbacks;
- measure a local router's accuracy against a labelled question set before trusting it.

> 💡 **Key Insight**
>
> Going local doesn't change the graph; it changes **how much you can trust each decision**. A small local model will sometimes return a misspelt label, prose instead of JSON, or no decision at all. So every decision node needs three layers: a **schema** that constrains the output, a **repair** step that rescues near-misses, and a **safe fallback** (usually "retrieve") when all else fails.

---

## Core Explanation

### 1. What changes when you go local

| | Hosted (previous lesson) | Local |
|---|---|---|
| **Where data goes** | To the provider's servers | Nowhere: stays on your machine or network |
| **Cost** | Per token | Hardware and electricity; no per-call bill |
| **Model size** | Very large models | Typically a few billion to a few tens of billions of parameters, limited by your RAM or GPU memory |
| **Decision quality** | High: reliable tool calls and structured output | Lower: occasional malformed or wrong decisions |
| **Latency** | Network round trip plus fast inference | No network, but inference speed depends entirely on your hardware |
| **Context window** | Large | Often configured small by default; set it explicitly |
| **Web search** | Easy to add | Possible, but the request leaves your machine; many local deployments drop the web route |

The last row matters for design: if "nothing leaves the building" is the requirement, a web-search route breaks it. A fully local adaptive RAG system therefore often has only complexity routes (no retrieval, single-step, multi-step) plus an honest "I can't check live information" answer for live questions.

### 2. The local stack

**Ollama** is the most common way to run open models locally. It downloads models, runs them as a local server on port 11434, and exposes an API that LangChain's `langchain-ollama` package wraps.

```bash
# Install Ollama from ollama.com, then download the models once:
ollama pull llama3.1:8b          # router and graders: small and fast
ollama pull gpt-oss:20b          # answers: larger, better writing (needs more memory)
ollama pull nomic-embed-text     # local embedding model
pip install langchain-ollama
```

Model names in Ollama are tags such as `llama3.1:8b`; the part after the colon picks a size or variant. These are reasonable choices in October 2026, but local models change monthly, so treat them as examples: any model that supports structured output works with the code below.

```python
# not-run: needs Ollama running locally with these models pulled
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import ChatOllama, OllamaEmbeddings

router_llm = ChatOllama(model="llama3.1:8b", temperature=0, num_ctx=8192, keep_alive="30m")
answer_llm = ChatOllama(model="gpt-oss:20b", temperature=0, num_ctx=8192)
embeddings = OllamaEmbeddings(model="nomic-embed-text")
help_centre = InMemoryVectorStore(embeddings)    # or a persistent local store such as Chroma (module 4)
```

Three settings deserve a word:

- **`temperature=0`** makes decisions repeatable. You want the same question routed the same way every time.
- **`num_ctx`** is the context window Ollama allocates. Its default is much smaller than hosted models offer, and a RAG prompt with several retrieved pages can silently overflow it, which cuts off the start of your prompt. Set it explicitly to cover your longest prompt.
- **`keep_alive`** keeps the model loaded in memory between requests. Loading a model can take seconds; a router that reloads on every question makes the whole system feel slow.

Ollama also accepts a JSON schema and constrains the model's output to match it. LangChain uses that automatically: for `ChatOllama`, `with_structured_output(Schema)` defaults to the `json_schema` method, which sends your Pydantic schema to Ollama. That one feature removes most "the small model wrote prose instead of JSON" failures, but, as you'll see, not all of them.

### 3. The setup

The same help centre and stand-in model as before. This time the stand-in will imitate a **small** model, mistakes included.

```python
import math, re
from typing import Callable, Literal
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.vectorstores import InMemoryVectorStore
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

HELP_CENTRE = [
    ("fees", "refunds.md §1", "Cancelling a confirmed ticket more than 48 hours before departure costs a flat "
     "fee of ₹60 per passenger. Between 48 and 12 hours before departure, 25% of the fare is deducted. "
     "Less than 12 hours before departure, 50% is deducted."),
    ("tatkal", "tatkal.md §2", "Tatkal tickets are not refunded when you cancel them yourself. If the railway "
     "cancels the train, Tatkal tickets are refunded in full."),
    ("train-cancelled", "refunds.md §3", "If the railway cancels a train, every ticket on it is refunded in full "
     "automatically, with no form to fill. The money goes back to the original payment method; payments.md "
     "lists how long each method takes."),
    ("payment-times", "payments.md §2", "Refund timelines by payment method: SaathiRail Wallet is instant, UPI "
     "takes 1 to 3 working days, and credit or debit cards take 5 to 7 working days."),
    ("luggage", "luggage.md §1", "Each passenger may carry one bag of up to 15 kg free. Extra luggage costs "
     "₹30 per kg, paid at the parcel counter."),
    ("pets", "pets.md §1", "Pets such as dogs and cats travel only in a fully booked first class cabin, with "
     "a vaccination certificate."),
]
help_centre = InMemoryVectorStore(KeywordEmbeddings(STEMS))
help_centre.add_documents([Document(text, metadata={"source": src}) for _, src, text in HELP_CENTRE],
                          ids=[doc_id for doc_id, _, _ in HELP_CENTRE])

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
```

### 4. How small models get decisions wrong

Here is the classifier schema again, now with a fourth label for live questions, since a fully local system has no web route:

```python
class QueryComplexity(BaseModel):
    """How much retrieval a question needs before it can be answered well."""
    level: Literal["no_retrieval", "single_step", "multi_step", "live"] = Field(
        description="no_retrieval: general knowledge; single_step: one help-centre page; "
                    "multi_step: several pages found one after another; live: needs today's real-time data")

LABELLED = [   # a small evaluation set: question -> the label a careful human gave it
    ("What does PNR stand for?", "no_retrieval"),
    ("Good morning!", "no_retrieval"),
    ("What is the fee to cancel 3 days before departure?", "single_step"),
    ("Can I take my dog on the train?", "single_step"),
    ("How many kg of luggage can I carry free?", "single_step"),
    ("Do I get a refund if I cancel my Tatkal ticket?", "single_step"),
    ("How long does the refund take when the railway cancels my train?", "multi_step"),
    ("Is the Vande Bharat to Varanasi running late today?", "live"),
]
```

The stand-in below behaves the way small local models commonly do. It gets most questions right, but sometimes returns a **near-miss label** ("multi-step" with a hyphen, which isn't one of the allowed values), sometimes writes **prose with JSON inside** instead of a clean structured reply, and sometimes is simply **wrong**. Constrained JSON decoding prevents the second kind on Ollama, but you'll meet all three with some model or other.

```python
def small_model_rules(messages):
    q = messages[-1].content.split("Question:")[-1].strip().lower()
    if "railway cancel" in q:
        return structured_reply("QueryComplexity", level="multi-step")              # near-miss label
    if "luggage" in q:
        return AIMessage('Sure! Here is my answer: {"level": "single_step"}')    # prose around JSON
    if "today" in q or "tatkal" in q:
        return structured_reply("QueryComplexity", level="no_retrieval")         # plainly wrong
    if any(w in q for w in ["fee", "cancel", "dog", "pet"]):
        return structured_reply("QueryComplexity", level="single_step")
    return structured_reply("QueryComplexity", level="no_retrieval")

small_model = StandInModel(respond=small_model_rules)
PROMPT = "Classify how much retrieval this SaathiRail question needs.\nQuestion: {question}"

naive = small_model.with_structured_output(QueryComplexity)
for question, expected in LABELLED:
    try:
        got = naive.invoke(PROMPT.format(question=question))
        got = got.level if got else None
    except Exception as err:
        got = f"ERROR ({type(err).__name__})"
    print(f"{'ok ' if got == expected else 'BAD'} {expected:13} got={got}")
```

Output:

```
ok  no_retrieval  got=no_retrieval
ok  no_retrieval  got=no_retrieval
ok  single_step   got=single_step
ok  single_step   got=single_step
BAD single_step   got=None
BAD single_step   got=no_retrieval
BAD multi_step    got=ERROR (ValidationError)
BAD live          got=no_retrieval
```

Out of eight questions, the naive classifier crashed the whole request once, returned nothing once, and silently misrouted twice. Worse, the two silent mistakes are of the dangerous kind from [What is Adaptive RAG?](what-is-adaptive-rag.md): a rule question (Tatkal refunds) and a live question routed to **no retrieval**, so the model would answer them from memory.

### 5. Layer 1: see the failure instead of crashing

`with_structured_output(..., include_raw=True)` never raises on bad output. It returns a dictionary with the raw message, the parsed object (or `None`) and the parsing error (or `None`), so your code decides what to do:

```python
inspecting = small_model.with_structured_output(QueryComplexity, include_raw=True)

result = inspecting.invoke(PROMPT.format(question="How long does the refund take when the railway cancels my train?"))
print("parsed:", result["parsed"])
print("error: ", type(result["parsing_error"]).__name__)
print("raw args:", result["raw"].tool_calls[0]["args"])

result = inspecting.invoke(PROMPT.format(question="How many kg of luggage can I carry free?"))
print("parsed:", result["parsed"], "| raw text:", result["raw"].content)
```

Output:

```
parsed: None
error:  ValidationError
raw args: {'level': 'multi-step'}
parsed: None | raw text: Sure! Here is my answer: {"level": "single_step"}
```

Now both failures are data you can work with: the first had a label that *almost* matched, the second had valid JSON buried in prose.

### 6. Layer 2: repair near-misses

Most small-model failures are recoverable with a few lines of deterministic code: normalise the label's spelling, or pull the JSON object out of the surrounding text. Repair is cheap and runs only when parsing failed.

```python
import json

VALID = {"no_retrieval", "single_step", "multi_step", "live"}

def normalise(label):
    label = str(label).strip().lower().replace("-", "_").replace(" ", "_")
    return label if label in VALID else None

def repair(raw_message):
    """Try to rescue a decision from a malformed reply. Returns a label or None."""
    if raw_message.tool_calls:                                   # structured, but with a bad value
        return normalise(raw_message.tool_calls[0]["args"].get("level", ""))
    match = re.search(r"\{.*\}", raw_message.content, re.S)     # JSON buried in prose
    if match:
        try:
            return normalise(json.loads(match.group(0)).get("level", ""))
        except json.JSONDecodeError:
            return None
    return None

for question in ["How long does the refund take when the railway cancels my train?",
                 "How many kg of luggage can I carry free?"]:
    print(repair(inspecting.invoke(PROMPT.format(question=question))["raw"]))
```

Output:

```
multi_step
single_step
```

Repairing is not the same as guessing. We only accept a repaired label if it normalises to one of the four valid values; anything else still counts as a failure and goes to the next layer.

### 7. Layer 3: a safe fallback, and a rule-based backstop

When neither parsing nor repair works, the router must still return *something*, and it should be the safe choice: **retrieve**. A useful extra trick is a tiny **keyword backstop** that overrides the model in the cases where its mistakes are dangerous. Live questions are a good example: phrases like "today", "right now" and "running late" are a strong, cheap signal that no amount of model confidence should overrule.

```python
LIVE_WORDS = ["today", "right now", "running late", "delayed", "live status"]
HELP_WORDS = ["cancel", "refund", "fee", "tatkal", "luggage", "bag", "pet", "dog", "upi", "wallet"]

def robust_classify(question, model=small_model):
    q = question.lower()
    if any(w in q for w in LIVE_WORDS):                          # backstop: never answer live questions from memory
        return "live", "keyword backstop"
    result = model.with_structured_output(QueryComplexity, include_raw=True).invoke(PROMPT.format(question=question))
    if result["parsed"] is not None:
        label, how = result["parsed"].level, "parsed"
    else:
        label, how = repair(result["raw"]), "repaired"
        if label is None:
            return "single_step", "fallback"                    # safe default: retrieve
    if label == "no_retrieval" and any(w in q for w in HELP_WORDS):
        return "single_step", "override: help-centre topic"     # backstop: rule questions always retrieve
    return label, how

correct = 0
for question, expected in LABELLED:
    label, how = robust_classify(question)
    correct += label == expected
    print(f"{'ok ' if label == expected else 'BAD'} {label:13} via {how}")
print(f"accuracy: {correct}/{len(LABELLED)}")
```

Output:

```
ok  no_retrieval  via parsed
ok  no_retrieval  via parsed
ok  single_step   via parsed
ok  single_step   via parsed
ok  single_step   via repaired
ok  single_step   via override: help-centre topic
ok  multi_step    via repaired
ok  live          via keyword backstop
accuracy: 8/8
```

The same weak model now routes every question correctly, and the label says *how* each decision was reached. In production, log that `how` field: if "repaired" and "override" climb over time, your model or your prompt needs attention.

The pattern generalises beyond routing. Every grader you build later in this course (document relevance, answer support) is a small structured decision, and every one deserves the same three layers when a small model makes it.

LangChain also has a built-in way to express "try this, and if it raises, try that": `with_fallbacks`. It's handy when the fallback is another model (say, a local 8B model first, a bigger local model second):

```python
from langchain_core.runnables import RunnableLambda

safe_default = RunnableLambda(lambda _: QueryComplexity(level="single_step"))
router_with_fallback = small_model.with_structured_output(QueryComplexity).with_fallbacks([safe_default])

print(router_with_fallback.invoke(PROMPT.format(question="How long does the refund take when the railway cancels my train?")))
```

Output:

```
level='single_step'
```

Note that `with_fallbacks` only reacts to **exceptions**. It didn't help with the luggage reply (no exception, just `None`) or the wrong labels (valid but wrong), which is why the explicit three-layer function above is the more complete answer.

### 8. The local graph

Here is the adaptive graph from [What is Adaptive RAG?](what-is-adaptive-rag.md) with the robust router, a `live` route that answers honestly, and the "how" recorded in state. The generator and planner are stand-ins with the same rules as before.

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

ANSWER_PROMPT = """Answer the question using only the context. Cite sources in square brackets.
If the context doesn't contain the answer, say what is missing.

Context:
{context}

Question: {question}"""

def answer_rules(messages):
    prompt = messages[-1].content
    if "Context:" not in prompt:
        return AIMessage("PNR stands for Passenger Name Record, the booking reference on every ticket."
                         if "pnr" in prompt.lower() else "Good morning! How can I help with your journey?")
    if "payments.md §2" in prompt and "refunds.md §3" in prompt:
        return AIMessage("It's automatic and goes back to how you paid: instant for SaathiRail Wallet, 1 to 3 "
                         "working days for UPI, 5 to 7 for cards [refunds.md §3][payments.md §2].")
    if "luggage.md §1" in prompt:
        return AIMessage("One bag of up to 15 kg is free; extra luggage is ₹30 per kg [luggage.md §1].")
    if "refunds.md §1" in prompt:
        return AIMessage("More than 48 hours ahead, it's a flat ₹60 per passenger [refunds.md §1].")
    return AIMessage("I couldn't find that in the help centre.")

class NextHop(BaseModel):
    done: bool
    follow_up_query: str = ""

def hop_rules(messages):
    prompt = messages[-1].content
    if "payments.md lists" in prompt and "payments.md §2" not in prompt:
        return structured_reply("NextHop", done=False, follow_up_query="refund timelines by payment method")
    return structured_reply("NextHop", done=True)

answer_llm = StandInModel(respond=answer_rules)
hop_planner = StandInModel(respond=hop_rules).with_structured_output(NextHop)

def format_docs(docs):
    return "\n".join(f"[{d.metadata['source']}] {d.page_content}" for d in docs)

class LocalState(TypedDict):
    question: str
    level: str
    how: str
    sources: list
    answer: str

def classify(state: LocalState):
    level, how = robust_classify(state["question"])
    return {"level": level, "how": how}

def no_retrieval(state: LocalState):
    return {"answer": answer_llm.invoke(state["question"]).content, "sources": []}

def retrieve_and_answer(state: LocalState, max_hops: int):
    docs, query = [], state["question"]
    for _ in range(max_hops):
        for doc in help_centre.similarity_search(query, k=2):
            if doc.page_content not in [d.page_content for d in docs]:
                docs.append(doc)
        if max_hops == 1:
            break
        step = hop_planner.invoke(f"Question: {state['question']}\n\nDocuments:\n{format_docs(docs)}")
        if step.done:
            break
        query = step.follow_up_query
    prompt = ANSWER_PROMPT.format(context=format_docs(docs), question=state["question"])
    return {"answer": answer_llm.invoke(prompt).content, "sources": [d.metadata["source"] for d in docs]}

def live(state: LocalState):
    return {"answer": "I can't check live train status from this offline assistant. "
                      "Please use the railway's official running-status service.", "sources": []}

builder = StateGraph(LocalState)
builder.add_node(classify)
builder.add_node(no_retrieval)
builder.add_node("single_step", lambda s: retrieve_and_answer(s, max_hops=1))
builder.add_node("multi_step", lambda s: retrieve_and_answer(s, max_hops=3))
builder.add_node(live)
builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", lambda s: s["level"],
                              ["no_retrieval", "single_step", "multi_step", "live"])
for node in ["no_retrieval", "single_step", "multi_step", "live"]:
    builder.add_edge(node, END)
local_rag = builder.compile()

for question in ["How many kg of luggage can I carry free?",
                 "How long does the refund take when the railway cancels my train?",
                 "Is the Vande Bharat to Varanasi running late today?"]:
    out = local_rag.invoke({"question": question})
    print(f"{out['level']} (via {out['how']}) sources={out['sources']}")
    print("  ", out["answer"])
```

Output:

```
single_step (via repaired) sources=['luggage.md §1', 'pets.md §1']
   One bag of up to 15 kg is free; extra luggage is ₹30 per kg [luggage.md §1].
multi_step (via repaired) sources=['tatkal.md §2', 'refunds.md §3', 'payments.md §2']
   It's automatic and goes back to how you paid: instant for SaathiRail Wallet, 1 to 3 working days for UPI, 5 to 7 for cards [refunds.md §3][payments.md §2].
live (via keyword backstop) sources=[]
   I can't check live train status from this offline assistant. Please use the railway's official running-status service.
```

Two small LangGraph details are new here. Nodes can be lambdas, which is a neat way to reuse one function with different settings (`max_hops=1` vs `3`). And because the routing function is a lambda without a `Literal` return type, we pass the list of possible destinations as the third argument to `add_conditional_edges`, so LangGraph still knows the graph's shape.

### 9. Measure before you trust

The single most important habit when going local: **build a labelled question set and measure the router before shipping**. Section 7 is the template: run every labelled question, count correct labels, and print how each label was reached. A few guidelines:

| Practice | Why |
|---|---|
| 50 to 200 real questions from logs, labelled by a person | Eight is enough for a lesson, not for a decision |
| Report accuracy **per label**, not just overall | A router that's 95% accurate overall but 60% on "live" is dangerous |
| Weight the dangerous errors | One rule question routed to "no_retrieval" is worse than five easy questions sent to retrieval |
| Re-run after every model or prompt change | Swapping `llama3.1:8b` for a newer model can change behaviour in either direction |
| Compare against a hosted model once | It tells you how much quality the local constraint is costing you |

You'll build a fuller evaluation in the lab, and the [Agent Evals, Observability and Reliability](../../agent-evals-observability-and-reliability/course.md) course covers evaluation in depth.

---

## Try It Yourself

1. **Per-label accuracy.** Using `robust_classify` and `LABELLED`, print the accuracy for each expected label separately.
2. **A new near-miss.** A model returns `{"level": "Single Step"}` as a tool call. Does `repair` rescue it? What about `{"level": "one search"}`?
3. **Tighten the backstop.** "Can I cancel today and still get ₹60 back?" contains "today" but is a rules question. What does `robust_classify` return, and how would you fix it?

<details>
<summary>Show answers</summary>

**1.**

```python
from collections import defaultdict

totals, hits = defaultdict(int), defaultdict(int)
for question, expected in LABELLED:
    totals[expected] += 1
    hits[expected] += robust_classify(question)[0] == expected
for label in sorted(totals):
    print(f"{label:13} {hits[label]}/{totals[label]}")
```

Output:

```
live          1/1
multi_step    1/1
no_retrieval  2/2
single_step   4/4
```

**2.**

```python
print(repair(AIMessage("", tool_calls=[{"name": "QueryComplexity", "args": {"level": "Single Step"}, "id": "x"}])))
print(repair(AIMessage("", tool_calls=[{"name": "QueryComplexity", "args": {"level": "one search"}, "id": "x"}])))
```

Output:

```
single_step
None
```

"Single Step" normalises to `single_step`. "one search" means the same thing to a human but isn't a spelling variant, so `repair` correctly refuses to guess and the fallback (`single_step`) takes over anyway.

**3.**

```python
print(robust_classify("Can I cancel today and still get ₹60 back?"))
```

Output:

```
('live', 'keyword backstop')
```

The backstop fires on "today" and calls it a live question, so the user gets "I can't check live status" instead of the fee rules. Fix it by making the backstop more specific: require a live word **and** no help-centre word, or use phrases like "running late" and "live status" rather than the single word "today". Keyword backstops should be narrow; their job is to catch a few dangerous cases with near certainty, not to classify everything.

</details>

---

## Real-World Examples

- **Banks and insurers** in regulated markets run local or private-cloud RAG over circulars and policy wordings, with small models for routing and grading and a larger self-hosted model for answers.
- **Hospitals** run local assistants over clinical protocols on hospital servers, often dropping web search entirely so no patient context can leak in a query.
- **Field engineers** use laptop-sized local RAG over equipment manuals in places with poor connectivity, such as plants, mines and ships.

---

## Common Misconceptions

### "Local models are too weak for agentic RAG"

They're weaker at free-form decisions, but routing and grading are narrow tasks. With a schema, repair and a safe fallback, a small model routes well; measure it rather than assume either way.

### "JSON mode or schemas make structured output perfect"

Constrained decoding guarantees the *shape* (valid JSON matching the schema). It can't guarantee the *content*: the label can still be wrong, which is why you still need evaluation and backstops.

### "Running locally means it's automatically private"

Only if every component is local. A local model with a hosted embedding API, a cloud vector database or a web-search route still sends data out. Check every arrow in the diagram.

### "A bigger num_ctx is free"

A larger context window needs more memory and makes every call slower. Size it to your longest real prompt plus a margin.

---

## Interview Relevance

*"How would you build RAG that never sends data outside the company?"* Local embedding model, local or self-hosted vector store, local LLMs served by something like Ollama, no web route (or an approved proxy), and the same graph as the hosted version. Mention sizing models to hardware and setting the context window explicitly.

*"Small models give you malformed structured output. What do you do?"* Constrain with a schema (JSON schema decoding), use `include_raw=True` to inspect failures instead of crashing, repair near-misses deterministically, fall back to the safe choice (retrieve), add narrow keyword backstops for dangerous errors, and log how each decision was reached.

*"How do you know the local router is good enough?"* A labelled set of real questions, per-label accuracy, extra weight on dangerous misroutes, and re-running it on every model or prompt change.

---

## Key Takeaways

- **Local adaptive RAG is the same graph** with local plug-ins: Ollama models, local embeddings, a local vector store.
- **Set `temperature=0`, `num_ctx` and `keep_alive`** deliberately; defaults are tuned for chat, not RAG.
- **Small models make three kinds of decision errors**: near-miss labels, JSON in prose, and wrong labels.
- **Three layers fix most of them**: schema plus `include_raw`, deterministic repair, and a safe fallback with narrow keyword backstops.
- **Measure the router on labelled questions**, per label, before and after every change.

---

**Up next:** [Lab: Adaptive RAG end to end](lab-adaptive-rag-end-to-end.md)
