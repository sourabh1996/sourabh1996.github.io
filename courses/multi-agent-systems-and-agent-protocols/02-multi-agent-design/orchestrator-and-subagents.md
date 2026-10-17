---
title: "Orchestrator and Subagents"
course: "Multi-Agent Systems and Agent Protocols"
module: "2. Multi-Agent Design"
type: Article
level: Advanced
reading_time: 34 min
---

# Orchestrator and Subagents: The Complete Guide

> 📚 **Before you start**
>
> - [When Multiple Agents Help and When They Hurt](when-multiple-agents-help-and-when-they-hurt.md), for why fresh context windows and parallel work are the reasons to split.
> - [Parallel Workflows](../../langgraph-complete-guide/03-workflow-patterns-in-langgraph/parallel-workflows.md), for LangGraph's `Send` and fan-out with a reducer.
> - [Function Calling Step by Step](../../agentic-ai-fundamentals/04-tools-and-function-calling/function-calling-step-by-step.md), because the lead agent usually starts subagents through a tool call.

## Introduction

A chartered accountant's firm gets a big audit: a company with offices in Pune, Chennai and Kolkata. The partner doesn't fly to all three cities and read every ledger. She writes a one-page brief for each junior team ("Check Chennai's inventory records for March; flag any stock write-off above ₹5 lakh; send me a one-page summary by Friday with page references"), sends three teams out at once, and then reads three one-page summaries. If something looks odd, she asks for the page reference and reads that page herself.

That is the **orchestrator and subagents** pattern, also called **orchestrator-workers** or **lead agent and subagents**. One lead agent plans, writes briefs and merges results. Several subagents each take one brief, work in their own fresh context window, and report back something short. It is the most widely used multi-agent pattern in production, and the one behind most "deep research" features.

The pattern sounds simple, and its success depends almost entirely on details: how the brief is written, how much effort each subagent is allowed, what comes back and in what form, and how the lead checks the result. This lesson covers each of those, then builds a working orchestrator in LangGraph and shows the same idea in real agent SDKs.

> 💡 **Key Insight**
>
> The lead agent's real job is **delegation**: writing briefs that a subagent with zero background can follow, and **condensation**: getting back short, checkable results instead of raw notes. Most failures of this pattern are bad briefs or bloated returns, not bad subagents.

---

## Core Explanation

### 1. The architecture

![The orchestrator pattern. A user asks the lead agent to compare three EV makers. The lead saves its plan to memory and sets an effort budget, then fans task briefs out to three subagents in parallel, each with a fresh window and web search. Subagents save full notes to a shared store and return short summaries with references to a verify-and-cite step, which produces the final report](/img/diagrams/multi-agent-systems-and-agent-protocols/orchestrator-subagents.svg)
*The lead never reads the raw search results. It reads short summaries and can follow a reference when it needs detail.*

| Part | Job | Typical model |
|---|---|---|
| **Lead agent (orchestrator)** | Understands the request, plans, decides how many subagents to start, writes their briefs, merges results, decides when to stop | The strongest model you can afford, because planning and judging are hard |
| **Subagents (workers)** | Do one focused piece of work with their own tools in a fresh context window; return a condensed result | Often a faster, cheaper model |
| **Shared store** | Holds full notes, files and data so they don't have to travel through the lead's context | A file system, database or object store |
| **Verifier** | Checks claims against sources, removes duplicates, adds citations | Another agent, or code |
| **Memory for the plan** | Keeps the plan safe if the lead's context gets compacted on a long run | A file or memory store |

The defining property: **subagents don't talk to each other**. Everything flows through the lead (or the store). That keeps coordination simple and is the main difference from the group chat pattern in the next lesson.

### 2. Writing a task brief a subagent can follow

A subagent knows nothing except its own system prompt and the brief. It has not seen the user's question, the conversation, or what the other subagents are doing. Anthropic's write-up on their research system described early versions where the lead gave briefs like "research the semiconductor shortage", and several subagents duplicated each other's work or chased the wrong period. Their fix was to teach the lead to delegate properly.

A good brief has six parts:

| Part | Question it answers | Example |
|---|---|---|
| **Objective** | What exactly should you find out or do? | "Find Tata Motors' EV sales volumes in India for FY2024-25 and FY2025-26." |
| **Why** | What is this for? | "Part of a comparison of three EV makers for an investor note." |
| **Scope and boundaries** | What should you *not* do? Who covers the rest? | "Only Tata. Mahindra and MG are covered by other agents. Ignore two-wheelers." |
| **Sources and tools** | Where to look, what to trust | "Prefer company filings and SIAM data over news articles." |
| **Output format** | What exactly should you return? | "At most 200 words, then a JSON list of facts with source URLs." |
| **Budget** | How much effort? When to stop? | "At most 8 searches. Stop early if two independent sources agree." |

Let's make that concrete. The brief is just text, but building it from a structure means no part gets forgotten.

```python
from dataclasses import dataclass, field

@dataclass
class TaskBrief:
    objective: str
    why: str
    boundaries: list = field(default_factory=list)
    sources: str = ""
    output_format: str = ""
    max_tool_calls: int = 8

    def render(self):
        lines = [f"OBJECTIVE: {self.objective}", f"WHY: {self.why}"]
        lines += [f"DO NOT: {b}" for b in self.boundaries]
        lines += [f"SOURCES: {self.sources}", f"RETURN: {self.output_format}",
                  f"BUDGET: at most {self.max_tool_calls} tool calls; stop early when two independent sources agree."]
        return "\n".join(lines)

bad_brief = "Research Tata EVs."

good_brief = TaskBrief(
    objective="Find Tata Motors' passenger EV sales volumes in India for FY2024-25 and FY2025-26.",
    why="Part of a three-company comparison for an investor note.",
    boundaries=["research Mahindra or MG (other agents cover them)", "include two-wheelers or exports"],
    sources="Prefer company filings and SIAM/Vahan data over news articles.",
    output_format="Max 200 words, then a JSON list of facts, each with a source URL.",
)

print("BAD :", bad_brief)
print()
print(good_brief.render())
```

Output:

```
BAD : Research Tata EVs.

OBJECTIVE: Find Tata Motors' passenger EV sales volumes in India for FY2024-25 and FY2025-26.
WHY: Part of a three-company comparison for an investor note.
DO NOT: research Mahindra or MG (other agents cover them)
DO NOT: include two-wheelers or exports
SOURCES: Prefer company filings and SIAM/Vahan data over news articles.
RETURN: Max 200 words, then a JSON list of facts, each with a source URL.
BUDGET: at most 8 tool calls; stop early when two independent sources agree.
```

Notice the **boundaries** line. Telling a subagent what the other subagents are doing is the cheapest fix for duplicated work.

### 3. Scaling effort to the question

A lead agent with no guidance tends to over-delegate: Anthropic reported early versions spawning **50 subagents for simple queries**. Their fix was explicit effort rules in the lead's prompt. Their published rule of thumb:

| Kind of request | Subagents | Tool calls each |
|---|---|---|
| Simple fact-finding | 1 | 3 to 10 |
| Direct comparison | 2 to 4 | 10 to 15 |
| Complex research | more than 10, with clearly divided jobs | as needed |

Encoding this as code (or as plain rules in the prompt) gives the lead a budget to plan against:

```python
def effort_plan(kind, parts=1):
    if kind == "fact":
        return {"subagents": 1, "calls_each": (3, 10)}
    if kind == "comparison":
        return {"subagents": max(2, min(parts, 4)), "calls_each": (10, 15)}
    if kind == "complex":
        return {"subagents": max(10, parts), "calls_each": (10, 20)}
    raise ValueError(f"unknown kind: {kind}")

for kind, parts in [("fact", 1), ("comparison", 3), ("comparison", 7), ("complex", 12)]:
    print(f"{kind:<10} parts={parts:<2} -> {effort_plan(kind, parts)}")
```

Output:

```
fact       parts=1  -> {'subagents': 1, 'calls_each': (3, 10)}
comparison parts=3  -> {'subagents': 3, 'calls_each': (10, 15)}
comparison parts=7  -> {'subagents': 4, 'calls_each': (10, 15)}
complex    parts=12 -> {'subagents': 12, 'calls_each': (10, 20)}
```

Note the comparison of seven things still gets at most four subagents: past that point, it's usually better to give each subagent a group of items than to start more agents.

### 4. Building an orchestrator in LangGraph

Now a working orchestrator. LangGraph's `Send` lets one node start any number of copies of another node in parallel, each with its own input. That maps perfectly onto "the lead fans out briefs, each subagent works alone". A list field with the `operator.add` reducer collects the results.

The subagents here use a pretend search tool with canned pages so the example runs offline. Each subagent does the two things a real one must: it **saves full notes to the shared store** and **returns only a short summary and a reference**.

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

# Pretend web pages a search tool would return.
PAGES = {
    "Tata": ["Tata Motors sells the Nexon.ev, Punch.ev and Curvv.ev in India.",
             "Tata was India's largest passenger EV seller for several years.",
             "New launches by rivals have cut into Tata's EV market share."],
    "Mahindra": ["Mahindra launched the BE 6 and XEV 9e electric SUVs in 2025.",
                 "Both models are built on Mahindra's INGLO electric platform."],
    "MG": ["JSW MG's Windsor EV was among India's best-selling EVs in 2025.",
           "MG offers a battery-rental option on the Windsor."],
}
STORE = {}   # the shared store: full notes live here, not in the lead's context

class Finding(TypedDict):
    company: str
    summary: str
    ref: str
    sources_read: int

class TeamState(TypedDict):
    question: str
    companies: list
    findings: Annotated[list, operator.add]   # each subagent appends one Finding
    report: str

class SubagentInput(TypedDict):
    company: str
    brief: str

def lead_plan(state: TeamState):
    """The lead decides the split. A real lead is a model call that writes the briefs."""
    return {"companies": ["Tata", "Mahindra", "MG"]}

def fan_out(state: TeamState):
    return [Send("subagent", {"company": c,
                              "brief": f"Find {c}'s EV position in India. Only {c}. Max 3 searches."})
            for c in state["companies"]]

def subagent(inp: SubagentInput):
    pages = PAGES[inp["company"]][:3]              # obey the budget in the brief
    ref = f"store://notes/{inp['company'].lower()}"
    STORE[ref] = "\n".join(pages)                  # full notes go to the store
    summary = pages[0]                             # a real subagent would summarise with a model
    return {"findings": [{"company": inp["company"], "summary": summary,
                          "ref": ref, "sources_read": len(pages)}]}

def lead_synthesise(state: TeamState):
    rows = sorted(state["findings"], key=lambda f: f["company"])   # parallel results arrive in any order
    lines = [f"- {f['company']}: {f['summary']} [{f['ref']}]" for f in rows]
    return {"report": "EV makers in India:\n" + "\n".join(lines)}

builder = StateGraph(TeamState)
builder.add_node("lead_plan", lead_plan)
builder.add_node("subagent", subagent)
builder.add_node("lead_synthesise", lead_synthesise)
builder.add_edge(START, "lead_plan")
builder.add_conditional_edges("lead_plan", fan_out, ["subagent"])
builder.add_edge("subagent", "lead_synthesise")
builder.add_edge("lead_synthesise", END)
team = builder.compile()

result = team.invoke({"question": "Compare EV makers in India", "findings": []})
print(result["report"])
print()
print("Sources read by subagents:", sum(f["sources_read"] for f in result["findings"]))
print("Notes kept in the store  :", sorted(STORE))
```

Output:

```
EV makers in India:
- MG: JSW MG's Windsor EV was among India's best-selling EVs in 2025. [store://notes/mg]
- Mahindra: Mahindra launched the BE 6 and XEV 9e electric SUVs in 2025. [store://notes/mahindra]
- Tata: Tata Motors sells the Nexon.ev, Punch.ev and Curvv.ev in India. [store://notes/tata]

Sources read by subagents: 7
Notes kept in the store  : ['store://notes/mahindra', 'store://notes/mg', 'store://notes/tata']
```

Three things to notice:

- **The lead's context only ever holds three one-line summaries.** The full notes sit in `STORE` under references like `store://notes/tata`. If the lead needs detail, it can read one reference; it never has to carry all of them.
- **Results are sorted before use.** Parallel subagents finish in any order, so anything that depends on order must sort first.
- **The fan-out is dynamic.** If the lead decided on five companies, `Send` would start five subagents with no change to the graph.

### 5. Returning references instead of raw content

Anthropic's write-up describes a refinement worth copying: subagents write bulky outputs (code, long tables, full notes) **directly to a file system or store** and pass back a lightweight reference, so large content doesn't go through the lead's context as a game of telephone. The lead reads the reference only if needed.

```python
def read_ref(ref, max_chars=200):
    """What a 'read_note' tool would give the lead: a bounded slice of a stored note."""
    note = STORE[ref]
    return note if len(note) <= max_chars else note[:max_chars] + " ...[truncated]"

lead_context_chars = sum(len(f["summary"]) for f in result["findings"])
store_chars = sum(len(v) for v in STORE.values())
print(f"Characters in the lead's context : {lead_context_chars}")
print(f"Characters kept in the store     : {store_chars}")
print()
print("Lead follows one reference:")
print(read_ref("store://notes/mg"))
```

Output:

```
Characters in the lead's context : 186
Characters kept in the store     : 422

Lead follows one reference:
JSW MG's Windsor EV was among India's best-selling EVs in 2025.
MG offers a battery-rental option on the Windsor.
```

With three short pages the difference is small. With real subagents reading 50,000 tokens each, the gap is the whole point of the pattern.

### 6. Subagents as tools

In many frameworks the lead doesn't use a graph at all. It is an ordinary agent loop whose tool list includes **"start a subagent"**. The model writes a tool call with a brief as its input; your code runs a subagent and returns its final message as the tool result. Here is what such a tool definition looks like:

```json
{
  "name": "delegate_research",
  "description": "Start a research subagent with a fresh context. Use for one self-contained question. Write a complete brief: objective, scope, sources, output format and budget. The subagent cannot see this conversation.",
  "input_schema": {
    "type": "object",
    "properties": {
      "brief": {"type": "string", "description": "Complete, self-contained task brief"},
      "max_tool_calls": {"type": "integer", "minimum": 1, "maximum": 20}
    },
    "required": ["brief"]
  }
}
```

The description does a lot of work: it tells the lead that the subagent **cannot see the conversation**, which pushes the model to write complete briefs.

Models can emit several tool calls in one turn, so the lead can start subagents in parallel. Your loop runs them concurrently and returns the results in the same order as the calls:

```python
from concurrent.futures import ThreadPoolExecutor

def run_subagent(brief, max_tool_calls=3):
    company = brief.split()[1].rstrip("'s")        # pretend parsing; a real subagent is an agent loop
    pages = PAGES[company][:max_tool_calls]
    return f"{company}: {pages[0]} (read {len(pages)} pages)"

# One assistant turn from the lead containing three parallel tool calls.
lead_turn = [
    {"id": "call_1", "name": "delegate_research", "input": {"brief": "Research Tata's EV sales. Only Tata."}},
    {"id": "call_2", "name": "delegate_research", "input": {"brief": "Research Mahindra's EV launches. Only Mahindra."}},
    {"id": "call_3", "name": "delegate_research", "input": {"brief": "Research MG's EV pricing. Only MG.", "max_tool_calls": 2}},
]

with ThreadPoolExecutor(max_workers=3) as pool:
    futures = [pool.submit(run_subagent, **call["input"]) for call in lead_turn]
    tool_results = [{"tool_use_id": call["id"], "content": f.result()} for call, f in zip(lead_turn, futures)]

for r in tool_results:
    print(r["tool_use_id"], "->", r["content"])
```

Output:

```
call_1 -> Tata: Tata Motors sells the Nexon.ev, Punch.ev and Curvv.ev in India. (read 3 pages)
call_2 -> Mahindra: Mahindra launched the BE 6 and XEV 9e electric SUVs in 2025. (read 2 pages)
call_3 -> MG: JSW MG's Windsor EV was among India's best-selling EVs in 2025. (read 2 pages)
```

This "agents as tools" style is what most agent SDKs give you out of the box.

### 7. The same pattern in real SDKs

**Claude Agent SDK.** Subagents are declared with `AgentDefinition` and the main agent starts them through its built-in `Agent` tool. Each subagent gets a fresh context containing its own prompt and the brief the main agent writes; only its final message returns.

```python
# not-run: needs the claude-agent-sdk package and an API key
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

researcher = AgentDefinition(
    description="Researches ONE company. Give it a complete brief; it cannot see this conversation.",
    prompt="You research a single company. Return at most 200 words, then a list of facts with source URLs.",
    tools=["WebSearch", "WebFetch"],
    model="sonnet",
)

async def main():
    async for message in query(
        prompt="Compare Tata, Mahindra and MG on EV sales in India. Use one researcher per company, in parallel.",
        options=ClaudeAgentOptions(
            allowed_tools=["WebSearch", "WebFetch", "Agent"],
            agents={"company-researcher": researcher},
            max_budget_usd=2.0,
        ),
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

The SDK also lets you cap how deep subagents may nest, how many run at once and how much the whole query may spend, which directly addresses the "50 subagents" failure.

**OpenAI Agents SDK.** Any agent can be turned into a tool for another agent with `as_tool`. Control stays with the calling agent, which receives the sub-agent's output as a tool result.

```python
# not-run: needs the openai-agents package and an API key
from agents import Agent, Runner

tata = Agent(name="Tata researcher", instructions="Research only Tata Motors' EV business in India.")
mg = Agent(name="MG researcher", instructions="Research only JSW MG Motor's EV business in India.")

lead = Agent(
    name="Lead analyst",
    instructions="Plan the comparison, call each researcher tool once, then write a 5-line summary.",
    tools=[
        tata.as_tool(tool_name="research_tata", tool_description="Research Tata's EV business."),
        mg.as_tool(tool_name="research_mg", tool_description="Research MG's EV business."),
    ],
)
result = Runner.run_sync(lead, "Compare Tata and MG on EVs in India.")
print(result.final_output)
```

**LangChain Deep Agents** (built on LangGraph) gives its main agent a `task` tool that starts subagents with their own context, alongside a to-do list and a virtual file system for exactly the "write notes to a store, pass a reference" idea above. You'll meet it properly in [Agent Frameworks and SDKs](../../agent-frameworks-and-sdks/course.md#m3).

### 8. Verifying and citing at the end

When results come back, the lead must not simply paste them together. A dedicated **verification step** should:

1. **Remove duplicates** (two subagents found the same fact).
2. **Check claims against their sources** (a summary can drift from what the page said).
3. **Flag conflicts** (one source says 61,000 units, another 65,000) instead of silently picking one.
4. **Attach citations** to every claim that survives.

Anthropic's system uses a separate citation agent for step 4. Steps 1 and 3 can often be plain code over the structured facts subagents return, which is one more reason to ask for structured output in the brief.

```python
facts = [   # made-up figures, to show a conflict between two sources
    {"claim": "Tata sold about 61,000 EVs in FY2024-25", "source": "report.example/ev", "by": "A"},
    {"claim": "Tata sold about 61,000 EVs in FY2024-25", "source": "report.example/ev", "by": "B"},
    {"claim": "Tata sold about 65,000 EVs in FY2024-25", "source": "news.example/tata", "by": "A"},
    {"claim": "MG Windsor was a top-selling EV in 2025", "source": "registrations.example", "by": "C"},
]

unique = {(f["claim"], f["source"]): f for f in facts}.values()
by_topic = {}
for f in unique:
    topic = " ".join(f["claim"].split()[:2])            # crude topic key: "Tata sold", "MG Windsor"
    by_topic.setdefault(topic, set()).add(f["claim"])

print(f"{len(facts)} facts in, {len(unique)} after removing duplicates")
for topic, claims in sorted(by_topic.items()):
    status = "CONFLICT, needs a check" if len(claims) > 1 else "ok"
    print(f"{topic:<11} {status}")
```

Output:

```
4 facts in, 3 after removing duplicates
MG Windsor  ok
Tata sold   CONFLICT, needs a check
```

### 9. Long runs: protect the plan

A complex research run can exceed one context window even for the lead. Anthropic's lead agent saves its plan to memory early, because if the context is compacted or truncated later, a plan that only lived in the conversation is lost. The same applies to your orchestrator: **write the plan, the list of briefs sent and the references received to durable state** (a LangGraph checkpoint or a file), so a crash or compaction doesn't send the lead back to square one.

---

## Try It Yourself

1. **Add a fourth company.** Add `"Hyundai"` with two pretend pages to `PAGES`, change `lead_plan` to include it, and rerun the graph. Did you need to change any edges?
2. **Enforce the budget.** Change `subagent` so it reads the number after "Max" in its brief instead of the hard-coded `3`. Send MG a brief with "Max 1 searches" and check `sources_read`.
3. **Improve a brief.** Rewrite `"Find out about UPI fraud"` as a `TaskBrief` for one of three subagents (the others cover RBI rules and bank-side controls).

<details>
<summary>Show answers</summary>

**1.**

```python
PAGES["Hyundai"] = ["Hyundai launched the Creta Electric in January 2025.",
                    "The Creta Electric is made at Hyundai's plant near Chennai."]

def lead_plan(state: TeamState):
    return {"companies": ["Tata", "Mahindra", "MG", "Hyundai"]}

builder = StateGraph(TeamState)
builder.add_node("lead_plan", lead_plan)
builder.add_node("subagent", subagent)
builder.add_node("lead_synthesise", lead_synthesise)
builder.add_edge(START, "lead_plan")
builder.add_conditional_edges("lead_plan", fan_out, ["subagent"])
builder.add_edge("subagent", "lead_synthesise")
builder.add_edge("lead_synthesise", END)
print(builder.compile().invoke({"question": "Compare EV makers", "findings": []})["report"])
```

Output:

```
EV makers in India:
- Hyundai: Hyundai launched the Creta Electric in January 2025. [store://notes/hyundai]
- MG: JSW MG's Windsor EV was among India's best-selling EVs in 2025. [store://notes/mg]
- Mahindra: Mahindra launched the BE 6 and XEV 9e electric SUVs in 2025. [store://notes/mahindra]
- Tata: Tata Motors sells the Nexon.ev, Punch.ev and Curvv.ev in India. [store://notes/tata]
```

No edges changed: `Send` creates one subagent per item, however many there are.

**2.**

```python
import re

def subagent(inp: SubagentInput):
    limit = int(re.search(r"Max (\d+)", inp["brief"]).group(1))
    pages = PAGES[inp["company"]][:limit]
    ref = f"store://notes/{inp['company'].lower()}"
    STORE[ref] = "\n".join(pages)
    return {"findings": [{"company": inp["company"], "summary": pages[0], "ref": ref, "sources_read": len(pages)}]}

print(subagent({"company": "MG", "brief": "Find MG's EV position. Only MG. Max 1 searches."}))
```

Output:

```
{'findings': [{'company': 'MG', 'summary': "JSW MG's Windsor EV was among India's best-selling EVs in 2025.", 'ref': 'store://notes/mg', 'sources_read': 1}]}
```

**3.**

```python
upi = TaskBrief(
    objective="Describe the three most common UPI fraud methods reported in India in 2025-26, with one real example each.",
    why="One part of a briefing on UPI fraud for a bank's customer-education team.",
    boundaries=["cover RBI regulations (another agent does)", "cover bank-side technical controls (another agent does)"],
    sources="Prefer NPCI, RBI and CERT-In publications; use news only for examples.",
    output_format="Max 250 words, then a JSON list of {method, example, source_url}.",
    max_tool_calls=10,
)
print(upi.render())
```

Output:

```
OBJECTIVE: Describe the three most common UPI fraud methods reported in India in 2025-26, with one real example each.
WHY: One part of a briefing on UPI fraud for a bank's customer-education team.
DO NOT: cover RBI regulations (another agent does)
DO NOT: cover bank-side technical controls (another agent does)
SOURCES: Prefer NPCI, RBI and CERT-In publications; use news only for examples.
RETURN: Max 250 words, then a JSON list of {method, example, source_url}.
BUDGET: at most 10 tool calls; stop early when two independent sources agree.
```

</details>

---

## Real-World Examples

- **Claude's Research feature** uses a lead agent that plans, starts parallel subagents with separate context windows and combines their findings, with a final citation step.
- **Claude Code** lets the main agent start subagents (for example, an explorer that searches a large codebase) whose intermediate tool calls never enter the main conversation.
- **LangChain Deep Agents** combines a planning to-do list, a virtual file system for notes and a `task` tool for subagents, which is this lesson's architecture packaged as a library.
- **Due diligence and market research tools** in finance and consulting fan out one subagent per company or document, then verify and merge.

---

## Common Misconceptions

### "Subagents should see the whole conversation, to be safe"

That throws away the main benefit (a clean, focused context) and multiplies token cost. Give each subagent a complete **brief**, not the whole history. When a subtask truly needs the full history, it probably shouldn't be a subagent.

### "More subagents means more thorough research"

Past a handful, more subagents mostly means more duplication and more merging work. Scale effort to the question and give each subagent a clearly separated piece.

### "The lead should paste subagent outputs into the answer"

Subagent outputs are raw material. The lead must deduplicate, check, resolve conflicts and cite before anything reaches the user.

### "Subagents can coordinate among themselves"

In this pattern they don't; all coordination goes through the lead or the shared store. If you need agents to react to each other's messages, that's the group chat pattern, with its own costs.

---

## Interview Relevance

*"Design a deep research agent."* A strong answer describes a lead agent that classifies the request and sets an effort budget, writes complete briefs (objective, scope and boundaries, sources, output format, budget), fans out subagents in parallel with fresh context windows and restricted tools, has them store bulky output externally and return short summaries plus references, then runs a verification and citation step. It mentions limits on subagent count, depth and spend; sorting or keying parallel results; saving the plan to durable memory for long runs; and evaluating with an LLM judge plus human spot checks.

*"Why not just give one agent all the tools?"* Because one agent would read every source into one window (context rot and cost), work sequentially (latency), and hold every permission. The orchestrator pattern trades extra tokens for clean context, parallel speed and least privilege.

---

## Key Takeaways

- **The lead delegates and condenses**: it plans, writes briefs, merges, verifies and decides when to stop.
- **A brief has six parts**: objective, why, boundaries, sources, output format and budget. Boundaries prevent duplicated work.
- **Scale effort to the question**: one subagent for a fact, a few for a comparison, many only for complex research.
- **Return references, not raw content**: bulky notes go to a shared store; the lead reads a slice only when needed.
- **Verify before answering**: deduplicate, flag conflicts and cite every claim.

---

**Up next:** [Handoffs, Group Chat and Magentic Orchestration](handoffs-group-chat-and-magentic-orchestration.md)
