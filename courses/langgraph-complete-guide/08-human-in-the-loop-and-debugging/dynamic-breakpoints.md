---
title: "Dynamic Breakpoints"
course: "LangGraph Complete Guide"
module: "8. Human-in-the-Loop and Debugging"
type: Article
level: Intermediate
reading_time: 30 min
---

# Dynamic Breakpoints: The Complete Guide

> 📚 **Before you start**
>
> - [Breakpoints](breakpoints.md), the static kind this lesson makes conditional.
> - [Pausing with interrupt and Resuming with Command](pausing-with-interrupt-and-resuming-with-command.md), especially the rule that a node re-runs from the top when resumed.
> - [Editing State with Human Input](editing-state-with-human-input.md), for `update_state` and the tool-call review node.

## Introduction

A UPI app doesn't ask for your PIN twice for every ₹20 chai. But send ₹50,000 to someone you've never paid before, late at night, and it slows down: a warning, a cooling-off period, an extra confirmation. The **same action** gets a different amount of friction depending on **the situation**.

That's a dynamic breakpoint: a pause that happens **only when the state says it should**. Static breakpoints (module 2) stop at a node every time, which is perfect for debugging and annoying in production. A good human-in-the-loop design asks rarely and precisely: high amounts, new payees, low model confidence, sensitive words, a policy violation. Everything else flows through untouched.

In LangGraph, the old way to do this was to raise a special `NodeInterrupt` exception inside a node. That exception is now **deprecated**; the current way is simply to call `interrupt()` inside an `if`. This lesson shows both (so you recognise the old one in tutorials), then covers writing pause policies, pausing inside tools and its surprising re-run behaviour, validation loops that ask again until an answer is acceptable, and choosing breakpoints per call.

> 💡 **Key Insight**
>
> A dynamic breakpoint is just `interrupt()` behind a condition. The condition must depend only on things that are the **same every time the node runs** (the state, the config, fixed rules), because a resumed node runs again from the top and must reach the same `interrupt()` calls in the same order.

---

## Core Explanation

### 1. The old way: `NodeInterrupt` (deprecated)

Older tutorials (and the "Dynamic Breakpoints" lessons of many courses) raise `NodeInterrupt` from a node when a condition holds:

```python
import operator
import warnings
from typing import Annotated, Literal, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import NodeInterrupt
from langgraph.types import interrupt, Command

class Payment(TypedDict):
    payee: str
    amount: float
    log: Annotated[list, operator.add]

def pay_old_style(state: Payment):
    if state["amount"] > 10_000:
        raise NodeInterrupt(f"₹{state['amount']:,.0f} to {state['payee']} needs approval")
    return {"log": [f"paid ₹{state['amount']:,.0f}"]}

b = StateGraph(Payment)
b.add_node("pay", pay_old_style)
b.add_edge(START, "pay")
old = b.compile(checkpointer=InMemorySaver())
cfg = {"configurable": {"thread_id": "old-1"}}

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    out = old.invoke({"payee": "Sai Electricals", "amount": 25000.0, "log": []}, cfg)
dep = next(w for w in caught if issubclass(w.category, DeprecationWarning))  # skip unrelated warnings
print(dep.category.__name__, "-", str(dep.message).split(".")[0])
print("paused with:", out["__interrupt__"][0].value, "| next:", old.get_state(cfg).next)
```

Output:

```
LangGraphDeprecatedSinceV10 - NodeInterrupt is deprecated
paused with: ₹25,000 to Sai Electricals needs approval | next: ('pay',)
```

It still works in LangGraph 1.2, with a deprecation warning saying it will be removed in 2.0. Its weakness shows when you try to continue: the human can't send an answer, so resuming just runs the node again, which raises again. The only way through was to **change the state** so the condition no longer held:

```python
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    again = old.invoke(None, cfg)
    print("resume with None -> paused again:", "__interrupt__" in again)
    old.update_state(cfg, {"amount": 9999.0})       # e.g. a manager lowers the amount
    print(old.invoke(None, cfg)["log"])
```

Output:

```
resume with None -> paused again: True
['paid ₹9,999']
```

There's no clean way to say "approved, pay the full ₹25,000". That's why `interrupt()` replaced it.

### 2. The current way: `interrupt()` behind a condition

The same rule with `interrupt()`, which can pause **and** receive an answer:

```python
paid = []

def pay(state: Payment):
    if state["amount"] > 10_000:
        answer = interrupt({"question": "Approve this payment?", "payee": state["payee"],
                            "amount": state["amount"]})
        if answer != "approve":
            return {"log": [f"blocked: {answer}"]}
    paid.append(state["amount"])
    return {"log": [f"paid ₹{state['amount']:,.0f}"]}

b = StateGraph(Payment)
b.add_node(pay)
b.add_edge(START, "pay")
payments = b.compile(checkpointer=InMemorySaver())

def attempt(thread, amount, answer=None):
    c = {"configurable": {"thread_id": thread}}
    out = payments.invoke({"payee": "Sai Electricals", "amount": amount, "log": []}, c)
    paused = "__interrupt__" in out
    if paused:
        out = payments.invoke(Command(resume=answer), c)
    return paused, out["log"]

print(attempt("p-small", 4500.0))
print(attempt("p-big-ok", 25000.0, "approve"))
print(attempt("p-big-no", 60000.0, "not in this month's budget"))
print("paid:", paid)
```

Output:

```
(False, ['paid ₹4,500'])
(True, ['paid ₹25,000'])
(True, ["blocked: not in this month's budget"])
paid: [4500.0, 25000.0]
```

Small payments never paused; large ones paused, carried a clear question, and continued according to the answer. Note that `paid.append` comes **after** the `interrupt()`, so it runs once.

### 3. Writing a pause policy

Real rules are rarely one `if`. Put them in a small **policy function** that returns the reasons a human is needed (empty means "no"). It keeps the node short, is easy to unit-test, and its output is exactly what a reviewer wants to read:

```python
KNOWN_PAYEES = {"Sai Electricals", "BESCOM", "Airtel"}

class Transfer(TypedDict):
    payee: str
    amount: float
    hour: int
    log: Annotated[list, operator.add]

def review_reasons(state: Transfer) -> list[str]:
    reasons = []
    if state["amount"] > 10_000:
        reasons.append(f"amount ₹{state['amount']:,.0f} is above ₹10,000")
    if state["payee"] not in KNOWN_PAYEES:
        reasons.append(f"first payment to {state['payee']}")
    if state["hour"] >= 23 or state["hour"] < 6:
        reasons.append("late-night transfer")
    return reasons

for case in [{"payee": "BESCOM", "amount": 1840.0, "hour": 10},
             {"payee": "Unknown Traders", "amount": 15000.0, "hour": 23}]:
    print(case["payee"], "->", review_reasons(case))
```

Output:

```
BESCOM -> []
Unknown Traders -> ['amount ₹15,000 is above ₹10,000', 'first payment to Unknown Traders', 'late-night transfer']
```

```python
def guarded_transfer(state: Transfer):
    reasons = review_reasons(state)
    if reasons:
        answer = interrupt({"question": "Approve this transfer?", "reasons": reasons,
                            "payee": state["payee"], "amount": state["amount"]})
        if answer != "approve":
            return {"log": [f"blocked ({answer})"]}
    return {"log": [f"sent ₹{state['amount']:,.0f} to {state['payee']}"]}

b = StateGraph(Transfer)
b.add_node(guarded_transfer)
b.add_edge(START, "guarded_transfer")
transfers = b.compile(checkpointer=InMemorySaver())

c = {"configurable": {"thread_id": "t-night"}}
out = transfers.invoke({"payee": "Unknown Traders", "amount": 15000.0, "hour": 23, "log": []}, c)
print(out["__interrupt__"][0].value["reasons"])
print(transfers.invoke(Command(resume="approve"), c)["log"])
```

Output:

```
['amount ₹15,000 is above ₹10,000', 'first payment to Unknown Traders', 'late-night transfer']
['sent ₹15,000 to Unknown Traders']
```

Because `review_reasons` depends only on the state, it returns the same reasons when the node re-runs on resume, so the `interrupt()` call is reached again in the same position. Don't base the decision on `datetime.now()` inside the node: if the clock crosses 6 am between the pause and the resume, the re-run node would skip the `interrupt()` and the human's answer would be lost. Put the hour **in the state** (as here), set once when the request arrives.

### 4. Pausing inside a tool, and the re-run surprise

`interrupt()` also works inside a tool function run by `ToolNode`, which makes the tool itself responsible for its own safety check. But remember the big rule: on resume, the **node** re-runs from the top, and here the node is the whole `ToolNode`, which runs **every tool call** in the model's message:

```python
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

executed = []

@tool
def send_upi(upi_id: str, amount: float) -> str:
    """Send money over UPI."""
    if amount > 10_000:
        if interrupt({"confirm": f"Send ₹{amount:,.0f} to {upi_id}?"}) != "yes":
            return "Cancelled by the user."
    executed.append((upi_id, amount))
    return f"Sent ₹{amount:,.0f} to {upi_id}"

class ToolFake(GenericFakeChatModel):
    """A scripted chat model that accepts bind_tools, for offline examples."""
    def bind_tools(self, tools, **kwargs):
        return self

llm = ToolFake(messages=iter([
    AIMessage("", tool_calls=[
        {"name": "send_upi", "args": {"upi_id": "milkman@upi", "amount": 900.0}, "id": "a"},
        {"name": "send_upi", "args": {"upi_id": "landlord@upi", "amount": 32000.0}, "id": "b"}]),
    AIMessage("Both payments are done."),
]))

def assistant(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}

b = StateGraph(MessagesState)
b.add_node(assistant)
b.add_node("tools", ToolNode([send_upi]))
b.add_edge(START, "assistant")
b.add_conditional_edges("assistant", tools_condition)
b.add_edge("tools", "assistant")
agent = b.compile(checkpointer=InMemorySaver())
c = {"configurable": {"thread_id": "rent-day"}}

out = agent.invoke({"messages": [("user", "Pay the milkman 900 and rent 32000")]}, c)
print("paused:", out["__interrupt__"][0].value, "| executed so far:", executed)
agent.invoke(Command(resume="yes"), c)
print("executed after resume:", executed)
```

Output:

```
paused: {'confirm': 'Send ₹32,000 to landlord@upi?'} | executed so far: [('milkman@upi', 900.0)]
executed after resume: [('milkman@upi', 900.0), ('milkman@upi', 900.0), ('landlord@upi', 32000.0)]
```

The milkman was paid **twice**. The small payment didn't need approval, so it ran in the first pass; when the `ToolNode` re-ran on resume, it ran again. Three ways to avoid this:

- **Review before the tools node** (the review node from [Editing State with Human Input](editing-state-with-human-input.md)), so nothing has executed when the pause happens. This is what the lab does.
- **Make tools idempotent**, for example with a payment idempotency key derived from the tool call id.
- **Disable parallel tool calls** in the model (many providers support this) so each `ToolNode` run has a single call.

### 5. Ask again until the answer is valid

Sometimes the human's answer itself needs checking: a corrected amount must be a positive number, an IFSC code must have 11 characters. Don't loop inside the node with `while True: interrupt(...)`; the matching-by-order rule makes that fragile. Instead, **route back to the same node** with a conditional edge, so each question is a fresh run of the node:

```python
import re

class Beneficiary(TypedDict):
    name: str
    ifsc: str
    error: str

def ask_ifsc(state: Beneficiary):
    prompt = f"IFSC code for {state['name']}?"
    if state.get("error"):
        prompt = f"{state['error']} {prompt}"
    answer = interrupt(prompt).strip().upper()
    if re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", answer):
        return {"ifsc": answer, "error": ""}
    return {"error": f"'{answer}' is not a valid IFSC."}

def needs_retry(state: Beneficiary):
    return "ask_ifsc" if state.get("error") else END

b = StateGraph(Beneficiary)
b.add_node(ask_ifsc)
b.add_edge(START, "ask_ifsc")
b.add_conditional_edges("ask_ifsc", needs_retry, ["ask_ifsc", END])
onboard = b.compile(checkpointer=InMemorySaver())

c = {"configurable": {"thread_id": "add-payee"}}
out = onboard.invoke({"name": "Meera Iyer"}, c)
for typed in ["HDFC12345", "hdfc0001234"]:
    print("asked:", out["__interrupt__"][0].value, "| user types:", typed)
    out = onboard.invoke(Command(resume=typed), c)
print("saved:", out)
```

Output:

```
asked: IFSC code for Meera Iyer? | user types: HDFC12345
asked: 'HDFC12345' is not a valid IFSC. IFSC code for Meera Iyer? | user types: hdfc0001234
saved: {'name': 'Meera Iyer', 'ifsc': 'HDFC0001234', 'error': ''}
```

Each retry is a new super-step, so it's checkpointed, visible in history, and the error message is part of the state (handy for the UI and for audits).

### 6. Choosing static breakpoints per call

"Dynamic" can also mean deciding **where** to stop at call time. Since `invoke` accepts `interrupt_before`, your application can compute the list per request, for example from the user's role or a feature flag:

```python
class Order(TypedDict):
    items: list
    log: Annotated[list, operator.add]

def build_cart(state: Order):
    return {"log": ["cart built"]}

def charge(state: Order):
    return {"log": ["charged"]}

b = StateGraph(Order)
b.add_sequence([build_cart, charge])
b.add_edge(START, "build_cart")
shop = b.compile(checkpointer=InMemorySaver())

def breakpoints_for(user_role: str):
    return ["charge"] if user_role == "trainee" else []

for role in ["trainee", "manager"]:
    c = {"configurable": {"thread_id": f"order-{role}"}}
    shop.invoke({"items": ["laptop"], "log": []}, c, interrupt_before=breakpoints_for(role))
    print(role, "-> next:", shop.get_state(c).next, "| log:", shop.get_state(c).values["log"])
```

Output:

```
trainee -> next: ('charge',) | log: ['cart built']
manager -> next: () | log: ['cart built', 'charged']
```

This is convenient for testing and supervised modes, but it inherits the limits of static breakpoints (no payload, no answer). For production approvals prefer `interrupt()` with a policy, which can also read the role from runtime context.

### 7. Summary of the options

| Technique | Pauses when | Human can answer? | Status |
|---|---|---|---|
| `raise NodeInterrupt(...)` | A condition in the node holds | No, only by changing state | Deprecated since LangGraph 1.0, removed in 2.0 |
| `if ...: interrupt(...)` in a node | A condition in the node holds | Yes, via `Command(resume=...)` | Recommended |
| `interrupt()` inside a tool | The tool decides | Yes | Works; beware re-running sibling tool calls |
| Conditional edge back to an asking node | Answer fails validation | Yes, each retry is a new step | Recommended for validation |
| Run-time `interrupt_before=[...]` | Chosen per call by your app | No | Fine for testing and supervised modes |

---

## Try It Yourself

1. **Confidence threshold.** A classifier node writes `label` and `confidence`. Add a node that interrupts only when `confidence < 0.8`, asking a human for the correct label. Test with 0.95 and 0.55.
2. **Test the policy.** Write three `assert` statements for `review_reasons`: a known payee by day for ₹500 (no reasons), a known payee at 2 am (one reason), and an unknown payee for ₹50,000 at noon (two reasons).
3. **Fix the double payment.** Make `send_upi` idempotent using a set of already-processed tool call ids. (Hint: a tool can receive its tool call id by declaring a parameter `tool_call_id: Annotated[str, InjectedToolCallId]`, from `langchain_core.tools`.) Re-run the rent-day example and show the milkman is paid once.

<details>
<summary>Show answers</summary>

**1.**

```python
class Ticket(TypedDict):
    text: str
    label: str
    confidence: float

def maybe_review(state: Ticket):
    if state["confidence"] < 0.8:
        label = interrupt({"question": "Correct label?", "text": state["text"], "guess": state["label"]})
        return {"label": label, "confidence": 1.0}
    return {}

b = StateGraph(Ticket)
b.add_node(maybe_review)
b.add_edge(START, "maybe_review")
triage = b.compile(checkpointer=InMemorySaver())

for conf in [0.95, 0.55]:
    c = {"configurable": {"thread_id": f"ticket-{conf}"}}
    out = triage.invoke({"text": "UPI debited, not credited", "label": "billing", "confidence": conf}, c)
    if "__interrupt__" in out:
        out = triage.invoke(Command(resume="failed-transaction"), c)
    print(conf, "->", out["label"])
```

Output:

```
0.95 -> billing
0.55 -> failed-transaction
```

**2.**

```python
assert review_reasons({"payee": "BESCOM", "amount": 500.0, "hour": 14}) == []
assert review_reasons({"payee": "Airtel", "amount": 500.0, "hour": 2}) == ["late-night transfer"]
assert len(review_reasons({"payee": "New Shop", "amount": 50000.0, "hour": 12})) == 2
print("policy tests passed")
```

Output:

```
policy tests passed
```

**3.**

```python
from typing import Annotated as Ann
from langchain_core.tools import InjectedToolCallId

processed = set()
executed.clear()

@tool
def send_upi_once(upi_id: str, amount: float, tool_call_id: Ann[str, InjectedToolCallId]) -> str:
    """Send money over UPI (idempotent per tool call)."""
    if amount > 10_000:
        if interrupt({"confirm": f"Send ₹{amount:,.0f} to {upi_id}?"}) != "yes":
            return "Cancelled by the user."
    if tool_call_id in processed:
        return f"Already sent ₹{amount:,.0f} to {upi_id}"
    processed.add(tool_call_id)
    executed.append((upi_id, amount))
    return f"Sent ₹{amount:,.0f} to {upi_id}"

llm = ToolFake(messages=iter([
    AIMessage("", tool_calls=[
        {"name": "send_upi_once", "args": {"upi_id": "milkman@upi", "amount": 900.0}, "id": "a"},
        {"name": "send_upi_once", "args": {"upi_id": "landlord@upi", "amount": 32000.0}, "id": "b"}]),
    AIMessage("Both payments are done."),
]))
b = StateGraph(MessagesState)
b.add_node(assistant)
b.add_node("tools", ToolNode([send_upi_once]))
b.add_edge(START, "assistant")
b.add_conditional_edges("assistant", tools_condition)
b.add_edge("tools", "assistant")
safe_agent = b.compile(checkpointer=InMemorySaver())
c = {"configurable": {"thread_id": "rent-day-safe"}}
safe_agent.invoke({"messages": [("user", "Pay the milkman 900 and rent 32000")]}, c)
safe_agent.invoke(Command(resume="yes"), c)
print(executed)
```

Output:

```
[('milkman@upi', 900.0), ('landlord@upi', 32000.0)]
```

In production the "processed" record lives in your payments database (or the payment provider enforces an idempotency key), not in a Python set.

</details>

---

## Real-World Examples

- **Banking and UPI apps** apply risk rules (amount, new payee, time, device) and only then add friction, exactly like `review_reasons`.
- **Customer-support agents** escalate to a human only when classifier confidence is low or the customer mentions legal action.
- **Coding agents** ask before running shell commands that match a "dangerous" pattern (`rm -rf`, `git push --force`) and run the rest automatically.
- **Onboarding flows** re-ask for an IFSC code or PAN until it passes validation, with each attempt recorded.

---

## Common Misconceptions

### "Dynamic breakpoints need a special API"

Today they're just `interrupt()` inside an `if`. `NodeInterrupt` is deprecated.

### "The condition can use anything, like the current time"

It must give the same result when the node re-runs on resume. Use values stored in the state or fixed config.

### "An interrupt inside a tool only re-runs that tool"

The whole `ToolNode` re-runs, including sibling tool calls that already succeeded. Review before the tools node, make tools idempotent, or avoid parallel calls.

### "Validation needs a loop inside the node"

Use a conditional edge back to the asking node; each retry becomes a clean, checkpointed step.

---

## Interview Relevance

*"How do you pause an agent only for risky actions?"* Put `interrupt()` behind a policy function (amount thresholds, new payees, low confidence, sensitive patterns) whose inputs come from state, so the decision is stable across re-runs. Mention that `NodeInterrupt` was the older approach and is deprecated, that interrupts in tools re-run the whole `ToolNode`, and that validation loops should route back with a conditional edge.

*"What's the difference between static and dynamic breakpoints?"* Static breakpoints stop at named nodes every time (compile or call time) and carry no payload; dynamic ones are decided by state inside a node with `interrupt()` and can carry a question and receive an answer.

---

## Key Takeaways

- A **dynamic breakpoint** is **`interrupt()` behind a condition**; `NodeInterrupt` is **deprecated**.
- Write the condition as a **policy function** of the state; it must be **deterministic** across re-runs.
- `interrupt()` in a **tool** re-runs the **whole `ToolNode`**: review before tools or make tools **idempotent**.
- **Validate answers** by routing back to the asking node with a conditional edge, not with a loop.
- **Run-time `interrupt_before`** can be chosen per call, but carries no payload or answer.

---

**Up next:** [Lab: Approval step before a risky tool](lab-approval-step-before-a-risky-tool.md)
