---
title: "A2A vs MCP"
course: "Multi-Agent Systems and Agent Protocols"
module: "3. The A2A Protocol"
type: Article
level: Advanced
reading_time: 30 min
---

# A2A vs MCP: The Complete Guide

> 📚 **Before you start**
>
> - [What is MCP?](../../model-context-protocol-mcp/course.md#m2) and [MCP Primitives: Tools, Resources and Prompts](../../model-context-protocol-mcp/course.md#m2) in the MCP course.
> - [What Changed in the 2026 MCP Specification](../../model-context-protocol-mcp/course.md#m6), for the stateless design and the tasks extension mentioned below.
> - [Tasks, Messages, Artifacts and Streaming](tasks-messages-artifacts-and-streaming.md), for A2A's task lifecycle.

## Introduction

A wedding caterer in Jaipur has a kitchen full of tools: tandoors, mixers, a cold store, a billing app. The head chef uses them directly; they do exactly what they're told. But for the sweets, the caterer calls a halwai down the road, and for the flowers, a decorator. Nobody tells the halwai which kadhai to use. You tell him "500 pieces of ghevar by Saturday, less sugar", and he decides how. He may call back with a question, and he delivers when it's ready.

Agents have the same two kinds of relationship. Some things they **use** (a database, a search API, a calculator). Other things they **delegate to**: another agent with its own judgement, its own tools and its own owner. The **Model Context Protocol (MCP)** standardises the first relationship; **A2A** standardises the second.

People often ask "should I use A2A or MCP?" as if they compete. They don't, and by the end of this lesson you'll be able to explain the difference precisely, decide which one a given integration needs, see how a production system uses both, and spot the places where they're starting to overlap.

> 💡 **Key Insight**
>
> Ask one question: **am I calling a capability, or delegating a goal?** If you know the inputs, want a predictable result and control the thing you call, it's a tool: use MCP. If the other side decides how to do the work, may take a long time, may ask questions back and belongs to someone else, it's an agent: use A2A.

---

## Core Explanation

### 1. Two directions: down and across

The A2A project describes MCP as **vertical** and A2A as **horizontal**. MCP goes *down* from an agent to the tools, data and prompts it controls; every MCP server you connect gives that one agent more abilities. A2A goes *across* to peer agents, often owned by another team or company.

![A trip planner agent in the middle, used by a traveller through the app. To the right, the planner calls its own Maps MCP server. Across, it talks A2A to a rail agent run by the rail company and a hotel agent run by a hotel chain. Below each of those, the agent calls its own tools over MCP: seat database and fare API for rail, rooms database and payments for the hotel. A rule-of-thumb box says A2A goes across to delegate a goal to an agent you don't control, and MCP goes down to call a tool or read data your agent controls](/img/diagrams/multi-agent-systems-and-agent-protocols/a2a-and-mcp-together.svg)
*Each agent uses MCP for its own tools; agents use A2A to work with each other.*

Notice that the rail agent's tools are invisible to the trip planner. That's A2A's opacity at work: the planner asks for seats; how the rail agent finds them (and which MCP servers it uses) is its own business.

### 2. Side by side

| Question | MCP (2026-07-28 specification) | A2A (v1.0) |
|---|---|---|
| What's on the other side? | Tools, resources and prompts the host app chose to connect | An independent agent with its own goals, tools and owner |
| How do you find out what it offers? | `tools/list`, `resources/list`, `prompts/list`; `server/discover` for versions and capabilities | The Agent Card, usually at `/.well-known/agent-card.json` |
| Unit of work | A tool call with JSON arguments matching an `inputSchema` | A message made of parts, which creates a task |
| Results | `content` blocks and optional `structuredContent` | Artifacts made of parts |
| State | Stateless at the protocol level (since 2026-07-28) | Tasks with a lifecycle, grouped by `contextId` |
| Long-running work | The official tasks extension (`io.modelcontextprotocol/tasks`), polled with `tasks/get` | Built in: task states, streaming, `SubscribeToTask`, push notifications |
| Asking back for input | Multi round-trip requests: an `input_required` result, then the client retries with answers | `TASK_STATE_INPUT_REQUIRED`, answered with a message on the same task |
| Transport | JSON-RPC 2.0 over stdio or Streamable HTTP | JSON-RPC, gRPC or HTTP+JSON, over HTTPS |
| Authentication | OAuth 2.1-based authorisation for HTTP servers | Schemes declared in the card: OAuth 2.0, OpenID Connect, API key, HTTP auth, mTLS |
| Who governs it | Created by Anthropic; now under the Linux Foundation's Agentic AI Foundation | Created by Google; a Linux Foundation project since June 2025 |

Both use JSON-RPC 2.0 and both have adopted ideas from each other's world (MCP gained tasks and input-required results; A2A uses structured `data` parts that look a lot like tool outputs). The difference is less about wire format and more about **who decides**.

### 3. The same capability, two shapes

Suppose the rail company wants to offer seat availability. As an **MCP tool**, it is a function with a schema. The calling model fills in the arguments:

```json
{
  "name": "check_availability",
  "title": "Check seat availability",
  "description": "Seat availability and fare for one train, date and class.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "train": {"type": "string", "pattern": "^[0-9]{5}$"},
      "date": {"type": "string", "format": "date"},
      "travel_class": {"type": "string", "enum": ["1A", "2A", "3A", "SL"]}
    },
    "required": ["train", "date", "travel_class"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {"available": {"type": "integer"}, "fare_inr": {"type": "integer"}},
    "required": ["available", "fare_inr"]
  }
}
```

As an **A2A skill**, it is a described ability. The caller sends a request in words or data, and the agent decides what to do:

```json
{
  "id": "plan-rail-journey",
  "name": "Plan a rail journey",
  "description": "Finds trains, classes and dates that fit a traveller's constraints, holds seats, and explains trade-offs. May ask follow-up questions.",
  "tags": ["rail", "planning", "booking"],
  "examples": ["Get two of us from Mumbai to Delhi before 10 am on 14 Nov, under Rs 8,000 total, lower berths if possible"]
}
```

The tool answers one precise question. The skill accepts a fuzzy goal ("before 10 am, under Rs 8,000, lower berths if possible"), and behind it the agent might call `check_availability` a dozen times over MCP, compare trains, ask whether a 2A upgrade is acceptable, and come back with a held booking. **That's the dividing line.** If the rail company only exposes `check_availability`, MCP fits perfectly. If it wants partners to hand over a whole journey-planning job, that's an agent, and A2A fits.

### 4. A decision helper

The choice comes down to a handful of properties of the thing you're connecting to. Here they are as code:

```python
def choose_protocol(name, *, you_control_it, fixed_inputs, multi_turn, long_running, own_reasoning):
    agent_signals = [not you_control_it, not fixed_inputs, multi_turn, long_running, own_reasoning]
    labels = ["owned by someone else", "open-ended request", "asks questions back",
              "runs for a long time", "decides how to do the work"]
    reasons = [l for l, s in zip(labels, agent_signals) if s]
    choice = "A2A" if own_reasoning or sum(agent_signals) >= 3 else "MCP"
    return f"{name:30} -> {choice:3}  ({', '.join(reasons) or 'a plain tool'})"

cases = [
    ("GST calculator",              dict(you_control_it=True,  fixed_inputs=True,  multi_turn=False, long_running=False, own_reasoning=False)),
    ("Company SQL database",        dict(you_control_it=True,  fixed_inputs=True,  multi_turn=False, long_running=False, own_reasoning=False)),
    ("Partner's seat-lookup API",   dict(you_control_it=False, fixed_inputs=True,  multi_turn=False, long_running=False, own_reasoning=False)),
    ("Bank's KYC agent",            dict(you_control_it=False, fixed_inputs=False, multi_turn=True,  long_running=True,  own_reasoning=True)),
    ("Another team's research agent", dict(you_control_it=False, fixed_inputs=False, multi_turn=False, long_running=True, own_reasoning=True)),
    ("Overnight data export job",   dict(you_control_it=True,  fixed_inputs=True,  multi_turn=False, long_running=True,  own_reasoning=False)),
]
for name, props in cases:
    print(choose_protocol(name, **props))
```

Output:

```
GST calculator                 -> MCP  (a plain tool)
Company SQL database           -> MCP  (a plain tool)
Partner's seat-lookup API      -> MCP  (owned by someone else)
Bank's KYC agent               -> A2A  (owned by someone else, open-ended request, asks questions back, runs for a long time, decides how to do the work)
Another team's research agent  -> A2A  (owned by someone else, open-ended request, runs for a long time, decides how to do the work)
Overnight data export job      -> MCP  (runs for a long time)
```

Two cases deserve a comment. The partner's seat-lookup API belongs to someone else but is still a plain tool, so MCP (with proper auth) is right; ownership alone doesn't make something an agent. And the overnight export runs for hours but has no judgement of its own, so MCP's tasks extension covers it; you don't need an agent protocol just because something is slow.

### 5. Using both: an agent that is an A2A server and an MCP client

In a real system, one agent usually speaks both protocols. Below, the rail agent exposes one A2A skill and internally uses two MCP-style tools. The trip planner calls the rail agent over A2A. To keep the lesson self-contained, the "MCP tools" are local functions with MCP-shaped definitions; the MCP course shows real servers.

```python
import json
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

TRACE = []

# The rail agent's private MCP tools (in production, separate MCP servers it connects to).
RAIL_TOOLS = {
    "find_trains": lambda a: [{"train": "12951", "dep": "17:00"}, {"train": "12953", "dep": "17:40"}],
    "check_availability": lambda a: {"12951": {"available": 0, "fare_inr": 3215},
                                     "12953": {"available": 18, "fare_inr": 2890}}[a["train"]],
}

def call_tool(name, args):
    TRACE.append(f"  rail agent  --MCP tools/call--> {name}({json.dumps(args)})")
    return RAIL_TOOLS[name](args)

def plan_journey(request_text):
    """The rail agent's own reasoning: search, check each option, pick the first with seats."""
    for option in call_tool("find_trains", {"from": "MMCT", "to": "NDLS", "date": "2026-11-14"}):
        seats = call_tool("check_availability", {"train": option["train"], "date": "2026-11-14", "travel_class": "3A"})
        if seats["available"] > 0:
            return {"train": option["train"], "dep": option["dep"], **seats}
    return None

rail = FastAPI()

@rail.post("/a2a")
async def rail_a2a(request: Request):
    body = await request.json()
    text = body["params"]["message"]["parts"][0]["text"]
    TRACE.append(f"  rail agent  <--A2A SendMessage-- \"{text}\"")
    best = plan_journey(text)
    task = {"id": "task-0001", "contextId": "ctx-0001", "status": {"state": "TASK_STATE_COMPLETED"},
            "artifacts": [{"artifactId": "plan", "parts": [{"data": best, "mediaType": "application/json"}]}]}
    return {"jsonrpc": "2.0", "id": body["id"], "result": {"task": task}}

rail_client = TestClient(rail, base_url="https://rail-agent.example.in")

def ask_rail_agent(goal):
    TRACE.append("trip planner --A2A SendMessage--> rail agent")
    body = {"jsonrpc": "2.0", "id": 1, "method": "SendMessage",
            "params": {"message": {"messageId": "m-1", "role": "ROLE_USER", "parts": [{"text": goal}]}}}
    task = rail_client.post("/a2a", json=body, headers={"A2A-Version": "1.0"}).json()["result"]["task"]
    TRACE.append(f"trip planner <--task {task['status']['state']}-- rail agent")
    return task["artifacts"][0]["parts"][0]["data"]

plan = ask_rail_agent("Mumbai to Delhi on 14 Nov in 3A, evening departure")
print("\n".join(TRACE))
print("\nPlanner received:", plan)
```

Output:

```
trip planner --A2A SendMessage--> rail agent
  rail agent  <--A2A SendMessage-- "Mumbai to Delhi on 14 Nov in 3A, evening departure"
  rail agent  --MCP tools/call--> find_trains({"from": "MMCT", "to": "NDLS", "date": "2026-11-14"})
  rail agent  --MCP tools/call--> check_availability({"train": "12951", "date": "2026-11-14", "travel_class": "3A"})
  rail agent  --MCP tools/call--> check_availability({"train": "12953", "date": "2026-11-14", "travel_class": "3A"})
trip planner <--task TASK_STATE_COMPLETED-- rail agent

Planner received: {'train': '12953', 'dep': '17:40', 'available': 18, 'fare_inr': 2890}
```

The planner made **one** A2A call and received a decision. Inside the rail agent, three MCP tool calls happened that the planner never saw: the first train was full, so the rail agent moved on by itself. If the planner had connected to the rail company's tools directly over MCP, its own model would have had to run that search loop, and the rail company would have had to expose its internal tools to an outside party.

### 6. Bridging: an A2A agent as a tool

Many agent frameworks let a model call a remote A2A agent **as if it were a tool**: the framework generates a tool from the Agent Card's skills and, when the model calls it, sends an A2A message. It's convenient, and you built the core of it in section 5 (`ask_rail_agent`). The A2A project's own guide notes the other direction too: a remote agent can expose well-defined, stateless skills as MCP-compatible tools.

Be careful about what the bridge hides. A tool call is one request and one result, while an A2A task can pause for input, stream progress or run for hours. A good bridge turns these into something the calling model can act on rather than losing them:

```python
def a2a_task_to_tool_result(task):
    state = task["status"]["state"]
    if state == "TASK_STATE_COMPLETED":
        return {"isError": False, "content": task["artifacts"]}
    if state == "TASK_STATE_INPUT_REQUIRED":
        question = task["status"]["message"]["parts"][0]["text"]
        return {"isError": False, "content": f"The remote agent needs more information: {question} "
                f"Ask the user, then call again with task_id={task['id']}."}
    if state in ("TASK_STATE_SUBMITTED", "TASK_STATE_WORKING"):
        return {"isError": False, "content": f"Still running. Check back with task_id={task['id']}."}
    return {"isError": True, "content": f"Remote task ended in {state}."}

paused = {"id": "task-0007", "status": {"state": "TASK_STATE_INPUT_REQUIRED", "message": {
          "role": "ROLE_AGENT", "parts": [{"text": "Is a 2A upgrade at Rs 1,265 extra acceptable?"}]}}}
for t in [paused, {"id": "task-0008", "status": {"state": "TASK_STATE_REJECTED"}}]:
    print(a2a_task_to_tool_result(t))
```

Output:

```
{'isError': False, 'content': 'The remote agent needs more information: Is a 2A upgrade at Rs 1,265 extra acceptable? Ask the user, then call again with task_id=task-0007.'}
{'isError': True, 'content': 'Remote task ended in TASK_STATE_REJECTED.'}
```

A bridge that simply waited or returned "error" in these cases would throw away the remote agent's question. Wrapping `REJECTED` as an error (`isError: True`) lets the calling model see the failure and try something else, the same way MCP reports tool execution errors.

### 7. Where they overlap, and how to choose anyway

The two protocols have been moving toward each other. MCP's tasks extension and multi round-trip requests give tools a way to be slow and to ask questions, and some MCP servers wrap an LLM and behave more like agents than functions. A2A's `data` parts and skill examples make agents easier to call like tools.

In practice, teams settle on a few rules:

| Situation | Use |
|---|---|
| Your agent needs data or an action from a system you control | MCP |
| A partner offers a well-defined API and you want your own model to drive it | MCP, with OAuth |
| A partner or another team offers a capability that needs judgement, multi-turn dialogue or long-running work | A2A |
| You're splitting your own agent into subagents inside one codebase | Neither: use your framework's subagent support (Module 2) |
| You want your in-house agents callable by other teams across the company | A2A, with cards in an internal registry |

That fourth row matters: protocols are for crossing boundaries. Inside one process, a LangGraph subgraph or an SDK subagent is simpler, faster and easier to debug than any network protocol.

---

## Try It Yourself

1. **Classify more cases.** Run `choose_protocol` for a weather API and for a travel insurer's claims agent that needs documents and may take days. Do the answers match your intuition?
2. **Full trains.** Change `RAIL_TOOLS` so both trains have 0 seats and rerun the planner. What does the planner receive, and what should a better rail agent return instead?
3. **Bridge an auth-required task.** Add a branch to `a2a_task_to_tool_result` for `TASK_STATE_AUTH_REQUIRED`. What should the message tell the calling model to do?

<details>
<summary>Show answers</summary>

**1.**

```python
print(choose_protocol("Weather API", you_control_it=False, fixed_inputs=True, multi_turn=False,
                      long_running=False, own_reasoning=False))
print(choose_protocol("Insurer's claims agent", you_control_it=False, fixed_inputs=False, multi_turn=True,
                      long_running=True, own_reasoning=True))
```

Output:

```
Weather API                    -> MCP  (owned by someone else)
Insurer's claims agent         -> A2A  (owned by someone else, open-ended request, asks questions back, runs for a long time, decides how to do the work)
```

**2.**

```python
RAIL_TOOLS["check_availability"] = lambda a: {"available": 0, "fare_inr": 3215}
TRACE.clear()
print(ask_rail_agent("Mumbai to Delhi on 14 Nov in 3A"))
```

Output:

```
None
```

The planner gets `None` inside a "completed" task, which hides what happened. A better rail agent would finish with `TASK_STATE_INPUT_REQUIRED` and a question ("No 3A seats. Try 2A at Rs 4,480 or the next day?"), or complete with an artifact that says clearly that nothing was available and lists alternatives.

**3.**

```python
def a2a_task_to_tool_result_v2(task):
    if task["status"]["state"] == "TASK_STATE_AUTH_REQUIRED":
        return {"isError": False, "content": "The remote agent needs the user's authorisation. Ask the user to "
                f"approve it in the app, then call again with task_id={task['id']}."}
    return a2a_task_to_tool_result(task)

print(a2a_task_to_tool_result_v2({"id": "task-0009", "status": {"state": "TASK_STATE_AUTH_REQUIRED"}}))
```

Output:

```
{'isError': False, 'content': "The remote agent needs the user's authorisation. Ask the user to approve it in the app, then call again with task_id=task-0009."}
```

The model must never be asked to type credentials into the conversation. It should route the user to an out-of-band approval and then resume the same task.

</details>

---

## Real-World Examples

- **Google's Agent Development Kit** lets an agent call remote A2A agents as sub-agents and also use MCP tools, the "A2A across, MCP down" pattern in one framework.
- **Enterprise platforms** commonly expose internal systems (CRM, ticketing, HR data) through MCP servers while offering their own higher-level agents to partners over A2A.
- **Microsoft Agent Framework, LangGraph, CrewAI and AG2** all support both MCP tools and A2A agents, so the choice is per integration, not per framework.

---

## Common Misconceptions

### "A2A and MCP are competitors"

They solve different problems. The A2A specification itself describes them as complementary, and most serious systems use both.

### "If it's slow, it needs A2A"

Slowness alone is a tool problem; MCP's tasks extension handles it. Use A2A when the other side exercises judgement and owns its own process.

### "An A2A agent wrapped as a tool is the same as a tool"

The wrapper hides the task lifecycle. Unless it surfaces input-required, auth-required and still-running states, you lose the reasons A2A exists.

### "Protocols are the best way to split my own agent"

Inside one codebase, framework-level subagents are simpler. Use protocols at ownership or deployment boundaries.

---

## Interview Relevance

*"What's the difference between MCP and A2A, and when would you use each?"* A strong answer gives the vertical-versus-horizontal picture, the "capability versus goal" test, the concrete differences (discovery through tool lists versus Agent Cards, stateless tool calls versus stateful tasks, who controls the other side), and an architecture where one agent is both an A2A server and an MCP client.

*"Could you just expose your agent as an MCP tool?"* Yes, for well-defined, stateless skills. Explain what you lose (multi-turn, streaming, long-running tracking, opacity guarantees) and how a bridge should map task states to tool results.

---

## Key Takeaways

- **MCP goes down, A2A goes across**: tools and data an agent controls versus peer agents it delegates to.
- **The test is "capability or goal"**: precise inputs and predictable output mean a tool; open-ended work with its own judgement means an agent.
- **Most real agents speak both**: an A2A server outside, an MCP client inside, with tools hidden from callers.
- **Bridges must preserve task states**: map input-required, auth-required and working states to actionable tool results.
- **Protocols are for boundaries**: inside one codebase, use your framework's subagents instead.

---

**Up next:** [Securing Agent-to-Agent Communication](securing-agent-to-agent-communication.md)
