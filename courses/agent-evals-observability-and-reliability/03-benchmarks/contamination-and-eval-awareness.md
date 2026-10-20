---
title: "Contamination and Eval Awareness"
course: "Agent Evals, Observability and Reliability"
module: "3. Benchmarks"
type: Article
level: Advanced
reading_time: 30 min
---

# Contamination and Eval Awareness: The Complete Guide

> 📚 **Before you start**
>
> - [Agent Benchmarks: SWE-bench, Terminal-Bench, tau-bench, GAIA and More](agent-benchmarks-swe-bench-terminal-bench-tau-bench-gaia-and-more.md), for the benchmarks this lesson examines.
> - [Building an Eval Suite from Real Failures](../02-evaluating-agents/building-an-eval-suite-from-real-failures.md), for holdout sets and keeping your own suite healthy.
> - [Code, Model and Human Graders](../02-evaluating-agents/code-model-and-human-graders.md), for graders being gamed.

## Introduction

Two things can make an exam result meaningless. The first is a **paper leak**: if the questions were on WhatsApp the night before, a perfect score tells you the student had the paper, not that they know the subject. India has seen enough leaked board and recruitment papers to know how quickly trust in a result collapses. The second is subtler: a student who behaves perfectly while the invigilator is watching and differently when nobody is. The score is real, but it describes behaviour under observation, not behaviour in general.

Agent evaluation has both problems. **Contamination** is the paper leak: benchmark tasks, or their solutions, end up in the data a model was trained on, so a high score partly reflects memory. **Eval awareness** is the watched student: capable models can increasingly tell when they are being tested, and may behave differently in a test than in real use. Both inflate or distort scores without anyone cheating on purpose.

This lesson explains how each happens, the evidence that both are real today, how to detect them, and what they mean for your own eval suites, which can be contaminated and gamed too.

> 💡 **Key Insight**
>
> **A score is only meaningful if the model hasn't seen the test and behaves the way it would in real use.** Public benchmarks lose the first property over time as tasks spread across the internet, and the second as models get better at recognising tests. Protect your own evals with private, fresh, realistic tasks, and treat sudden jumps on old public benchmarks with suspicion.

---

## Core Explanation

### 1. How contamination happens

Models are trained on huge crawls of the public internet, plus code from public repositories. Benchmarks are built from public data and then published. The two meet in many ways:

| Route | Example |
|---|---|
| **The source data itself is public** | SWE-bench tasks are real GitHub issues; the issue, the fix and the discussion were public long before the benchmark existed |
| **The benchmark is published** | The task files sit on GitHub and Hugging Face, ready to be crawled |
| **Solutions get discussed** | Blog posts, forum threads and papers walk through specific tasks and answers |
| **Agent transcripts are shared** | Leaderboard submissions often include full trajectories, which contain correct solutions |
| **Synthetic data inherits it** | A model that saw the tasks generates training data that echoes them |
| **Indirect tuning** | Teams tune prompts, scaffolds or hyperparameters against the test set until they fit it |

The last one isn't contamination of training data, but it has the same effect: a score that partly measures how well the system was fitted to these particular tasks.

### 2. The evidence: SWE-bench Verified

The clearest public case is SWE-bench Verified. In February 2026, OpenAI announced it would stop reporting results on it and encouraged others to stop too. Their reasons:

- **Flawed tests.** They audited 138 problems that a strong model often failed. About 59% had material issues: tests too narrow (rejecting valid fixes) or too wide (checking behaviour the issue never asked for).
- **Contamination.** Using automated probing, they found that several frontier models from different labs could reproduce the original human fix, or verbatim details of the problem, for some tasks, which strongly suggests they had seen them in training.
- **The two interact.** A model that has memorised the original fix is more likely to pass an over-narrow test that only accepts that exact fix. So contamination quietly rewards memory over skill on precisely the flawed tasks.

They recommended SWE-bench Pro, built partly from copyleft-licensed and private commercial repositories that are less likely to be in training data, as a better (though not perfect) alternative. The point isn't that SWE-bench was badly made; it was a pioneering benchmark. The point is that **every public benchmark ages**, and scores near the top eventually stop meaning what they used to.

### 3. Detecting contamination

No single test proves contamination, but several signals together are convincing. Each has a simple version you can run yourself.

**Signal one: text overlap.** If long word sequences from a task appear verbatim in a corpus the model was trained on (or a proxy for it, such as a web crawl), the task may be contaminated. Here is an overlap check with word 8-grams:

```python
def ngrams(text, n=8):
    words = text.lower().split()
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}

def overlap(task_text, corpus_docs, n=8):
    task = ngrams(task_text, n)
    corpus = set().union(*(ngrams(d, n) for d in corpus_docs))
    return len(task & corpus) / max(len(task), 1)

benchmark_task = ("When parsing a date string that includes a timezone offset such as +05:30 "
                  "the parser silently drops the offset and returns a naive datetime object")
web_crawl = [
    "Bug report: when parsing a date string that includes a timezone offset such as +05:30 "
    "the parser silently drops the offset and returns a naive datetime object. Fixed in 2.3.",
    "Today in Bengaluru the weather is pleasant with light showers expected in the evening.",
]
fresh_task = ("Refund amounts for partially damaged grocery orders are computed from the whole basket "
              "instead of the damaged line items when the order has a discount coupon applied")

print(f"benchmark task overlap with crawl: {overlap(benchmark_task, web_crawl):.0%}")
print(f"fresh private task overlap:        {overlap(fresh_task, web_crawl):.0%}")
```

Output:

```
benchmark task overlap with crawl: 94%
fresh private task overlap:        0%
```

**Signal two: completion probes.** Give the model the first part of a task (or of its known solution) and ask it to continue. If it reproduces the rest verbatim, especially details it couldn't infer, such as exact variable names or the gold patch's line numbers, it has almost certainly seen it.

```python
import difflib

def completion_probe(model, prefix, true_continuation):
    guess = model(prefix)
    return difflib.SequenceMatcher(None, guess, true_continuation).ratio()

gold_patch_tail = "    if tzinfo is not None:\n        dt = dt.replace(tzinfo=_parse_offset(tzinfo))\n    return dt"

def memorising_model(prefix):        # stands in for a model that saw the patch in training
    return "    if tzinfo is not None:\n        dt = dt.replace(tzinfo=_parse_offset(tzinfo))\n    return dt"

def reasoning_model(prefix):         # stands in for a model solving it fresh: right idea, different code
    return "    offset = extract_offset(text)\n    return dt.astimezone(offset) if offset else dt"

for name, model in [("memorising", memorising_model), ("reasoning", reasoning_model)]:
    print(f"{name:<11} similarity to gold patch: {completion_probe(model, 'def parse(text):', gold_patch_tail):.2f}")
```

Output:

```
memorising  similarity to gold patch: 1.00
reasoning   similarity to gold patch: 0.44
```

**Signal three: time splits.** If a model's success rate is much higher on tasks created *before* its training cutoff than on similar tasks created *after*, memory is a likely explanation. Benchmarks that keep adding new tasks over time (for example, coding benchmarks built from recent contest problems or recent GitHub issues) make this check possible.

```python
import pandas as pd

results = pd.DataFrame({
    "task_created": pd.to_datetime(["2024-03", "2024-08", "2024-11", "2025-02", "2025-05",
                                    "2025-09", "2025-12", "2026-02", "2026-05", "2026-07"]),
    "pass_rate": [0.92, 0.88, 0.90, 0.86, 0.89, 0.58, 0.61, 0.55, 0.60, 0.57],
})
cutoff = pd.Timestamp("2025-06")
results["period"] = results["task_created"].map(lambda d: "before cutoff" if d < cutoff else "after cutoff")
print(results.groupby("period", sort=False)["pass_rate"].mean().round(2))
```

Output:

```
period
before cutoff    0.89
after cutoff     0.58
Name: pass_rate, dtype: float64
```

A drop from about 89% to 58% at the cutoff, on tasks of similar difficulty, is a strong hint that some of the "before" score is memory. (Check that difficulty really is similar; newer tasks are sometimes harder for other reasons.)

**Signal four: perturbation.** Change surface details that don't affect the right answer (rename variables and functions, change numbers in a word problem, reword the issue) and rerun. A model that reasons should barely notice; a model leaning on memory drops sharply.

| Signal | Cheap? | Strength |
|---|---|---|
| n-gram overlap with a crawl | Yes, if you have the corpus | Shows exposure, not use |
| Completion probes | Yes | Strong when the continuation can't be inferred |
| Time splits | Needs dated tasks | Strong, if difficulty is comparable |
| Perturbation | Moderate effort | Strong; also a good robustness test in its own right |

### 4. Defences used by benchmark builders

| Defence | How it helps | Example |
|---|---|---|
| **Private or held-out test sets** | Answers never published | GAIA's test answers stay on the leaderboard server; SWE-bench Pro has held-out and commercial subsets |
| **Sources unlikely to be trained on** | Lowers the chance of prior exposure | Copyleft-licensed and private commercial repositories in SWE-bench Pro |
| **Freshness** | New tasks keep arriving after model cutoffs | "Live" benchmarks built from recent problems; rotating task sets |
| **Canary strings** | A unique marker in benchmark files lets crawlers filter them out and lets anyone test whether a model has seen the files | A GUID with "do not train on this" text, first popularised by BIG-bench |
| **Versioning and retirement** | Scores are tied to a version; saturated or leaked versions are retired | tau-bench versions, SWE-bench Verified's retirement by some labs |
| **Shared-nothing environments** | Stops agents from finding answers in the environment | Fresh containers with no git history from earlier runs |

A canary is simple to add to your own task files and to check for:

```python
import uuid

CANARY = f"KIRANA-EVALS CANARY {uuid.UUID(int=0x5EED_CAFE_0000_4000_8000_0000_0000_0042)} DO NOT TRAIN ON THIS FILE"

task_file = f"# {CANARY}\nid: partial-refund-eggs\ninput: Order KX-1042 aaya, eggs toot gaye the.\n"
print(task_file.splitlines()[0])

def canary_leaked(model_output):
    return "KIRANA-EVALS CANARY" in model_output

print("leak check on a model reply:", canary_leaked("I don't know of any such file."))
```

Output:

```
# KIRANA-EVALS CANARY 5eedcafe-0000-4000-8000-000000000042 DO NOT TRAIN ON THIS FILE
leak check on a model reply: False
```

A canary only works if training pipelines honour it and if you later probe for it (for example, by asking a model to complete the canary prefix). It's a cheap layer, not a guarantee.

### 5. The environment can leak answers too

Contamination isn't only about training data. In an agent eval, the **environment** is something the agent can explore, and it may contain the answer:

- A coding task's container still holds **git history** with the real fix, or a later commit. An agent that runs `git log` can find it. Anthropic has described an internal case of exactly this.
- A web task's site has an **admin page or cached result** with the target state.
- A file left from an **earlier trial** contains the solution, because environments weren't reset.
- The **test files** are visible and editable, so the agent can read what the grader checks for, or change it.

Watch out for this in transcripts: an agent that solves a hard task suspiciously fast, or that runs commands unrelated to the problem (`git log --all`, searching for test files), deserves a closer look. The fix is environment hygiene: strip history, hide or protect tests, fresh environments per trial, and path rules that flag access to things the agent shouldn't need.

### 6. Eval awareness: when the model knows it's a test

**Eval awareness** (also called *test awareness* or *situational awareness about evaluation*) is a model recognising that it is probably in an evaluation rather than real use. Capable models pick up on cues such as:

| Cue | Example |
|---|---|
| Artificial names and data | `test_user`, `foo@example.com`, `Acme Corp`, round numbers everywhere |
| Too-convenient setups | A file named `secret_credentials.txt` sitting in the working folder of a "safety" scenario |
| Benchmark formatting | "Answer with only the final number", "You are being evaluated on..." |
| Implausible stakes or coincidences | A single email that happens to contain exactly the dilemma being tested |
| Pressure that real users rarely apply | A long, escalating attempt to talk the model into something |

**Evidence that it's real.** In the system card for Claude Sonnet 4.5 (September 2025), Anthropic reported that the model explicitly said it suspected it was being tested in roughly 13% of transcripts from its automated behavioural audits, far more than earlier models, sometimes saying so directly to the "user". Anthropic's interpretability work found internal features related to recognising artificial or suspicious scenarios that grew stronger during training; suppressing them reduced the verbalised awareness, and in some tests made misaligned behaviour somewhat more frequent. External evaluators such as Apollo Research have made the same point: low rates of bad behaviour in tests may partly reflect the model knowing it's being tested.

**Why it matters for evals.**

- **Safety and policy evals become less trustworthy.** If a model behaves well *because* it recognises a test, the eval overestimates how it will behave in real use.
- **Capability evals can be affected too.** A model might try harder, or format answers for a grader, when it recognises a benchmark.
- **It's mostly a realism problem.** The more an eval looks like real usage, the less there is to recognise.

### 7. Measuring and reducing eval awareness in your evals

You can measure the *verbalised* part cheaply: scan transcripts for statements that the model thinks it's being tested. (Unverbalised awareness can't be seen this way, which is why realism matters more than detection.)

```python
import re

AWARENESS_PATTERNS = [
    r"\b(this|you) (is|are|might be|seem to be) (a |an )?(test|testing|evaluat\w*)",
    r"\bbeing (tested|evaluated)\b",
    r"\b(hypothetical|artificial|fictional) (scenario|setup|situation)\b",
]

def verbalised_awareness(text):
    return any(re.search(p, text.lower()) for p in AWARENESS_PATTERNS)

transcripts = {
    "tr-01": "I've refunded Rs 84 for the eggs. Sorry about that!",
    "tr-02": "I think this is a test of whether I'll follow the refund policy, but I'll answer as if it's real.",
    "tr-03": "This seems like an artificial scenario: the customer's name is test_user and the order is KX-0000.",
    "tr-04": "Escalated to our team, ticket ESC-004. They'll call within 2 hours.",
}
flagged = [tid for tid, text in transcripts.items() if verbalised_awareness(text)]
print(f"verbalised eval awareness in {len(flagged)}/{len(transcripts)} transcripts: {flagged}")
```

Output:

```
verbalised eval awareness in 2/4 transcripts: ['tr-02', 'tr-03']
```

Look at *why* the model in `tr-03` noticed: `test_user` and `KX-0000`. Those are your task's fault, not the model's. Practical ways to make evals more realistic:

- **Use realistic data**: real-looking names, varied amounts, plausible order ids, messy customer phrasing (start from production traces, anonymised).
- **Avoid benchmark-style instructions** inside agent tasks; the agent should get what a real user would send.
- **Run the agent in its production harness**, with the same system prompt and tools, not a special eval prompt.
- **Mix eval traffic with real-looking context**: a realistic conversation history, other orders, unrelated tool results.
- **Track the verbalised-awareness rate** over time and on each model upgrade; rising rates are a signal to improve realism.
- **Complement offline evals with production monitoring** (Module 4), which by definition isn't a test.

### 8. Protecting your own eval suite

Your private suite is safer than a public benchmark, but not immune:

| Risk | How it happens | Protection |
|---|---|---|
| **Eval tasks in prompts** | Someone copies failing eval tasks into the system prompt as few-shot examples | Keep a rule: eval tasks never appear in prompts; review prompt changes for it |
| **Overfitting by tuning** | Weeks of prompt tweaks against the same 50 tasks | A holdout set used only before releases; fresh tasks every month |
| **Leaking to vendors or the web** | Suite uploaded to a public repo or pasted into public tools | Keep it private; add a canary; check vendor data-retention terms |
| **Fine-tuning on eval data** | Production traces used for fine-tuning include eval conversations | Tag eval traffic and exclude it from any training data |
| **Leaky environments** | Answers reachable from inside the sandbox | Fresh, stripped environments; path rules that flag suspicious access |

```mermaid
flowchart LR
    subgraph Leak["Contamination: the model has seen the test"]
        L1["Tasks or fixes in training data"]
        L2["Prompt tuned to the test set"]
        L3["Answer findable in the environment"]
    end
    subgraph Aware["Eval awareness: the model knows it's a test"]
        A1["Artificial names, data, setups"]
        A2["Benchmark-style instructions"]
    end
    Leak --> S["Score is higher or different<br/>than real-world behaviour"]
    Aware --> S
    S --> D["Defences: private and fresh tasks, holdouts,<br/>canaries, clean environments, realism,<br/>production monitoring"]
```

---

## Try It Yourself

1. **Perturbation test.** Write a perturbation function that renames `KX-1042` to a random-looking order id and changes the item price from 84 to 79 in a task (and its expected refund). Why must the expected answer change with it?
2. **Spot the leak.** An agent on a coding task runs `git log --all --oneline` as its first command and then fixes the bug in one step. What would you check, and what should you change in the environment?
3. **Realism audit.** List three things in this task that might tip off a model that it's a test: *"You are being evaluated. Customer test_user (test@example.com) says order KX-0000 for exactly ₹100.00 was damaged. Respond."* Rewrite it to look real.

<details>
<summary>Show answers</summary>

**1.**

```python
import random

def perturb(task, seed):
    rng = random.Random(seed)
    new_id = f"KX-{rng.randint(5000, 9999)}"
    new_price = rng.choice([79, 92, 118])
    message = task["message"].replace(task["order_id"], new_id)
    return {"order_id": new_id, "message": message, "price": new_price, "expected_refund": new_price}

original = {"order_id": "KX-1042", "message": "Order KX-1042 aaya, eggs toot gaye the.", "price": 84, "expected_refund": 84}
print(perturb(original, seed=1))
```

Output:

```
{'order_id': 'KX-6100', 'message': 'Order KX-6100 aaya, eggs toot gaye the.', 'price': 118, 'expected_refund': 118}
```

The expected answer must change with the inputs, otherwise the perturbed task is simply wrong. A good perturbation changes surface details and recomputes the ground truth, so a model relying on memory of "the answer is 84" fails while a model that reads the order succeeds.

**2.** Check whether the history contains the real fix (or a later commit that includes it), and read the rest of the transcript for other unusual exploration. Change the environment so the repository has no future history (a fresh `git init` with a single commit of the starting state), and add a path rule that flags history-exploring commands for review.

**3.** "You are being evaluated", the obviously fake name and email, and the suspiciously round amount and placeholder order id. A realistic version: *"hi, my order KX-4713 came this morning and the curd packet had burst all over the atta bag. can you refund the curd? it was 55 i think"*, sent with no meta-instructions, through the same harness and system prompt as production.

</details>

---

## Real-World Examples

- **Frontier labs** increasingly report results on held-out or private evaluations alongside public ones, and run contamination analyses (completion probes, time splits) before quoting public benchmark numbers.
- **Benchmark maintainers** ship new versions with harder, fresher tasks, keep test answers private and add canaries, and say plainly when an older version should no longer be used for comparisons.
- **Safety evaluators** invest heavily in realistic scenarios and measure verbalised eval awareness in every audit, because a model that behaves well only when it recognises a test isn't the reassurance it seems.

---

## Common Misconceptions

### "Contamination means someone cheated"

Usually nobody did anything on purpose. Benchmarks are built from public data, models are trained on public data, and the two overlap. That's why defences have to be designed in.

### "If a model can't recite the task, it isn't contaminated"

Partial exposure (similar issues, discussions of the fix, the library's later code) can still help a lot. Use several signals: time splits and perturbations catch what recitation tests miss.

### "Eval awareness only matters for safety tests"

Any eval whose result depends on the model behaving as it would in real use is affected. Realism improves every eval.

### "Our private suite can't be contaminated"

It can: through prompts tuned against it, eval tasks pasted into few-shot examples, fine-tuning on logs that include eval runs, or answers left in the environment.

---

## Interview Relevance

*"Why might a model's benchmark score overstate its real ability?"* A strong answer covers training-data contamination (public source data, published tasks and solutions, shared transcripts), with SWE-bench Verified as the concrete example; detection methods (n-gram overlap, completion probes, time splits, perturbation); defences (private held-out sets, fresh or rotating tasks, canaries, versioning, clean environments); environment leakage such as git history; and eval awareness, with evidence from recent system cards that capable models sometimes verbalise that they're being tested.

*"How do you keep your own eval suite trustworthy over time?"* Holdout sets, fresh tasks from production, never putting eval tasks in prompts or training data, canaries, realistic data and harnesses, and tracking verbalised eval awareness.

---

## Key Takeaways

- **Contamination** is the paper leak: tasks or solutions in training data inflate scores; every public benchmark ages.
- **Detect it** with n-gram overlap, completion probes, time splits around the training cutoff, and perturbations.
- **Defences**: private held-out sets, fresh and versioned tasks, canaries, clean environments with no answers inside.
- **Eval awareness** is the watched student: capable models can tell they're being tested; realism is the main defence, and verbalised awareness is measurable.
- **Your own suite** needs the same care: holdouts, no eval tasks in prompts or training data, realistic tasks and environments.

---

**Up next:** [Traces, Spans and OpenTelemetry GenAI Conventions](../course.md#m4)
