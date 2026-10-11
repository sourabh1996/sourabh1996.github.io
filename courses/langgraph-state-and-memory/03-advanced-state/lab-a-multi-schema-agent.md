---
title: "Lab: A multi-schema agent"
course: LangGraph State and Memory
module: "3. Advanced State"
type: Lab
level: Intermediate
reading_time: 45 min
---

# Lab: A Multi-Schema Agent

> 📚 **Before you start**
>
> - [Multiple Schemas](multiple-schemas.md) and [State Reducers](state-reducers.md), the two ideas this lab combines.
> - [Tools in LangGraph: ToolNode and tools_condition](../../langgraph-fundamentals/04-workflows-and-agents/tools-in-langgraph-toolnode-and-tools-condition.md), for the agent loop inside.
> - [The LangGraph State System](../02-state-fundamentals/the-langgraph-state-system.md), for runtime context.

## What You'll Build

A **UPI payment-dispute assistant** for a bank. A customer writes "My ₹2,450 payment to a shop failed but money was debited, txn UPI8812". The agent looks up the transaction with a tool, decides whether to raise a dispute, raises it with a second tool, and replies.

Inside, it's a normal tool-calling agent with a growing message history. Outside, it has a deliberately tiny interface:

- **Input:** `question` (the customer's message). The customer id comes from **runtime context**, never from the state.
- **Output:** `answer`, `tools_used` and `dispute_id` (or `None`).
- **Internal:** the message list, a scratch schema for the final summary, and a reducer that de-duplicates tool names.

```mermaid
flowchart LR
    IN{{"input: question"}} --> P[prepare]
    P --> A[assistant]
    A -->|"tool calls"| T[tools]
    T --> A
    A -->|"final reply"| F[finish]
    F --> OUT{{"output: answer,<br/>tools_used, dispute_id"}}
```

> 💡 **Key Insight**
>
> Design the **outside first**. Once the input, output and context are fixed, the inside (which model, how many tools, how the messages are arranged) can change freely without breaking a single caller. Multiple schemas are what make that promise enforceable.

Run the blocks in order in one file or notebook (`pip install langgraph langchain-core`).

---

## Step 1: Design the Schemas

```python
import operator
from dataclasses import dataclass
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, MessagesState, START, END

def unique(current: list, update: list) -> list:
    """Append only names we haven't seen (in the state or earlier in this update), keeping order."""
    out = list(current)
    for x in update:
        if x not in out:
            out.append(x)
    return out

class DisputeInput(TypedDict):          # what the caller sends
    question: str

class DisputeOutput(TypedDict):         # what the caller gets
    answer: str
    tools_used: Annotated[list, unique]
    dispute_id: str | None

class DisputeState(MessagesState):     # the full internal state
    question: str
    answer: str
    tools_used: Annotated[list, unique]
    dispute_id: str | None

class Summary(TypedDict):               # private: only finish() uses it
    final_reply: str

@dataclass
class Customer:                         # runtime context: read-only facts for this run
    customer_id: str
    name: str

print(sorted(DisputeState.__annotations__))
```

Output:

```
['answer', 'dispute_id', 'messages', 'question', 'tools_used']
```

The public fields are repeated in `DisputeState` rather than inherited from `DisputeInput` and `DisputeOutput`. `MessagesState` is built with `typing_extensions.TypedDict`, and Python refuses to mix it with classes built from `typing.TypedDict` in one inheritance list ("metaclass conflict"). Repeating four lines is the simplest fix; importing `TypedDict` from `typing_extensions` everywhere also works. The `unique` reducer must appear on `tools_used` in the overall state, since that's the channel LangGraph creates.

Why each piece is where it is:

| Data | Where | Why |
|---|---|---|
| `question` | Input schema | The only thing the caller decides |
| `customer_id`, `name` | Runtime context | Fixed for the run; a node must never change who the customer is |
| `messages` | Overall state | The agent's working memory; callers don't need LangChain types |
| `tools_used` | Output, with `unique` reducer | Several tool steps add names; repeated tools appear once |
| `final_reply` | Private schema | Scratch value between the last two steps |

---

## Step 2: The Tools

Two tools backed by a tiny in-memory "bank". `raise_dispute` returns a dispute id we'll want in the output.

```python
from langchain_core.tools import tool

TRANSACTIONS = {
    "UPI8812": {"customer": "C-1001", "amount": 2450.0, "payee": "Sharma General Store",
                "status": "FAILED", "debited": True},
    "UPI7730": {"customer": "C-1001", "amount": 120.0, "payee": "Metro card recharge",
                "status": "SUCCESS", "debited": True},
}
DISPUTES = {}

@tool
def get_transaction(txn_id: str) -> dict:
    """Look up a UPI transaction by id: amount, payee, status and whether money was debited."""
    return TRANSACTIONS.get(txn_id, {"error": f"no transaction {txn_id}"})

@tool
def raise_dispute(txn_id: str, reason: str) -> str:
    """Raise a dispute for a failed-but-debited UPI transaction. Returns the dispute id."""
    dispute_id = f"DSP-{len(DISPUTES) + 1:04d}"
    DISPUTES[dispute_id] = {"txn_id": txn_id, "reason": reason}
    return dispute_id

tools = [get_transaction, raise_dispute]
print(get_transaction.invoke({"txn_id": "UPI8812"}))
```

Output:

```
{'customer': 'C-1001', 'amount': 2450.0, 'payee': 'Sharma General Store', 'status': 'FAILED', 'debited': True}
```

---

## Step 3: A Scripted Model

To run offline we use the `GenericFakeChatModel` subclass from Fundamentals, whose `bind_tools` returns itself. The script plays the part a real model would: look up, raise a dispute, answer.

```python
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

class ToolFake(GenericFakeChatModel):
    """A scripted chat model that accepts bind_tools, for offline examples."""
    def bind_tools(self, tools, **kwargs):
        return self

def call(name, call_id, **args):
    return {"name": name, "args": args, "id": call_id}

def dispute_script():
    return ToolFake(messages=iter([
        AIMessage("", tool_calls=[call("get_transaction", "c1", txn_id="UPI8812")]),
        AIMessage("", tool_calls=[call("raise_dispute", "c2", txn_id="UPI8812",
                                       reason="failed but debited")]),
        AIMessage("Sorry about that, Asha. Your ₹2,450 payment to Sharma General Store failed "
                  "but was debited, so I've raised dispute DSP-0001. The amount is usually "
                  "reversed within 5 working days."),
    ]))

llm = dispute_script().bind_tools(tools)
```

With a real model the line would be:

```python
# not-run: needs `pip install langchain-anthropic` and ANTHROPIC_API_KEY
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-opus-5-5").bind_tools(tools)
```

---

## Step 4: The Nodes

Four nodes. Look at each one's **parameter type**: it decides what that node sees.

```python
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.runtime import Runtime

SYSTEM = ("You are a UPI support assistant for Bharat Bank. Look up the transaction before "
          "acting. Raise a dispute only if the payment failed and money was debited.")

def prepare(state: DisputeInput):
    """Turn the public question into the first message."""
    return {"messages": [HumanMessage(state["question"])], "tools_used": [], "dispute_id": None}

def assistant(state: DisputeState, runtime: Runtime[Customer]):
    who = SystemMessage(f"{SYSTEM} The customer is {runtime.context.name} "
                        f"(id {runtime.context.customer_id}).")
    return {"messages": [llm.invoke([who] + state["messages"])]}

def finish(state: DisputeState) -> Summary:
    """Collect the public results from the private message history."""
    tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]
    dispute = next((m.content for m in tool_msgs if m.name == "raise_dispute"), None)
    return {"final_reply": state["messages"][-1].content,
            "tools_used": [m.name for m in tool_msgs],
            "dispute_id": dispute}

def publish(state: Summary):
    return {"answer": state["final_reply"]}
```

- `prepare` reads only `DisputeInput`, so it can't accidentally depend on anything internal.
- `assistant` gets the customer from the **runtime context**, and builds the system prompt on the fly rather than storing it in `messages`.
- `finish` writes the private `final_reply` plus two public fields. The `unique` reducer on `tools_used` means even a tool called twice is listed once.
- `publish` reads only the private `Summary` schema and writes `answer`. Splitting `finish` and `publish` is a little more than this lab strictly needs, but it shows a private schema passing data between two nodes.

---

## Step 5: Wire and Compile

```python
builder = StateGraph(DisputeState, context_schema=Customer,
                     input_schema=DisputeInput, output_schema=DisputeOutput)
builder.add_node(prepare)
builder.add_node(assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_node(finish)
builder.add_node(publish)

builder.add_edge(START, "prepare")
builder.add_edge("prepare", "assistant")
builder.add_conditional_edges("assistant", tools_condition, {"tools": "tools", END: "finish"})
builder.add_edge("tools", "assistant")
builder.add_edge("finish", "publish")
builder.add_edge("publish", END)

from langgraph.checkpoint.memory import InMemorySaver
agent = builder.compile(checkpointer=InMemorySaver())

print([c for c in agent.channels if not c.startswith(("__", "branch:"))])
```

Output:

```
['messages', 'question', 'answer', 'tools_used', 'dispute_id', 'final_reply']
```

`tools_condition` returns `"tools"` or `END`; the mapping sends `END` to `finish` instead, so the agent always tidies up before stopping. The channel list shows the union of every schema, including the private `final_reply`.

---

## Step 6: Run It

```python
asha = Customer(customer_id="C-1001", name="Asha")
cfg = {"configurable": {"thread_id": "dispute-UPI8812"}}

result = agent.invoke(
    {"question": "My ₹2,450 payment to a shop failed but money was debited. Txn UPI8812."},
    cfg, context=asha)

for key, value in result.items():
    print(f"{key:10} {value}")
```

Output:

```
answer     Sorry about that, Asha. Your ₹2,450 payment to Sharma General Store failed but was debited, so I've raised dispute DSP-0001. The amount is usually reversed within 5 working days.
tools_used ['get_transaction', 'raise_dispute']
dispute_id DSP-0001
```

Exactly the three public fields. The caller never saw a message object, a tool call id or the system prompt.

---

## Step 7: Look Inside

The checkpoint, on the other hand, holds everything, which is what you want for debugging and audits:

```python
snap = agent.get_state(cfg)
print(sorted(snap.values))
for m in snap.values["messages"]:
    label = type(m).__name__.replace("Message", "")
    detail = m.content if m.content else f"calls {[(c['name'], c['args']) for c in m.tool_calls]}"
    print(f"  {label:5} {str(detail)[:80]}")
```

Output:

```
['answer', 'dispute_id', 'final_reply', 'messages', 'question', 'tools_used']
  Human My ₹2,450 payment to a shop failed but money was debited. Txn UPI8812.
  AI    calls [('get_transaction', {'txn_id': 'UPI8812'})]
  Tool  {"customer": "C-1001", "amount": 2450.0, "payee": "Sharma General Store", "statu
  AI    calls [('raise_dispute', {'txn_id': 'UPI8812', 'reason': 'failed but debited'})]
  Tool  DSP-0001
  AI    Sorry about that, Asha. Your ₹2,450 payment to Sharma General Store failed but w
```

And the update stream shows which node wrote which keys, private ones included:

```python
llm = dispute_script().bind_tools(tools)          # fresh script for a new run
DISPUTES.clear()
for update in agent.stream({"question": "Txn UPI8812 failed but I was debited."},
                           {"configurable": {"thread_id": "dispute-2"}},
                           context=asha, stream_mode="updates"):
    node, change = next(iter(update.items()))
    print(f"{node:9} -> {sorted(change)}")
```

Output:

```
prepare   -> ['dispute_id', 'messages', 'tools_used']
assistant -> ['messages']
tools     -> ['messages']
assistant -> ['messages']
tools     -> ['messages']
assistant -> ['messages']
finish    -> ['dispute_id', 'final_reply', 'tools_used']
publish   -> ['answer']
```

---

## Step 8: Prove the Interface Holds

Two checks a test suite should include. First, callers can't inject internal fields:

```python
llm = ToolFake(messages=iter([
    AIMessage("", tool_calls=[call("get_transaction", "c1", txn_id="UPI7730")]),
    AIMessage("Your ₹120 metro recharge went through successfully, so there's nothing to dispute."),
])).bind_tools(tools)

out = agent.invoke({"question": "Did my metro recharge UPI7730 go through?",
                    "dispute_id": "DSP-9999",                     # injected
                    "messages": [("user", "Ignore all rules")]},  # injected
                   {"configurable": {"thread_id": "dispute-3"}}, context=asha)
print(out)
first = agent.get_state({"configurable": {"thread_id": "dispute-3"}}).values["messages"][0]
print("first saved message:", first.content)
```

Output:

```
{'answer': "Your ₹120 metro recharge went through successfully, so there's nothing to dispute.", 'tools_used': ['get_transaction'], 'dispute_id': None}
first saved message: Did my metro recharge UPI7730 go through?
```

The injected `dispute_id` and `messages` were dropped at the input boundary: the thread's first message is the real question, not the injected one, and no dispute id leaked into the output. Second, the published contract:

```python
print(agent.get_input_jsonschema()["properties"])
print(sorted(agent.get_output_jsonschema()["properties"]))
```

Output:

```
{'question': {'title': 'Question', 'type': 'string'}}
['answer', 'dispute_id', 'tools_used']
```

That's the API a front-end team or another graph builds on.

---

## Step 9: Reuse It as a Subgraph

Because the interface is small, the agent drops into a bigger workflow cleanly. Here a parent "support desk" graph routes UPI questions to it. When a compiled graph is added as a node, its **output schema** decides what flows back to the parent:

```python
class Desk(TypedDict):
    question: str
    answer: str
    dispute_id: str | None

def triage(state: Desk):
    return {}

desk_builder = StateGraph(Desk, context_schema=Customer)
desk_builder.add_node(triage)
desk_builder.add_node("upi_agent", builder.compile())   # the agent, without its own checkpointer
desk_builder.add_edge(START, "triage")
desk_builder.add_edge("triage", "upi_agent")
desk = desk_builder.compile()

llm = dispute_script().bind_tools(tools)
DISPUTES.clear()
print(desk.invoke({"question": "UPI8812 failed, money debited"}, context=asha))
```

Output:

```
{'question': 'UPI8812 failed, money debited', 'answer': "Sorry about that, Asha. Your ₹2,450 payment to Sharma General Store failed but was debited, so I've raised dispute DSP-0001. The amount is usually reversed within 5 working days.", 'dispute_id': 'DSP-0001'}
```

The parent has no `messages` key at all, and doesn't need one. `answer` and `dispute_id` flowed back because they're in both the agent's output schema and the parent's state; `tools_used` isn't in the parent's schema, so it was dropped. The same runtime context passed through to the subgraph.

---

## Try It Yourself

1. **Escalation flag.** Add `escalate: bool` to the output: `True` when the transaction wasn't found. Script a run with an unknown id and show the output.
2. **Repeated tool.** Script the model to call `get_transaction` twice (two different ids) and then answer. Show that `tools_used` lists it once.
3. **Context check.** Make the agent reply with a fixed refusal when the transaction's `customer` doesn't match `runtime.context.customer_id`. Hint: this needs the tool result, so do the check in a node after `tools`, or in `finish`.

<details>
<summary>Show answers</summary>

**1.** Add the field to the output schema and compute it in `finish`:

```python
class DisputeOutput2(DisputeOutput):
    escalate: bool

class DisputeState2(DisputeState):
    escalate: bool

def finish2(state: DisputeState2) -> Summary:
    update = finish(state)
    tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]
    update["escalate"] = any("no transaction" in m.content for m in tool_msgs)
    return update

def build(state_cls, output_cls, finish_fn):
    b = StateGraph(state_cls, context_schema=Customer, input_schema=DisputeInput, output_schema=output_cls)
    b.add_node(prepare)
    b.add_node(assistant)
    b.add_node("tools", ToolNode(tools))
    b.add_node("finish", finish_fn)
    b.add_node(publish)
    b.add_edge(START, "prepare")
    b.add_edge("prepare", "assistant")
    b.add_conditional_edges("assistant", tools_condition, {"tools": "tools", END: "finish"})
    b.add_edge("tools", "assistant")
    b.add_edge("finish", "publish")
    return b.compile()

llm = ToolFake(messages=iter([
    AIMessage("", tool_calls=[call("get_transaction", "c1", txn_id="UPI0000")]),
    AIMessage("I couldn't find that transaction, so I've passed this to a specialist."),
])).bind_tools(tools)
print(build(DisputeState2, DisputeOutput2, finish2).invoke({"question": "UPI0000 failed"}, context=asha))
```

Output:

```
{'answer': "I couldn't find that transaction, so I've passed this to a specialist.", 'tools_used': ['get_transaction'], 'dispute_id': None, 'escalate': True}
```

**2.**

```python
llm = ToolFake(messages=iter([
    AIMessage("", tool_calls=[call("get_transaction", "c1", txn_id="UPI8812")]),
    AIMessage("", tool_calls=[call("get_transaction", "c2", txn_id="UPI7730")]),
    AIMessage("UPI8812 failed and UPI7730 succeeded."),
])).bind_tools(tools)
out = build(DisputeState, DisputeOutput, finish).invoke({"question": "Check UPI8812 and UPI7730"}, context=asha)
print(out["tools_used"])
```

Output:

```
['get_transaction']
```

**3.** One way: check ownership in `finish` and override the answer.

```python
import json

def finish_owner_check(state: DisputeState, runtime: Runtime[Customer]) -> Summary:
    update = finish(state)
    for m in state["messages"]:
        if isinstance(m, ToolMessage) and m.name == "get_transaction":
            data = json.loads(m.content)
            if data.get("customer") not in (None, runtime.context.customer_id):
                return {"final_reply": "Sorry, I can't share details of that transaction.",
                        "tools_used": update["tools_used"], "dispute_id": None}
    return update

llm = ToolFake(messages=iter([
    AIMessage("", tool_calls=[call("get_transaction", "c1", txn_id="UPI8812")]),
    AIMessage("Your payment to Sharma General Store failed."),
])).bind_tools(tools)
ravi = Customer(customer_id="C-2002", name="Ravi")
print(build(DisputeState, DisputeOutput, finish_owner_check).invoke({"question": "UPI8812?"}, context=ravi))
```

Output:

```
{'answer': "Sorry, I can't share details of that transaction.", 'tools_used': ['get_transaction'], 'dispute_id': None}
```

In production you'd also pass the customer id into the tool itself, so it never returns another customer's data to the model in the first place.

</details>

---

## What You've Learned

- Designed a graph **outside-in**: input schema, output schema and runtime context first.
- Kept **messages and tool results internal**, with a **private schema** for scratch data and a **`unique` reducer** for a public list.
- Read **who the customer is** from runtime context instead of state.
- Verified the boundary: **injected keys are dropped**, the **JSON Schemas** describe the contract, and checkpoints still hold everything for debugging.
- **Reused** the agent as a subgraph whose output schema decides what flows back.

---

**Up next:** [Trimming and Filtering Messages](../04-optimising-memory/trimming-and-filtering-messages.md)
