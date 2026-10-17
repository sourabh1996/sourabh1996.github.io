---
title: "Lab: A typed routing layer for an agent"
course: "Agent Frameworks and SDKs"
module: "4. Type-Safe AI and Decision Models"
type: Lab
level: Intermediate
reading_time: 45 min
---

# Lab: A Typed Routing Layer for an Agent

> 📚 **Before you start**
>
> - [Decision Models: Typed Answers instead of Text (Jev)](decision-models-typed-answers-instead-of-text-jev.md), for question types, confidence and three-band routing.
> - [Why Type Safety Matters for LLM Apps](why-type-safety-matters-for-llm-apps.md), for Pydantic validation and retrying with the error.
> - [Conditional Workflows](../../langgraph-complete-guide/03-workflow-patterns-in-langgraph/conditional-workflows.md) and [State Reducers](../../langgraph-complete-guide/04-state-in-depth/state-reducers.md) from the LangGraph course, since the router is a small `StateGraph`.

## What You'll Build

**Thali Express**, a food delivery app, gets tens of thousands of support tickets a day. Each must go to the right team agent (billing, delivery, account) with an urgency flag. Sending every ticket through a large LLM is slow and expensive; sending everything through a cheap classifier blindly mis-routes the hard cases.

You'll build the routing layer in front of the team agents:

1. A **decision model** step answers two typed questions (which team? urgent?) with probabilities. Here it is a pretend model with exactly Jev's request and response shapes, so the code runs anywhere and you can swap in the real API later.
2. Every answer is **validated with Pydantic** before anything uses it.
3. A **confidence gate** sends each ticket one of three ways: act immediately, ask an LLM to double-check (with schema validation and a retry), or put it in a human review queue.
4. Finally, you'll **measure** the router on labelled tickets and choose the thresholds from data.

![Lab: a typed routing layer in front of an agent](/img/diagrams/agent-frameworks-and-sdks/typed-routing-lab.svg)

> 💡 **Key Insight**
>
> The routing layer is where speed, cost and safety are traded off, so make every trade-off a **typed, testable number**: answers are Pydantic objects, the bands are named thresholds, and the thresholds are chosen by measuring accuracy per band, not by intuition.

---

## Step 1: Define the Types

Two kinds of types: the **wire format** of the decision model's answers (as documented for Jev) and the **Route** that the rest of the system will consume.

```python
import math
import operator
from typing import Annotated, Literal, Optional, TypedDict, Union
from pydantic import BaseModel, Field, ValidationError

Team = Literal["billing", "delivery", "account", "other"]

class ChoiceAnswer(BaseModel):
    type: Literal["choice"]
    choice: str
    confidence: float = Field(ge=0, le=1)
    probabilities: dict[str, float]

class NoulAnswer(BaseModel):
    type: Literal["noul"]
    noul: float = Field(ge=0, le=1)

Answer = Annotated[Union[ChoiceAnswer, NoulAnswer], Field(discriminator="type")]

class DecisionResponse(BaseModel):
    model: str
    answers: dict[str, Answer]

class Route(BaseModel):
    team: Team
    urgent: bool
    decided_by: Literal["decision_model", "llm"]
    confidence: float = Field(ge=0, le=1)

print(Route(team="billing", urgent=True, decided_by="decision_model", confidence=0.93))
try:
    Route(team="payments", urgent=True, decided_by="llm", confidence=1.2)
except ValidationError as e:
    print([err["loc"][0] for err in e.errors()])
```

Output:

```
team='billing' urgent=True decided_by='decision_model' confidence=0.93
['team', 'confidence']
```

`Route` is the contract with the team agents. Nothing downstream ever sees an unknown team or an out-of-range confidence.

## Step 2: A Pretend Decision Model

The pretend model takes the same `state` and `questions` as Jev's `POST /v1/systemone` and returns the same JSON shape. Inside, it counts keywords and turns the counts into probabilities with a softmax, then computes choice confidence with the documented formula `(p_max − 1/n) / (1 − 1/n)`. It is crude on purpose: it's the **interface** that matters.

```python
KEYWORDS = {
    "billing": ["charged", "refund", "upi", "payment", "deducted", "invoice"],
    "delivery": ["late", "rider", "cold", "missing", "delivered", "address"],
    "account": ["login", "otp", "password", "profile", "email"],
    "other": [],
}
URGENT_WORDS = ["now", "today", "urgent", "asap", "cold", "immediately"]

class PretendDecisionModel:
    """Stands in for Jev: same request and response shapes, keyword maths inside."""
    model_name = "pretend-jev-1"

    def system_one(self, state, questions):
        text = state.lower()
        answers = {}
        for name, q in questions.items():
            if q["type"] == "choice":
                logits = {opt: 1.5 * sum(w in text for w in KEYWORDS.get(opt, [])) for opt in q["criteria"]}
                total = sum(math.exp(v) for v in logits.values())
                probs = {k: round(math.exp(v) / total, 3) for k, v in logits.items()}
                best = max(probs, key=probs.get)
                n = len(probs)
                conf = round((probs[best] - 1 / n) / (1 - 1 / n), 3)
                answers[name] = {"type": "choice", "choice": best, "confidence": conf, "probabilities": probs}
            elif q["type"] == "noul":
                hits = sum(w in text for w in URGENT_WORDS)
                answers[name] = {"type": "noul", "noul": round(1 / (1 + math.exp(-(2.2 * hits - 1.5))), 3)}
        return {"model": self.model_name, "answers": answers}

QUESTIONS = {
    "team": {"type": "choice", "instructions": "Which team should handle this ticket?",
             "criteria": {"billing": "Payments, refunds, invoices",
                          "delivery": "Late, missing or damaged orders",
                          "account": "Login, OTP, profile", "other": None}},
    "urgent": {"type": "noul", "instructions": "Does the customer need help within the hour?"},
}

jev = PretendDecisionModel()
resp = DecisionResponse.model_validate(jev.system_one("UPI payment deducted twice, refund now please", QUESTIONS))
print(resp.answers["team"])
print(resp.answers["urgent"])
```

Output:

```
type='choice' choice='billing' confidence=0.991 probabilities={'billing': 0.993, 'delivery': 0.002, 'account': 0.002, 'other': 0.002}
type='noul' noul=0.668
```

Notice the two questions are separate and narrow, as the Jev docs recommend: team and urgency are asked independently and combined in code later.

## Step 3: An LLM Fallback with a Typed Boundary

For the middle band, an LLM double-checks. Its answer goes through the same kind of boundary as everything else: a Pydantic model, one retry with the validation error, and `None` if it still fails. `FakeListChatModel` from LangChain plays the LLM here, returning scripted replies, the first of which is deliberately invalid.

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel

class LLMVerdict(BaseModel):
    team: Team
    urgent: bool

def llm_route(llm, ticket, suggestion, max_retries=1):
    prompt = (f"Ticket: {ticket}\nA fast classifier suggested team={suggestion} but was unsure. "
              'Reply with JSON only: {"team": ..., "urgent": true or false}')
    for attempt in range(max_retries + 1):
        raw = llm.invoke(prompt).content
        try:
            return LLMVerdict.model_validate_json(raw)
        except ValidationError as e:
            problem = f"{e.errors()[0]['loc'][0]}: {e.errors()[0]['msg']}"
            print(f"  llm attempt {attempt} invalid ({problem})")
            prompt += f"\nYour last reply was invalid: {problem}. Try again."
    return None

demo_llm = FakeListChatModel(responses=['{"team": "delivery", "urgent": "very"}',
                                        '{"team": "delivery", "urgent": true}'])
print(llm_route(demo_llm, "Rider is late", "delivery"))
```

Output:

```
  llm attempt 0 invalid (urgent: Input should be a valid boolean, unable to interpret input)
team='delivery' urgent=True
```

## Step 4: Wire the Graph

The graph has four nodes. `decide` calls the decision model and validates its response. A conditional edge (`gate`) picks one of three paths from the team confidence. `llm_check` runs the fallback and a second conditional edge sends it to `act` if it produced a valid verdict or to `human` if not. The `path` list uses an `operator.add` reducer so every node appends its name, which makes runs easy to inspect.

```python
from langgraph.graph import StateGraph, START, END

class RouterState(TypedDict, total=False):
    ticket: str
    decision: DecisionResponse
    route: Optional[Route]
    path: Annotated[list[str], operator.add]

ACT_FLOOR, REVIEW_FLOOR, URGENT_YES = 0.80, 0.40, 0.5

def decide(state):
    raw = jev.system_one(state["ticket"], QUESTIONS)
    return {"decision": DecisionResponse.model_validate(raw), "path": ["decide"]}

def gate(state):
    confidence = state["decision"].answers["team"].confidence
    if confidence >= ACT_FLOOR:
        return "act"
    if confidence >= REVIEW_FLOOR:
        return "llm_check"
    return "human"

def act(state):
    if state.get("route"):                      # already decided by the LLM
        return {"path": ["act"]}
    a = state["decision"].answers
    route = Route(team=a["team"].choice, urgent=a["urgent"].noul >= URGENT_YES,
                  decided_by="decision_model", confidence=a["team"].confidence)
    return {"route": route, "path": ["act"]}

def llm_check(state):
    suggestion = state["decision"].answers["team"].choice
    verdict = llm_route(fallback_llm, state["ticket"], suggestion)
    if verdict is None:
        return {"route": None, "path": ["llm_check"]}
    route = Route(team=verdict.team, urgent=verdict.urgent, decided_by="llm", confidence=0.8)
    return {"route": route, "path": ["llm_check"]}

def after_llm(state):
    return "act" if state.get("route") else "human"

def human(state):
    return {"route": None, "path": ["human"]}

builder = StateGraph(RouterState)
builder.add_node("decide", decide)
builder.add_node("act", act)
builder.add_node("llm_check", llm_check)
builder.add_node("human", human)
builder.add_edge(START, "decide")
builder.add_conditional_edges("decide", gate, ["act", "llm_check", "human"])
builder.add_conditional_edges("llm_check", after_llm, ["act", "human"])
builder.add_edge("act", END)
builder.add_edge("human", END)
router = builder.compile()
print(sorted(router.get_graph().nodes))
```

Output:

```
['__end__', '__start__', 'act', 'decide', 'human', 'llm_check']
```

The `0.8` confidence given to LLM verdicts is a placeholder; Step 6 shows how to replace guesses like this with measurements.

## Step 5: Run It

Three tickets: one clear, one mixed (delivery words and a billing word), one with no signal at all.

```python
fallback_llm = FakeListChatModel(responses=['{"team": "delivery", "urgent": true}'])

tickets = [
    "UPI payment deducted twice, refund now please",
    "Rider is late, also I was charged extra for delivery",
    "Hello, I have a question about Thali Express",
]
for t in tickets:
    out = router.invoke({"ticket": t, "path": []})
    team = out["decision"].answers["team"]
    r = out["route"]
    print(f"{team.choice:8} conf={team.confidence:.2f}  {' -> '.join(out['path']):24} "
          f"{r.model_dump() if r else 'human review queue'}")
```

Output:

```
billing  conf=0.99  decide -> act            {'team': 'billing', 'urgent': True, 'decided_by': 'decision_model', 'confidence': 0.991}
delivery conf=0.68  decide -> llm_check -> act {'team': 'delivery', 'urgent': True, 'decided_by': 'llm', 'confidence': 0.8}
billing  conf=0.00  decide -> human          human review queue
```

The clear ticket never touched the LLM. The mixed one was double-checked. The empty one had perfectly flat probabilities (confidence 0); its "choice" is simply the first option in the list, a small example of the first-option bias the Jev docs warn about. The gate ignores that meaningless pick and sends the ticket to a person.

## Step 6: Choose Thresholds from Data

The thresholds `0.80` and `0.40` were guesses. Here is how to replace them with evidence: run the decision step on labelled tickets, group results by confidence, and check accuracy in each group. You want the "act" band to be accurate enough for the cost of a mis-route, and the review bands to be small enough to staff.

```python
labelled = [
    ("Refund not credited after cancellation", "billing"),
    ("Charged twice on UPI", "billing"),
    ("Invoice shows wrong GST amount", "billing"),
    ("Payment deducted but order failed", "billing"),
    ("Rider delivered to wrong address", "delivery"),
    ("Food came cold and very late", "delivery"),
    ("Order missing one item", "delivery"),
    ("OTP not coming for login", "account"),
    ("Cannot change email on profile", "account"),
    ("Forgot password, reset link broken", "account"),
    ("Rider asked me for extra payment in cash", "delivery"),
    ("Refund came but order still shows late", "billing"),
    ("Login works but my address list is gone", "account"),
    ("What are your opening hours", "other"),
]

rows = []
for ticket, gold in labelled:
    a = DecisionResponse.model_validate(jev.system_one(ticket, QUESTIONS)).answers["team"]
    rows.append((a.confidence, a.choice == gold))

def band_report(rows, act_floor, review_floor):
    bands = {"act": [], "llm": [], "human": []}
    for conf, ok in rows:
        band = "act" if conf >= act_floor else "llm" if conf >= review_floor else "human"
        bands[band].append(ok)
    return {b: f"{sum(v)}/{len(v)}" for b, v in bands.items()}

for act_floor in (0.6, 0.8, 0.95):
    print(f"act_floor={act_floor}:", band_report(rows, act_floor, 0.40))
```

Output:

```
act_floor=0.6: {'act': '6/6', 'llm': '4/4', 'human': '1/4'}
act_floor=0.8: {'act': '6/6', 'llm': '4/4', 'human': '1/4'}
act_floor=0.95: {'act': '1/1', 'llm': '9/9', 'human': '1/4'}
```

Read the table as a trade-off. At `0.6` and `0.8` the act band is right every time (6 of 6) and the LLM handles 4 tickets. Raising the floor to `0.95` buys nothing: the act band shrinks to 1 ticket and 9 go to the LLM, costing more for the same accuracy. The human band is right only 1 time in 4, which confirms those tickets should not be auto-routed. So `0.8` is a sensible choice **for this data**. Two warnings: 14 tickets is far too few for a real decision (use hundreds, and recompute when the model version changes), and a model can be **confidently wrong** on patterns your sample doesn't contain, because confidence measures how decided the model is, not whether it is right. Keep sampling act-band tickets for review in production.

## Step 7: Swap in the Real Services

Only two functions touch the outside world. To go live, replace them; the graph, types and tests stay the same.

```python
# not-run: needs typesafe-sdk with an early-access key, and langchain-anthropic with an API key
from typesafe_sdk import TypeSafeClient, Choice, Noul
from langchain_anthropic import ChatAnthropic

client = TypeSafeClient()                     # TYPESAFE_API_KEY from the environment

def decide(state):
    resp = client.system_one(
        state=state["ticket"],
        questions={
            "team": Choice(instructions=QUESTIONS["team"]["instructions"], criteria=QUESTIONS["team"]["criteria"]),
            "urgent": Noul(instructions=QUESTIONS["urgent"]["instructions"]),
        },
    )
    raw = resp.model_dump()                    # same shape as Step 2; validate it the same way
    return {"decision": DecisionResponse.model_validate(raw), "path": ["decide"]}

fallback_llm = ChatAnthropic(model="claude-opus-5-5")
```

If you'd rather not hand-write the graph, Pydantic AI does the equivalent: `FallbackModel(TypeSafeModel(...), AnthropicModel(...))` with `decision_route_threshold` set sends unsure decisions to the LLM automatically, as described in the Jev lesson. The hand-built version here makes every step visible and testable.

---

## Try It Yourself

1. **Third band for urgency.** Make urgency three-way: `noul >= 0.8` urgent, `<= 0.2` not urgent, otherwise send the ticket to `llm_check` even if the team was confident. Run the first ticket again.
2. **LLM fails twice.** Give `fallback_llm` two invalid replies and run the mixed ticket. Which path does it take?
3. **Add a question.** Add a noul question `"money"`: "Is this mainly about money the customer paid?". In `act`, if `money >= 0.8` and the team isn't billing, route to the LLM instead. Which labelled tickets would this help?

<details>
<summary>Show answers</summary>

**1.**

```python
def gate3(state):
    a = state["decision"].answers
    if 0.2 < a["urgent"].noul < 0.8:
        return "llm_check"
    return gate(state)

b = StateGraph(RouterState)
for name, fn in [("decide", decide), ("act", act), ("llm_check", llm_check), ("human", human)]:
    b.add_node(name, fn)
b.add_edge(START, "decide")
b.add_conditional_edges("decide", gate3, ["act", "llm_check", "human"])
b.add_conditional_edges("llm_check", after_llm, ["act", "human"])
b.add_edge("act", END)
b.add_edge("human", END)
router3 = b.compile()

fallback_llm = FakeListChatModel(responses=['{"team": "billing", "urgent": true}'])
out = router3.invoke({"ticket": tickets[0], "path": []})
print(out["decision"].answers["urgent"].noul, " -> ".join(out["path"]), out["route"].decided_by)
```

Output:

```
0.668 decide -> llm_check -> act llm
```

The urgency probability 0.668 is in the uncertain middle, so even a confidently-routed ticket gets a second opinion on urgency.

**2.**

```python
fallback_llm = FakeListChatModel(responses=['{"team": "kitchen"}', '{"team": "delivery"}'])
out = router.invoke({"ticket": tickets[1], "path": []})
print(" -> ".join(out["path"]), out["route"])
```

Output:

```
  llm attempt 0 invalid (team: Input should be 'billing', 'delivery', 'account' or 'other')
  llm attempt 1 invalid (urgent: Field required)
decide -> llm_check -> human None
```

After the retry budget runs out, the ticket goes to a person; it is never routed on invalid data.

**3.** Tickets like "Rider asked me for extra payment in cash" (labelled delivery, but full of money words) and "Refund came but order still shows late" are the confusing ones. A narrow money question gives the router a second, independent signal so it can notice when the team answer and the money answer disagree and send those to the LLM, rather than relying on a single confident pick.

</details>

---

## What You've Learned

- Put a **typed boundary** around a decision model: its JSON answers are validated into Pydantic models before use.
- Built a **three-band confidence gate** in LangGraph: act, double-check with an LLM, or send to a person.
- Wrapped the **LLM fallback** in the same boundary, with a retry and a safe failure path.
- **Measured** confidence bands on labelled data and saw why a confident answer can still be wrong.
- Kept the outside world behind **two swappable functions**, so the real Jev and Claude can replace the pretend ones without touching the graph.

---

**Up next:** [Comparing Frameworks on One Task](../course.md#m5)
