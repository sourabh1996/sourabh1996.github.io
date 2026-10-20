---
title: "Handoffs, Group Chat and Magentic Orchestration"
course: "Multi-Agent Systems and Agent Protocols"
module: "2. Multi-Agent Design"
type: Article
level: Advanced
reading_time: 36 min
---

# Handoffs, Group Chat and Magentic Orchestration: The Complete Guide

> 📚 **Before you start**
>
> - [Orchestrator and Subagents](orchestrator-and-subagents.md), for the lead-and-workers pattern this lesson contrasts with.
> - [Conditional Workflows](../../langgraph-complete-guide/03-workflow-patterns-in-langgraph/conditional-workflows.md), for `Command(update=..., goto=...)` in LangGraph.
> - [Planning and Reflection](../../agentic-ai-fundamentals/05-reasoning-patterns/planning-and-reflection.md), because the Magentic pattern is planning and replanning applied to a team.

## Introduction

Walk into a big government hospital's OPD and you meet three different ways of working together.

At the registration desk, the clerk listens for ten seconds and sends you to the right department: "Cardiology, room 12". From then on, the cardiologist owns your case; the clerk is out of the picture. That is a **handoff**.

On Thursday afternoons the hospital holds a tumour board: a surgeon, an oncologist, a radiologist and a pathologist sit around one table with one patient file. A senior doctor chairs the meeting, decides who speaks next, and closes the discussion when they agree. That is a **group chat**.

When a rare case arrives that nobody can solve quickly, the head of department keeps a whiteboard: what we know, what we're guessing, the plan, and a column for "are we getting anywhere?". Each morning she reads the board, picks one specialist, gives them a precise instruction, and redraws the plan if two days pass without progress. That is **Magentic orchestration**.

The previous lesson covered the orchestrator with subagents, where workers never see each other. This lesson covers the three patterns where agents **do** share the conversation, in different ways. You'll build each one, see where each breaks, and see how real frameworks (OpenAI Agents SDK, Microsoft Agent Framework, LangGraph) implement them.

> 💡 **Key Insight**
>
> The patterns differ in two things: **who holds control** and **who sees what**. In a handoff, control moves and the conversation moves with it. In a group chat, a manager keeps control and everyone sees everything. In Magentic orchestration, a planning manager keeps control **and a written ledger**, and uses it to notice when the team is stuck.

---

## Core Explanation

### 1. The patterns side by side

![Three bands. Handoff: a customer talks to a triage agent, which hands off to a refunds or billing agent through a tool call such as transfer_to_refunds, and the new agent then talks to the customer. Group chat: a chat manager and one shared thread that every agent (writer, critic, fact-checker) reads and writes; each turn re-reads the whole thread. Magentic: a manager keeps a task ledger (facts, guesses, plan) and a progress ledger (done, looping, progressing, next speaker and instruction), instructs specialists, and replans when the team stalls](/img/diagrams/multi-agent-systems-and-agent-protocols/coordination-patterns.svg)
*Three ways for agents to share one conversation.*

Microsoft Agent Framework names five orchestration patterns, which is a handy checklist for the whole module:

| Pattern | Who holds control | Who sees what | Best for |
|---|---|---|---|
| **Sequential** | Fixed order in code | Each agent sees the previous output | Pipelines: draft, edit, translate |
| **Concurrent** | Code fans out and gathers | Each agent sees only its input | Independent analyses (the orchestrator pattern from the last lesson) |
| **Handoff** | Whichever agent currently has the conversation | The receiving agent gets the conversation history | Customer service routing, escalation |
| **Group chat** | A manager that picks the next speaker | Everyone sees the whole thread | Debate, review, brainstorming with a few agents |
| **Magentic** | A planning manager with ledgers | Everyone sees the thread; the manager also keeps a plan and progress record | Open-ended tasks where the steps aren't known upfront |

Sequential and concurrent you already know from LangGraph. The rest of this lesson is the other three.

### 2. Handoffs: passing the baton

In a handoff, one agent decides that another agent should take over, and **control transfers**. The new agent talks to the user directly; the old one is done unless control comes back.

How does an agent "decide" to hand off? Exactly the way it decides anything: by calling a tool. Frameworks give each agent one tool per allowed target. In the OpenAI Agents SDK, a handoff to an agent named `Refund Agent` appears to the model as a tool called `transfer_to_refund_agent`. In Microsoft Agent Framework, handoff tools are added automatically from the allowed routes. When the model calls one, the framework switches the active agent.

Here is what that looks like inside the model's turn:

```json
{"type": "tool_use", "id": "toolu_01", "name": "transfer_to_refunds_agent",
 "input": {"reason": "Customer wants money back for a cancelled order"}}
```

Let's build the mechanism in plain Python. Each pretend agent either answers or returns a handoff, and the loop keeps a single shared history.

```python
AGENTS = {
    "triage": {"handoffs": ["refunds", "billing"]},
    "refunds": {"handoffs": ["triage"]},
    "billing": {"handoffs": ["triage"]},
}

def pretend_model(agent, history):
    """Stands in for each agent's model call: returns either a handoff or an answer."""
    last_user = [text for who, text in history if who == "user"][-1].lower()
    if agent == "triage":
        if "refund" in last_user:
            return {"handoff": "refunds", "reason": "customer asked for a refund"}
        if "invoice" in last_user or "gst" in last_user:
            return {"handoff": "billing", "reason": "invoice question"}
        return {"answer": "Could you tell me a little more about the problem?"}
    if agent == "refunds":
        return {"answer": "I've raised refund R-2291 for Rs 1,499. It reaches your UPI account in 3-5 days."}
    if agent == "billing":
        return {"answer": "Your GST invoice INV-7781 has been emailed to you."}

def run_conversation(user_message, start="triage", max_handoffs=3):
    history = [("user", user_message)]
    active, handoffs = start, 0
    while True:
        step = pretend_model(active, history)
        if "handoff" in step:
            target = step["handoff"]
            if target not in AGENTS[active]["handoffs"]:
                raise ValueError(f"{active} may not hand off to {target}")
            handoffs += 1
            if handoffs > max_handoffs:
                return history + [("system", "too many handoffs; escalating to a human")]
            history.append((active, f"[handoff -> {target}: {step['reason']}]"))
            active = target
            continue
        history.append((active, step["answer"]))
        return history

for who, text in run_conversation("I want a refund for order 5521, it was cancelled"):
    print(f"{who:>8}: {text}")
```

Output:

```
    user: I want a refund for order 5521, it was cancelled
  triage: [handoff -> refunds: customer asked for a refund]
 refunds: I've raised refund R-2291 for Rs 1,499. It reaches your UPI account in 3-5 days.
```

Three rules are already visible in this small loop:

- **Routes are restricted.** `refunds` can only hand back to `triage`. Without restrictions, any agent can hand off to any other, and debugging becomes guesswork.
- **There is a handoff limit.** Two agents that each think the other should handle a case will bounce it forever.
- **The history moves with control.** The refunds agent sees the user's original message. By default both the OpenAI Agents SDK and Microsoft Agent Framework pass the conversation along; both let you filter it (for example, removing tool calls).

### 3. Handoffs in LangGraph with `Command`

In LangGraph, each agent is a node and a handoff is a node returning `Command(goto=<other agent>, update=...)`. No edges between agents are needed; the `Command` is the edge. The return type annotation tells LangGraph which nodes a `Command` may go to, which also restricts the routes.

```python
import operator
from typing import Annotated, Literal, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

class SupportState(TypedDict):
    messages: Annotated[list, operator.add]
    handoffs: int

def triage(state: SupportState) -> Command[Literal["refunds", "billing", "__end__"]]:
    text = state["messages"][-1][1].lower()
    if "refund" in text:
        return Command(goto="refunds", update={"messages": [("triage", "[handoff -> refunds]")],
                                               "handoffs": state["handoffs"] + 1})
    if "gst" in text or "invoice" in text:
        return Command(goto="billing", update={"messages": [("triage", "[handoff -> billing]")],
                                               "handoffs": state["handoffs"] + 1})
    return Command(goto=END, update={"messages": [("triage", "How can I help?")]})

def refunds(state: SupportState) -> Command[Literal["__end__"]]:
    return Command(goto=END, update={"messages": [("refunds", "Refund R-2291 raised for Rs 1,499.")]})

def billing(state: SupportState) -> Command[Literal["__end__"]]:
    return Command(goto=END, update={"messages": [("billing", "Invoice INV-7781 emailed.")]})

g = StateGraph(SupportState)
g.add_node("triage", triage)
g.add_node("refunds", refunds)
g.add_node("billing", billing)
g.add_edge(START, "triage")
support = g.compile()

out = support.invoke({"messages": [("user", "Please send my GST invoice")], "handoffs": 0})
for who, text in out["messages"]:
    print(f"{who:>8}: {text}")
print("handoffs:", out["handoffs"])
```

Output:

```
    user: Please send my GST invoice
  triage: [handoff -> billing]
 billing: Invoice INV-7781 emailed.
handoffs: 1
```

When each agent is its own **subgraph** (a full agent with its own internal loop), a node inside it hands control to a sibling agent in the parent graph with `Command(goto="billing", graph=Command.PARENT)`. That's the line the [subgraphs lesson](../../langgraph-complete-guide/09-subgraphs/shared-vs-different-state-in-subgraphs.md) pointed forward to.

### 4. Handoffs in real SDKs

**OpenAI Agents SDK.** List the agents an agent may hand off to; each becomes a `transfer_to_...` tool. `handoff()` adds options such as `input_filter` to control what history the next agent sees.

```python
# not-run: needs the openai-agents package and an API key
from agents import Agent, Runner, handoff
from agents.extensions import handoff_filters

refunds = Agent(name="Refunds agent", instructions="Handle refunds. Ask for the order ID if missing.")
billing = Agent(name="Billing agent", instructions="Answer invoice and GST questions.")

triage = Agent(
    name="Triage agent",
    instructions="Work out what the customer needs and hand off. Never answer refund questions yourself.",
    handoffs=[refunds, handoff(billing, input_filter=handoff_filters.remove_all_tools)],
)
result = Runner.run_sync(triage, "I want a refund for order 5521")
print(result.last_agent.name, "->", result.final_output)
```

Example output:

```
Refunds agent -> I've started a refund for order 5521. You'll see it in 3-5 working days.
```

**Microsoft Agent Framework.** `HandoffBuilder` builds a mesh of agents; `add_handoff` restricts the routes, exactly like the `AGENTS` table in our plain-Python version.

```python
# not-run: needs the agent-framework package and model credentials
from agent_framework.orchestrations import HandoffBuilder

workflow = (
    HandoffBuilder(
        name="support",
        participants=[triage_agent, refunds_agent, billing_agent],
        termination_condition=lambda conv: "anything else" in conv[-1].text.lower(),
    )
    .with_start_agent(triage_agent)
    .add_handoff(triage_agent, [refunds_agent, billing_agent])
    .add_handoff(refunds_agent, [triage_agent])
    .add_handoff(billing_agent, [triage_agent])
    .build()
)
```

**Handoff or agent-as-tool?** Both use a tool call. The difference is what happens after it:

| | Handoff | Agent as tool |
|---|---|---|
| After the call | The other agent takes over the conversation | The other agent returns a result; the caller continues |
| Who answers the user | The receiving agent | The calling agent |
| Who owns the task | The receiving agent | The calling agent |
| Typical use | Routing to a department | Delegating a sub-question |

### 5. Group chat: one thread, a chair, many voices

In a group chat, all agents share **one conversation thread**. A **manager** (sometimes called the chat manager or orchestrator) does two things each round: picks who speaks next and checks whether to stop. Whatever the chosen agent says is added to the thread, so every agent sees it on its next turn.

The speaker can be picked by a simple rule (round robin, or "writer, then critic, then fact-checker") or by a model reading the thread. The stop condition is usually a phrase ("APPROVED"), a maximum number of rounds, or both.

```python
def writer(thread):
    drafts = sum(1 for who, _ in thread if who == "writer")
    if drafts == 0:
        return "Draft: UPI handled over 18 billion transactions in one month in 2025."
    return "Draft v2: UPI handled over 18 billion transactions in one month in 2025 (NPCI data)."

def critic(thread):
    last_draft = [text for who, text in thread if who == "writer"][-1]
    return "APPROVED" if "NPCI" in last_draft else "Please name the source of the figure."

def fact_checker(thread):
    return "The figure matches NPCI's published monthly statistics."

PARTICIPANTS = {"writer": writer, "fact_checker": fact_checker, "critic": critic}
ORDER = ["writer", "fact_checker", "critic"]

def group_chat(task, max_rounds=9):
    thread = [("user", task)]
    for rnd in range(max_rounds):
        speaker = ORDER[rnd % len(ORDER)]                 # round-robin selection
        reading = sum(len(text) for _, text in thread)    # every speaker reads the whole thread
        message = PARTICIPANTS[speaker](thread)
        thread.append((speaker, message))
        print(f"round {rnd + 1}: {speaker:<12} read {reading:>3} chars -> {message}")
        if message == "APPROVED":
            break
    return thread

_ = group_chat("Write one sentence on UPI's scale, with a source.")
```

Output:

```
round 1: writer       read  49 chars -> Draft: UPI handled over 18 billion transactions in one month in 2025.
round 2: fact_checker read 118 chars -> The figure matches NPCI's published monthly statistics.
round 3: critic       read 173 chars -> Please name the source of the figure.
round 4: writer       read 210 chars -> Draft v2: UPI handled over 18 billion transactions in one month in 2025 (NPCI data).
round 5: fact_checker read 294 chars -> The figure matches NPCI's published monthly statistics.
round 6: critic       read 349 chars -> APPROVED
```

Two things to see in the trace:

- **The reading cost grows every round.** Each speaker re-reads the whole thread. With real agents and long messages, a ten-round chat with four agents re-reads the conversation forty times. This is why group chats should stay small (three or four agents) and short.
- **The stop condition does real work.** Without "APPROVED" or the round limit, the agents would keep talking politely forever.

In Microsoft Agent Framework, `GroupChatBuilder` takes the participants plus either a `selection_func` (a plain function that returns the next speaker's name, like our round robin) or an `orchestrator_agent` (a model that chooses), and a `termination_condition`.

```python
# not-run: needs the agent-framework package and model credentials
from agent_framework.orchestrations import GroupChatBuilder, GroupChatState

def pick_next(state: GroupChatState) -> str:
    names = list(state.participants.keys())
    return names[state.current_round % len(names)]

workflow = GroupChatBuilder(
    participants=[writer_agent, fact_checker_agent, critic_agent],
    selection_func=pick_next,
    termination_condition=lambda conversation: "APPROVED" in conversation[-1].text,
).build()
```

### 6. Magentic orchestration: a manager with a ledger

Group chat with a model as manager works for short discussions, but on open-ended tasks it drifts: the manager forgets the plan, agents repeat themselves, and nobody notices the team is stuck. **Magentic orchestration** fixes this by making the manager keep two written records. It comes from **Magentic-One**, a generalist multi-agent system published by Microsoft Research in late 2024 with an Orchestrator agent directing a web surfer, a file surfer, a coder and a computer terminal. It now ships as a pattern in Microsoft Agent Framework.

**The task ledger** is written once at the start and rewritten when the team gets stuck. It has a fact sheet (facts given in the request, facts to look up, facts to derive, educated guesses) and a short plan.

**The progress ledger** is written every round. In Magentic-One it is a small JSON object answering five questions:

```json
{
  "is_request_satisfied":   {"reason": "We have the fare but not the seat availability.", "answer": false},
  "is_in_loop":             {"reason": "Each search returned new information.",          "answer": false},
  "is_progress_being_made": {"reason": "We found the Rajdhani fare in the last round.",    "answer": true},
  "next_speaker":           {"reason": "Availability needs the booking site.",             "answer": "WebSurfer"},
  "instruction_or_question": {"reason": "Be precise about class and date.",
                              "answer": "Open the IRCTC availability page for train 12951 on 14 Nov, 3A class, and report the waitlist number."}
}
```

The manager's loop is then simple and robust:

1. Read the ledgers and the thread; write a new progress ledger.
2. If the request is satisfied, write the final answer and stop.
3. If the team is looping or not progressing, add one to a **stall counter**. When the counter passes a limit, **rewrite the task ledger** (update facts and guesses, explain what went wrong, make a new plan) and reset.
4. Otherwise, send `instruction_or_question` to `next_speaker` and go round again.
5. Stop anyway if the maximum number of rounds or resets is reached.

Because the progress ledger is structured, you can validate it with Pydantic before trusting it. That turns "the manager wrote something odd" into a clean, retryable error.

```python
from pydantic import BaseModel

class BoolAnswer(BaseModel):
    reason: str
    answer: bool

class StrAnswer(BaseModel):
    reason: str
    answer: str

class ProgressLedger(BaseModel):
    is_request_satisfied: BoolAnswer
    is_in_loop: BoolAnswer
    is_progress_being_made: BoolAnswer
    next_speaker: StrAnswer
    instruction_or_question: StrAnswer

def ledger(done=False, loop=False, progress=True, speaker="WebSurfer", instruction=""):
    """Builds the JSON a manager model would write, so the example runs offline."""
    return {"is_request_satisfied": {"reason": "-", "answer": done},
            "is_in_loop": {"reason": "-", "answer": loop},
            "is_progress_being_made": {"reason": "-", "answer": progress},
            "next_speaker": {"reason": "-", "answer": speaker},
            "instruction_or_question": {"reason": "-", "answer": instruction}}

# What the manager model writes each round in this run.
MANAGER_OUTPUTS = [
    ledger(instruction="Find the 3A fare for train 12951 Mumbai-Delhi."),
    ledger(instruction="Find seat availability on 14 Nov."),
    ledger(loop=True, progress=False, instruction="Find seat availability on 14 Nov."),
    ledger(loop=True, progress=False, instruction="Find seat availability on 14 Nov."),
    ledger(speaker="Coder", instruction="Query the availability API with train=12951, date=2026-11-14, class=3A."),
    ledger(done=True, speaker="none"),
]

def magentic(max_rounds=10, max_stall=1, max_resets=2):
    plan_version, stalls, resets = 1, 0, 0
    for rnd, raw in enumerate(MANAGER_OUTPUTS[:max_rounds], start=1):
        pl = ProgressLedger.model_validate(raw)
        if pl.is_request_satisfied.answer:
            print(f"round {rnd}: request satisfied -> write final answer")
            return
        if pl.is_in_loop.answer or not pl.is_progress_being_made.answer:
            stalls += 1
            print(f"round {rnd}: stalled ({stalls})")
            if stalls > max_stall:
                resets += 1
                if resets > max_resets:
                    print("too many resets -> stop and report what we have")
                    return
                plan_version, stalls = plan_version + 1, 0
                print(f"         replan -> task ledger v{plan_version}: availability page blocks bots; try the API")
            continue
        stalls = 0
        print(f"round {rnd}: plan v{plan_version} -> {pl.next_speaker.answer}: {pl.instruction_or_question.answer}")

magentic()
```

Output:

```
round 1: plan v1 -> WebSurfer: Find the 3A fare for train 12951 Mumbai-Delhi.
round 2: plan v1 -> WebSurfer: Find seat availability on 14 Nov.
round 3: stalled (1)
round 4: stalled (2)
         replan -> task ledger v2: availability page blocks bots; try the API
round 5: plan v2 -> Coder: Query the availability API with train=12951, date=2026-11-14, class=3A.
round 6: request satisfied -> write final answer
```

The run shows the pattern's value: after two rounds without progress, the manager stops repeating itself, rewrites the plan with what it learned, and routes the work to a different specialist.

In Microsoft Agent Framework the same loop is configured rather than written:

```python
# not-run: needs the agent-framework package and model credentials
from agent_framework.orchestrations import MagenticBuilder

workflow = MagenticBuilder(
    participants=[researcher_agent, coder_agent],
    manager_agent=manager_agent,
    max_round_count=10,     # hard cap on coordination rounds
    max_stall_count=3,      # rounds without progress before replanning
    max_reset_count=2,      # replans allowed before giving up
    enable_plan_review=True,  # a human approves or revises the plan first
).build()
```

Microsoft's documentation is candid about one thing worth repeating: Magentic-One was tuned for its own four specialists, and how well the pattern works with your own agents is something you must measure. If you don't need planning and stall detection, a plain group chat is simpler.

### 7. Choosing between the patterns

| Your situation | Pattern |
|---|---|
| Independent pieces of work, results merged at the end | Orchestrator with subagents (concurrent) |
| A fixed series of stages | Sequential |
| The user should end up talking to the right specialist | Handoff |
| A few agents should critique and improve one artefact | Group chat with a clear stop rule |
| An open-ended goal where steps emerge as you go | Magentic, with round, stall and reset limits |
| A short, well-defined job | One agent |

Patterns also nest. A handoff system's billing agent can itself be an orchestrator with subagents; a Magentic manager's "coder" can be a single agent with helpers.

---

## Try It Yourself

1. **Make a ping-pong.** Change `pretend_model` so `refunds` always hands back to `triage` and `triage` always sends refund requests to `refunds`. Run `run_conversation` and check that the handoff limit stops it.
2. **Model-picked speakers.** Replace round robin in `group_chat` with a selector: the critic speaks right after every writer turn, and the fact-checker only speaks once, after the first draft.
3. **Stricter stall handling.** Run `magentic(max_stall=0, max_resets=1)`. How many replans happen before it gives up?

<details>
<summary>Show answers</summary>

**1.**

```python
def pretend_model(agent, history):
    if agent == "triage":
        return {"handoff": "refunds", "reason": "refund request"}
    if agent == "refunds":
        return {"handoff": "triage", "reason": "not my department"}

for who, text in run_conversation("refund please"):
    print(f"{who:>8}: {text}")
```

Output:

```
    user: refund please
  triage: [handoff -> refunds: refund request]
 refunds: [handoff -> triage: not my department]
  triage: [handoff -> refunds: refund request]
  system: too many handoffs; escalating to a human
```

**2.**

```python
def pick_speaker(thread):
    last = thread[-1][0]
    checked = any(who == "fact_checker" for who, _ in thread)
    if last == "writer" and not checked:
        return "fact_checker"
    if last in ("writer", "fact_checker"):
        return "critic"
    return "writer"

def group_chat_selected(task, max_rounds=9):
    thread = [("user", task)]
    for rnd in range(max_rounds):
        speaker = pick_speaker(thread)
        message = PARTICIPANTS[speaker](thread)
        thread.append((speaker, message))
        print(f"round {rnd + 1}: {speaker:<12} -> {message}")
        if message == "APPROVED":
            break

group_chat_selected("Write one sentence on UPI's scale, with a source.")
```

Output:

```
round 1: writer       -> Draft: UPI handled over 18 billion transactions in one month in 2025.
round 2: fact_checker -> The figure matches NPCI's published monthly statistics.
round 3: critic       -> Please name the source of the figure.
round 4: writer       -> Draft v2: UPI handled over 18 billion transactions in one month in 2025 (NPCI data).
round 5: critic       -> APPROVED
```

**3.**

```python
magentic(max_stall=0, max_resets=1)
```

Output:

```
round 1: plan v1 -> WebSurfer: Find the 3A fare for train 12951 Mumbai-Delhi.
round 2: plan v1 -> WebSurfer: Find seat availability on 14 Nov.
round 3: stalled (1)
         replan -> task ledger v2: availability page blocks bots; try the API
round 4: stalled (1)
too many resets -> stop and report what we have
```

With no tolerance for stalls, the first stalled round triggers a replan and the second exceeds the reset limit, so the run stops before trying the API. Limits that are too tight give up early; limits that are too loose burn tokens. Tune them on real traces.

</details>

---

## Real-World Examples

- **Customer support platforms** use handoffs from a triage agent to billing, returns and technical agents, with a route back to triage and an escalation path to a human.
- **OpenAI's Agents SDK** shipped handoffs as a core primitive, and many support-bot templates are built on exactly the triage-and-specialists shape.
- **Content review pipelines** use small group chats (writer, critic, compliance checker) with a strict approval phrase and a round cap.
- **Magentic-One** was evaluated by Microsoft Research on agentic benchmarks such as GAIA, AssistantBench and WebArena, and the pattern is now a built-in orchestration in Microsoft Agent Framework.

---

## Common Misconceptions

### "A handoff is just calling another agent"

Calling another agent as a tool keeps control with the caller. A handoff gives control away: the next agent answers the user and owns the task.

### "In a group chat, agents talk to each other freely"

Free-for-all chats are hard to control. Production group chats have a manager that picks every speaker and a stop rule that ends the chat.

### "Magentic is just group chat with a smarter manager"

The difference is the **written ledgers**: a plan and fact sheet that survive the conversation, and a per-round progress check that detects loops and triggers replanning.

### "Sharing the full conversation is always safer"

It is more convenient, but every agent then pays to read everything, and one agent's mistake or injected instruction reaches all of them. Filter what each agent sees.

---

## Interview Relevance

*"Compare handoffs and supervisor-style orchestration."* Handoffs move control to the receiving agent, which talks to the user and owns the task; routes should be restricted and capped. A supervisor (or agent-as-tool) keeps control, delegates sub-questions and composes the answer. Mention that both are implemented with tool calls, and that handoffs pass conversation history by default, with filters available.

*"How would you stop a multi-agent conversation from looping?"* Give concrete mechanisms: a round limit, a stop phrase or structured "done" signal, a handoff counter, and a Magentic-style progress ledger with stall counting and replanning, plus a hard cap on resets and a human escalation path.

---

## Key Takeaways

- **Handoff**: control moves via a `transfer_to_...` tool call; restrict the routes and cap the number of handoffs.
- **Group chat**: one shared thread, a manager that picks speakers, and a stop rule; keep it small because every turn re-reads the thread.
- **Magentic**: a planning manager with a task ledger and a per-round progress ledger; it detects stalls and replans within round, stall and reset limits.
- **LangGraph** implements handoffs with `Command(goto=...)`, and `graph=Command.PARENT` when agents are subgraphs.
- **Pick by control and visibility**: who should own the task, and who needs to see what.

---

**Up next:** [Failure Modes of Multi-Agent Systems](failure-modes-of-multi-agent-systems.md)
