---
title: "Chat Models"
course: LangChain Complete Guide
module: "3. Models"
type: Article
level: Intermediate
reading_time: 30 min
---

# Chat Models: The Complete Guide

> 📚 **Before you start**
>
> - [LLMs vs Chat Models](llms-vs-chat-models.md), for the chat model interface and the `AIMessage` it returns.
> - [Temperature and Model Settings](../../generative-ai-and-llm-foundations/03-how-llms-work/temperature-and-model-settings.md), for temperature, max tokens and reasoning effort.
> - [Setting Up a LangChain Project and API Keys](../02-langchain-foundations/setting-up-a-langchain-project-and-api-keys.md), for keys and the model factory.

## Introduction

Think of booking a cab in an Indian city. Ola, Uber, Rapido and the local auto stand all get you from A to B, but each has its own app, its own fare screen and its own way of saying "driver arriving". Now imagine one app where you type the destination once and pick any operator from a dropdown, and the ride, fare and receipt screens look the same whichever you chose.

LangChain's chat models are that one app for language models. Claude, GPT, Gemini, Llama running on your laptop: each is a **chat model** class with the same methods (`invoke`, `stream`, `batch`), the same input (messages) and the same output (`AIMessage`). This lesson is the full tour: creating models (with `init_chat_model` or a provider class), the settings every model shares, reading everything in the reply, streaming, batching, async, token tracking, retries, rate limits and fallbacks. By the end you can use any chat model in production-quality code, and switch between them without touching the rest of your app.

> 💡 **Key Insight**
>
> A chat model is a **runnable with a standard contract**: messages in, `AIMessage` out, with `invoke` for one call, `stream` for tokens as they arrive, and `batch` for many inputs at once. Provider differences live in the constructor; everything after creation is the same code.

---

## Core Explanation

### 1. Two ways to create a chat model

**Option A: `init_chat_model`** (from `langchain`) creates any supported model from a `"provider:model"` string:

```python
# not-run: needs `pip install langchain langchain-anthropic` and ANTHROPIC_API_KEY
from langchain.chat_models import init_chat_model

model = init_chat_model("anthropic:claude-opus-5-5", temperature=0, max_tokens=1024)
print(type(model).__name__)
```

Example output:

```
ChatAnthropic
```

**Option B: the provider class** directly, from the provider package:

```python
# not-run: needs `pip install langchain-anthropic` and ANTHROPIC_API_KEY
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-opus-5-5", temperature=0, max_tokens=1024)
```

Both give you the same object. Which to use?

| | `init_chat_model("provider:model")` | Provider class (`ChatAnthropic(...)`) |
|---|---|---|
| Switching models by config | Easy: the whole choice is one string | You import a different class |
| Provider-specific options | Passed through as keyword arguments | Visible in your editor's autocomplete |
| Good for | Apps where the model is a setting; comparing providers | Code that uses one provider's special features |

A few `provider:` prefixes you'll see: `anthropic`, `openai`, `google_genai`, `bedrock_converse`, `ollama`, `huggingface`, `mistralai`, `groq`. Each needs its provider package installed. If the provider can be guessed from the model name, the prefix is optional, and you can also pass `model_provider="..."` separately.

### 2. Settings every chat model understands

These **standard parameters** work the same across providers (each provider maps them to its own API):

| Parameter | What it controls | Typical value |
|---|---|---|
| `model` | Which model | `"claude-opus-5-5"` |
| `temperature` | Randomness of token choice | `0` for extraction, `0.7` for creative text |
| `max_tokens` | Upper limit on the reply length | `1024` |
| `timeout` | Seconds to wait before giving up | `30` |
| `max_retries` | How many times to retry temporary failures | `6` (the default) |
| `api_key` | The key, if not taken from the environment | Usually leave unset |
| `base_url` | A different endpoint (proxies, OpenAI-compatible servers) | Usually leave unset |
| `rate_limiter` | Throttle requests per second | See section 9 |

Newer reasoning models also accept `reasoning_effort` (for example `"low"`, `"medium"`, `"high"`), which LangChain maps to each provider's own name for it. You met these settings conceptually in [Temperature and Model Settings](../../generative-ai-and-llm-foundations/03-how-llms-work/temperature-and-model-settings.md).

### 3. What you can pass to `invoke`

A chat model accepts three input shapes, which all become a list of messages:

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel, ParrotFakeChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

parrot = ParrotFakeChatModel()      # replies with the last message it received

inputs = {
    "a plain string": "Which platform does the Shatabdi leave from?",
    "role/content dicts": [{"role": "system", "content": "You help at New Delhi station."},
                           {"role": "user", "content": "Which platform does the Shatabdi leave from?"}],
    "message objects": [SystemMessage("You help at New Delhi station."),
                        HumanMessage("Which platform does the Shatabdi leave from?")],
}
for label, value in inputs.items():
    last = parrot.invoke(value)
    print(f"{label:<20} -> last message is a {type(last).__name__}")
```

Output:

```
a plain string       -> last message is a HumanMessage
role/content dicts   -> last message is a HumanMessage
message objects      -> last message is a HumanMessage
```

Message objects are the clearest and are what prompt templates produce, so you'll use them most. The dict form is handy when messages come from JSON (for example, a web front end).

### 4. Everything in the reply

Real replies carry a lot more than text. Here is a reply shaped like one from Claude, built with `GenericFakeChatModel` (a fake that returns whatever messages you script, including their metadata):

```python
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

scripted = AIMessage(
    content="Platform 1. The 12002 Shatabdi departs at 06:00.",
    usage_metadata={"input_tokens": 31, "output_tokens": 14, "total_tokens": 45},
    response_metadata={"model_name": "claude-opus-5-5", "stop_reason": "end_turn"},
)
model = GenericFakeChatModel(messages=iter([scripted]))
reply = model.invoke("Which platform does the Shatabdi leave from?")

print("text         :", reply.text)
print("usage        :", reply.usage_metadata)
print("model        :", reply.response_metadata["model_name"])
print("stop reason  :", reply.response_metadata["stop_reason"])
print("tool calls   :", reply.tool_calls)
```

Output:

```
text         : Platform 1. The 12002 Shatabdi departs at 06:00.
usage        : {'input_tokens': 31, 'output_tokens': 14, 'total_tokens': 45}
model        : claude-opus-5-5
stop reason  : end_turn
tool calls   : []
```

| What you want | Where it is | Why it matters |
|---|---|---|
| The answer text | `reply.text` (or `reply.content` for plain text) | Show it to the user |
| Token counts | `reply.usage_metadata` | Cost tracking and limits |
| Why it stopped | `reply.response_metadata` (the key name varies by provider: `stop_reason`, `finish_reason`) | Detect cut-off replies (`max_tokens`) |
| Tool requests | `reply.tool_calls` | Run tools (Module 7) |
| Provider-neutral parts | `reply.content_blocks` | Read text, reasoning, images or tool calls the same way for every provider |

`usage_metadata` uses the same keys for every provider; `response_metadata` holds the provider's own fields, so its keys differ. When you need to check a cut-off reply, look up the provider's key once and wrap it in a helper.

### 5. Streaming: tokens as they arrive

A long answer can take several seconds. **Streaming** shows it word by word, which feels much faster to users. `stream()` returns a generator of `AIMessageChunk`s (you met generators in [Iterators and Generators](../../python-programming/06-functions-and-iterators/iterators-and-generators.md)):

```python
model = FakeListChatModel(responses=["Platform 1, departs 06:00."])
for chunk in model.stream("Which platform for the Shatabdi?"):
    print(repr(chunk.content), end=" ")
print()
```

Output:

```
'P' 'l' 'a' 't' 'f' 'o' 'r' 'm' ' ' '1' ',' ' ' 'd' 'e' 'p' 'a' 'r' 't' 's' ' ' '0' '6' ':' '0' '0' '.'
```

(The fake streams one character at a time; real models stream a few tokens per chunk.) Chunks can be **added together** with `+` to rebuild the full message, which is how you keep the final answer while showing it live:

```python
full = None
for chunk in model.stream("Which platform for the Shatabdi?"):
    full = chunk if full is None else full + chunk
print(type(full).__name__, "->", full.content)
```

Output:

```
AIMessageChunk -> Platform 1, departs 06:00.
```

In a web app, you'd forward each chunk's text to the browser as it arrives (Module 8 shows streaming over HTTP).

### 6. Batching: many inputs at once

`batch()` runs several independent inputs **in parallel** (using threads) and returns results in the same order as the inputs:

Because batched calls run in parallel, a fake that hands out scripted replies in call order could give them to the wrong question. So here's a tiny deterministic chat model instead: `SimpleChatModel` lets you write a chat model as one `_call` method that returns a string.

```python
from langchain_core.language_models import SimpleChatModel

PLATFORMS = {"Shatabdi": "Platform 1", "Rajdhani": "Platform 16", "Duronto": "Platform 3"}

class TimetableModel(SimpleChatModel):
    """Answers platform questions from a dict, so parallel calls stay predictable."""
    @property
    def _llm_type(self):
        return "timetable"

    def _call(self, messages, stop=None, run_manager=None, **kwargs):
        question = messages[-1].content
        return next((p for train, p in PLATFORMS.items() if train in question), "Please check the display board.")

model = TimetableModel()
questions = ["Shatabdi platform?", "Rajdhani platform?", "Duronto platform?"]
answers = model.batch(questions, config={"max_concurrency": 2})
for q, a in zip(questions, answers):
    print(f"{q:<20} {a.content}")
```

Output:

```
Shatabdi platform?   Platform 1
Rajdhani platform?   Platform 16
Duronto platform?    Platform 3
```

`max_concurrency` caps how many calls run at once, which protects you from provider rate limits. Use `batch` whenever you have a list of independent items: classifying 500 reviews, translating 200 product titles. (`batch_as_completed` yields each result as soon as it's ready, paired with its index.) Note this is LangChain's **client-side** parallelism; some providers also offer a separate, cheaper "batch API" for offline jobs, which is a different feature.

### 7. Async: `ainvoke`, `astream`, `abatch`

Every method has an async twin with an `a` prefix. In a web server (like FastAPI) async calls let one process handle many users while waiting on the model:

```python
import asyncio

async def main():
    model = FakeListChatModel(responses=["Platform 1", "Platform 16"])
    replies = await asyncio.gather(
        model.ainvoke("Shatabdi platform?"),
        model.ainvoke("Rajdhani platform?"),
    )
    return sorted(r.content for r in replies)

print(asyncio.run(main()))
```

Output:

```
['Platform 1', 'Platform 16']
```

(We sort because concurrent calls may finish in any order.) You learned `async`/`await` in [async and await in Streamlit](../../apis-and-apps-fastapi-streamlit-and-docker/07-state-and-responsiveness/async-and-await-in-streamlit.md); the same rules apply here.

### 8. Tracking tokens and cost across many calls

`usage_metadata` tells you the cost of one reply. To total several calls, attach a `UsageMetadataCallbackHandler`; it adds up usage per model name:

```python
from langchain_core.callbacks import UsageMetadataCallbackHandler

def reply(text, i, o):
    return AIMessage(text, usage_metadata={"input_tokens": i, "output_tokens": o, "total_tokens": i + o},
                     response_metadata={"model_name": "claude-opus-5-5"})

model = GenericFakeChatModel(messages=iter([reply("Platform 1", 30, 4), reply("Platform 16", 32, 5)]))
usage = UsageMetadataCallbackHandler()
for q in ["Shatabdi platform?", "Rajdhani platform?"]:
    model.invoke(q, config={"callbacks": [usage]})
totals = usage.usage_metadata["claude-opus-5-5"]
print({k: totals[k] for k in ("input_tokens", "output_tokens", "total_tokens")})   # fixed key order
```

Output:

```
{'input_tokens': 62, 'output_tokens': 9, 'total_tokens': 71}
```

`usage.usage_metadata` is a dict keyed by model name; we picked out the three counts in a fixed order for printing. Multiply by your provider's price per million tokens and you have the cost of a request, a user or a day. ([The GenAI Project Lifecycle](../../generative-ai-and-llm-foundations/05-advances-and-applications/the-genai-project-lifecycle.md) covered why this number matters.)

### 9. When things go wrong: retries, rate limits and fallbacks

Model APIs fail in predictable ways: rate limits (HTTP 429), overloaded servers (5xx), timeouts, network errors. Chat models already **retry** these with exponential backoff (`max_retries`, default 6); authentication errors (401) and wrong model names (404) are not retried, because retrying can't fix them.

On top of that you have two more tools.

**Rate limiting** spaces out your own requests so you stay under a provider's limit, which matters most with `batch`:

```python
# not-run: needs `pip install langchain langchain-anthropic` and ANTHROPIC_API_KEY
from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter

limiter = InMemoryRateLimiter(requests_per_second=2, check_every_n_seconds=0.1, max_bucket_size=5)
model = init_chat_model("anthropic:claude-opus-5-5", rate_limiter=limiter)
results = model.batch([f"Summarise review {i}" for i in range(50)])   # never more than ~2 requests/second
```

**Fallbacks** switch to a backup model when the main one fails, so a provider outage doesn't take your app down. Every runnable has `.with_fallbacks([...])`:

```python
class DownModel(FakeListChatModel):
    """Pretends the provider is down."""
    def _call(self, *args, **kwargs):
        raise ConnectionError("503 Service Unavailable")

primary = DownModel(responses=["unused"])
backup = FakeListChatModel(responses=["Platform 1 (answered by the backup model)"])
resilient = primary.with_fallbacks([backup])
print(resilient.invoke("Which platform for the Shatabdi?").content)
```

Output:

```
Platform 1 (answered by the backup model)
```

A common production setup: a strong model as primary, a model from a different provider as fallback, so an outage at one company doesn't stop you.

### 10. Choosing the model at run time

Sometimes the model should be picked per request: a cheaper model for free users, a stronger one for paid users, or a model the user picks from a dropdown. `init_chat_model` can create a **configurable** model whose choice is supplied in the config at call time:

```python
# not-run: needs `pip install langchain langchain-anthropic langchain-openai` and both API keys
from langchain.chat_models import init_chat_model

model = init_chat_model(temperature=0)          # no model fixed yet
fast = model.invoke("Hi", config={"configurable": {"model": "anthropic:claude-haiku-4-5"}})
strong = model.invoke("Plan a 3-day Jaipur trip", config={"configurable": {"model": "anthropic:claude-opus-5-5"}})
```

With fakes, the same idea is simply a function or a dict of models; a plain `dict` lookup is often all you need.

### 11. A model-agnostic `ask()` helper

Here is everything together: one function that works with any chat model and returns what production code needs.

```python
def ask(model, question, system="You are a helpful railway enquiry assistant. Be brief."):
    reply = model.invoke([SystemMessage(system), HumanMessage(question)])
    usage = reply.usage_metadata or {}
    return {
        "answer": reply.text,
        "tokens": usage.get("total_tokens"),
        "stopped_because": reply.response_metadata.get("stop_reason") or reply.response_metadata.get("finish_reason"),
    }

fake = GenericFakeChatModel(messages=iter([scripted]))
print(ask(fake, "Which platform does the Shatabdi leave from?"))
```

Output:

```
{'answer': 'Platform 1. The 12002 Shatabdi departs at 06:00.', 'tokens': 45, 'stopped_because': 'end_turn'}
```

Swap `fake` for `init_chat_model("anthropic:claude-opus-5-5")` and nothing else changes:

```python
# not-run: needs `pip install langchain langchain-anthropic` and ANTHROPIC_API_KEY
from langchain.chat_models import init_chat_model

print(ask(init_chat_model("anthropic:claude-opus-5-5", temperature=0), "Which platform does the Shatabdi leave from at New Delhi?"))
```

Example output:

```
{'answer': "Platform numbers can change daily, so check the NTES app or the station display. The New Delhi–Bhopal Shatabdi usually departs from platform 1.", 'tokens': 78, 'stopped_because': 'end_turn'}
```

Notice the real model's caution about live data it can't know. That's exactly the gap tools fill in Module 7.

---

## Try It Yourself

1. **Stream and count.** Stream a `FakeListChatModel` reply of `"Namaste, welcome aboard!"` and count how many chunks arrive. Then rebuild the full text with `+`.
2. **Two fallbacks.** Make a chain of fallbacks where the first two models are `DownModel`s and the third answers. Does it work?
3. **Batch order.** Batch 4 questions with `max_concurrency=1` and then with `max_concurrency=4`. Is the order of answers the same?
4. **Cut-off detection.** Write `was_cut_off(reply)` that returns `True` when the stop reason is `"max_tokens"` (Anthropic) or `"length"` (OpenAI). Test it on an `AIMessage` with `response_metadata={"stop_reason": "max_tokens"}`.

<details>
<summary>Show answers</summary>

**1.**

```python
chunks = list(FakeListChatModel(responses=["Namaste, welcome aboard!"]).stream("hi"))
full = chunks[0]
for c in chunks[1:]:
    full = full + c
print(len(chunks), "chunks ->", full.content)
```

Output:

```
24 chunks -> Namaste, welcome aboard!
```

**2.**

```python
chain_of_backups = DownModel(responses=["x"]).with_fallbacks([
    DownModel(responses=["x"]),
    FakeListChatModel(responses=["third model answered"]),
])
print(chain_of_backups.invoke("hello").content)
```

Output:

```
third model answered
```

Fallbacks are tried in order until one succeeds.

**3.**

```python
qs = ["q1", "q2", "q3", "q4"]
for c in (1, 4):
    m = ParrotFakeChatModel()
    print(c, [r.content for r in m.batch(qs, config={"max_concurrency": c})])
```

Output:

```
1 ['q1', 'q2', 'q3', 'q4']
4 ['q1', 'q2', 'q3', 'q4']
```

`batch` always returns results in input order, however many run at once. (We used the parrot so each answer matches its question.)

**4.**

```python
def was_cut_off(reply):
    reason = reply.response_metadata.get("stop_reason") or reply.response_metadata.get("finish_reason")
    return reason in {"max_tokens", "length"}

print(was_cut_off(AIMessage("The Shatabdi departs at", response_metadata={"stop_reason": "max_tokens"})))
print(was_cut_off(scripted))
```

Output:

```
True
False
```

</details>

---

## Real-World Examples

- **Chat UIs** (support widgets, internal assistants) use `astream` so text appears instantly, and keep the combined chunk for logging.
- **Bulk jobs** (tagging thousands of support tickets) use `batch` with `max_concurrency` and a rate limiter to stay within provider limits.
- **High-availability apps** wrap their main model with `with_fallbacks` to a second provider; outages at one provider then only raise latency, not errors.
- **Cost dashboards** sum `usage_metadata` per user and per feature, often through LangSmith (Module 8).

---

## Common Misconceptions

### "Each provider needs different code"

Only the constructor differs. `invoke`, `stream`, `batch`, messages and `AIMessage` are the same across providers. Provider-specific extras (like prompt caching options) are the exception, and they're passed as extra arguments.

### "`batch` is cheaper than calling `invoke` in a loop"

It's **faster** (parallel), not cheaper: it makes the same number of API calls. Providers' own offline batch APIs, which are a separate feature, are what give discounts.

### "Retries mean my app can't fail"

Retries handle temporary errors. A bad key, a wrong model name or an invalid request fails every time; and a long outage outlasts any retry budget. That's what fallbacks and good error messages are for.

### "Streaming changes the answer"

Streaming changes only **when** you see the tokens. The combined chunks equal the non-streamed reply.

---

## Interview Relevance

*"How do you call LLMs in LangChain, and how do you make it production-ready?"* A strong answer: create models with `init_chat_model("provider:model")` or a provider class; use standard parameters (`temperature`, `max_tokens`, `timeout`, `max_retries`); call with `invoke`, `stream` (chunks combine with `+`), `batch` (parallel, ordered, `max_concurrency`) and their async versions; read `text`, `usage_metadata`, `response_metadata` and `tool_calls` from the `AIMessage`. For production: built-in retries with backoff for transient errors, an `InMemoryRateLimiter`, `with_fallbacks` to another provider, usage tracking with `UsageMetadataCallbackHandler` or LangSmith, configurable models for per-request choice, and fake models for tests.

---

## Key Takeaways

- **Create** with `init_chat_model("provider:model", ...)` for configurability, or the provider class for its specific features.
- **Call** with `invoke`, `stream`, `batch` (and `ainvoke`, `astream`, `abatch`); results come back as `AIMessage`s or chunks.
- **Read the whole reply**: `text`, `usage_metadata` for tokens, `response_metadata` for the stop reason, `tool_calls` for tools.
- **Make it robust** with built-in retries, a rate limiter for bulk work and `with_fallbacks` for outages.
- **Keep it swappable**: write helpers that take any chat model, and test them with fakes.

---

**Up next:** [Embedding Models](embedding-models.md)
