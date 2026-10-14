---
title: "What is a Large Language Model?"
course: "Generative AI and LLM Foundations"
module: "3. How LLMs Work"
type: Article
level: Beginner
reading_time: 40 min
---

# What is a Large Language Model?: The Complete Guide

> 📚 **Before you start**
>
> - [How Generative Models Work](../02-fundamentals-of-generative-ai/how-generative-models-work.md), for autoregressive generation and training as "make real data likely".
> - [Foundation Models](../02-fundamentals-of-generative-ai/foundation-models.md), for pretraining, scale and adaptation.
> - The [Transformers module](../../sequence-models-attention-and-transformers/course.md#m6) covers the architecture mathematically. This lesson gives you the intuition, so it is fine to read it first.

## Introduction

Your phone keyboard suggests the next word as you type. Type *"Happy"* and it offers *"birthday"*. Type *"I'll reach in"* and it offers *"10 minutes"*. It does this with a small model that has seen lots of messages.

Now imagine that keyboard model grown a million times larger, trained on a large share of all the text and code humans have written, and then carefully coached to be a helpful assistant. Ask it *"Explain why my UPI payment failed but money got debited"* and the "next word" suggestions, chosen one after another, add up to a clear, structured explanation. That, in one sentence, is a **large language model (LLM)**.

The "it just predicts the next word" description is true but misleading, the way "a cricket match is just 22 people and a ball" is true but misses the game. To predict the next word well across every topic, the model has to build internal representations of grammar, facts, arithmetic, code, cause and effect, and the intentions behind a question.

This lesson opens the box. By the end you'll be able to draw the full path from your text to the model's next token (tokens, embeddings, attention, logits, sampling), explain how parameters store what the model knows, and describe the four training stages (pretraining, instruction tuning, preference training with human or AI feedback, and reinforcement learning for reasoning) that turn random numbers into an assistant.

> 💡 **Key Insight**
>
> An LLM is a **transformer neural network that, given a sequence of tokens, outputs a probability for every possible next token**. Generation is that one step repeated. Its abilities come from **pretraining** on enormous text (learning the world's patterns) and its helpfulness comes from **post-training** (learning to follow instructions and match human preferences).

---

## Core Explanation

### 1. The definition, word by word

| Word | Meaning |
|---|---|
| **Large** | Billions to trillions of parameters, trained on trillions of tokens. "Large" is relative; today's small models would have been giant in 2019. |
| **Language** | It models sequences of tokens: natural language, but also code, maths notation, JSON, and (in multimodal models) image and audio pieces. |
| **Model** | A function with learned parameters. Given input tokens, it computes an output: a probability distribution over the next token. |

The models you know (Claude, GPT, Gemini, Llama, Qwen, DeepSeek, Mistral) are all **decoder-only transformers**: they read the text so far and predict what comes next. ("Decoder-only" distinguishes them from encoder models like BERT, which read a whole text at once to understand it, and from the original encoder-decoder transformer used for translation.)

### 2. The whole pipeline in one picture

![A pipeline. Your text "Ek cutting chai and one" goes into a tokenizer that splits it into common pieces, which become token IDs, then embedding vectors of thousands of numbers plus position. These flow through stacked transformer blocks: attention, where each token looks back at earlier tokens and pulls in what matters, and a feed-forward layer that applies patterns stored in the weights. The final vector for the last position becomes a score for every token in the vocabulary; softmax turns scores into probabilities such as samosa 36 percent and vada 24 percent; a sampler picks one token, which is appended to the text, and the whole thing repeats until done](/img/diagrams/generative-ai-and-llm-foundations/llm-pipeline.svg)
*One pass through this pipeline produces exactly one token. Keep this picture in mind for the rest of the module.*

We'll walk through each box with a tiny working example.

### 3. Step 1: text becomes tokens

A model can't read letters directly; it works with numbers. A **tokenizer** splits text into **tokens** (common words, parts of words, punctuation, spaces) and maps each to an integer **token ID** from a fixed **vocabulary**, typically 30,000 to a few hundred thousand entries.

Real tokenizers learn their vocabulary from data (you'll build one in [Tokens and Context Windows](tokens-and-context-windows.md)). For now a tiny word-level vocabulary is enough to see the idea:

```python
vocab = ["<end>", "ek", "do", "cutting", "masala", "chai", "and", "one", "samosa", "vada", "pav", "please"]
token_id = {tok: i for i, tok in enumerate(vocab)}

text = "ek cutting chai and one"
ids = [token_id[w] for w in text.split()]
print("Tokens:   ", text.split())
print("Token IDs:", ids)
```

Output:

```
Tokens:    ['ek', 'cutting', 'chai', 'and', 'one']
Token IDs: [1, 3, 5, 6, 7]
```

From here on, the model only ever sees those integers. It never sees letters, which is why LLMs are oddly bad at questions like "how many r's are in strawberry?": the word may arrive as one or two tokens, not as letters.

### 4. Step 2: tokens become vectors (embeddings)

Each token ID is looked up in a big table called the **embedding matrix**, which gives back a **vector**: a list of numbers (thousands of them in real models). These vectors are learned during training, and they end up placing tokens with related meanings near each other.

Here are hand-made 4-number vectors to show what "near each other" means. Imagine the four numbers loosely capture *is it a drink*, *is it food*, *is it hot*, *is it about travel*:

```python
import numpy as np

embedding = {
    "chai":   np.array([0.9, 0.1, 0.8, 0.0]),
    "coffee": np.array([0.8, 0.1, 0.7, 0.1]),
    "samosa": np.array([0.1, 0.9, 0.6, 0.0]),
    "vada":   np.array([0.1, 0.8, 0.5, 0.1]),
    "train":  np.array([0.0, 0.0, 0.1, 0.9]),
}

def cosine(a, b):
    """Similarity of direction: 1 means pointing the same way, 0 means unrelated."""
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

for other in ["coffee", "samosa", "train"]:
    print(f"similarity(chai, {other:<6}) = {cosine(embedding['chai'], embedding[other]):.2f}")
```

Output:

```
similarity(chai, coffee) = 1.00
similarity(chai, samosa) = 0.50
similarity(chai, train ) = 0.07
```

"chai" and "coffee" point in almost exactly the same direction (0.996, which rounds to 1.00); "chai" is further from "samosa" and far from "train". Nobody tells a real model what each dimension means; training discovers whatever arrangement helps predict the next token, and similar words end up in similar places because they appear in similar contexts. This is the same idea behind the embedding models used for search in [Embeddings and Similarity Search](../../retrieval-augmented-generation-rag/course.md#m3).

The model also needs to know **word order** ("dog bites man" versus "man bites dog"), so it adds information about each token's **position**. Modern LLMs mostly use a technique called rotary position embeddings, which encodes the relative distance between tokens.

### 5. Step 3: attention lets tokens look at each other

A token's embedding on its own is ambiguous. "Bank" means something different in "river bank" and "bank account". **Attention** is the mechanism that lets each token gather information from the tokens before it, so its vector becomes **context-aware**.

The intuition: each token asks a question (its **query**), every earlier token advertises what it contains (its **key**), and the token collects information (the **values**) mostly from those whose key matches its query. Mathematically:

1. Score each earlier token: dot product of my query with its key.
2. Turn scores into weights that add up to 1 with **softmax** (bigger score, bigger weight).
3. My new vector = weighted average of the values.

Let's watch the token "one" in *"ek cutting chai and one"* decide whom to pay attention to. We'll use tiny made-up query and key vectors in which "one" is looking for a *quantity-or-item* signal.

```python
def softmax(scores):
    e = np.exp(scores - np.max(scores))      # subtract the max for numerical stability
    return e / e.sum()

tokens = ["ek", "cutting", "chai", "and", "one"]
keys = np.array([
    [1.0, 0.0, 0.2],   # ek: a quantity
    [0.0, 0.6, 0.1],   # cutting: describes an item
    [0.1, 1.0, 0.0],   # chai: an item
    [0.0, 0.0, 1.0],   # and: a joiner
    [1.0, 0.1, 0.1],   # one: a quantity
])
query_for_one = np.array([1.2, 1.5, 0.0])     # "one" looks for quantities and items it might refer to

scores = keys @ query_for_one
weights = softmax(scores)
for tok, w in zip(tokens, weights):
    print(f"{tok:<8} {'#' * int(w * 40):<16} {w:.2f}")
```

Output:

```
ek       ########         0.21
cutting  ######           0.16
chai     ############     0.32
and      ##               0.06
one      #########        0.25
```

"one" pays most attention to "chai" and to the earlier quantity "ek". That is the kind of information the model needs to predict a sensible next token (another food or drink). In a real transformer:

- Queries, keys and values are produced by **learned weight matrices**, not set by hand.
- There are many **attention heads** in parallel (each can track a different relationship: grammar, coreference, "which item is being counted"), and dozens to over a hundred **layers** stacked on top of each other.
- In a decoder, attention is **causal**: a token can only look at itself and earlier tokens, never the future, because at generation time the future doesn't exist yet.

After attention, each layer applies a **feed-forward network** to every token's vector separately. A good intuition is that attention *moves information between tokens* and the feed-forward part *applies knowledge stored in the weights* (much of a model's factual knowledge seems to live there). Each layer refines every token's vector a little; after the last layer, the vector at the final position summarises "what should come next".

### 6. Step 4: from the final vector to probabilities

The final vector is multiplied by an output matrix to give one **score**, called a **logit**, for **every token in the vocabulary**. Softmax turns the logits into probabilities that add up to 1.

```python
# Pretend logits the model produced for the next token after "ek cutting chai and one"
logits = np.array([-1.0, -3.0, -2.0, 0.5, 0.2, 1.1, -2.5, -3.0, 2.0, 1.6, 0.3, -1.5])
probs = softmax(logits)

top = np.argsort(probs)[::-1][:5]
for i in top:
    print(f"{vocab[i]:<8} {probs[i]:.1%}")
print(f"Sum of all probabilities: {probs.sum():.2f}")
```

Output:

```
samosa   36.1%
vada     24.2%
chai     14.7%
cutting  8.1%
pav      6.6%
Sum of all probabilities: 1.00
```

This probability list is the model's real output. The text you see is produced by a **sampler** that picks one token from this list: always the top one (**greedy decoding**), or randomly in proportion to the probabilities, reshaped by settings like **temperature** and **top-p**. That choice is so important it gets its own lesson, [Temperature and Model Settings](temperature-and-model-settings.md).

### 7. Step 5: append and repeat

The chosen token is added to the input and the whole pipeline runs again to get the next one. This loop continues until the model emits a special **end-of-turn** token or hits the **maximum token limit** you set.

```python
def toy_next_token(context):
    """A stand-in for the transformer: returns logits for the next token given the context."""
    rules = {"one": "samosa", "samosa": "please", "please": "<end>"}
    best = rules.get(context[-1], "<end>")
    scores = np.full(len(vocab), -5.0)
    scores[token_id[best]] = 5.0
    return scores

context = text.split()
while True:
    nxt = vocab[int(np.argmax(toy_next_token(context)))]     # greedy: take the most likely token
    if nxt == "<end>":
        break
    context.append(nxt)
    print(" ".join(context))
```

Output:

```
ek cutting chai and one samosa
ek cutting chai and one samosa please
```

Two practical consequences fall straight out of this loop:

- **Output costs time.** Each output token is a full pass through the model, so long answers take longer. Input tokens can be processed in parallel, which is why providers charge less for input tokens than for output tokens.
- **The model can't take back a token.** Once a word is chosen, every later word is conditioned on it. A wrong early choice can snowball. Reasoning models reduce this by "thinking" before committing to an answer (section 12).

### 8. Parameters: where the knowledge lives

A model's **parameters** are all the numbers in its embedding table, attention matrices and feed-forward layers. A rough estimate for a standard transformer is about **12 × d² parameters per layer** (where *d* is the size of each token's vector, the "model width"), plus the embedding table.

```python
def estimate_params(n_layers, d_model, vocab_size):
    per_layer = 12 * d_model**2          # attention (about 4·d²) + feed-forward (about 8·d²)
    embeddings = vocab_size * d_model
    return n_layers * per_layer + embeddings

for name, layers, width in [("small", 24, 2048), ("medium", 32, 4096), ("large", 80, 8192)]:
    print(f"{name:<7} {layers:>3} layers, width {width:>5}: about {estimate_params(layers, width, 128_000) / 1e9:.1f} billion parameters")
```

Output:

```
small    24 layers, width  2048: about 1.5 billion parameters
medium   32 layers, width  4096: about 7.0 billion parameters
large    80 layers, width  8192: about 65.5 billion parameters
```

Those shapes give roughly 1.5, 7 and 65 billion parameters, close to real model families of those sizes. Two things to remember about parameters:

- **Knowledge is distributed.** There is no row that stores "the capital of Karnataka is Bengaluru". The fact is spread across many weights and can only be read out by running the model. That's why you can't simply edit or delete one fact.
- **Weights are frozen after training.** The model doesn't learn from your chat. Within a conversation it can use what you tell it (that's **in-context learning**), but once the conversation ends, nothing is remembered unless the application stores it.

Many large models in 2026 use a **mixture-of-experts (MoE)** design: each layer has many feed-forward "experts", and a small router sends each token to only a few of them. A model can then have a huge total parameter count while using only a fraction of it per token, which keeps it fast. DeepSeek's open-weight models are well-known examples.

### 9. How LLMs are trained: the four stages

![Four stages in bands. Stage 1, pretraining: huge raw text of trillions of tokens is used to predict the next token for months on GPU clusters, giving a base model that knows language but only continues text. Stage 2, supervised fine-tuning: thousands to millions of instruction and ideal reply examples train an instruction-following model. Stage 3, RLHF or RLAIF: a judge, human or AI guided by written principles, picks the better of two replies; a reward model learns to score replies and reinforcement learning improves the model, giving an assistant model; DPO learns from the pairs directly. Stage 4, RLVR: checkable problems like maths with known answers and code with unit tests reward correct final answers, producing a reasoning model that thinks before answering](/img/diagrams/generative-ai-and-llm-foundations/llm-training-stages.svg)
*Each stage starts from the model the previous stage produced. Stages 2 to 4 together are called post-training.*

### 10. Stage 1: pretraining

**Pretraining** is where nearly all the compute goes and nearly all the knowledge comes from. The model reads a huge, cleaned mix of web pages, books, code, scientific papers and other text, and at every position it is asked to predict the next token. The loss is the **cross-entropy**: how surprised the model was by the token that actually came next, measured as the negative log of the probability it gave that token.

```python
def next_token_loss(probabilities, actual_token):
    return -np.log(probabilities[token_id[actual_token]])

print(f"Actual next token 'samosa': loss {next_token_loss(probs, 'samosa'):.2f}  (model gave it {probs[token_id['samosa']]:.0%})")
print(f"Actual next token 'please': loss {next_token_loss(probs, 'please'):.2f}  (model gave it {probs[token_id['please']]:.0%})")
```

Output:

```
Actual next token 'samosa': loss 1.02  (model gave it 36%)
Actual next token 'please': loss 4.52  (model gave it 1%)
```

Training nudges every parameter to make the actual next token a little more likely, trillions of times over. To get good at this across all text, the model has to learn spelling, grammar, facts, styles, translation, code syntax and even some reasoning, because all of these help predict the next token.

The result is a **base model**: knowledgeable, but it simply continues text. Give it *"Q: What is the capital of India?\nA:"* and it may well answer, because that pattern is common, but give it *"Write a leave application"* and it might continue with *"for a school teacher. Template 2: ..."*, imitating a web page full of templates.

Pretraining data also sets the model's **knowledge cutoff**: it knows nothing about events after its training data was collected.

### 11. Stage 2: instruction tuning (supervised fine-tuning)

**Supervised fine-tuning (SFT)**, also called **instruction tuning**, trains the base model further on examples of the behaviour we want: an instruction or conversation, followed by an ideal assistant reply, often written or checked by skilled people. The loss is the same next-token loss, but computed only on the reply tokens.

A single training example looks something like this (shown as JSON; formats vary by lab):

```python
import json

sft_example = {
    "messages": [
        {"role": "system", "content": "You are a helpful banking assistant."},
        {"role": "user", "content": "My UPI payment failed but money was debited. What should I do?"},
        {"role": "assistant", "content": "Failed UPI payments are usually reversed automatically within a few working days. "
                                         "Note the transaction reference number, check your bank statement after that period, "
                                         "and if it isn't reversed, raise a complaint in your UPI app or with your bank."},
    ]
}
print(json.dumps(sft_example, indent=2))
```

Output:

```
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful banking assistant."
    },
    {
      "role": "user",
      "content": "My UPI payment failed but money was debited. What should I do?"
    },
    {
      "role": "assistant",
      "content": "Failed UPI payments are usually reversed automatically within a few working days. Note the transaction reference number, check your bank statement after that period, and if it isn't reversed, raise a complaint in your UPI app or with your bank."
    }
  ]
}
```

After SFT the model answers in the assistant format: it responds to the request, uses the conversation roles, and stops at the end of its turn. You'll meet these **roles** (system, user, assistant) again in [System Prompts and Roles](../course.md#m4).

### 12. Stage 3: preference training with RLHF, RLAIF or DPO

Writing a perfect answer for every situation is impossible, but **comparing** two answers is easy. Preference training uses comparisons to teach the model what "better" means: more helpful, more honest, more careful with harmful requests.

**RLHF (reinforcement learning from human feedback)** works in three steps:

1. The model writes two (or more) replies to the same prompt. **Human raters** pick the better one.
2. A **reward model** (usually another copy of an LLM with a scoring head) is trained on these comparisons to predict which reply people would prefer, outputting a score.
3. The LLM is trained with **reinforcement learning (RL)**: it writes replies, the reward model scores them, and the LLM's parameters are nudged towards higher-scoring replies. A penalty keeps it from drifting too far from the SFT model, so it doesn't learn to "game" the reward model with weird text.

The reward model's core idea is simple: if it scores reply A higher than reply B, it should predict that people prefer A. A common formula turns the score difference into a probability with the **sigmoid** function:

```python
def prob_a_preferred(reward_a, reward_b):
    return 1 / (1 + np.exp(-(reward_a - reward_b)))

preference_pair = {
    "prompt": "My UPI payment failed but money was debited. What should I do?",
    "reply_a": "Wait a few working days for the automatic reversal, keep the reference number, then complain via your app or bank if needed.",
    "reply_b": "Payments fail sometimes.",
    "human_choice": "a",
}
for ra, rb in [(2.0, -1.0), (0.5, 0.0), (-1.0, 2.0)]:
    print(f"reward A {ra:+.1f}, reward B {rb:+.1f} -> P(A preferred) = {prob_a_preferred(ra, rb):.2f}")
```

Output:

```
reward A +2.0, reward B -1.0 -> P(A preferred) = 0.95
reward A +0.5, reward B +0.0 -> P(A preferred) = 0.62
reward A -1.0, reward B +2.0 -> P(A preferred) = 0.05
```

Training the reward model means adjusting it so that, on real comparisons like `preference_pair`, the reply people chose gets the higher score.

**RLAIF (reinforcement learning from AI feedback)** replaces most human raters with an AI judge. Anthropic's **Constitutional AI** method (published in 2022) is the best-known version: the AI judge compares replies against a written set of principles, the "constitution", such as *choose the response that is more honest and less likely to cause harm*. RLAIF scales to far more comparisons than humans could label, and the principles are written down and inspectable, though humans still design the principles and check the results.

**DPO (direct preference optimisation)**, introduced in 2023, skips the separate reward model and the RL loop: it adjusts the LLM directly so that preferred replies become more likely than rejected ones. It is simpler and cheaper, and widely used for open-weight models. Labs combine these methods in different ways.

### 13. Stage 4: reinforcement learning for reasoning

From late 2024, a fourth stage became central: **reinforcement learning with verifiable rewards (RLVR)**. The model is given problems whose answers can be **checked automatically**: maths with known answers, code with unit tests, puzzles with verifiable solutions. It writes out its reasoning, gives an answer, and is rewarded only if the answer is correct.

```python
problems = [
    {"question": "A chai costs ₹15. How much do 7 chais cost?", "answer": 105},
    {"question": "Train leaves 09:40, journey 2h 35m. Arrival minute past the hour?", "answer": 15},
]
attempts = [
    {"thinking": "15 x 7 = 105", "final": 105},
    {"thinking": "09:40 + 2:35 = 11:75", "final": 75},     # forgot that 75 minutes is 1h 15m
]
for prob, att in zip(problems, attempts):
    reward = 1.0 if att["final"] == prob["answer"] else 0.0
    print(f"reward {reward}  <- {prob['question']}")
```

Output:

```
reward 1.0  <- A chai costs ₹15. How much do 7 chais cost?
reward 0.0  <- Train leaves 09:40, journey 2h 35m. Arrival minute past the hour?
```

The second attempt forgot to carry the hour, so it earns nothing. Nobody has to label how to think; the model discovers that **longer, more careful reasoning** (checking its work, trying another approach when stuck) earns more reward. The results are **reasoning models**, such as OpenAI's o1 (2024) and its successors, DeepSeek-R1 (January 2025), and the extended or adaptive thinking modes in Claude and Gemini. They "think" in hidden or summarised reasoning tokens before answering, and you can often set how much effort they spend. You'll see this as a setting in [Temperature and Model Settings](temperature-and-model-settings.md) and as a breakthrough in [Recent Breakthroughs in GenAI](../course.md#m5).

### 14. What an LLM is and isn't

| An LLM is | An LLM is not |
|---|---|
| A function from tokens to next-token probabilities | A database that looks up stored answers |
| Knowledgeable up to its training cutoff | Aware of today's news (unless given tools or documents) |
| Able to use whatever you put in its context window | Able to remember past conversations on its own |
| Often able to reason through problems step by step | Guaranteed correct; it can make confident errors |
| Shaped by post-training to be helpful and careful | A person with opinions, memories or goals of its own |

The next lessons build on this picture: [Tokens and Context Windows](tokens-and-context-windows.md) zooms in on step 1 and on how much the model can read at once; [Temperature and Model Settings](temperature-and-model-settings.md) zooms in on the sampler; [Where LLMs Fail](where-llms-fail.md) explains the failure modes that follow from all of this.

---

## Try It Yourself

1. **Change the query.** In the attention example, make "one" look only for quantities by setting `query_for_one = np.array([2.0, 0.0, 0.0])`. Which tokens get the most attention now?
2. **Greedy vs probable.** From the `probs` printed in section 6, what token would greedy decoding pick? What is the chance that random sampling picks something else?
3. **Loss intuition.** What loss does the model get if it gave the correct next token a probability of 0.99? Of 0.01? Why does the loss punish confident mistakes so heavily?

<details>
<summary>Show answers</summary>

**1.**

```python
weights = softmax(keys @ np.array([2.0, 0.0, 0.0]))
for tok, w in zip(tokens, weights):
    print(f"{tok:<8} {w:.2f}")
```

Output:

```
ek       0.41
cutting  0.06
chai     0.07
and      0.06
one      0.41
```

Attention shifts to the quantity words "ek" and "one". Different queries pull different information, which is why real models use many attention heads, each with its own learned queries.

**2.**

```python
best = int(np.argmax(probs))
print(f"Greedy picks {vocab[best]!r}; chance of sampling something else: {1 - probs[best]:.0%}")
```

Output:

```
Greedy picks 'samosa'; chance of sampling something else: 64%
```

**3.**

```python
for p in [0.99, 0.5, 0.01]:
    print(f"P(correct) = {p:<4} -> loss {-np.log(p):.2f}")
```

Output:

```
P(correct) = 0.99 -> loss 0.01
P(correct) = 0.5  -> loss 0.69
P(correct) = 0.01 -> loss 4.61
```

The loss is the negative log, which grows without limit as the probability approaches 0. Being confidently wrong costs far more than being unsure, so training pushes the model to spread probability sensibly.

</details>

---

## Real-World Examples

- **Chat assistants** (Claude, ChatGPT, Gemini) are decoder-only transformers that went through all four training stages; their reasoning modes come from stage 4.
- **Coding assistants** are LLMs heavily trained on code and, increasingly, with RL against unit tests, which is why they've improved so fast at real programming tasks.
- **On-device models**: smaller LLMs run on phones and laptops for quick tasks like summarising notifications, trading capability for privacy and speed.
- **Open-weight models** let companies run LLMs on their own servers and fine-tune them, for example on Indian legal or medical text.

---

## Common Misconceptions

### "It's just autocomplete, so it can't reason"

The training objective is next-token prediction, but to predict well across all text the model builds rich internal representations, and RL training explicitly rewards correct multi-step reasoning. It reasons imperfectly, but it does reason in a practical sense.

### "The model looks up answers on the internet"

A plain LLM doesn't browse. It generates from what its parameters encode, plus whatever is in its context. Products that "search the web" give the model a search tool and put the results into its context.

### "It learns from my conversations as I chat"

The weights don't change during a chat. Some products store your conversations (and some providers may use data for future training under their policies), but the model you're talking to isn't updating itself live.

### "RLHF teaches the model new knowledge"

Preference training mainly shapes **behaviour**: tone, helpfulness, honesty, refusals. Knowledge overwhelmingly comes from pretraining.

---

## Interview Relevance

*"Explain how an LLM generates text"* is one of the most common AI-engineering interview questions. A strong answer walks the pipeline: tokenizer to token IDs; embedding lookup plus positional information; stacked transformer blocks of causal self-attention and feed-forward layers; final vector to logits over the vocabulary; softmax to probabilities; a sampling strategy picks a token; append and repeat until an end token or the max-token limit.

*"How are models like Claude or GPT trained?"* Cover pretraining (self-supervised next-token prediction on trillions of tokens, giving a base model and a knowledge cutoff), SFT on instruction-reply demonstrations, preference training (RLHF with a reward model and RL; RLAIF and Constitutional AI with an AI judge and written principles; DPO as a simpler alternative), and RL with verifiable rewards producing reasoning models. Bonus points: explain why output tokens cost more than input tokens, what mixture-of-experts is, and why the model can't "unlearn" a single fact easily.

---

## Key Takeaways

- **An LLM maps tokens to next-token probabilities**; generation is that step in a loop.
- **The pipeline**: tokenize, embed, attend (tokens look at earlier tokens), feed-forward, logits, softmax, sample, append.
- **Knowledge lives in billions of frozen parameters**, spread across the network, up to a training cutoff.
- **Four training stages**: pretraining (knowledge), SFT (follow instructions), RLHF/RLAIF/DPO (preferences and safety), RL with verifiable rewards (reasoning).
- **Behaviour comes from post-training; knowledge comes from pretraining**; context comes from you.

---

**Up next:** [Tokens and Context Windows](tokens-and-context-windows.md)
