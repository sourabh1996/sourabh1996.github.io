---
title: "Why Agent Evals Are Hard"
course: "Agent Evals, Observability and Reliability"
module: "2. Evaluating Agents"
type: Article
level: Advanced
reading_time: 26 min
---

# Why Agent Evals Are Hard: The Complete Guide

> 📚 **Before you start**
>
> - [How This Course Works](../01-start-here/how-this-course-works.md), which introduces the Kirana Express support agent used throughout.
> - [The Agent Loop: Decide, Act, Observe](../../agentic-ai-fundamentals/03-the-agent-loop/the-agent-loop-decide-act-observe.md), for the loop whose runs we will now grade.
> - [Temperature and Model Settings](../../generative-ai-and-llm-foundations/03-how-llms-work/temperature-and-model-settings.md), for why the same prompt can give different answers.
> - [RAG Evaluation](../../retrieval-augmented-generation-rag/course.md#m9), which evaluated single question-answer pairs. This lesson shows what breaks when the system is an agent.

## Introduction

Think about the driving test at an RTO. The examiner doesn't only check where your car ends up. Parking neatly in the box is necessary, but if you jumped a red light on the way, you fail. If you took a longer route than expected but drove safely and parked perfectly, you pass. And here is the uncomfortable part: the same learner, on the same track, can pass on Monday and fail on Thursday. One test on one day tells you something, but not everything.

Evaluating an agent is exactly this kind of problem. When you evaluated a RAG app, each test case was one question and one answer: compare the answer with what you expected and you're mostly done. An agent instead *drives*: it takes ten, twenty or two hundred steps, calls tools that change real systems, and chooses a different route on every run. "Is the final message correct?" is no longer enough. You need to ask whether the right thing happened in the world, whether anything unsafe happened on the way, and how often it all works across many runs.

This lesson explains, one by one, the reasons agent evaluation is hard, and gives you the vocabulary the rest of the course uses. By the end you'll be able to name every part of an agent eval, explain why a single run proves very little, and recognise the traps (claimed-but-not-done actions, compounding errors, leaky environments) that catch most teams.

> 💡 **Key Insight**
>
> An agent eval doesn't grade an *answer*. It grades a *run*: a sequence of decisions and actions that changed some environment. So you must decide **what to check** (the final state of the world, the steps, or both), **how many times to run** (because every run can differ), and **how to reset the world** between runs (because actions leave traces). Getting those three right matters more than which eval tool you pick.

---

## Core Explanation

### 1. What changes when the system is an agent

Here is the same business question evaluated two ways. A plain LLM app answers "What is your refund policy for damaged items?". The Kirana Express agent is asked "My order KX-1042 arrived with crushed eggs, please refund me."

| | Single LLM call (or RAG) | Agent |
|---|---|---|
| **Unit being graded** | One response | A whole run of many steps |
| **What can be right or wrong** | The text | The text, every tool call, and the state of the world afterwards |
| **Number of correct outputs** | Usually a few phrasings of one answer | Many different valid paths to the same result |
| **Randomness** | One sample per call | Randomness at every step, compounding |
| **Side effects** | None | Refunds issued, emails sent, files changed |
| **Cost per test** | One model call | Tens or hundreds of calls, plus tool calls |
| **Environment** | Not needed | Needs a realistic, resettable world: databases, APIs, files |

Every row in the right-hand column is a reason agent evals are harder. Let's take them apart.

### 2. The vocabulary of agent evals

Teams use these words loosely, which causes confusion. This course uses them precisely:

| Term | Meaning | Kirana Express example |
|---|---|---|
| **Task** | One test case: an input, a starting environment and success criteria | "Customer says eggs in KX-1042 were crushed; agent should refund ₹84 for the eggs only" |
| **Trial** | One attempt at a task. You usually run several trials per task. | Run number 3 of 5 on that task |
| **Transcript** (also *trajectory* or *trace*) | The full record of a trial: every message, model output, tool call and tool result | The list of steps the agent took |
| **Outcome** | The state of the environment when the trial ends | The refunds table now has one row: KX-1042, ₹84 |
| **Grader** | Logic that scores one aspect of a trial. A task can have several. | "Exactly one refund row exists for ₹84" |
| **Agent harness** | The code that turns a model into an agent: the loop, tools, permissions | Your Kirana Express agent code |
| **Eval harness** | The code that runs tasks, records transcripts, applies graders and adds up results | The script you'll build in this module's lab |
| **Eval suite** | A collection of tasks measuring one capability or behaviour | "Refunds and escalations" suite of 40 tasks |

Two of these deserve a second look. First, you are always evaluating **the model and the agent harness together**. Change the system prompt, a tool description or the loop's step limit and you have a different agent, even with the same model. Second, the **transcript and the outcome are different things**. The transcript says what the agent *did and said*; the outcome says what is *actually true now*. Much of this lesson is about the gap between them.

Here is what a task looks like as data. Real eval suites store tasks like this, one per file or one per row:

```json
{
  "id": "refund-damaged-eggs-001",
  "input": "Hi, order KX-1042 came today and the eggs were all crushed. Please refund me.",
  "environment": {
    "orders": {"KX-1042": {"items": [{"name": "eggs (12)", "price": 84}, {"name": "atta 5kg", "price": 265}],
                            "status": "delivered", "upi": "priya@okaxis"}},
    "refunds": []
  },
  "success_criteria": [
    "exactly one refund for KX-1042",
    "refund amount is 84 (eggs only, not the whole order)",
    "agent tells the customer the amount and that it goes to their UPI account"
  ],
  "tags": ["refund", "partial", "damaged"]
}
```

And here is the transcript of one trial, written as the list of steps your harness would record:

```json
[
  {"role": "user", "content": "Hi, order KX-1042 came today and the eggs were all crushed. Please refund me."},
  {"role": "assistant", "tool_call": {"name": "lookup_order", "args": {"order_id": "KX-1042"}}},
  {"role": "tool", "name": "lookup_order", "content": {"items": [{"name": "eggs (12)", "price": 84}, {"name": "atta 5kg", "price": 265}], "status": "delivered"}},
  {"role": "assistant", "tool_call": {"name": "check_refund_policy", "args": {"reason": "damaged"}}},
  {"role": "tool", "name": "check_refund_policy", "content": {"eligible": true, "scope": "damaged items only"}},
  {"role": "assistant", "tool_call": {"name": "issue_refund", "args": {"order_id": "KX-1042", "amount": 84}}},
  {"role": "tool", "name": "issue_refund", "content": {"refund_id": "RF-0091", "status": "credited"}},
  {"role": "assistant", "content": "Sorry about the eggs! I've refunded ₹84 to priya@okaxis. It should reflect within a few minutes."}
]
```

The outcome after this trial is simply the environment's new state: `refunds = [{"order_id": "KX-1042", "amount": 84}]`.

### 3. Hard part one: many valid paths

A good agent can reach the right outcome by different routes. To make this concrete, here is a tiny pretend version of the Kirana Express agent. Instead of a real model, a seeded random choice picks between three strategies a real model might plausibly follow. All three are correct.

```python
import random

def fresh_environment():
    return {
        "orders": {"KX-1042": {"items": {"eggs (12)": 84, "atta 5kg": 265}, "status": "delivered"}},
        "refunds": [],
    }

def run_agent(env, rng):
    """A pretend agent: picks one of several reasonable strategies, like a real model might."""
    steps = []
    def call(tool, **args):
        steps.append(tool)
        if tool == "lookup_order":
            return env["orders"][args["order_id"]]
        if tool == "check_refund_policy":
            return {"eligible": args["reason"] == "damaged"}
        if tool == "issue_refund":
            env["refunds"].append({"order_id": args["order_id"], "amount": args["amount"]})
            return {"status": "credited"}

    strategy = rng.choice(["lookup_then_policy", "policy_then_lookup", "lookup_twice"])
    if strategy == "lookup_then_policy":
        order = call("lookup_order", order_id="KX-1042")
        call("check_refund_policy", reason="damaged")
    elif strategy == "policy_then_lookup":
        call("check_refund_policy", reason="damaged")
        order = call("lookup_order", order_id="KX-1042")
    else:  # looks the order up, checks policy, then re-reads the order to confirm the price
        call("lookup_order", order_id="KX-1042")
        call("check_refund_policy", reason="damaged")
        order = call("lookup_order", order_id="KX-1042")
    call("issue_refund", order_id="KX-1042", amount=order["items"]["eggs (12)"])
    return steps

rng = random.Random(7)
for trial in range(1, 5):
    env = fresh_environment()
    steps = run_agent(env, rng)
    print(f"trial {trial}: {' -> '.join(steps)}")
    print(f"         outcome: {env['refunds']}")
```

Output:

```
trial 1: check_refund_policy -> lookup_order -> issue_refund
         outcome: [{'order_id': 'KX-1042', 'amount': 84}]
trial 2: lookup_order -> check_refund_policy -> issue_refund
         outcome: [{'order_id': 'KX-1042', 'amount': 84}]
trial 3: check_refund_policy -> lookup_order -> issue_refund
         outcome: [{'order_id': 'KX-1042', 'amount': 84}]
trial 4: lookup_order -> check_refund_policy -> lookup_order -> issue_refund
         outcome: [{'order_id': 'KX-1042', 'amount': 84}]
```

Four trials, three different step sequences, one identical and correct outcome. If your grader insisted on the exact sequence `lookup_order -> check_refund_policy -> issue_refund`, it would pass only trial 2 and mark trials 1, 3 and 4 as failures, and you'd conclude your agent was much worse than it is. Worse, you'd start "fixing" a working agent to match your arbitrary script.

This is why the default advice is **grade the outcome, and check only the parts of the path that genuinely matter** (for example, "never call `issue_refund` before checking the policy"). The next lesson, [Outcome, Trajectory and Tool-Use Grading](outcome-trajectory-and-tool-use-grading.md), shows how to write path checks that are strict where it matters and loose everywhere else.

### 4. Hard part two: every run is different

Models sample their output, and in an agent that sampling happens at every step. A slightly different first step leads to a different tool result, which changes the next decision. So the same task can succeed in one trial and fail in the next. Let's give our pretend agent a realistic flaw: in some runs it refunds the whole order instead of only the damaged item.

```python
def run_agent_with_flaw(env, rng, p_mistake=0.3):
    order = env["orders"]["KX-1042"]
    if rng.random() < p_mistake:
        amount = sum(order["items"].values())      # refunds the whole order: wrong
    else:
        amount = order["items"]["eggs (12)"]        # refunds only the eggs: right
    env["refunds"].append({"order_id": "KX-1042", "amount": amount})

def passed(env):
    return env["refunds"] == [{"order_id": "KX-1042", "amount": 84}]

rng = random.Random(1)
results = []
for trial in range(10):
    env = fresh_environment()
    run_agent_with_flaw(env, rng)
    results.append(passed(env))

print("per-trial results:", ["PASS" if r else "FAIL" for r in results])
print("first trial alone says:", "PASS" if results[0] else "FAIL")
print(f"success rate over 10 trials: {sum(results) / len(results):.0%}")
```

Output:

```
per-trial results: ['FAIL', 'PASS', 'PASS', 'FAIL', 'PASS', 'PASS', 'PASS', 'PASS', 'FAIL', 'FAIL']
first trial alone says: FAIL
success rate over 10 trials: 60%
```

If you had run this task once, you'd have seen FAIL and might have concluded the agent can't do partial refunds at all. Ten trials say 60%. The true rate, which we know only because we built the flaw ourselves, is 70%. Even 10 trials give only a rough estimate. Two consequences follow, and both get their own lesson later in this module:

- You must run **several trials per task** and report rates, not single results. [pass@k, pass^k and Noise](pass-k-pass-k-and-noise.md) shows how many, and how to read the numbers.
- Small differences between two agent versions are often **just noise**. Before you celebrate a 3-point improvement, you need to know how much the score moves on its own.

### 5. Hard part three: saying is not doing

An agent's final message is a *claim* about what it did. The environment is the *truth*. They can disagree, and when they do, the environment wins. This is the single most common mistake in home-made agent evals: grading the agent's final message instead of the world.

```python
def run_agent_that_claims(env, rng):
    """In some runs, the refund call fails silently but the agent says it succeeded anyway."""
    tool_failed = rng.random() < 0.4
    if not tool_failed:
        env["refunds"].append({"order_id": "KX-1042", "amount": 84})
    return "I've refunded ₹84 to your UPI account."    # same message either way

def grade_by_message(message):
    return "refunded ₹84" in message

def grade_by_outcome(env):
    return env["refunds"] == [{"order_id": "KX-1042", "amount": 84}]

rng = random.Random(3)
msg_passes = outcome_passes = 0
for trial in range(20):
    env = fresh_environment()
    message = run_agent_that_claims(env, rng)
    msg_passes += grade_by_message(message)
    outcome_passes += grade_by_outcome(env)

print(f"graded by final message: {msg_passes}/20 pass")
print(f"graded by outcome:       {outcome_passes}/20 pass")
```

Output:

```
graded by final message: 20/20 pass
graded by outcome:       13/20 pass
```

The message-based grader says the agent is perfect. In reality, seven customers were told they had their money back when they didn't. That is worse than an agent that admits failure, because nobody will follow up. In an airline-booking agent the same gap is "the agent says the seat is booked" versus "a reservation row exists in the database".

So for any agent that acts on the world, **your eval environment must be inspectable**: you need to be able to read the database, the files, the sent-messages outbox or the API mock's call log after the trial, and grade that.

### 6. Hard part four: errors compound over long runs

Suppose each step of a run is right 95% of the time and a single wrong step ruins the task. The chance that every step is right falls quickly as runs get longer:

```python
for steps in [1, 5, 10, 20, 50, 100]:
    print(f"{steps:>3} steps at 95% each -> whole run succeeds {0.95 ** steps:6.1%}")
```

Output:

```
  1 steps at 95% each -> whole run succeeds  95.0%
  5 steps at 95% each -> whole run succeeds  77.4%
 10 steps at 95% each -> whole run succeeds  59.9%
 20 steps at 95% each -> whole run succeeds  35.8%
 50 steps at 95% each -> whole run succeeds   7.7%
100 steps at 95% each -> whole run succeeds   0.6%
```

Real agents are kinder than this toy, because good agents notice and recover from many mistakes. But the shape is real, and it has three practical effects on evals:

- **Long tasks need more trials** to measure, because their success rates are lower and more variable.
- **Where it failed matters as much as whether it failed.** A run that fails at step 3 and one that fails at step 48 need different fixes. That is why you need transcripts and, later, traces.
- **Recovery is a skill worth testing on purpose.** Some of your tasks should deliberately inject a tool error halfway and check that the agent copes.

### 7. Hard part five: the environment is part of the test

Because agents act on an environment, the environment can quietly change your results:

| Problem | What happens | Fix |
|---|---|---|
| **Leftover state** | Trial 2 sees the refund trial 1 issued, and refuses as a "duplicate" | Build a fresh environment for every trial |
| **Shared state that leaks answers** | A coding agent reads the git history left by an earlier trial and copies its fix | Isolate trials in separate containers or databases |
| **Flaky dependencies** | A mock API times out 5% of the time; failures get blamed on the agent | Separate infrastructure errors from agent errors in your results |
| **Resource limits** | A container runs out of memory while installing packages; the task fails | Give clear, documented, consistent resources |
| **Unrealistic environment** | The test database has 3 orders; production has 3 crore | Make environments look like production where it matters |

Anthropic reported in early 2026 that on Terminal-Bench 2.0, simply changing how strictly container memory and CPU limits were enforced moved scores by about 6 percentage points, a gap bigger than many leaderboard differences between models. The environment isn't background; it is part of the measurement. You'll return to this in [pass@k, pass^k and Noise](pass-k-pass-k-and-noise.md).

### 8. Hard part six: "good" has many dimensions

For a single answer, "correct" often covers most of what you care about. For an agent run, you usually care about several separate things at once:

| Dimension | Question | Kirana Express example |
|---|---|---|
| **Task success** | Did the right thing happen? | Refund of ₹84 exists |
| **Safety and policy** | Did anything forbidden happen? | No refund above ₹500 without escalation; no refund to a different UPI ID |
| **Communication** | Did the user get a clear, honest, polite reply? | Told the amount and the timeline |
| **Efficiency** | How many steps, tokens, rupees, seconds? | 4 tool calls, ₹1.20 of model cost, 6 seconds |
| **Robustness** | Does it still work with typos, Hinglish, angry customers, tool errors? | "anday toot gaye the, paise wapas karo" |

These pull in different directions: an agent can be safe by refusing everything, or efficient by skipping the policy check. A useful eval reports them **separately** first, and only combines them when you know how much each matters. Different dimensions also need different kinds of grader (code for the refund row, a model for tone, a human for edge cases), which is the topic of [Code, Model and Human Graders](code-model-and-human-graders.md).

### 9. Hard part seven: every trial costs money and time

A single-turn eval of 200 questions is 200 model calls. An agent eval of 200 tasks, 5 trials each, averaging 12 model calls per trial, is 12,000 model calls, plus tool calls and environment setup. That changes how you work:

- You can't run the full suite on every keystroke, so you keep a **small, fast suite** for development and a **larger suite** for releases.
- You start with **20 to 50 well-chosen tasks**, not 2,000 generated ones (see [Building an Eval Suite from Real Failures](building-an-eval-suite-from-real-failures.md)).
- You run trials **in parallel**, which is only safe if each trial's environment is isolated.

### 10. The whole picture

Here is everything from this lesson in one diagram. Read it left to right: a task defines the starting world and the goal, the eval harness runs the agent in a fresh copy of that world, the trial produces both a transcript and an outcome, graders check both, and the suite turns many trial results into numbers you can act on.

![An agent eval: a task (input, starting environment, success criteria) goes to an eval harness that creates a fresh, isolated environment per trial and runs the agent harness and model inside it. Each trial produces a transcript (messages, tool calls, results) and an outcome (the final state of the world). Code, model and human graders check both. Results from many trials of many tasks are aggregated into a suite report with success rates, consistency, cost and failures to read](/img/diagrams/agent-evals-observability-and-reliability/anatomy-of-an-agent-eval.svg)
*The anatomy of an agent eval. The two outputs of a trial, transcript and outcome, are graded separately because they can disagree.*

### 11. Where evals sit among other kinds of checking

Evals aren't the only way to know how an agent behaves. They sit alongside other methods, each catching what the others miss:

| Method | When it runs | Strength | Weakness |
|---|---|---|---|
| **Unit tests of tools and code** | Every commit | Fast, exact, cheap | Don't test the model's decisions |
| **Offline evals** (this module) | Before release, in CI | Repeatable, no user harm, comparable over time | Only cover the cases you thought of |
| **Production monitoring and traces** (Module 4) | All the time | Shows real behaviour at scale | Reactive: users already saw the failure |
| **User feedback** (Module 4) | All the time | Finds problems you never imagined | Sparse, biased towards angry users |
| **Human review of transcripts** | Regularly | Builds real understanding | Slow, doesn't scale |
| **A/B tests** | For big changes | Measures real business outcomes | Needs traffic and time |

Think of these as slices of Swiss cheese: each has holes, but stacked together very little gets through. Two kinds of offline eval are also worth naming now, because you'll design for both:

- **Capability evals** ask "what can the agent do?" They should be *hard*, with a low pass rate that gives you room to improve.
- **Regression evals** ask "does it still do what it used to?" They should pass close to 100%, and any drop is an alarm. Capability tasks that the agent reliably passes "graduate" into the regression suite.

---

## Try It Yourself

1. **Spot the outcome.** For a travel agent asked to "book the cheapest Mumbai to Delhi flight on 5 March", write one outcome check and one transcript check. Which one would you trust more, and why?
2. **Measure the flaw.** Rerun the `run_agent_with_flaw` experiment with 1,000 trials instead of 10, using `random.Random(1)`. How close is the success rate to the true 70%?
3. **Leaky environment.** Modify the claims experiment so that it *doesn't* create a fresh environment for each trial (create one `env` before the loop). What does the outcome grader report now, and why is the number meaningless?

<details>
<summary>Show answers</summary>

**1.** Outcome check: "the bookings table contains exactly one booking, BOM to DEL, on 5 March, at the lowest fare available in the mock fare table". Transcript check: "the agent called `search_flights` with origin BOM, destination DEL and date 5 March before calling `book_flight`". Trust the outcome check more for success, because the booking either exists or it doesn't. The transcript check is still useful for *safety* rules, such as never booking before searching.

**2.**

```python
rng = random.Random(1)
results = []
for trial in range(1000):
    env = fresh_environment()
    run_agent_with_flaw(env, rng)
    results.append(passed(env))
print(f"success rate over 1000 trials: {sum(results) / len(results):.1%}")
```

Output:

```
success rate over 1000 trials: 72.0%
```

With 1,000 trials the estimate lands within about 2 points of the true 70%. With 10 trials it came out at 60%, and with a different seed it could easily have been anywhere from 50% to 90%. More trials, less noise.

**3.**

```python
rng = random.Random(3)
env = fresh_environment()          # created once: state leaks between trials
outcome_passes = 0
for trial in range(20):
    run_agent_that_claims(env, rng)
    outcome_passes += grade_by_outcome(env)
print(f"graded by outcome with a shared environment: {outcome_passes}/20 pass")
print("refund rows piled up:", len(env["refunds"]))
```

Output:

```
graded by outcome with a shared environment: 2/20 pass
refund rows piled up: 13
```

Refunds from earlier trials pile up in the shared environment. The two "passes" are early trials where exactly one row happened to exist, one of them only because the refund left over from an earlier trial was still there. Once a second row appears, the "exactly one refund" check can never pass again. The 2/20 says nothing about the agent; it only reflects the leaked state. Every trial needs its own fresh world.

</details>

---

## Real-World Examples

- **Coding agents** are graded mostly by outcome: after the agent finishes, the eval harness runs the repository's tests in the agent's container. Benchmarks such as SWE-bench work this way (you'll meet them in [Module 3](../../agent-evals-observability-and-reliability/course.md#m3)).
- **Customer-service agents** are graded on the final state of a mock database (was the booking actually changed?) plus checks on what was communicated. The tau-bench family of benchmarks uses a simulated customer played by another model, so every trial is a fresh conversation.
- **Research agents** have no single correct path and often no single correct answer, so teams combine checks that key facts appear, that sources are cited and real, and LLM-judge rubrics for coverage, calibrated against human reviewers.

---

## Common Misconceptions

### "If the final answer is right, the run was fine"

The final message is a claim. Grade the state of the world, and add separate checks for forbidden actions on the way, such as refunding before checking the policy.

### "One passing run means the task works"

Agents are random at every step. One pass might be the lucky 70%. Run several trials and report a rate.

### "A strict expected sequence of tool calls is the most rigorous grader"

It is the most *brittle* one. It fails valid alternative paths and pushes you to make the agent rigid. Be strict only about the steps that genuinely matter.

### "We'll build evals once the agent is finished"

Evals are hardest to build late, when nobody remembers what "correct" was supposed to mean. Teams that write a few tasks early catch regressions from day one and argue less about whether a change helped.

---

## Interview Relevance

*"How would you evaluate an LLM agent, and how is that different from evaluating a chatbot?"* A strong answer separates the **transcript** (what the agent did and said) from the **outcome** (the final state of the environment) and says to grade the outcome by default, with targeted checks on the path for safety rules. It mentions **non-determinism** (several trials per task, report rates and noise), **isolated, resettable environments** per trial, **compounding errors** over long horizons, **multiple dimensions** (success, safety, communication, efficiency), and the **cost** of agent evals. Bonus points for naming capability versus regression evals and for saying you'd start from real failures with 20 to 50 tasks.

*"Your agent says it completed the task but users complain. What's wrong with your evals?"* Probably grading the final message instead of the world state. Inspect the environment after each trial.

---

## Key Takeaways

- **An agent eval grades a run, not an answer**: tasks, trials, transcripts, outcomes, graders, harnesses and suites are the vocabulary.
- **Many paths can be correct**: grade the outcome by default and only check the parts of the path that really matter.
- **Every run differs**: one trial proves little; run several and report rates.
- **Saying is not doing**: grade the environment's final state, not the agent's claim about it.
- **The environment is part of the test**: fresh, isolated, realistic environments per trial, with infrastructure errors counted separately.

---

**Up next:** [Outcome, Trajectory and Tool-Use Grading](outcome-trajectory-and-tool-use-grading.md)
