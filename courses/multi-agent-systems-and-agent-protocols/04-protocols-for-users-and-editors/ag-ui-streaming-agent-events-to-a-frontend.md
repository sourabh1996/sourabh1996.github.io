---
title: "AG-UI: Streaming Agent Events to a Frontend"
course: "Multi-Agent Systems and Agent Protocols"
module: "4. Protocols for Users and Editors"
type: Article
level: Advanced
reading_time: 38 min
---

# AG-UI: Streaming Agent Events to a Frontend: The Complete Guide

> 📚 **Before you start**
>
> - [Tasks, Messages, Artifacts and Streaming](../03-the-a2a-protocol/tasks-messages-artifacts-and-streaming.md), for Server-Sent Events and how a client parses them.
> - [A2A vs MCP](../03-the-a2a-protocol/a2a-vs-mcp.md), for where agent-to-tool and agent-to-agent protocols sit.
> - [Streaming Real-Time Updates](../../langgraph-complete-guide/08-human-in-the-loop-and-debugging/streaming-real-time-updates.md) in the LangGraph course.

## Introduction

When you order food on a delivery app, you don't get one message at the end saying "delivered". You see "order confirmed", "restaurant is preparing", a rider's dot moving on a map, and an alert asking whether the rider may leave the parcel at the gate. The app is a live window onto work happening somewhere else, and it can ask you things along the way.

An agent inside a product needs the same window. A user who asks a travel app to "plan my Diwali trip home" should see the answer typing out, see which tools the agent is calling, watch an itinerary card fill in, and approve the booking before money moves. Every framework streams differently, though: LangGraph emits graph updates, other SDKs emit their own event objects, and each frontend team ends up writing a custom adapter.

The **Agent-User Interaction protocol (AG-UI)** standardises that window. It began at CopilotKit, out of its work with LangChain and CrewAI, and reached version **1.0** in September 2026 with a written behavioural specification and first-party SDKs in TypeScript, Python and .NET. In this lesson you'll learn its model (one request in, one ordered stream of typed events out), build an AG-UI endpoint and a frontend-style event reducer in Python, and handle the two human-in-the-loop patterns: frontend tools and interrupts.

> 💡 **Key Insight**
>
> AG-UI makes the frontend a **reducer over events**. The agent never sends "HTML" or "the final answer"; it sends small, typed facts (a message started, here's more text, a tool is being called, the state changed, the run finished). Any frontend that folds those facts into its UI works with any agent that emits them.

---

## Core Explanation

### 1. Where AG-UI sits

| Protocol | Connects | Typical message |
|---|---|---|
| MCP | An agent to its tools and data | "Call `search_trains` with these arguments" |
| A2A | An agent to another agent | "Here's a task; tell me when it's done" |
| **AG-UI** | An agent to the **user-facing app** | "The assistant's message continues with ' to Patna'" |

The three stack neatly: a user talks to an app; the app talks to its agent over AG-UI; the agent uses MCP for its tools and A2A for partner agents. AG-UI's own documentation describes it as complementary to the other two.

![AG-UI architecture. On the left, the frontend: the chat and app UI, an event reducer that applies each event to local UI state, frontend tools such as confirm_booking and show_map, and shared state kept as a snapshot plus JSON Patch. In the middle, the app POSTs a RunAgentInput (threadId, runId, messages, tools, context, state, resume) to the agent, and receives an SSE event stream: RUN_STARTED, STEP_STARTED and STEP_FINISHED, TEXT_MESSAGE_START, CONTENT and END, TOOL_CALL_START, ARGS and END, TOOL_CALL_RESULT, STATE_SNAPSHOT and STATE_DELTA, and RUN_FINISHED with an outcome. On the right, the agent backend in any framework, an AG-UI adapter that converts framework events to AG-UI events, and backend tools such as MCP servers, APIs and other agents over A2A](/img/diagrams/multi-agent-systems-and-agent-protocols/ag-ui-event-flow.svg)
*The app sends one request per run; everything the user sees comes back as events.*

### 2. A run: input and lifecycle

Each interaction is a **run** inside a **thread** (a conversation). The app POSTs a `RunAgentInput`:

```json
{
  "threadId": "thread-diwali-trip",
  "runId": "run-1",
  "protocolVersion": "1.0",
  "messages": [{"id": "u1", "role": "user", "content": "Find me a train from Delhi to Patna on 18 Oct"}],
  "tools": [{"name": "confirm_booking", "description": "Ask the user to confirm a booking in a dialog",
             "parameters": {"type": "object", "properties": {"train": {"type": "string"}, "fare_inr": {"type": "integer"}}}}],
  "context": [{"description": "User's home city", "value": "Patna"}],
  "state": {"itinerary": []}
}
```

`messages` carries the conversation so far, `tools` lists tools **the frontend** can execute, `context` adds facts the app knows, and `state` is shared state the agent and the app keep in sync. The response is `text/event-stream`, one JSON event per SSE `data:` line, with camelCase field names.

The lifecycle rules are strict: a stream **must** start with `RUN_STARTED` (or `RUN_ERROR` if the run couldn't start) and each run ends with `RUN_FINISHED` or `RUN_ERROR`. In 1.0, `RUN_FINISHED` carries an optional **outcome**: success (or absent), **interrupt** (the run stopped to ask for something) or **cancelled** (stopped on purpose). An HTTP 200 alone never means success; a failure after the stream opens arrives as `RUN_ERROR`. There's no stream resumption: if the connection drops, the app starts a new run.

### 3. The event families

| Family | Events | What the UI does |
|---|---|---|
| Lifecycle | `RUN_STARTED`, `RUN_FINISHED`, `RUN_ERROR`, `STEP_STARTED`, `STEP_FINISHED` | Show "thinking", progress steps, errors |
| Text messages | `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT` (`delta`), `TEXT_MESSAGE_END` | Type out the reply |
| Tool calls | `TOOL_CALL_START`, `TOOL_CALL_ARGS` (`delta`), `TOOL_CALL_END`, `TOOL_CALL_RESULT` | Show tool cards; run frontend tools |
| State | `STATE_SNAPSHOT`, `STATE_DELTA` (JSON Patch), `MESSAGES_SNAPSHOT` | Keep a shared object (form, plan, cart) in sync |
| Activity | `ACTIVITY_SNAPSHOT`, `ACTIVITY_DELTA` | Structured progress such as "searching 3 sources" |
| Reasoning | `REASONING_START`, `REASONING_MESSAGE_*`, `REASONING_END`, `REASONING_ENCRYPTED_VALUE` | Optional "thinking" display |
| Subagents | `SUBAGENT_STARTED`, `SUBAGENT_FINISHED`, `SUBAGENT_ERROR` | Attribute work to delegated agents |
| Escape hatches | `RAW`, `CUSTOM` | App-specific extras |

Text and tool calls follow a **start → deltas → end** pattern, matched by `messageId` or `toolCallId`; there are also compact `*_CHUNK` forms. A consumer must not act on tool arguments before `TOOL_CALL_END`, because until then the text is only a prefix. State changes use **snapshot–delta**: a snapshot replaces the whole state, and a delta is an RFC 6902 **JSON Patch**, a list of operations such as `{"op": "add", "path": "/itinerary/0", "value": {...}}`.

### 4. Build an AG-UI endpoint

Here is a train-planning agent that emits AG-UI events over SSE from FastAPI. Its "reasoning" is scripted so the lesson runs offline; the event sequence is what a real adapter would produce from a model.

```python
import itertools, json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

def to_camel(name):
    head, *rest = name.split("_")
    return head + "".join(w.title() for w in rest)

def event(type_, **fields):
    return {"type": type_, **{to_camel(k): v for k, v in fields.items()}}

TRAINS = [{"train": "12309", "name": "Rajdhani", "dep": "16:50", "fare_inr": 2645},
          {"train": "12393", "name": "Sampoorna Kranti", "dep": "17:20", "fare_inr": 1655}]

def trip_agent(run):
    t, r = run["threadId"], run["runId"]
    yield event("RUN_STARTED", thread_id=t, run_id=r, protocol_version="1.0")
    yield event("STATE_SNAPSHOT", snapshot=run.get("state") or {"itinerary": []})
    yield event("STEP_STARTED", step_name="search")
    yield event("TOOL_CALL_START", tool_call_id="call-1", tool_call_name="search_trains", parent_message_id="a1")
    for piece in ['{"from": "NDLS", ', '"to": "PNBE", ', '"date": "2026-10-18"}']:
        yield event("TOOL_CALL_ARGS", tool_call_id="call-1", delta=piece)
    yield event("TOOL_CALL_END", tool_call_id="call-1")
    yield event("TOOL_CALL_RESULT", message_id="tool-1", tool_call_id="call-1", content=json.dumps(TRAINS))
    yield event("STEP_FINISHED", step_name="search")
    yield event("TEXT_MESSAGE_START", message_id="a1", role="assistant")
    for piece in ["Two good options: ", "the Rajdhani at 16:50 (Rs 2,645) ", "and Sampoorna Kranti at 17:20 (Rs 1,655)."]:
        yield event("TEXT_MESSAGE_CONTENT", message_id="a1", delta=piece)
    yield event("TEXT_MESSAGE_END", message_id="a1")
    yield event("STATE_DELTA", delta=[{"op": "add", "path": "/itinerary/0",
                                       "value": {"leg": "Delhi to Patna", "options": [x["train"] for x in TRAINS]}}])
    yield event("RUN_FINISHED", thread_id=t, run_id=r, outcome={"type": "success"})

app = FastAPI()

@app.post("/agent")
async def agent_endpoint(request: Request):
    run = await request.json()
    sse = ("data: " + json.dumps(e) + "\n\n" for e in trip_agent(run))
    return StreamingResponse(sse, media_type="text/event-stream")

client = TestClient(app, base_url="https://travel-app.example.in")

def run_agent(run_input):
    with client.stream("POST", "/agent", json=run_input, headers={"Accept": "text/event-stream"}) as resp:
        return [json.loads(line[6:]) for line in resp.iter_lines() if line.startswith("data: ")]

run_input = {"threadId": "thread-diwali-trip", "runId": "run-1", "protocolVersion": "1.0", "state": {"itinerary": []},
             "messages": [{"id": "u1", "role": "user", "content": "Find me a train from Delhi to Patna on 18 Oct"}]}
events = run_agent(run_input)
for e in events:
    extra = e.get("delta") if isinstance(e.get("delta"), str) else e.get("stepName") or e.get("toolCallName") or ""
    print(f"{e['type']:22} {extra}")
```

Output:

```
RUN_STARTED            
STATE_SNAPSHOT         
STEP_STARTED           search
TOOL_CALL_START        search_trains
TOOL_CALL_ARGS         {"from": "NDLS", 
TOOL_CALL_ARGS         "to": "PNBE", 
TOOL_CALL_ARGS         "date": "2026-10-18"}
TOOL_CALL_END          
TOOL_CALL_RESULT       
STEP_FINISHED          search
TEXT_MESSAGE_START     
TEXT_MESSAGE_CONTENT   Two good options: 
TEXT_MESSAGE_CONTENT   the Rajdhani at 16:50 (Rs 2,645) 
TEXT_MESSAGE_CONTENT   and Sampoorna Kranti at 17:20 (Rs 1,655).
TEXT_MESSAGE_END       
STATE_DELTA            
RUN_FINISHED
```

Read the stream like the user would see it: a "search" step starts, a tool card appears and its arguments fill in, the result arrives, the step ends, the reply types out, and an itinerary entry appears in shared state.

### 5. The frontend side: a reducer

A frontend keeps a small store and applies each event to it. Here is that reducer in Python (a React app would do the same in TypeScript), including a minimal JSON Patch for `add`, `replace` and `remove`:

```python
import copy

def apply_patch(doc, ops):
    doc = copy.deepcopy(doc)
    for op in ops:
        *parents, last = [p for p in op["path"].split("/")[1:]]
        target = doc
        for p in parents:
            target = target[int(p)] if isinstance(target, list) else target[p]
        key = int(last) if isinstance(target, list) and last != "-" else last
        if op["op"] == "add" and isinstance(target, list):
            target.insert(len(target) if key == "-" else key, op["value"])
        elif op["op"] in ("add", "replace"):
            target[key] = op["value"]
        elif op["op"] == "remove":
            del target[key]
    return doc

def reduce(ui, e):
    t = e["type"]
    if t == "RUN_STARTED":
        ui["status"] = "running"
    elif t == "STEP_STARTED":
        ui["steps"].append(e["stepName"])
    elif t == "TEXT_MESSAGE_START":
        ui["messages"][e["messageId"]] = {"role": e.get("role", "assistant"), "text": ""}
    elif t == "TEXT_MESSAGE_CONTENT":
        ui["messages"][e["messageId"]]["text"] += e["delta"]
    elif t == "TOOL_CALL_START":
        ui["tool_calls"][e["toolCallId"]] = {"name": e["toolCallName"], "args": "", "done": False}
    elif t == "TOOL_CALL_ARGS":
        ui["tool_calls"][e["toolCallId"]]["args"] += e["delta"]
    elif t == "TOOL_CALL_END":
        call = ui["tool_calls"][e["toolCallId"]]
        call["done"], call["args"] = True, json.loads(call["args"])       # only parse once the call is closed
    elif t == "TOOL_CALL_RESULT":
        ui["tool_calls"][e["toolCallId"]]["result"] = e["content"]
    elif t == "STATE_SNAPSHOT":
        ui["state"] = e["snapshot"]
    elif t == "STATE_DELTA":
        ui["state"] = apply_patch(ui["state"], e["delta"])
    elif t == "RUN_FINISHED":
        ui["status"] = (e.get("outcome") or {"type": "success"})["type"]
    elif t == "RUN_ERROR":
        ui["status"] = "error: " + e["message"]
    return ui

ui = {"status": "idle", "steps": [], "messages": {}, "tool_calls": {}, "state": {}}
for e in events:
    ui = reduce(ui, e)
print("status :", ui["status"], "| steps:", ui["steps"])
print("tool   :", ui["tool_calls"]["call-1"]["name"], ui["tool_calls"]["call-1"]["args"])
print("reply  :", ui["messages"]["a1"]["text"])
print("state  :", ui["state"])
```

Output:

```
status : success | steps: ['search']
tool   : search_trains {'from': 'NDLS', 'to': 'PNBE', 'date': '2026-10-18'}
reply  : Two good options: the Rajdhani at 16:50 (Rs 2,645) and Sampoorna Kranti at 17:20 (Rs 1,655).
state  : {'itinerary': [{'leg': 'Delhi to Patna', 'options': ['12309', '12393']}]}
```

That store is everything a chat UI needs to render: a status badge, a step list, a tool card with parsed arguments, the assistant's message, and an itinerary panel driven by shared state. Because state arrives as patches, a long itinerary can be updated one field at a time instead of being resent.

### 6. Humans in the loop: frontend tools and interrupts

AG-UI has **no mid-run channel** from the app to the agent. Anything the user decides travels in the **next** run's input. There are two patterns:

**Frontend tools.** The app lists tools in `tools` (here `confirm_booking`). When the agent calls one, it streams the call but does **not** answer it; it ends the run with a success outcome that can list `pendingToolCallIds`. The app executes the tool (shows a dialog), then starts the next run with a `tool` message answering the call.

**Interrupts.** When the agent itself needs a decision, approval or credential, it ends the run with `"outcome": {"type": "interrupt", "interrupts": [...]}`. Each interrupt has an `id`, a `reason`, an optional human-readable `message` and an optional `responseSchema` the app can turn into a form. The next run carries a `resume` list answering **every** interrupt, with `status` `resolved` or `cancelled`.

```python
def booking_agent(run):
    t, r = run["threadId"], run["runId"]
    yield event("RUN_STARTED", thread_id=t, run_id=r, protocol_version="1.0")
    answers = {a["interruptId"]: a for a in run.get("resume", [])}
    if "approve-1" not in answers:
        yield event("RUN_FINISHED", thread_id=t, run_id=r, outcome={"type": "interrupt", "interrupts": [{
            "id": "approve-1", "reason": "payment_approval",
            "message": "Book 12393 Sampoorna Kranti, 3A, for Rs 1,655?",
            "responseSchema": {"type": "object", "properties": {"approved": {"type": "boolean"}}}}]})
        return
    if answers["approve-1"]["status"] == "resolved" and answers["approve-1"]["payload"].get("approved"):
        text = "Booked. PNR 2468013579."
    else:
        text = "Okay, I won't book it."
    yield event("TEXT_MESSAGE_START", message_id="a2", role="assistant")
    yield event("TEXT_MESSAGE_CONTENT", message_id="a2", delta=text)
    yield event("TEXT_MESSAGE_END", message_id="a2")
    yield event("RUN_FINISHED", thread_id=t, run_id=r, outcome={"type": "success"})

def last_outcome(evts):
    return evts[-1]["outcome"]

first = list(booking_agent({"threadId": "thread-diwali-trip", "runId": "run-2", "messages": []}))
outcome = last_outcome(first)
print("run-2 ->", outcome["type"], "|", outcome["interrupts"][0]["message"])

resume = [{"interruptId": "approve-1", "status": "resolved", "payload": {"approved": True}}]
second = list(booking_agent({"threadId": "thread-diwali-trip", "runId": "run-3", "messages": [], "resume": resume}))
print("run-3 ->", last_outcome(second)["type"], "|", [e["delta"] for e in second if e["type"] == "TEXT_MESSAGE_CONTENT"])
```

Output:

```
run-2 -> interrupt | Book 12393 Sampoorna Kranti, 3A, for Rs 1,655?
run-3 -> success | ['Booked. PNR 2468013579.']
```

The specification puts the duty to cover every interrupt on the **app**: it must not start a resuming run that leaves an interrupt unanswered, and an omitted entry never counts as "no". On the agent side, a missing answer must never be treated as permission to do the interrupted action.

### 7. The official SDKs and integrations

The Python package `ag-ui-protocol` (1.0.0, September 2026) provides typed Pydantic models for every event in `ag_ui.core` and an SSE encoder in `ag_ui.encoder`. The same endpoint looks like this:

```python
# not-run: needs the ag-ui-protocol package
from ag_ui.core import (EventType, RunAgentInput, RunFinishedEvent, RunStartedEvent,
                        TextMessageContentEvent, TextMessageEndEvent, TextMessageStartEvent, PROTOCOL_VERSION)
from ag_ui.encoder import EventEncoder
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/agent")
async def agent(run: RunAgentInput, request: Request):
    encoder = EventEncoder(accept=request.headers.get("accept"))
    async def stream():
        yield encoder.encode(RunStartedEvent(thread_id=run.thread_id, run_id=run.run_id,
                                             protocol_version=PROTOCOL_VERSION))
        yield encoder.encode(TextMessageStartEvent(message_id="a1", role="assistant"))
        yield encoder.encode(TextMessageContentEvent(message_id="a1", delta="Namaste! Where to?"))
        yield encoder.encode(TextMessageEndEvent(message_id="a1"))
        yield encoder.encode(RunFinishedEvent(thread_id=run.thread_id, run_id=run.run_id))
    return StreamingResponse(stream(), media_type=encoder.get_content_type())
```

Note that the SDK leaves `protocol_version` for you to set explicitly on `RUN_STARTED`. In practice you rarely emit events by hand: AG-UI integrations exist for LangGraph, CrewAI, Microsoft Agent Framework, Google ADK, Pydantic AI, Mastra, LlamaIndex, AG2 and others, converting each framework's native stream to AG-UI. On the frontend, CopilotKit's React components are the most common consumer, and the 1.0 specification also defines a binary HTTP + Protobuf binding alongside SSE.

### 8. Security notes

The AG-UI specification is explicit that **model output is untrusted input**: tool arguments, results and state cross a trust boundary. Apps must validate what they act on, must not render streamed content as executable markup, should get user consent before side-effectful frontend tools, and must never present an action as approved when it wasn't. Also remember that `state` and `messages` round-trip on every run, so neither side should put secrets in them.

---

## Try It Yourself

1. **Replace a field.** Send a `STATE_DELTA` that changes the first itinerary leg's options to just `["12393"]` and apply it with `apply_patch`.
2. **Decline the booking.** Resume `booking_agent` with `"status": "cancelled"` and no payload. What does the agent say?
3. **Reject a bad stream.** Write `check_stream(events)` that returns an error if the first event isn't `RUN_STARTED` or `RUN_ERROR`, or if any tool call's arguments arrive after its `TOOL_CALL_END`.

<details>
<summary>Show answers</summary>

**1.**

```python
patched = apply_patch(ui["state"], [{"op": "replace", "path": "/itinerary/0/options", "value": ["12393"]}])
print(patched)
```

Output:

```
{'itinerary': [{'leg': 'Delhi to Patna', 'options': ['12393']}]}
```

**2.**

```python
declined = list(booking_agent({"threadId": "thread-diwali-trip", "runId": "run-4", "messages": [],
                               "resume": [{"interruptId": "approve-1", "status": "cancelled"}]}))
print([e["delta"] for e in declined if e["type"] == "TEXT_MESSAGE_CONTENT"])
```

Output:

```
["Okay, I won't book it."]
```

**3.**

```python
def check_stream(evts):
    if not evts or evts[0]["type"] not in ("RUN_STARTED", "RUN_ERROR"):
        return "error: stream must open with RUN_STARTED or RUN_ERROR"
    closed = set()
    for e in evts:
        if e["type"] == "TOOL_CALL_END":
            closed.add(e["toolCallId"])
        if e["type"] == "TOOL_CALL_ARGS" and e["toolCallId"] in closed:
            return f"error: arguments after TOOL_CALL_END for {e['toolCallId']}"
    return "ok"

print(check_stream(events))
print(check_stream(events[1:]))
print(check_stream(events + [event("TOOL_CALL_ARGS", tool_call_id="call-1", delta="x")]))
```

Output:

```
ok
error: stream must open with RUN_STARTED or RUN_ERROR
error: arguments after TOOL_CALL_END for call-1
```

(Strictly, the specification lets a producer reopen a closed call with a new `TOOL_CALL_START` with the same ID; a fuller checker would allow arguments after such a reopening.)

</details>

---

## Real-World Examples

- **Copilot-style assistants inside SaaS products** use AG-UI (often through CopilotKit) so the agent can fill forms, update dashboards through shared state, and ask for approval through frontend tools.
- **Framework vendors** such as Microsoft (Agent Framework), Google (ADK) and AWS (Strands Agents) list first-party AG-UI integrations, so the same React frontend can sit on top of agents built with any of them.
- **Generative UI**: AG-UI carries UI specifications such as A2UI and MCP Apps between agent and app, the subject of the Generative UI lesson in this module.

---

## Common Misconceptions

### "AG-UI is a UI component library"

It's a protocol for the stream between agent and app. How the app renders events is up to the app (CopilotKit is one implementation).

### "The agent can wait mid-run for the user's click"

There's no mid-run channel. Frontend tool calls and interrupts end the run; the answer comes in the next run's input.

### "A 200 response means the run worked"

Failures after the stream opens arrive as `RUN_ERROR`. Only `RUN_FINISHED` reports how a run ended.

### "AG-UI and A2UI are the same thing"

AG-UI is the transport for agent–user interaction; A2UI is a format for describing UI. They work together, as you'll see two lessons from now.

---

## Interview Relevance

*"How would you stream an agent's work into a web app?"* Describe AG-UI's run model (POST `RunAgentInput`, SSE events), the start–delta–end pattern for text and tool calls, snapshot–delta state with JSON Patch, lifecycle rules (`RUN_STARTED` first, `RUN_FINISHED` with an outcome), and the frontend reducer.

*"How do you put a human approval step into an agent UI?"* Compare frontend tools (pending tool calls answered in the next run's messages) with interrupts (an interrupt outcome answered by a `resume` list), and mention consent, validation and never treating silence as approval.

---

## Key Takeaways

- **AG-UI connects agents to user-facing apps**, complementing MCP (tools) and A2A (agents).
- **One request in, one ordered event stream out**: `RunAgentInput` over POST, typed events over SSE, `RUN_STARTED` first and `RUN_FINISHED` or `RUN_ERROR` last.
- **The frontend is a reducer**: text and tool calls stream as start–delta–end; state syncs by snapshot and JSON Patch.
- **Humans answer between runs**: frontend tools leave calls pending; interrupts end with an interrupt outcome answered by `resume`.
- **Treat model output as untrusted**: validate before acting, never render it as code, ask before side effects.

---

**Up next:** [Agent Client Protocol: Agents inside Editors](agent-client-protocol-agents-inside-editors.md)
