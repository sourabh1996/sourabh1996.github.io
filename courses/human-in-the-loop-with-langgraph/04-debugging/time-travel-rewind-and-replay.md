---
title: "Time Travel: Rewind and Replay"
course: Human-in-the-Loop with LangGraph
module: "4. Debugging"
type: Article
level: Intermediate
reading_time: 32 min
---

# Time Travel: Rewind and Replay: The Complete Guide

> 📚 **Before you start**
>
> - [Persistence and Checkpointers](../../langgraph-fundamentals/05-chatbots-and-persistence/persistence-and-checkpointers.md), where you first listed history, replayed and forked. This lesson goes much deeper.
> - [Editing State with Human Input](../03-human-feedback/editing-state-with-human-input.md), for `update_state` and `as_node`.
> - [Pausing with interrupt and Resuming with Command](../03-human-feedback/pausing-with-interrupt-and-resuming-with-command.md), because interrupts behave in a particular way during replays.

## Introduction

Cricket's Decision Review System (DRS) is time travel for umpires. A batter is given out lbw; the captain asks for a review; the third umpire **rewinds** to the exact ball, watches it frame by frame, checks where it pitched and where it would have gone, and if the original call was wrong, the match **continues from that ball with the corrected decision**. Nobody replays the whole innings, and the original call isn't erased from history: the scorecard shows that a review happened and what it changed.

Agents need DRS. When an agent gives a wrong answer after twelve steps, you want to find **the exact step** where it went wrong, look at the state at that moment, change it (a wrong tool argument, a misleading search result, a bad plan), and **run forward from there**, without repeating the eleven good steps and without losing the record of what originally happened.

Because a checkpointer saves the state after every super-step, LangGraph already has everything needed. In this lesson you'll navigate a thread's history efficiently (filters, limits, paging), understand exactly what **replay** re-executes, **fork** a new branch with `update_state` and `as_node`, see how **interrupts** behave when you travel back past them, draw a thread's **branch tree**, and learn the caveats that matter in production.

> 💡 **Key Insight**
>
> Time travel never rewrites history. **Replaying** from a checkpoint and **forking** with `update_state` both add **new checkpoints whose parent is the old one**, so a thread becomes a tree. "The current state" is just the newest checkpoint, at the tip of whichever branch ran last.

---

## Core Explanation

### 1. A thread to explore

A small research workflow for a personal-finance blog: plan a question, "search" for a rate, then write an answer. The search node reads a rate table that can change, and the writer is a scripted model, so we can see what replays re-run.

```python
import operator
from typing import Annotated, TypedDict
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

RATES = {"SBI": 6.8, "HDFC": 7.1}            # FD rates the "search" returns
runs = {"plan": 0, "search": 0, "write": 0}

class Research(TypedDict):
    question: str
    bank: str
    rate: float
    answer: str
    log: Annotated[list, operator.add]

def plan(state: Research):
    runs["plan"] += 1
    return {"bank": "SBI", "log": ["planned: look up SBI"]}

def search(state: Research):
    runs["search"] += 1
    return {"rate": RATES[state["bank"]], "log": [f"found {state['bank']} at {RATES[state['bank']]}%"]}

def write(state: Research):
    runs["write"] += 1
    text = writer.invoke(f"{state['bank']} FD rate {state['rate']}%").content
    return {"answer": text, "log": ["written"]}

b = StateGraph(Research)
b.add_sequence([plan, search, write])
b.add_edge(START, "plan")
b.add_edge("write", END)
app = b.compile(checkpointer=InMemorySaver())

writer = FakeListChatModel(responses=["Draft 1: SBI's 1-year FD pays 6.8%.",
                                      "Draft 2: SBI's 1-year FD pays 6.8%, a good safe option.",
                                      "Draft 3: HDFC's 1-year FD pays 7.1%."])
cfg = {"configurable": {"thread_id": "fd-blog"}}
print(app.invoke({"question": "Best 1-year FD rate?", "log": []}, cfg)["answer"])
```

Output:

```
Draft 1: SBI's 1-year FD pays 6.8%.
```

### 2. Navigating history

`get_state_history(config)` yields `StateSnapshot`s newest first. Each snapshot's `metadata` has the `step` and the `source` (`"input"`, `"loop"` for a normal step, `"update"` for `update_state`, `"fork"` when a replay starts a new branch, as you'll see in section 5), and its `config` holds the `checkpoint_id` that addresses it:

```python
for snap in app.get_state_history(cfg):
    print(f"step {snap.metadata['step']:2} {snap.metadata['source']:5} next={str(snap.next):12} "
          f"log={snap.values.get('log')}")
```

Output:

```
step  3 loop  next=()           log=['planned: look up SBI', 'found SBI at 6.8%', 'written']
step  2 loop  next=('write',)   log=['planned: look up SBI', 'found SBI at 6.8%']
step  1 loop  next=('search',)  log=['planned: look up SBI']
step  0 loop  next=('plan',)    log=[]
step -1 input next=('__start__',) log=[]
```

Long agent threads can have hundreds of checkpoints, so `get_state_history` has three narrowing options:

```python
loops = list(app.get_state_history(cfg, filter={"source": "loop"}))
latest_two = list(app.get_state_history(cfg, limit=2))
newest = latest_two[0]
older = list(app.get_state_history(cfg, before=newest.config))
print(len(loops), "loop checkpoints |", len(latest_two), "with limit=2 |",
      len(older), "older than the newest")
```

Output:

```
4 loop checkpoints | 2 with limit=2 | 4 older than the newest
```

- **`filter`** matches metadata fields (for example `source`, `step`, or metadata you passed in the run's config).
- **`limit`** stops after N snapshots.
- **`before`** starts below a given checkpoint, which is how you page through a long history.

Usually you search by **content**: "the checkpoint just before `search` ran" is the one whose `next` is `("search",)`:

```python
def find(app, config, next_node):
    return next(s for s in app.get_state_history(config) if s.next == (next_node,))

before_search = find(app, cfg, "search")
print(before_search.metadata["step"], before_search.values["bank"], before_search.config["configurable"]["checkpoint_id"][:8] != "")
```

Output:

```
1 SBI True
```

### 3. Replay: run again from an old checkpoint

Invoking with **`None`** as the input and an old checkpoint's **config** resumes from that checkpoint. Nodes before it are not run (their results are in the snapshot); nodes after it **run again for real**:

```python
before = dict(runs)
replayed = app.invoke(None, before_search.config)
print("answer:", replayed["answer"])
print("re-ran:", {k: runs[k] - before[k] for k in runs})
```

Output:

```
answer: Draft 2: SBI's 1-year FD pays 6.8%, a good safe option.
re-ran: {'plan': 0, 'search': 1, 'write': 1}
```

`plan` didn't run; `search` and `write` did, and the writer (like a real LLM) produced a **different** draft this time. That's the point of replay: it's a real re-execution, not a playback of recorded outputs. Use it when the cause of a bad result was outside the graph (a flaky API, a prompt you've since changed) and you want to rerun just the affected steps.

Replaying from the **final** checkpoint (where `next` is empty) does nothing: there's nothing left to run.

### 4. Fork: change the past, then continue

A fork is a replay **with an edit**. `update_state` on an old checkpoint's config writes a new checkpoint branching from it and returns that checkpoint's config; invoking `None` from there continues the new branch:

```python
fork_cfg = app.update_state(before_search.config, {"bank": "HDFC"})
print("fork's parent is before_search:",
      app.get_state(fork_cfg).parent_config["configurable"]["checkpoint_id"]
      == before_search.config["configurable"]["checkpoint_id"])
print("fork next:", app.get_state(fork_cfg).next)

forked = app.invoke(None, fork_cfg)
print(forked["answer"])
print(forked["log"])
```

Output:

```
fork's parent is before_search: True
fork next: ('search',)
Draft 3: HDFC's 1-year FD pays 7.1%.
['planned: look up SBI', 'found HDFC at 7.1%', 'written']
```

The fork kept `plan`'s log entry ("planned: look up SBI": that really happened) but searched HDFC, because we changed `bank` before `search` ran. `update_state` was treated as coming from `plan` (the node that ran last before that checkpoint), so the graph continued along `plan`'s edge to `search`.

**`as_node`** changes that. Naming a later node lets you **skip ahead**; naming the node itself lets you supply its output without running it:

```python
skip_cfg = app.update_state(before_search.config, {"rate": 7.4, "log": ["rate entered by an editor"]},
                            as_node="search")
print("next after pretending search ran:", app.get_state(skip_cfg).next)
print(app.invoke(None, skip_cfg)["log"])
```

Output:

```
next after pretending search ran: ('write',)
['planned: look up SBI', 'rate entered by an editor', 'written']
```

The docs recommend setting `as_node` explicitly when the last writer is ambiguous (for example after parallel branches, where LangGraph can't infer it and raises an `InvalidUpdateError`), on a fresh thread with no history, and whenever you mean to skip steps.

### 5. The thread is now a tree

Every replay and fork added checkpoints under an older parent. Using `parent_config`, we can draw the tree:

```python
def tree(app, config):
    snaps = list(app.get_state_history(config))
    by_id = {s.config["configurable"]["checkpoint_id"]: s for s in snaps}
    children = {}
    for s in snaps:
        parent = s.parent_config["configurable"]["checkpoint_id"] if s.parent_config else None
        children.setdefault(parent, []).append(s)
    def label(s):
        bits = [f"step {s.metadata['step']}", s.metadata["source"]]
        if s.next:
            bits.append(f"next={s.next[0]}")
        elif s.values.get("answer"):
            bits.append(f"DONE: {s.values['answer'][:22]}...")
        return " | ".join(bits)
    def walk(parent, depth):
        for s in sorted(children.get(parent, []), key=lambda s: s.created_at):
            print("    " * depth + "└─ " + label(s))
            walk(s.config["configurable"]["checkpoint_id"], depth + 1)
    walk(None, 0)

tree(app, cfg)
```

Output:

```
└─ step -1 | input | next=__start__
    └─ step 0 | loop | next=plan
        └─ step 1 | loop | next=search
            └─ step 2 | loop | next=write
                └─ step 3 | loop | DONE: Draft 1: SBI's 1-year ...
            └─ step 2 | fork | next=search
                └─ step 3 | loop | next=write
                    └─ step 4 | loop | DONE: Draft 2: SBI's 1-year ...
            └─ step 2 | update | next=search
                └─ step 3 | loop | next=write
                    └─ step 4 | loop | DONE: Draft 3: HDFC's 1-year...
            └─ step 2 | update | next=write
                └─ step 3 | loop | DONE: Draft 1: SBI's 1-year ...
```

Notice the replay's first checkpoint has `source="fork"`: when you invoke from an old checkpoint, LangGraph first saves a copy of it as the start of the new branch, then runs from there. Forks made with `update_state` start with a `source="update"` checkpoint instead. Four branches grow from the checkpoint before `search`: the original run, the replay, the HDFC fork, and the editor's skip-ahead. Nothing was lost, and `get_state(cfg)` (with no checkpoint id) returns the newest tip, the last branch that ran:

```python
print(app.get_state(cfg).values["log"][-2:])
```

Output:

```
['rate entered by an editor', 'written']
```

### 6. Interrupts re-trigger when you travel back

Time travel re-executes nodes, and that includes nodes that call `interrupt()`. If you replay or fork from a checkpoint **before** an interrupt, the node pauses again and waits for a new answer. Checkpoints **after** an answered interrupt keep that answer:

```python
from langgraph.types import interrupt, Command

class Publish(TypedDict):
    draft: str
    approved_by: str
    status: str

def draft_post(state: Publish):
    return {"draft": "SBI 1-year FD: 6.8%"}

def editor_ok(state: Publish):
    return {"approved_by": interrupt({"approve": state["draft"]})}

def post(state: Publish):
    return {"status": f"posted '{state['draft']}' (approved by {state['approved_by']})"}

b = StateGraph(Publish)
b.add_sequence([draft_post, editor_ok, post])
b.add_edge(START, "draft_post")
pub = b.compile(checkpointer=InMemorySaver())
pc = {"configurable": {"thread_id": "post-1"}}

pub.invoke({}, pc)
print(pub.invoke(Command(resume="Priya"), pc)["status"])

before_editor = find(pub, pc, "editor_ok")
fork = pub.update_state(before_editor.config, {"draft": "SBI 1-year FD: 6.8% (senior citizens 7.3%)"})
out = pub.invoke(None, fork)
print("fork paused again for:", out["__interrupt__"][0].value)
print(pub.invoke(Command(resume="Karan"), pc)["status"])
```

Output:

```
posted 'SBI 1-year FD: 6.8%' (approved by Priya)
fork paused again for: {'approve': 'SBI 1-year FD: 6.8% (senior citizens 7.3%)'}
posted 'SBI 1-year FD: 6.8% (senior citizens 7.3%)' (approved by Karan)
```

That's usually exactly what you want: if you change the draft, the editor's earlier approval of a different draft shouldn't count. Forking from **after** the approval (the checkpoint whose `next` is `("post",)`) keeps Priya's answer and asks nobody.

### 7. Time travel in an agent: fixing a wrong tool call

The most common real use: an agent called a tool with the wrong arguments several steps ago. Find the checkpoint where the tool call was decided, replace that AI message (by id) with a corrected one, and run forward:

```python
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

@tool
def fd_rate(bank: str, years: int) -> str:
    """Fixed-deposit interest rate for a bank and tenure in years."""
    table = {("SBI", 1): 6.8, ("SBI", 5): 6.5, ("HDFC", 1): 7.1}
    return f"{bank} {years}-year FD: {table[(bank, years)]}%"

class ToolFake(GenericFakeChatModel):
    """A scripted chat model that accepts bind_tools, for offline examples."""
    def bind_tools(self, tools, **kwargs):
        return self

llm = ToolFake(messages=iter([
    AIMessage("", tool_calls=[{"name": "fd_rate", "args": {"bank": "SBI", "years": 5}, "id": "t1"}]),
    AIMessage("SBI pays 6.5% on a 1-year FD."),                 # wrong: it looked up 5 years
    AIMessage("SBI pays 6.8% on a 1-year FD."),                 # used after the fix
]))

def agent(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}

b = StateGraph(MessagesState)
b.add_node(agent)
b.add_node("tools", ToolNode([fd_rate]))
b.add_edge(START, "agent")
b.add_conditional_edges("agent", tools_condition)
b.add_edge("tools", "agent")
fd_agent = b.compile(checkpointer=InMemorySaver())
ac = {"configurable": {"thread_id": "fd-agent"}}
print(fd_agent.invoke({"messages": [("user", "SBI 1-year FD rate?")]}, ac)["messages"][-1].content)

bad_step = find(fd_agent, ac, "tools")                      # tool call decided, not yet run
bad_call = bad_step.values["messages"][-1]
fixed = AIMessage("", id=bad_call.id,
                  tool_calls=[{**bad_call.tool_calls[0], "args": {"bank": "SBI", "years": 1}}])
fix_cfg = fd_agent.update_state(bad_step.config, {"messages": [fixed]})
result = fd_agent.invoke(None, fix_cfg)
print([m.content for m in result["messages"][-2:]])
```

Output:

```
SBI pays 6.5% on a 1-year FD.
['SBI 1-year FD: 6.8%', 'SBI pays 6.8% on a 1-year FD.']
```

We didn't re-ask the user, didn't redo the first model call, and the corrected branch shows a consistent history: the fixed tool call, its true result, and the right answer. The `update_state` came from `agent` (the last node before that checkpoint), so the graph continued to `tools`, exactly as if the model had made the right call in the first place.

### 8. Caveats for real systems

| Caveat | What to do |
|---|---|
| Replays **re-execute** nodes, including side effects (payments, emails) | Make side-effecting nodes idempotent, or fork *after* them; test with mocked tools |
| LLM nodes give **different outputs** on replay | Expected; to reproduce exactly, record model outputs or use a cached/fake model in tests |
| `durability="exit"` saves only the final state | Use the default or `"sync"` where you need step-by-step history |
| History **grows** with every step and branch | Delete old threads (`delete_thread`) or use your checkpointer's retention options |
| Subgraphs inherit the parent's checkpoints | By default you can travel only at the parent level; compile a subgraph with `checkpointer=True` to keep its own checkpoints and fork inside it |

LangGraph Studio's time-travel UI (edit a past step and "fork") is these same calls behind buttons.

---

## Try It Yourself

1. **Find a step by content.** On `"fd-blog"`, find the **oldest** checkpoint whose state has an `answer`. What's its step and which branch is it from?
2. **Fork on a fresh thread.** On a brand-new thread with no history, use `update_state` with `as_node="plan"` to supply `{"bank": "HDFC", "question": "...", "log": []}`, then `invoke(None, ...)`. Which nodes run?
3. **Page through history.** Write a generator `history_pages(app, config, size)` that yields lists of at most `size` snapshots using `limit` and `before`. Count the pages for `"fd-blog"` with `size=4`.

<details>
<summary>Show answers</summary>

**1.**

```python
with_answer = [s for s in app.get_state_history(cfg) if s.values.get("answer")]
oldest = min(with_answer, key=lambda s: s.created_at)
print(oldest.metadata["step"], "|", oldest.values["answer"])
```

Output:

```
3 | Draft 1: SBI's 1-year FD pays 6.8%.
```

It's the original run's final checkpoint (Draft 1), still in the thread after all the replays and forks.

**2.**

```python
before = dict(runs)
writer = FakeListChatModel(responses=["HDFC's 1-year FD pays 7.1%."])
fresh = {"configurable": {"thread_id": "fresh-fork"}}
new_cfg = app.update_state(fresh, {"question": "Best FD?", "bank": "HDFC", "log": ["bank chosen by hand"]},
                           as_node="plan")
print("next:", app.get_state(new_cfg).next)
print(app.invoke(None, new_cfg)["answer"], {k: runs[k] - before[k] for k in runs})
```

Output:

```
next: ('search',)
HDFC's 1-year FD pays 7.1%. {'plan': 0, 'search': 1, 'write': 1}
```

`plan` never ran; the update stood in for it, and the graph continued with `search` and `write`. On a fresh thread there's no history to infer the node from, so `as_node` is required here.

**3.**

```python
def history_pages(app, config, size):
    before = None
    while True:
        page = list(app.get_state_history(config, limit=size, before=before))
        if not page:
            return
        yield page
        before = page[-1].config

pages = list(history_pages(app, cfg, 4))
print(len(pages), "pages;", [len(p) for p in pages], "| total", sum(len(p) for p in pages))
```

Output:

```
4 pages; [4, 4, 4, 1] | total 13
```

</details>

---

## Real-World Examples

- **Debugging agents in Studio**: open a thread, click the step where the plan went wrong, edit the state, fork, and compare the new answer with the old.
- **Evaluating prompt changes**: replay the last step of a set of saved threads with a new prompt and compare outputs, without re-running expensive earlier tool calls.
- **Support "undo"**: when a bot misunderstood a customer three messages ago, an operator forks from before that message with a corrected interpretation.
- **Incident reviews**: the full branch tree shows what the agent did, what a human changed, and what happened after, like a DRS replay with the original call still on record.

---

## Common Misconceptions

### "Replay plays back the recorded outputs"

It re-executes every node after the checkpoint. Tools are called again and models can answer differently.

### "Forking overwrites the old run"

It adds a branch. Old checkpoints remain readable and replayable.

### "`update_state` on an old checkpoint changes that checkpoint"

Checkpoints are immutable. It creates a new child checkpoint with the update applied.

### "Answered interrupts stay answered after time travel"

Only if you fork from after the interrupt. Travelling to before it re-runs the node, which asks again.

---

## Interview Relevance

*"How do you debug a LangGraph agent that made a mistake several steps back?"* Use time travel: `get_state_history` (with `filter`, `limit`, `before`) to find the checkpoint before the bad step, inspect `values` and `next`, then either replay with `invoke(None, checkpoint_config)` or fork with `update_state(checkpoint_config, fix, as_node=...)` and `invoke(None, fork_config)`. Explain that both create branches, that nodes after the checkpoint re-execute (so side effects need idempotency), and that interrupts before the checkpoint re-trigger.

*"What does `as_node` do in a fork?"* It sets which node the update counts as, and therefore where execution continues; required on fresh threads or after parallel steps, and useful for skipping nodes.

---

## Key Takeaways

- A thread's checkpoints form a **tree**; replays and forks add **branches**, never overwrite.
- Navigate with **`get_state_history`** plus **`filter`**, **`limit`** and **`before`**, or search by `next` and `values`.
- **Replay** = `invoke(None, old_config)`: nodes after the checkpoint **really re-run**.
- **Fork** = `update_state(old_config, values, as_node=...)` then `invoke(None, fork_config)`.
- Interrupts **re-trigger** when you travel back past them; side effects need **idempotency**.

---

**Up next:** [Lab: Debug an agent with time travel](lab-debug-an-agent-with-time-travel.md)
