---
title: "Streaming Real-Time Updates"
course: "LangGraph Complete Guide"
module: "8. Human-in-the-Loop and Debugging"
type: Article
level: Intermediate
reading_time: 32 min
---

# Streaming Real-Time Updates: The Complete Guide

> 📚 **Before you start**
>
> - [The LangGraph State System](../04-state-in-depth/the-langgraph-state-system.md) and [State Schemas and Data Flow](../04-state-in-depth/state-schemas-and-data-flow.md), from the State in Depth module.
> - [The LangGraph Execution Model](../02-getting-started/the-langgraph-execution-model.md), where you first used `stream_mode="updates"` and `"values"`.
> - [Building a Chatbot with LangGraph](../06-chatbots-and-persistence/building-a-chatbot-with-langgraph.md), where you streamed tokens with `stream_mode="messages"`.

## Introduction

When you order food on Swiggy or Zomato, you don't stare at a blank screen for 35 minutes and then see "Delivered". You see "Order confirmed", "Restaurant is preparing your food", "Rider assigned: Imran", a little scooter moving on a map. Nothing about the food arrives faster, but the wait feels completely different, and if something goes wrong ("restaurant cancelled") you know immediately and can act.

Agents need the same. A research agent that works for two minutes in silence feels broken. One that shows "Searching 3 sources... reading the RBI circular... drafting the answer" and then types its reply word by word feels responsive, and, more importantly for this course, it lets a **human watch and step in**. Streaming is the first half of human-in-the-loop: you can't sensibly approve or correct what you can't see.

LangGraph's `stream` method can emit seven kinds of events, called **stream modes**. This lesson covers every one of them, the newer `version="v2"` output format, how to combine modes, filter LLM tokens by node or tag, send your own progress events, stream from subgraphs, see interrupts in the stream, and stream asynchronously from a web server.

> 💡 **Key Insight**
>
> `invoke` and `stream` run the **same** graph in the **same** way. Streaming doesn't change what happens; it chooses **which internal events you get to see while it happens**: state after each step (`values`), each node's output (`updates`), LLM tokens (`messages`), your own events (`custom`), or the engine's bookkeeping (`checkpoints`, `tasks`, `debug`). Pick the modes your UI or log actually needs.

---

## Core Explanation

### 1. The workflow we'll watch

A small "match report" workflow: fetch the scorecard, have a model write a two-line report, then format it for WhatsApp. The fetch node takes a while, so it reports progress; the writer uses a scripted model that streams word by word, like a real one.

```python
import operator
from typing import Annotated, TypedDict
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph, START, END

class Report(TypedDict):
    match: str
    scorecard: dict
    report: str
    message: str
    log: Annotated[list, operator.add]

def fetch_scorecard(state: Report):
    write = get_stream_writer()
    for pct, what in [(30, "batting card"), (70, "bowling card"), (100, "result")]:
        write({"progress": pct, "loaded": what})        # a custom event, sent immediately
    return {"scorecard": {"IND": "287/6", "AUS": "251 all out", "result": "India won by 36 runs"},
            "log": ["fetched"]}

def make_writer_llm():
    return GenericFakeChatModel(messages=iter([
        AIMessage("India beat Australia by 36 runs. Gill's 92 set it up and Bumrah took 4 wickets.")]))

def write_report(state: Report):
    reply = writer_llm.invoke(f"Write a two-line report: {state['scorecard']}")
    return {"report": reply.content, "log": ["written"]}

def format_message(state: Report):
    return {"message": f"🏏 {state['match']}\n{state['report']}", "log": ["formatted"]}

b = StateGraph(Report)
b.add_sequence([fetch_scorecard, write_report, format_message])
b.add_edge(START, "fetch_scorecard")
reporter = b.compile()

writer_llm = make_writer_llm()
print(reporter.invoke({"match": "IND vs AUS, 2nd ODI", "log": []})["message"])
```

Output:

```
🏏 IND vs AUS, 2nd ODI
India beat Australia by 36 runs. Gill's 92 set it up and Bumrah took 4 wickets.
```

`get_stream_writer()` returns a function that sends anything you give it to the `custom` stream. When nobody is streaming `custom`, the events are simply dropped, so the node works the same under `invoke`.

### 2. `updates` and `values`: progress by step

You've used these two before. With a single mode, `stream` yields the raw payloads:

```python
writer_llm = make_writer_llm()
print("updates:")
for chunk in reporter.stream({"match": "IND vs AUS", "log": []}, stream_mode="updates"):
    print(" ", {node: sorted(update) for node, update in chunk.items()})

writer_llm = make_writer_llm()
print("values:")
for state in reporter.stream({"match": "IND vs AUS", "log": []}, stream_mode="values"):
    print(" ", state["log"])
```

Output:

```
updates:
  {'fetch_scorecard': ['log', 'scorecard']}
  {'write_report': ['log', 'report']}
  {'format_message': ['log', 'message']}
values:
  []
  ['fetched']
  ['fetched', 'written']
  ['fetched', 'written', 'formatted']
```

- **`updates`** yields `{node_name: what_it_returned}` after each node. Best for "what just happened" progress and logs.
- **`values`** yields the **full state** after each super-step, including the input first. Best when the UI renders the whole state (for example, a document being built).

### 3. The `v2` format: one shape for every mode

With one mode, the chunks above are easy to read. With several modes at once, the default format yields `(mode, payload)` tuples, and with subgraphs it adds a namespace too, so the shape keeps changing. Passing **`version="v2"`** (available since LangGraph 1.1) makes **every** chunk a dictionary with the same three keys:

```python
writer_llm = make_writer_llm()
for part in reporter.stream({"match": "IND vs AUS", "log": []},
                            stream_mode=["updates", "custom"], version="v2"):
    print(part["type"], "|", part["ns"], "|", part["data"] if part["type"] == "custom"
          else list(part["data"]))
```

Output:

```
custom | () | {'progress': 30, 'loaded': 'batting card'}
custom | () | {'progress': 70, 'loaded': 'bowling card'}
custom | () | {'progress': 100, 'loaded': 'result'}
updates | () | ['fetch_scorecard']
updates | () | ['write_report']
updates | () | ['format_message']
```

| Key | Meaning |
|---|---|
| `type` | Which mode produced it: `"values"`, `"updates"`, `"messages"`, `"custom"`, `"checkpoints"`, `"tasks"` or `"debug"` |
| `ns` | Namespace: `()` for the main graph, a tuple of path segments for events from a subgraph |
| `data` | The payload, same as that mode's v1 payload |

Branching on `part["type"]` is the clean way to handle mixed streams, and the rest of this course uses `version="v2"`. (`invoke` also accepts `version="v2"`, returning a `GraphOutput` object with `.value` and `.interrupts`; you'll meet it later in this module.)

The order matters too: the three `custom` progress events arrived **before** `fetch_scorecard`'s update, because they were sent while the node was still running. That's what makes custom events useful for long nodes.

### 4. `messages`: LLM tokens as they're generated

`stream_mode="messages"` emits each chunk of text a chat model produces, from **inside** any node, even though the node itself calls `invoke` and waits for the whole reply. LangGraph listens to the model's callbacks, so you don't need to change the node:

```python
writer_llm = make_writer_llm()
tokens = []
for part in reporter.stream({"match": "IND vs AUS", "log": []}, stream_mode="messages", version="v2"):
    chunk, meta = part["data"]
    tokens.append(chunk.content)
print(len(tokens), "chunks:", tokens[:6], "...")
print("from node:", meta["langgraph_node"], "| step:", meta["langgraph_step"])
```

Output:

```
31 chunks: ['India', ' ', 'beat', ' ', 'Australia', ' '] ...
from node: write_report | step: 2
```

Each item is a `(message_chunk, metadata)` pair. The metadata tells you **where** the tokens came from: `langgraph_node` (which node), `langgraph_step` (which super-step), plus tags and model details. In a chat UI you'd print `chunk.content` with `end=""` to get the typing effect.

### 5. Filtering tokens: by node, by tag, or not at all

Real graphs often call several models: a router, a summariser, a guardrail checker. Users should only see the main answer being typed. Three tools:

- **Filter by node**: keep chunks whose `meta["langgraph_node"]` is the answering node.
- **Filter by tag**: give a model tags with `.with_config(tags=[...])`; they appear in `meta["tags"]`.
- **Exclude entirely**: a model tagged **`"nostream"`** still runs, but its tokens never enter the `messages` stream.

```python
class Answer(TypedDict):
    question: str
    category: str
    answer: str

router_llm = GenericFakeChatModel(messages=iter([AIMessage("refund policy")])).with_config(tags=["nostream"])
answer_llm = GenericFakeChatModel(messages=iter([AIMessage("Refunds reach your UPI account in 3 to 5 days.")])
                                  ).with_config(tags=["final_answer"])

def classify(state: Answer):
    return {"category": router_llm.invoke(state["question"]).content}

def respond(state: Answer):
    return {"answer": answer_llm.invoke(state["question"]).content}

b = StateGraph(Answer)
b.add_sequence([classify, respond])
b.add_edge(START, "classify")
support = b.compile()

shown = []
for part in support.stream({"question": "When will I get my refund?"}, stream_mode="messages", version="v2"):
    chunk, meta = part["data"]
    if "final_answer" in meta.get("tags", []):
        shown.append(chunk.content)
print("".join(shown))
print("router tokens streamed?", any(t in "".join(shown) for t in ["refund policy"]))
```

Output:

```
Refunds reach your UPI account in 3 to 5 days.
router tokens streamed? False
```

The router ran (the graph needed its answer) but the user never saw "refund policy" typed out.

### 6. `custom`: your own progress events

You saw `get_stream_writer()` in section 1. Anything JSON-like works as an event: percentages, status text, partial results, even "show this chart". Two more ways to get the writer:

- **From the runtime**: a node with a `runtime: Runtime` parameter can call `runtime.stream_writer(...)`.
- **From inside a tool**: `get_stream_writer()` also works inside a LangChain tool run by `ToolNode`, so a slow tool can report progress.

```python
from langgraph.runtime import Runtime

class Upload(TypedDict):
    files: list
    done: int

def process(state: Upload, runtime: Runtime):
    for i, name in enumerate(state["files"], start=1):
        runtime.stream_writer(f"processed {name} ({i}/{len(state['files'])})")
    return {"done": len(state["files"])}

b = StateGraph(Upload)
b.add_node(process)
b.add_edge(START, "process")
uploader = b.compile()

for part in uploader.stream({"files": ["aadhaar.pdf", "pan.jpg", "salary-slip.pdf"]},
                            stream_mode=["custom", "values"], version="v2"):
    print(part["type"], "->", part["data"])
```

Output:

```
values -> {'files': ['aadhaar.pdf', 'pan.jpg', 'salary-slip.pdf']}
custom -> processed aadhaar.pdf (1/3)
custom -> processed pan.jpg (2/3)
custom -> processed salary-slip.pdf (3/3)
values -> {'files': ['aadhaar.pdf', 'pan.jpg', 'salary-slip.pdf'], 'done': 3}
```

One caveat from the docs: in **async** code on Python older than 3.11, `get_stream_writer()` can't find the run's context. There, declare a `writer: StreamWriter` parameter on the node (from `langgraph.types`) or use `runtime.stream_writer`.

### 7. `checkpoints`, `tasks` and `debug`: the engine's view

Three modes expose LangGraph's own bookkeeping. They need a checkpointer:

```python
from langgraph.checkpoint.memory import InMemorySaver

saved_reporter = StateGraph(Report)
saved_reporter.add_sequence([fetch_scorecard, write_report, format_message])
saved_reporter.add_edge(START, "fetch_scorecard")
saved_reporter = saved_reporter.compile(checkpointer=InMemorySaver())

writer_llm = make_writer_llm()
cfg = {"configurable": {"thread_id": "match-42"}}
for part in saved_reporter.stream({"match": "IND vs AUS", "log": []}, cfg,
                                  stream_mode=["checkpoints", "tasks"], version="v2"):
    d = part["data"]
    if part["type"] == "checkpoints":
        print(f"checkpoint  step={d['metadata']['step']:2}  next={d['next']}")
    elif "result" in d:
        print(f"task done   {d['name']:16} wrote {sorted(d['result'])}")
    else:
        print(f"task start  {d['name']}")
```

Output:

```
checkpoint  step=-1  next=['__start__']
checkpoint  step= 0  next=['fetch_scorecard']
task start  fetch_scorecard
task done   fetch_scorecard  wrote ['log', 'scorecard']
checkpoint  step= 1  next=['write_report']
task start  write_report
task done   write_report     wrote ['log', 'report']
checkpoint  step= 2  next=['format_message']
task start  format_message
task done   format_message   wrote ['log', 'message']
checkpoint  step= 3  next=[]
```

| Mode | Emits | Typical use |
|---|---|---|
| `checkpoints` | Each saved checkpoint, in the same shape as `get_state` (`values`, `next`, `config`, `metadata`, `tasks`...) | Live "history" panels, audit logs |
| `tasks` | A start event (`id`, `name`, `input`, `triggers`) and a finish event (`result`, `error`, `interrupts`) per node run | Timelines, per-node timing, error dashboards |
| `debug` | Both of the above, wrapped with `type`, `step` and a `timestamp` | Development tools and deep debugging |

These are what tools like LangGraph Studio use to draw a run as it happens.

### 8. Streaming from subgraphs

By default, a subgraph's internal steps are invisible: the parent sees one update when the subgraph node finishes. Pass `subgraphs=True` to see inside, and use `ns` to tell where each event came from:

```python
class Inner(TypedDict):
    text: str

def to_hindi(state: Inner):
    return {"text": "भारत ने ऑस्ट्रेलिया को 36 रन से हराया।"}

def add_hashtags(state: Inner):
    return {"text": state["text"] + " #INDvAUS"}

inner = StateGraph(Inner)
inner.add_sequence([to_hindi, add_hashtags])
inner.add_edge(START, "to_hindi")
translator = inner.compile()

class Outer(TypedDict):
    text: str

outer = StateGraph(Outer)
outer.add_node("translate", translator)
outer.add_edge(START, "translate")
parent = outer.compile()

for subgraphs in [False, True]:
    print(f"subgraphs={subgraphs}:")
    for part in parent.stream({"text": "India beat Australia by 36 runs."}, stream_mode="updates",
                              subgraphs=subgraphs, version="v2"):
        where = "parent" if not part["ns"] else part["ns"][0].split(":")[0]
        print(f"  [{where}] {list(part['data'])}")
```

Output:

```
subgraphs=False:
  [parent] ['translate']
subgraphs=True:
  [translate] ['to_hindi']
  [translate] ['add_hashtags']
  [parent] ['translate']
```

Each `ns` entry looks like `"translate:<task id>"`; the part before the colon is the subgraph node's name. The same flag works for `messages`: without `subgraphs=True`, tokens from a model inside a compiled subgraph don't reach the parent's message stream.

### 9. Interrupts appear in the stream

Later in this module you'll pause graphs with `interrupt()`. When that happens during `stream`, the `updates` mode emits a special `__interrupt__` entry, so a UI can show the question right away:

```python
from langgraph.types import interrupt

class Publish(TypedDict):
    message: str
    status: str

def approve(state: Publish):
    ok = interrupt({"question": "Post this to the fan group?", "preview": state["message"]})
    return {"status": "posted" if ok else "discarded"}

b = StateGraph(Publish)
b.add_node(approve)
b.add_edge(START, "approve")
publisher = b.compile(checkpointer=InMemorySaver())

for part in publisher.stream({"message": "India won by 36 runs!"}, {"configurable": {"thread_id": "p1"}},
                             stream_mode="updates", version="v2"):
    for key, value in part["data"].items():
        print(key, "->", value[0].value if key == "__interrupt__" else value)
```

Output:

```
__interrupt__ -> {'question': 'Post this to the fan group?', 'preview': 'India won by 36 runs!'}
```

You'll learn to answer that question in [Pausing with interrupt and Resuming with Command](pausing-with-interrupt-and-resuming-with-command.md).

### 10. Async streaming for web servers

Web servers usually stream with `astream`, the async twin of `stream`, so one process can serve many users at once. It takes the same arguments:

```python
import asyncio

async def collect():
    global writer_llm
    writer_llm = make_writer_llm()
    events = []
    async for part in reporter.astream({"match": "IND vs AUS", "log": []},
                                       stream_mode=["custom", "updates"], version="v2"):
        events.append(part["type"])
    return events

print(asyncio.run(collect()))
```

Output:

```
['custom', 'custom', 'custom', 'updates', 'updates', 'updates']
```

A typical server turns each part into a **Server-Sent Event** (SSE), a simple HTTP format browsers can read as a stream:

```python
# not-run: a long-running server; run with `uvicorn app:api`
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

api = FastAPI()

@api.get("/report")
async def report(match: str):
    async def events():
        async for part in reporter.astream({"match": match, "log": []},
                                           stream_mode=["custom", "messages", "updates"], version="v2"):
            if part["type"] == "messages":
                payload = {"token": part["data"][0].content}
            elif part["type"] == "custom":
                payload = {"progress": part["data"]}
            else:
                payload = {"step": list(part["data"])}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")
```

Deployed LangGraph apps (the Agent Server, covered later in [Deploying and Running LangGraph Apps](../10-deployment-and-observability/deploying-and-running-langgraph-apps.md)) expose the same stream modes over HTTP for you.

### 11. A newer API to know about: `stream_events(version="v3")`

LangGraph 1.2 added an event-streaming API, `graph.stream_events(input, config, version="v3")`, which returns a run object with separate iterators (for example `.values` and `.messages`) and properties such as `.interrupted`, `.interrupts` and `.output`. The LangChain docs recommend it for new applications, but in LangGraph 1.2.14 it still emits a warning that the v3 protocol is **experimental**. This course sticks to `stream(..., version="v2")`, which is stable and gives direct access to every mode; check the streaming docs if you want to adopt v3.

---

## Try It Yourself

1. **Progress bar.** Write a node that processes 5 PAN-verification requests and emits `{"done": i, "total": 5}` after each. Stream with `custom` and print a text bar like `[###--] 3/5`.
2. **Only the final answer.** Using `support`, collect the answer tokens by **node name** instead of tag. Recreate both scripted models first.
3. **Count steps.** Using `stream_mode="tasks"` with `version="v2"`, count how many node runs `saved_reporter` performs for one input, and list their names in order.

<details>
<summary>Show answers</summary>

**1.**

```python
class Verify(TypedDict):
    requests: list
    verified: int

def verify_all(state: Verify):
    write = get_stream_writer()
    total = len(state["requests"])
    for i, _ in enumerate(state["requests"], start=1):
        write({"done": i, "total": total})
    return {"verified": total}

b = StateGraph(Verify)
b.add_node(verify_all)
b.add_edge(START, "verify_all")
for part in b.compile().stream({"requests": ["A1", "B2", "C3", "D4", "E5"]}, stream_mode="custom", version="v2"):
    d = part["data"]
    print(f"[{'#' * d['done']}{'-' * (d['total'] - d['done'])}] {d['done']}/{d['total']}")
```

Output:

```
[#----] 1/5
[##---] 2/5
[###--] 3/5
[####-] 4/5
[#####] 5/5
```

**2.**

```python
router_llm = GenericFakeChatModel(messages=iter([AIMessage("refund policy")]))
answer_llm = GenericFakeChatModel(messages=iter([AIMessage("Refunds reach your UPI account in 3 to 5 days.")]))
text = "".join(part["data"][0].content
               for part in support.stream({"question": "Refund?"}, stream_mode="messages", version="v2")
               if part["data"][1]["langgraph_node"] == "respond")
print(text)
```

Output:

```
Refunds reach your UPI account in 3 to 5 days.
```

This time the router wasn't tagged `nostream`, so its tokens were in the stream too; the node filter dropped them.

**3.**

```python
writer_llm = make_writer_llm()
starts = [part["data"]["name"]
          for part in saved_reporter.stream({"match": "IND vs AUS", "log": []},
                                            {"configurable": {"thread_id": "match-43"}},
                                            stream_mode="tasks", version="v2")
          if "result" not in part["data"]]
print(len(starts), starts)
```

Output:

```
3 ['fetch_scorecard', 'write_report', 'format_message']
```

</details>

---

## Real-World Examples

- **Chat assistants** stream `messages` filtered to the answering node for the typing effect, and `updates` to show "Searching...", "Reading 3 documents..." status lines.
- **Document-processing tools** (loan applications, KYC uploads) stream `custom` progress events for each page or file.
- **Agent dashboards and Studio** stream `checkpoints` and `tasks` to draw a live timeline that a reviewer can click into.
- **Approval workflows** watch the stream for `__interrupt__` to notify a reviewer the moment an action needs sign-off.

---

## Common Misconceptions

### "Streaming makes the graph faster"

Total time is the same. Streaming shows progress earlier, which changes how responsive the app feels and lets people react sooner.

### "To stream tokens I must call `llm.stream()` in my node"

`stream_mode="messages"` captures tokens from `invoke` calls through callbacks. Keep your nodes simple.

### "`values` and `updates` are interchangeable"

`values` sends the whole state each step (more data, easy to render); `updates` sends only what each node returned (less data, tells you who did what). `values` also exposes private state keys.

### "Subgraph steps stream automatically"

Only with `subgraphs=True`. Use `ns` to tell parent and subgraph events apart.

---

## Interview Relevance

*"What streaming options does LangGraph offer?"* Seven modes: `values` (full state per step), `updates` (per-node outputs), `messages` (LLM tokens with node and tag metadata), `custom` (your events via `get_stream_writer` or `runtime.stream_writer`), `checkpoints`, `tasks` and `debug`. Combine modes with a list, use `version="v2"` for a uniform `{type, ns, data}` shape, `subgraphs=True` for nested graphs, and `astream` in async servers (often over SSE).

*"How do you stream only the final answer when several models run?"* Filter `messages` by `langgraph_node` or by tags, or tag helper models `nostream`.

---

## Key Takeaways

- **`stream` runs the same graph as `invoke`**; modes choose which events you see.
- **`updates`** for per-node progress, **`values`** for full state, **`messages`** for tokens, **`custom`** for your own events.
- **`checkpoints`**, **`tasks`** and **`debug`** expose the engine's bookkeeping and need a checkpointer.
- Use **`version="v2"`** for one `{type, ns, data}` shape, **`subgraphs=True`** for nested graphs, and filter tokens by **node** or **tag** (or `nostream`).
- Interrupts show up as **`__interrupt__`** in the update stream, the hook for human-in-the-loop UIs.

---

**Up next:** [Breakpoints](breakpoints.md)
