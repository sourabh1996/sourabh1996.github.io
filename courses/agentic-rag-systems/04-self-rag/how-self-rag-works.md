---
title: "How Self-RAG Works"
course: Agentic RAG Systems
module: "4. Self-RAG"
type: Article
level: Advanced
reading_time: 40 min
---

# How Self-RAG Works: The Complete Guide

> 📚 **Before you start**
>
> - [Corrective RAG (CRAG)](../03-agentic-rag-architectures/corrective-rag-crag.md), for grading retrieved documents and rewriting queries.
> - [What is Adaptive RAG?](../02-adaptive-rag/what-is-adaptive-rag.md), for deciding whether to retrieve at all.
> - [RAG Evaluation](../../retrieval-augmented-generation-rag/course.md#m9), for the RAG triad (context relevance, groundedness, answer relevance), which Self-RAG checks while it runs.
> - [Iterative (Looping) Workflows](../../langgraph-complete-guide/03-workflow-patterns-in-langgraph/iterative-looping-workflows.md), for loops with caps.

## Introduction

Think of a careful student writing a board-exam answer with the textbook open. Before writing, they ask: *do I need to look this up, or do I know it?* When they look something up, they ask: *is this the right page?* After writing a line, they ask: *does the book actually say this, or did I make up that number?* And at the end: *did I actually answer what was asked?* Each check can send them back: to another page, or to rewrite a line.

The systems so far in this course check things **before** generation: Adaptive RAG decides how to retrieve, CRAG decides whether the documents are good. Neither looks at the **answer**. A model can receive perfect documents and still write "₹60 plus GST" when the page never mentions GST. That's a hallucination with the evidence sitting right there.

**Self-RAG** (self-reflective RAG) adds the missing checks. The model reflects on **whether to retrieve**, **whether each document is relevant**, **whether its answer is supported** by the documents, and **whether the answer is useful**, and acts on each verdict.

By the end of this lesson you will be able to:

- explain the four reflection decisions in the Self-RAG paper and how its special model is trained and decoded;
- see how weighting the reflection scores changes which answer wins;
- build the practical LangGraph version of Self-RAG with separate graders and capped loops;
- trace how it catches a hallucination and how it recovers from a useless answer.

> 💡 **Key Insight**
>
> Self-RAG closes the loop on the **answer**, not just the retrieval. Four questions are asked at run time: *Retrieve?* *Relevant?* *Supported?* *Useful?* An unsupported answer is regenerated; an unhelpful one triggers a better search. It's the RAG triad from evaluation, moved from a report you read next week into the pipeline itself.

---

## Core Explanation

### 1. The Self-RAG paper in one table

Self-RAG comes from *Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection* (Asai, Wu, Wang, Sil and Hajishirzi, 2023; presented at ICLR 2024). Its idea: train one language model to output, alongside its normal text, special **reflection tokens** that record its own judgements. There are four kinds:

| Reflection token | The question it answers | Possible values | RAG-triad cousin |
|---|---|---|---|
| **Retrieve** | Would retrieving help the next part of the answer? | yes, no, continue (keep using what I have) | (none: this is adaptive retrieval) |
| **IsRel** | Is this retrieved passage relevant to the question? | relevant, irrelevant | Context relevance |
| **IsSup** | Is what I just wrote supported by the passage? | fully supported, partially supported, no support | Groundedness / faithfulness |
| **IsUse** | Is my answer a useful response to the question? | a rating from 1 to 5 | Answer relevance |

Here is what an output looks like, written out with the tokens visible (the real tokens are special vocabulary items; the brackets are for reading):

```
Question: What is the fee to cancel a SaathiRail ticket 3 days before departure?

[Retrieve=yes]
<passage refunds.md §1: Cancelling a confirmed ticket more than 48 hours before departure costs a flat fee of ₹60...>
[IsRel=relevant]
Three days is more than 48 hours before departure, so the fee is a flat ₹60 per passenger.
[IsSup=fully supported]
[IsUse=5]
```

Because the judgements are tokens the model generates, they come with **probabilities**, and that is what makes them usable for control: "how sure is the model that this sentence is fully supported?" is a number.

### 2. How the Self-RAG model is trained

Training happens in two stages, so that the final model doesn't need a separate judge at run time:

1. **Train a critic.** A strong model (GPT-4 in the paper) labels a set of examples with reflection tokens: is this passage relevant, is this sentence supported, and so on. A smaller **critic model** is trained to imitate those labels.
2. **Train the generator.** The critic is run **offline** over a large training set, inserting reflection tokens and retrieved passages into ordinary question-answer texts. The **generator** (Llama 2 at 7B and 13B parameters in the paper) is then trained with normal next-token prediction on this enriched text, with the reflection tokens added to its vocabulary. It learns to write answers *and* the critiques, in one stream.

The result is a single model that decides when to retrieve and grades itself as it writes. The authors released the trained models, so you can download and run them.

### 3. How Self-RAG decodes: scoring candidates

At inference time, Self-RAG uses the reflection tokens in two ways.

**Adaptive retrieval.** Before each segment (roughly a sentence), the model predicts the Retrieve token. If the probability of "yes" is above a threshold you choose, retrieval happens. A lower threshold means more retrieval (safer for fact-heavy tasks); a higher one means less.

**Critique-guided selection.** When it retrieves, it fetches several passages and **writes one candidate continuation per passage, in parallel**. Each candidate gets a score that combines how likely the text is with a **weighted sum of its critique scores** (IsRel, IsSup, IsUse). The best candidate is kept, and generation continues segment by segment (the paper uses a beam search over segments).

The weights are the clever part: they let you **change the model's behaviour without retraining**. Weight support heavily for a legal or medical assistant; weight usefulness more for a casual one. Here's a small simulation with made-up probabilities for three candidates, one per retrieved passage:

```python
CANDIDATES = [
    {"passage": "refunds.md §1", "text": "The fee is a flat ₹60 per passenger.",
     "fluency": 0.80, "is_rel": 0.95, "is_sup": 0.95, "is_use": 0.80},
    {"passage": "tatkal.md §2", "text": "The fee is ₹60 plus 18% GST, and Tatkal tickets are refunded too.",
     "fluency": 0.95, "is_rel": 0.40, "is_sup": 0.15, "is_use": 0.90},
    {"passage": "refunds.md §3", "text": "Refunds go back to your original payment method.",
     "fluency": 0.85, "is_rel": 0.30, "is_sup": 0.90, "is_use": 0.20},
]

def best_candidate(weights):
    def score(c):
        return c["fluency"] + sum(w * c[k] for k, w in weights.items())
    winner = max(CANDIDATES, key=score)
    return winner["passage"], round(score(winner), 3), winner["text"]

print("fluency only:     ", best_candidate({}))
print("balanced critique:", best_candidate({"is_rel": 1.0, "is_sup": 1.0, "is_use": 0.5}))
print("strict support:   ", best_candidate({"is_rel": 0.5, "is_sup": 2.0, "is_use": 0.2}))
```

Output:

```
fluency only:      ('tatkal.md §2', 0.95, 'The fee is ₹60 plus 18% GST, and Tatkal tickets are refunded too.')
balanced critique: ('refunds.md §1', 3.1, 'The fee is a flat ₹60 per passenger.')
strict support:    ('refunds.md §1', 3.335, 'The fee is a flat ₹60 per passenger.')
```

With fluency alone, the confident-sounding hallucination ("₹60 plus 18% GST", invented and unsupported) wins: it's the most *likely-sounding* text. Add the critique scores and the supported answer wins, by a wider margin as the support weight rises. The third candidate is supported but not useful (true, but not what was asked), so the usefulness weight keeps it from winning. (The numbers here are invented for illustration; the real model produces them as token probabilities.)

### 4. From the paper to practice: Self-RAG as a graph

Using the original Self-RAG model means running that specific fine-tuned model. Most teams instead want the *behaviour* with the models they already use. The common practical version, popularised by LangGraph's Self-RAG tutorial, replaces the reflection tokens with **separate grader calls** and replaces segment-by-segment beam search with **loops in a graph**:

| Paper | Practical graph |
|---|---|
| Retrieve token | A routing decision (like Adaptive RAG) |
| IsRel token per passage | A document grader; irrelevant documents are dropped (like CRAG) |
| IsSup token per segment | A **hallucination grader** on the whole answer; if unsupported, regenerate |
| IsUse token | An **answer grader**; if not useful, rewrite the query and retrieve again |
| Parallel candidates + beam search | Sequential retries with caps |

![The question goes to Retrieve?, which either retrieves or generates without documents. Retrieved documents are graded for relevance and the good ones are kept, then the model generates. Generation is checked: Supported? If no, regenerate. If yes, Useful? If yes, answer. If no, rewrite the query and retrieve again. Every loop has a cap.](/img/diagrams/agentic-rag-systems/self-rag.svg)
*The practical Self-RAG graph: four checks, two loops, and caps on both.*

You lose the paper's fine-grained, per-sentence control and gain portability: any capable model can be the generator and the graders. Let's build it.

### 5. The setup

```python
import math, re
from typing import Callable, Literal, TypedDict
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

class KeywordEmbeddings(Embeddings):
    """Toy embedding: one dimension per keyword stem, plus a small constant. Offline stand-in only."""
    def __init__(self, stems):
        self.stems = stems

    def _embed(self, text):
        words = re.findall(r"[a-z]+", text.lower())
        vector = [float(sum(w.startswith(s) for w in words)) for s in self.stems]
        vector.append(0.1)
        norm = math.sqrt(sum(x * x for x in vector))
        return [x / norm for x in vector]

    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]

    def embed_query(self, text):
        return self._embed(text)

STEMS = ["cancel", "refund", "fee", "fare", "tatkal", "upi", "wallet", "card", "payment",
         "method", "bag", "luggage", "kg", "pet", "dog", "railway"]

HELP_CENTRE = [
    ("fees", "refunds.md §1", "Cancelling a confirmed ticket more than 48 hours before departure costs a flat "
     "fee of ₹60 per passenger. Between 48 and 12 hours before departure, 25% of the fare is deducted. "
     "Less than 12 hours before departure, 50% is deducted."),
    ("tatkal", "tatkal.md §2", "Tatkal tickets are not refunded when you cancel them yourself. If the railway "
     "cancels the train, Tatkal tickets are refunded in full."),
    ("train-cancelled", "refunds.md §3", "If the railway cancels a train, every ticket on it is refunded in full "
     "automatically, with no form to fill. The money goes back to the original payment method; payments.md "
     "lists how long each method takes."),
    ("payment-times", "payments.md §2", "Refund timelines by payment method: SaathiRail Wallet is instant, UPI "
     "takes 1 to 3 working days, and credit or debit cards take 5 to 7 working days."),
    ("luggage", "luggage.md §1", "Each passenger may carry one bag of up to 15 kg free. Extra luggage costs "
     "₹30 per kg, paid at the parcel counter."),
    ("pets", "pets.md §1", "Pets such as dogs and cats travel only in a fully booked first class cabin, with "
     "a vaccination certificate."),
]
help_centre = InMemoryVectorStore(KeywordEmbeddings(STEMS))
help_centre.add_documents([Document(text, metadata={"source": src}) for _, src, text in HELP_CENTRE],
                          ids=[doc_id for doc_id, _, _ in HELP_CENTRE])

class StandInModel(BaseChatModel):
    """A chat model whose replies come from a Python function. For offline lessons only."""
    respond: Callable

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return ChatResult(generations=[ChatGeneration(message=self.respond(messages))])

    @property
    def _llm_type(self):
        return "stand-in"

    def bind_tools(self, tools, **kwargs):
        return self

def structured_reply(schema_name, **fields):
    return AIMessage("", tool_calls=[{"name": schema_name, "args": fields, "id": "call_1"}])

def format_docs(docs):
    return "\n".join(f"[{d.metadata['source']}] {d.page_content}" for d in docs)
```

### 6. The four graders

Each reflection decision becomes one small structured-output call. These are the schemas and prompts you'd use with a real model; the shape of the `Literal` values deliberately mirrors the paper's tokens.

```python
class RetrieveDecision(BaseModel):
    """Does answering this question need facts from the SaathiRail help centre?"""
    retrieve: Literal["yes", "no"]

class IsRelevant(BaseModel):
    """Is this document relevant to the question?"""
    relevant: Literal["yes", "no"]

class IsSupported(BaseModel):
    """Is every factual claim in the answer supported by the documents?"""
    support: Literal["fully", "partially", "no"]
    unsupported_claims: list[str] = Field(default_factory=list, description="claims not found in the documents")

class IsUseful(BaseModel):
    """How well does the answer address the question?"""
    score: int = Field(ge=1, le=5, description="5 = fully answers it, 1 = doesn't answer it")

SUPPORT_PROMPT = """Documents:
{docs}

Answer: {answer}

Is every factual claim in the answer (numbers, amounts, rules) stated in the documents? List any that are not."""
```

The support grader's prompt is the most important one in the system. Note what it asks for: not "is this a good answer?" but **claim by claim, is it in the documents?**, plus the list of unsupported claims. That list is gold: it tells the generator exactly what to fix on the retry.

Offline, the stand-in graders are rules you can read. The support rule is a real, useful technique in its own right: it checks that every **number, amount and percentage** in the answer appears in the documents, which catches the most damaging kind of hallucination in a fees-and-refunds domain.

```python
HELP_WORDS = ["cancel", "refund", "fee", "tatkal", "luggage", "pet", "dog", "money back", "upi"]

def retrieve_rules(messages):
    q = messages[-1].content.lower()
    return structured_reply("RetrieveDecision", retrieve="yes" if any(w in q for w in HELP_WORDS) else "no")

PHRASES = {"money back": "refund", "doesn't run": "railway cancel", "how fast": "payment method"}

def topics(text):
    for phrase, meaning in PHRASES.items():       # a model understands everyday phrasing; the rules translate it
        text = text.replace(phrase, meaning)
    return {t for t in STEMS if t in text}

def relevance_rules(messages):
    question, document = messages[-1].content.lower().split("document:")
    wanted = topics(question)
    covered = len(wanted & topics(document)) / len(wanted) if wanted else 0
    return structured_reply("IsRelevant", relevant="yes" if covered > 0.5 else "no")

def support_rules(messages):
    prompt = messages[-1].content
    docs, answer = prompt.split("Answer:")[0], prompt.split("Answer:")[1].split("Is every")[0]
    claims = re.findall(r"₹?\d+(?:\.\d+)?%?(?: to \d+)?", answer)
    missing = [c for c in claims if c not in docs]
    level = "fully" if not missing else ("partially" if len(missing) < len(claims) else "no")
    return structured_reply("IsSupported", support=level, unsupported_claims=missing)

def usefulness_rules(messages):
    prompt = messages[-1].content.lower()
    question, answer = prompt.split("answer:")
    if "couldn't find" in answer:
        return structured_reply("IsUseful", score=1)
    if ("how fast" in question or "how long" in question) and "day" not in answer:
        return structured_reply("IsUseful", score=2)
    return structured_reply("IsUseful", score=5)

retrieval_grader = StandInModel(respond=retrieve_rules).with_structured_output(RetrieveDecision)
relevance_grader = StandInModel(respond=relevance_rules).with_structured_output(IsRelevant)
support_grader = StandInModel(respond=support_rules).with_structured_output(IsSupported)
usefulness_grader = StandInModel(respond=usefulness_rules).with_structured_output(IsUseful)

docs = help_centre.similarity_search("What is the fee to cancel 3 days before departure?", k=1)
for answer in ["The fee is a flat ₹60 per passenger.", "The fee is ₹60 plus 18% GST."]:
    print(support_grader.invoke(SUPPORT_PROMPT.format(docs=format_docs(docs), answer=answer)))
```

Output:

```
support='fully' unsupported_claims=[]
support='partially' unsupported_claims=['18%']
```

The grader caught the invented "18%" and named it. "Partially" is the honest verdict: one claim is backed, one isn't.

### 7. The generator, and its mistakes

The generator stand-in imitates a real model's most common failure: on its first attempt at the fee question it adds a plausible but invented GST charge. When the prompt contains feedback about unsupported claims, it sticks to the documents. For questions with no help-centre documents it either answers from general knowledge or says it couldn't find anything.

```python
GENERATE_PROMPT = """Answer the question using only the documents. Cite sources in square brackets.
{feedback}
Documents:
{docs}

Question: {question}"""

def generator_rules(messages):
    prompt = messages[-1].content
    question = prompt.split("Question:")[-1].lower()
    feedback = "unsupported" in prompt
    if "pnr" in question:
        return AIMessage("PNR stands for Passenger Name Record, the booking reference on every ticket.")
    if "payments.md §2" in prompt:
        return AIMessage("Yes, it's refunded in full automatically [refunds.md §3]. It reaches UPI in 1 to 3 "
                         "working days and cards in 5 to 7 working days [payments.md §2].")
    if "refunds.md §1" in prompt:
        if feedback:
            return AIMessage("Three days is more than 48 hours ahead, so it's a flat ₹60 per passenger [refunds.md §1].")
        return AIMessage("It's a flat ₹60 per passenger plus 18% GST [refunds.md §1].")
    return AIMessage("I couldn't find this in the help centre.")

generator = StandInModel(respond=generator_rules)
```

### 8. The Self-RAG graph

The state tracks the question, the current search query, the documents, the answer, and two counters that cap the loops: `generations` (how many times we've written an answer) and `rewrites` (how many times we've rewritten the query).

```python
MAX_GENERATIONS, MAX_REWRITES = 3, 1

class SelfRAGState(TypedDict):
    question: str
    query: str
    use_retrieval: bool
    docs: list
    answer: str
    feedback: str
    support: str
    usefulness: int
    generations: int
    rewrites: int

def decide_retrieval(state: SelfRAGState):
    decision = retrieval_grader.invoke(state["question"])
    return {"use_retrieval": decision.retrieve == "yes", "query": state["question"],
            "generations": 0, "rewrites": 0, "feedback": "", "docs": []}

def retrieve(state: SelfRAGState):
    return {"docs": help_centre.similarity_search(state["query"], k=3)}

def grade_documents(state: SelfRAGState):
    kept = [d for d in state["docs"]
            if relevance_grader.invoke(f"Question: {state['question']}\nDocument: {d.page_content}").relevant == "yes"]
    return {"docs": kept}

def generate(state: SelfRAGState):
    prompt = GENERATE_PROMPT.format(feedback=state["feedback"], docs=format_docs(state["docs"]),
                                    question=state["question"])
    return {"answer": generator.invoke(prompt).content, "generations": state["generations"] + 1}

def check_support(state: SelfRAGState):
    if not state["use_retrieval"]:
        return {"support": "fully"}              # nothing to check against: Self-RAG skips IsSup without retrieval
    verdict = support_grader.invoke(SUPPORT_PROMPT.format(docs=format_docs(state["docs"]), answer=state["answer"]))
    feedback = (f"Your previous answer had unsupported claims: {verdict.unsupported_claims}. Remove them."
                if verdict.support != "fully" else "")
    return {"support": verdict.support, "feedback": feedback}

def check_useful(state: SelfRAGState):
    verdict = usefulness_grader.invoke(f"Question: {state['question']}\nAnswer: {state['answer']}")
    return {"usefulness": verdict.score}

def rewrite_query(state: SelfRAGState):
    # Stand-in rewriter: a real model rewrites the question in the help centre's vocabulary.
    return {"query": "refund when the railway cancels a train, timelines by payment method",
            "rewrites": state["rewrites"] + 1, "feedback": ""}

def after_decide(state: SelfRAGState) -> Literal["retrieve", "generate"]:
    return "retrieve" if state["use_retrieval"] else "generate"

def after_support(state: SelfRAGState) -> Literal["generate", "check_useful"]:
    if state["support"] != "fully" and state["generations"] < MAX_GENERATIONS:
        return "generate"
    return "check_useful"

def after_useful(state: SelfRAGState) -> Literal["rewrite_query", "__end__"]:
    if state["usefulness"] < 4 and state["use_retrieval"] and state["rewrites"] < MAX_REWRITES:
        return "rewrite_query"
    return END

g = StateGraph(SelfRAGState)
for name, fn in [("decide_retrieval", decide_retrieval), ("retrieve", retrieve),
                 ("grade_documents", grade_documents), ("generate", generate),
                 ("check_support", check_support), ("check_useful", check_useful),
                 ("rewrite_query", rewrite_query)]:
    g.add_node(name, fn)
g.add_edge(START, "decide_retrieval")
g.add_conditional_edges("decide_retrieval", after_decide)
g.add_edge("retrieve", "grade_documents")
g.add_edge("grade_documents", "generate")
g.add_edge("generate", "check_support")
g.add_conditional_edges("check_support", after_support)
g.add_conditional_edges("check_useful", after_useful)
g.add_edge("rewrite_query", "retrieve")
self_rag = g.compile()

def trace(question):
    print(f"Q: {question}")
    for update in self_rag.stream({"question": question}, stream_mode="updates"):
        node, data = next(iter(update.items()))
        shown = {"retrieve": lambda d: [x.metadata["source"] for x in d["docs"]],
                 "grade_documents": lambda d: [x.metadata["source"] for x in d["docs"]],
                 "generate": lambda d: d["answer"],
                 "check_support": lambda d: d["support"],
                 "check_useful": lambda d: d["usefulness"],
                 "decide_retrieval": lambda d: "retrieve" if d["use_retrieval"] else "no retrieval",
                 "rewrite_query": lambda d: d["query"]}[node](data)
        print(f"  {node:17} {shown}")
```

Three questions show the three behaviours. First, one that needs no retrieval:

```python
trace("What does PNR stand for?")
```

Output:

```
Q: What does PNR stand for?
  decide_retrieval  no retrieval
  generate          PNR stands for Passenger Name Record, the booking reference on every ticket.
  check_support     fully
  check_useful      5
```

The retrieval decision said no, so there were no documents, no relevance grading and nothing to check support against; the answer was checked only for usefulness. Three model calls.

Second, a question where the generator hallucinates:

```python
trace("What is the fee to cancel 3 days before departure?")
```

Output:

```
Q: What is the fee to cancel 3 days before departure?
  decide_retrieval  retrieve
  retrieve          ['refunds.md §1', 'tatkal.md §2', 'refunds.md §3']
  grade_documents   ['refunds.md §1']
  generate          It's a flat ₹60 per passenger plus 18% GST [refunds.md §1].
  check_support     partially
  generate          Three days is more than 48 hours ahead, so it's a flat ₹60 per passenger [refunds.md §1].
  check_support     fully
  check_useful      5
```

This is the trace to remember. Retrieval and grading worked: only the fees page survived. The first answer still invented "18% GST". The support grader caught it as "partially" supported and handed back the exact unsupported claim, the generator rewrote without it, and the second answer passed both checks. A pipeline without the support check would have shown the user a fee that doesn't exist.

Third, a colloquial question where the first answer is useless:

```python
trace("Will I get my money back if my train doesn't run, and how fast?")
```

Output:

```
Q: Will I get my money back if my train doesn't run, and how fast?
  decide_retrieval  retrieve
  retrieve          ['pets.md §1', 'refunds.md §1', 'luggage.md §1']
  grade_documents   []
  generate          I couldn't find this in the help centre.
  check_support     fully
  check_useful      1
  rewrite_query     refund when the railway cancels a train, timelines by payment method
  retrieve          ['refunds.md §3', 'tatkal.md §2', 'payments.md §2']
  grade_documents   ['refunds.md §3', 'tatkal.md §2', 'payments.md §2']
  generate          Yes, it's refunded in full automatically [refunds.md §3]. It reaches UPI in 1 to 3 working days and cards in 5 to 7 working days [payments.md §2].
  check_support     fully
  check_useful      5
```

The user's words didn't match the help centre, so retrieval brought back weak pages and the relevance grader rejected all of them. The generator honestly said it couldn't find anything, which is fully supported (it claims nothing) but useless. The usefulness check sent the graph to rewrite the query in the help centre's vocabulary, the second retrieval found the right pages, and the final answer is grounded *and* useful.

### 9. Caps and what happens at the cap

Both loops have caps (`MAX_GENERATIONS`, `MAX_REWRITES`). Without them, a generator that keeps hallucinating or a question the knowledge base truly can't answer would loop until LangGraph's recursion limit raised an error. With them, the graph ends with the last answer. In production, don't silently return a last answer that failed its checks: attach the verdicts to the response and let the app decide.

| Final state | What to show the user |
|---|---|
| `support == "fully"` and `usefulness >= 4` | The answer, with citations |
| `support != "fully"` after the cap | A safe fallback: "I found related information but couldn't verify every detail", plus the sources |
| `usefulness < 4` after the cap | "I couldn't find this in the help centre", plus a route to a human |

### 10. Adaptive RAG, CRAG and Self-RAG side by side

| | Adaptive RAG | Corrective RAG | Self-RAG |
|---|---|---|---|
| **Main decision point** | Before retrieval | After retrieval | After generation (and before retrieval) |
| **Question it asks** | How much retrieval, from where? | Are these documents good enough? | Do I need retrieval, are documents relevant, is my answer supported and useful? |
| **What it fixes** | Wasted or insufficient retrieval | Irrelevant or missing documents | Hallucinated or unhelpful answers |
| **Corrective action** | Pick a strategy or source | Refine; rewrite and search the web | Regenerate; rewrite and retrieve again |
| **Extra cost** | One cheap classifier call | One evaluator call per document (and strip) | Several grader calls per attempt, plus retries |
| **Original form** | Trained complexity classifier | Trained retrieval evaluator | Fine-tuned model emitting reflection tokens |
| **Practical form** | Router node | Grader and fallback nodes | Grader nodes and capped loops |

They stack naturally. A production graph might route first (adaptive), grade and refine documents (corrective), and check the answer (self-reflective). The cost adds up too, which is why each check should earn its place on your evaluation set.

---

## Try It Yourself

1. **A stricter support check.** The support grader only checks numbers. Write an answer to the fee question that is wrong but contains only numbers from the document (for example, mixing up the 48-hour and 12-hour rules). Does the grader catch it? What does that tell you about rule-based graders?
2. **Change the weights.** In the decoding simulation, find weights under which the "Refunds go back to your original payment method" candidate wins. What does that weighting value?
3. **Hit the cap.** Set `MAX_GENERATIONS = 1` and trace the fee question again. What answer does the graph end with, and what should the app show the user?

<details>
<summary>Show answers</summary>

**1.**

```python
wrong = "Cancelling three days ahead loses 50% of the fare, as it's less than 12 hours before departure."
print(support_grader.invoke(SUPPORT_PROMPT.format(docs=format_docs(docs), answer=wrong)))
```

Output:

```
support='fully' unsupported_claims=[]
```

The rule says "fully supported" because "50%" and "12" both appear in the document, yet the answer applies the wrong rule. Rule-based checks catch invented facts, not misused ones. A real LLM grader reads the reasoning ("3 days is not less than 12 hours") and would flag it. In practice you combine both: cheap rules for invented numbers, an LLM grader for logic.

**2.**

```python
print(best_candidate({"is_sup": 3.0}))
```

Output:

```
('refunds.md §1', 3.65, 'The fee is a flat ₹60 per passenger.')
```

Even with all the weight on support, the correct answer still wins, because it is also well supported (0.95 against 0.90) and more fluent. No sensible weighting makes the third candidate win: you'd have to *reward* irrelevance or uselessness. That's the point of the exercise: support alone can't tell "true and relevant" from "true and irrelevant"; that's why IsRel and IsUse exist.

**3.**

```python
MAX_GENERATIONS = 1
out = self_rag.invoke({"question": "What is the fee to cancel 3 days before departure?"})
print(out["support"], out["generations"], "->", out["answer"])
MAX_GENERATIONS = 3
```

Output:

```
partially 1 -> It's a flat ₹60 per passenger plus 18% GST [refunds.md §1].
```

The graph stopped after one generation with a partially supported answer. The app should not show it as-is: it should show the fallback ("I found the fee rule but couldn't verify every detail") with the source, or strip the unsupported claim. The `support` field in the final state is what makes that decision possible.

</details>

---

## Real-World Examples

- **Healthcare and pharma assistants** run support checks on every answer about dosages and interactions, and refuse rather than answer when a claim can't be matched to a source document.
- **Financial services chatbots** check that every fee, rate and date in an answer appears in the retrieved terms and conditions, the exact numeric check you built, before a customer sees it.
- **Internal knowledge assistants** use the usefulness check to catch "I don't know" answers caused by poor queries, and retry with a rewritten query before giving up.

---

## Common Misconceptions

### "Self-RAG needs the special fine-tuned model"

The paper's version does. The practical graph version gets most of the behaviour with any capable model acting as generator and graders, at the cost of more calls.

### "Good retrieval prevents hallucination"

Models hallucinate even with perfect documents, especially numbers and conditions. Only a check on the answer itself catches that.

### "If the support check passes, the answer is correct"

It means the claims appear in the documents. The documents could be outdated, or the answer could combine true claims wrongly (as in exercise 1). Support is necessary, not sufficient.

### "Loop until every check passes"

Some questions can't pass: the knowledge base doesn't contain the answer. Without caps the graph loops until it errors. Cap every loop and design what happens at the cap.

---

## Interview Relevance

*"What is Self-RAG?"* A model trained to emit reflection tokens: Retrieve (should I retrieve?), IsRel (is this passage relevant?), IsSup (is my output supported?), IsUse (is it useful?). It retrieves on demand, generates candidates per passage, and ranks them with a weighted critique score whose weights can be tuned at inference time without retraining (Asai et al., 2023).

*"How would you build Self-RAG behaviour with an off-the-shelf model?"* LangGraph nodes for retrieval decision, document grading, generation, hallucination grading and answer grading, with conditional edges: unsupported → regenerate with feedback naming the unsupported claims; not useful → rewrite query and retrieve; caps on both loops and a defined fallback at the cap.

*"How does it differ from CRAG?"* CRAG checks documents before generation and corrects retrieval (including web search); Self-RAG also checks the generated answer for support and usefulness. They combine well.

---

## Key Takeaways

- **Self-RAG checks the answer**, not just the retrieval: Retrieve?, Relevant?, Supported?, Useful?
- **The paper's model emits reflection tokens** and ranks candidates with tunable weights, steering behaviour without retraining.
- **The practical version is a graph of graders** with two loops: regenerate when unsupported, rewrite and retrieve when not useful.
- **Give the generator specific feedback** (the unsupported claims), so retries fix the actual problem.
- **Cap every loop and define the fallback**, and pass the verdicts to the app.

---

**Up next:** [Self-RAG with a Vector DB](self-rag-with-a-vector-db.md)
