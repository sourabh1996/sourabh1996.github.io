---
title: "Persistence and Checkpointers"
course: LangGraph Complete Guide
module: "6. Chatbots and Persistence"
type: Article
level: Intermediate
reading_time: 30 min
---

# Persistence and Checkpointers: The Complete Guide

> 📚 **Before you start**
>
> - [Agents with Memory](../05-workflows-and-agents/agents-with-memory.md), where you first compiled a graph with `InMemorySaver`.
> - [The LangGraph Execution Model](../02-getting-started/the-langgraph-execution-model.md), because checkpoints are saved once per super-step.
> - [Building a Chatbot with LangGraph](building-a-chatbot-with-langgraph.md), for `update_state` on a conversation.

## Introduction

Video games learned long ago that players hate losing progress. So games **save** at checkpoints: reach the next village, and if you fall off a cliff later you restart there, not from the beginning. Many games also let you load an *older* save and play differently from that point.

LangGraph does the same for your graphs. With a **checkpointer**, it saves a snapshot of the state after **every super-step**. So far you've used that for memory: the next `invoke` on a thread starts from the latest save. But the saves are far more useful than that. You can list them, read any old one, **replay** from it, or **edit** the state and continue down a different path. These abilities power Studio's debugger, human-in-the-loop approvals and crash recovery.

By the end of this lesson you'll be able to read a `StateSnapshot`, walk a thread's history, replay and fork from an earlier checkpoint, change state with `update_state`, and choose a checkpointer and durability mode for your app.

> 💡 **Key Insight**
>
> A thread isn't one saved state; it's a **chain of snapshots**, one per super-step, each pointing to its parent. "The current state" is just the newest snapshot. Because the old ones are kept, you can go back to any point, change something, and continue, which creates a new branch rather than overwriting history.

---

## Core Explanation

### 1. A small workflow to inspect

A dosa counter: take the order, cook it, serve it. Each node appends to a log so we can see what ran.

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class OrderState(TypedDict):
    dish: str
    status: str
    log: Annotated[list, operator.add]

def take_order(state: OrderState):
    return {"status": "ordered", "log": [f"took order: {state['dish']}"]}

def cook(state: OrderState):
    return {"status": "cooked", "log": [f"cooked {state['dish']}"]}

def serve(state: OrderState):
    return {"status": "served", "log": [f"served {state['dish']} with chutney"]}

builder = StateGraph(OrderState)
builder.add_sequence([take_order, cook, serve])
builder.add_edge(START, "take_order")
builder.add_edge("serve", END)

saver = InMemorySaver()
counter = builder.compile(checkpointer=saver)

config = {"configurable": {"thread_id": "table-4"}}
print(counter.invoke({"dish": "masala dosa", "log": []}, config))
```

Output:

```
{'dish': 'masala dosa', 'status': 'served', 'log': ['took order: masala dosa', 'cooked masala dosa', 'served masala dosa with chutney']}
```

### 2. Anatomy of a `StateSnapshot`

`get_state(config)` returns the latest checkpoint of a thread as a **`StateSnapshot`**:

```python
snap = counter.get_state(config)
print("values:     ", snap.values)
print("next:       ", snap.next)
print("metadata:   ", {k: snap.metadata[k] for k in ("source", "step")})
print("config keys:", sorted(snap.config["configurable"]))
print("has parent: ", snap.parent_config is not None)
print("tasks:      ", snap.tasks)
```

Output:

```
values:      {'dish': 'masala dosa', 'status': 'served', 'log': ['took order: masala dosa', 'cooked masala dosa', 'served masala dosa with chutney']}
next:        ()
metadata:    {'source': 'loop', 'step': 3}
config keys: ['checkpoint_id', 'checkpoint_ns', 'thread_id']
has parent:  True
tasks:       ()
```

| Field | Meaning |
|---|---|
| `values` | The full state at this point |
| `next` | Nodes that would run next; empty `()` means the run finished |
| `config` | How to address this exact snapshot: `thread_id`, `checkpoint_ns` (namespace, used by subgraphs) and `checkpoint_id` |
| `metadata` | `source` (`"input"` for the starting input, `"loop"` for a super-step, `"update"` for a manual `update_state`), `step` number and more |
| `created_at` | When it was saved |
| `parent_config` | The config of the snapshot before this one |
| `tasks` | The pending tasks for `next`, including any errors or interrupts |

### 3. The history of a thread

`get_state_history(config)` yields every snapshot of the thread, **newest first**:

```python
history = list(counter.get_state_history(config))
for s in reversed(history):
    print(f"step {s.metadata['step']:2}  source={s.metadata['source']:5}  "
          f"next={str(s.next):16} status={s.values.get('status')}")
```

Output:

```
step -1  source=input  next=('__start__',)   status=None
step  0  source=loop   next=('take_order',)  status=None
step  1  source=loop   next=('cook',)        status=ordered
step  2  source=loop   next=('serve',)       status=cooked
step  3  source=loop   next=()               status=served
```

```mermaid
flowchart LR
    C0["step -1<br/>input<br/>next: __start__"] --> C1["step 0<br/>next: take_order"]
    C1 --> C2["step 1<br/>status: ordered<br/>next: cook"]
    C2 --> C3["step 2<br/>status: cooked<br/>next: serve"]
    C3 --> C4["step 3<br/>status: served<br/>next: ()"]
```

Five snapshots for a three-node run: one for the raw input (step −1), one with the input applied (step 0), then one after each node. Each points to the one before through `parent_config`:

```python
newest, previous = history[0], history[1]
print(newest.parent_config["configurable"]["checkpoint_id"] == previous.config["configurable"]["checkpoint_id"])
```

Output:

```
True
```

### 4. Reading an old checkpoint

Pass a config that includes a `checkpoint_id` to read the thread as it was at that moment:

```python
before_cooking = next(s for s in history if s.next == ("cook",))
old = counter.get_state(before_cooking.config)
print(old.values["status"], "| next:", old.next)
print(before_cooking.config["configurable"].keys())
```

Output:

```
ordered | next: ('cook',)
dict_keys(['thread_id', 'checkpoint_ns', 'checkpoint_id'])
```

This is how Studio shows you the state "after step 1": it's just reading an older snapshot.

### 5. Replaying from a checkpoint

If you **invoke** with `None` as the input and a config pointing at an old checkpoint, LangGraph resumes from that snapshot. Nodes before it are **not** re-run (their results are in the snapshot); nodes after it run again:

```python
replayed = counter.invoke(None, before_cooking.config)
print(replayed["log"])
print(len(list(counter.get_state_history(config))), "snapshots now in the thread")
```

Output:

```
['took order: masala dosa', 'cooked masala dosa', 'served masala dosa with chutney']
8 snapshots now in the thread
```

`take_order` didn't run again; `cook` and `serve` did. The log has exactly one entry per step because the replay started from the snapshot *before* cooking, whose log held only the `took order` line. The first run's "cooked" and "served" entries belong to the original branch, which is still in the history (that's why the thread now has 8 snapshots instead of 5).

So replaying didn't overwrite anything; it added new snapshots on a **branch** that starts at the old checkpoint. The thread's "latest state" is now the end of the new branch.

```mermaid
flowchart LR
    I["input"] --> O["ordered<br/>next: cook"]
    O --> A1["cooked"] --> A2["served<br/>(original)"]
    O --> B1["cooked"] --> B2["served<br/>(replay, now latest)"]
```

Replaying is useful when a node failed or produced a bad result because of something outside the graph (a flaky API, an updated prompt): fix the cause and run again from just before that node.

### 6. Changing the past: `update_state` and forking

Often you want to replay **with a change**: the customer changed their order after it was taken but before it was cooked. `update_state` writes new values into a checkpoint as though a node had returned them, and returns the config of the new snapshot:

```python
fork_config = counter.update_state(before_cooking.config, {"dish": "rava dosa"})
print("fork snapshot next:", counter.get_state(fork_config).next)
result = counter.invoke(None, fork_config)
print(result["dish"], "|", result["log"])
```

Output:

```
fork snapshot next: ('cook',)
rava dosa | ['took order: masala dosa', 'cooked rava dosa', 'served rava dosa with chutney']
```

The fork kept the original "took order: masala dosa" log line (that happened), changed the dish, and then cooked and served a rava dosa. The update itself is saved as a snapshot with `source="update"`:

```python
sources = [s.metadata["source"] for s in counter.get_state_history(config)]
print(sources.count("update"), "update snapshot(s);", len(sources), "snapshots in total")
```

Output:

```
1 update snapshot(s); 11 snapshots in total
```

Two details to know:

- `update_state` goes through the **reducers**. Updating `log` would **append**, not replace, because `log` uses `operator.add`. For `messages`, sending a message with an existing id replaces it, as you saw in the last lesson.
- By default the update is treated as coming from the node that ran last before that checkpoint, which decides what runs next. You can pass `as_node="some_node"` to pretend the update came from a specific node, so the graph continues from that node's outgoing edges.

These are the building blocks of **time travel** and **human-in-the-loop** editing, which have their own module later in this course: [Human-in-the-Loop and Debugging](../course.md#m8).

### 7. Choosing a checkpointer

All checkpointers implement the same interface (`put`, `get_tuple`, `list` and a few more), so you can switch by changing one line.

| Checkpointer | Package | Stores in | Use for |
|---|---|---|---|
| `InMemorySaver` | `langgraph` (built in) | Python memory | Tests, notebooks, demos |
| `SqliteSaver` / `AsyncSqliteSaver` | `langgraph-checkpoint-sqlite` | A SQLite file | Local apps, prototypes, single-machine tools |
| `PostgresSaver` / `AsyncPostgresSaver` | `langgraph-checkpoint-postgres` | PostgreSQL | Production servers, many workers |
| Others | separate packages (for example Redis and MongoDB integrations) | Those databases | When your stack already uses them |
| Managed | built into LangSmith Deployment | Provided Postgres | Deployed apps (module 10) |

```python
# not-run: needs `pip install langgraph-checkpoint-postgres "psycopg[binary,pool]"` and a database
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://postgres:postgres@localhost:5432/langgraph"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()                      # creates the tables, run once
    app = builder.compile(checkpointer=checkpointer)
    app.invoke({"dish": "uttapam", "log": []}, {"configurable": {"thread_id": "table-9"}})
```

SQLite gets its own lesson next but one: [Persistent Storage with SQLite](persistent-storage-with-sqlite.md).

### 8. Durability modes: when is a checkpoint written?

Writing a checkpoint takes time, especially to a remote database. The `durability` argument of `invoke`/`stream` controls the trade-off:

| `durability=` | When state is saved | Trade-off |
|---|---|---|
| `"async"` (default) | In the background while the next step runs | Fast; a crash at the wrong instant can lose the latest step |
| `"sync"` | Before the next step starts | Safest; slightly slower |
| `"exit"` | Only when the run finishes (or fails, or pauses) | Fastest; no mid-run recovery points |

```python
quick = counter.invoke({"dish": "plain dosa", "log": []},
                       {"configurable": {"thread_id": "table-5"}}, durability="exit")
steps = [s.metadata["step"] for s in counter.get_state_history({"configurable": {"thread_id": "table-5"}})]
print(quick["status"], "| saved steps:", steps)
```

Output:

```
served | saved steps: [3]
```

With `"exit"`, only the final state was saved, so there's no history to replay from. Use `"sync"` for long, expensive runs where you never want to repeat a finished step; keep the default for chat; consider `"exit"` for short runs where intermediate history isn't worth the writes.

### 9. What can go in a checkpoint?

A checkpointer has to **serialise** your state. LangGraph's default serializer handles the usual types: strings, numbers, lists and dicts, LangChain messages, Pydantic models, dataclasses, dates and more. Things like open file handles, database connections or clients **don't** belong in state; keep them in module-level variables or pass them through the run's context.

One security note: loading a checkpoint means deserialising data from your database. The LangGraph checkpoint packages recommend restricting deserialisation to known-safe types in production (the `LANGGRAPH_STRICT_MSGPACK=true` environment variable or an explicit allow-list), so that a tampered database can't trigger code execution. Treat your checkpoint database as sensitive: it contains every conversation.

---

## Try It Yourself

1. **Count snapshots.** For a fresh thread on `counter`, how many snapshots does one full run create? Predict, then check.
2. **Fork with `as_node`.** On a fresh thread, run the counter. Then take the **final** snapshot and call `update_state(..., {"status": "returned"}, as_node="take_order")`. What is `next` for the new snapshot, and what happens when you `invoke(None, ...)` from it?
3. **Find the branch point.** After section 6, how could you find all snapshots in `"table-4"` whose `status` is `"served"`? How many are there and why?

<details>
<summary>Show answers</summary>

**1.** Five: input, step 0, and one per node.

```python
c = {"configurable": {"thread_id": "fresh"}}
counter.invoke({"dish": "set dosa", "log": []}, c)
print(len(list(counter.get_state_history(c))))
```

Output:

```
5
```

**2.**

```python
c = {"configurable": {"thread_id": "returns"}}
counter.invoke({"dish": "onion dosa", "log": []}, c)
final = counter.get_state(c)
new_cfg = counter.update_state(final.config, {"status": "returned"}, as_node="take_order")
print(counter.get_state(new_cfg).next)
print(counter.invoke(None, new_cfg)["log"])
```

Output:

```
('cook',)
['took order: onion dosa', 'cooked onion dosa', 'served onion dosa with chutney', 'cooked onion dosa', 'served onion dosa with chutney']
```

Because the update pretends to come from `take_order`, the graph continues along `take_order`'s edge to `cook`, so the dosa is cooked and served again (a remake).

**3.**

```python
served = [s for s in counter.get_state_history(config) if s.values.get("status") == "served"]
print(len(served), [s.values["dish"] for s in served])
```

Output:

```
3 ['rava dosa', 'masala dosa', 'masala dosa']
```

One per branch: the original run, the replay, and the rava dosa fork each ended with a `served` snapshot.

</details>

---

## Real-World Examples

- **Debugging in Studio**: click a step, edit the state, and re-run from there. That's `get_state_history`, `update_state` and `invoke(None, config)` behind the buttons.
- **Approval workflows**: a payout graph pauses before `transfer_money`; a manager edits the amount (`update_state`) and resumes.
- **Long research agents** use `durability="sync"` so a crash after twenty minutes of searching doesn't repeat any finished step.

---

## Common Misconceptions

### "The checkpointer stores one state per thread"

It stores a snapshot per super-step, with parent links. "Current state" is the newest one.

### "Replaying re-runs the whole graph"

Only the nodes after the chosen checkpoint run again; earlier results come from the snapshot.

### "`update_state` overwrites fields"

It goes through the reducers. Fields with `operator.add` or `add_messages` append (or replace by id); only plain fields are overwritten.

### "Forking deletes the old branch"

The old snapshots remain in history and can still be read or replayed.

---

## Interview Relevance

*"How does persistence work in LangGraph?"* A checkpointer saves a `StateSnapshot` after every super-step, keyed by `thread_id` and `checkpoint_id`, with parent links. That enables memory across invocations, human-in-the-loop (pause and resume), time travel (replay and fork with `update_state`) and fault tolerance. Mention `InMemorySaver` vs SQLite vs Postgres, and durability modes.

*"What happens when you invoke with `None` and a checkpoint id?"* The graph resumes from that snapshot, re-running only the nodes after it, and records the new steps as a branch.

---

## Key Takeaways

- A checkpointer saves a **`StateSnapshot` after every super-step**: `values`, `next`, `config` (with `checkpoint_id`), `metadata`, `parent_config`, `tasks`.
- **`get_state_history`** lists a thread's snapshots, newest first.
- **`invoke(None, old_config)`** replays from a checkpoint; **`update_state`** edits state (through reducers) and creates a **fork**.
- Pick **InMemory** for tests, **SQLite** for local apps, **Postgres** (or a managed deployment) for production.
- **`durability`** (`"async"` default, `"sync"`, `"exit"`) trades speed for how much progress is saved mid-run.

---

**Up next:** [Threads, Fault Tolerance and Resuming](threads-fault-tolerance-and-resuming.md)
