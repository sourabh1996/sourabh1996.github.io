---
title: "Setting Up a LangChain Project and API Keys"
course: LangChain Complete Guide
module: "2. LangChain Foundations"
type: Article
level: Intermediate
reading_time: 22 min
---

# Setting Up a LangChain Project and API Keys: The Complete Guide

> 📚 **Before you start**
>
> - [What is LangChain?](what-is-langchain.md), for the package split (`langchain-core`, `langchain`, provider packages).
> - [Data Connectors and API Integrations](data-connectors-and-api-integrations.md), where connectors needed credentials.
> - [Lab: Your First LLM API Call](../../generative-ai-and-llm-foundations/03-how-llms-work/lab-your-first-llm-api-call.md), for the three rules about API keys.

## Introduction

Every year a few thousand API keys get leaked on GitHub, and bots scan public repositories within minutes of a push. A student in Bengaluru commits a notebook with `api_key="sk-ant-..."` on a Friday night; by Saturday morning someone has run up a bill on it. The fix is never clever code. It's a boring, correct project setup done once, on day one.

This lesson sets up a LangChain project the way you'll want it for the rest of the course and for real work: an isolated environment, the right packages pinned, keys kept out of code, a settings module that fails clearly when something is missing, and a smoke test that proves the wiring works, with or without a key.

> 💡 **Key Insight**
>
> **Keys live in the environment, never in code.** Your code reads them by name (`ANTHROPIC_API_KEY`), a git-ignored `.env` file supplies them on your laptop, and a secrets manager supplies them in production. The code is identical everywhere; only the environment changes.

---

## Core Explanation

### 1. The project at a glance

```mermaid
flowchart TB
    subgraph Repo["Git repository (shared)"]
      R["requirements.txt<br/>pinned versions"]
      S["app/settings.py<br/>reads env vars"]
      C["app/chains.py<br/>your LangChain code"]
      E1[".env.example<br/>names, no values"]
      G[".gitignore<br/>lists .env"]
    end
    subgraph Local["Your laptop only"]
      E[".env<br/>real keys"]
      V[".venv<br/>installed packages"]
    end
    subgraph Prod["Production"]
      SM["Secrets manager<br/>or platform env vars"]
    end
    E -->|load_dotenv| S
    SM -->|environment| S
    S --> C
```

A layout that works well:

```
saree-support-bot/
├── .venv/                  # virtual environment (git-ignored)
├── .env                    # real keys (git-ignored)
├── .env.example            # the same names with empty values (committed)
├── .gitignore
├── requirements.txt        # pinned versions
├── app/
│   ├── __init__.py
│   ├── settings.py         # reads and checks configuration
│   ├── models.py           # creates the chat model in one place
│   └── chains.py           # prompts, chains, tools
└── tests/
    └── test_chains.py      # uses fake models, no keys needed
```

### 2. An isolated environment and pinned packages

Create a virtual environment so this project's packages don't clash with others:

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install langchain langchain-anthropic python-dotenv
```

(If you use `uv`, `uv venv` and `uv pip install ...` do the same, faster.)

Which packages you need depends on what you use:

| You use | Install |
|---|---|
| Prompts, parsers, runnables, messages, tools | `langchain-core` (comes with everything) |
| `init_chat_model`, `create_agent` | `langchain` |
| Claude | `langchain-anthropic` |
| OpenAI models or embeddings | `langchain-openai` |
| Hugging Face or local models | `langchain-huggingface`, `langchain-ollama` |
| Community loaders and tools | `langchain-community` (plus each loader's own dependency, such as `pypdf`) |
| Tracing and evaluation | `langsmith` (already pulled in by `langchain-core`) |
| Reading `.env` files | `python-dotenv` |

Then **pin** what you installed, so a teammate (or your server) gets exactly the same versions:

```bash
pip freeze | grep -iE "^(langchain|langgraph|langsmith|python-dotenv)" > requirements.txt
cat requirements.txt
```

Example output:

```
langchain==1.4.6
langchain-anthropic==1.7.6
langchain-core==1.6.12
langgraph==1.2.16
langsmith==0.14.11
python-dotenv==1.2.4
```

LangChain releases often. Pinning means an upgrade is a deliberate change you test, not a surprise on Monday morning.

### 3. Getting the keys

Each provider issues keys from its own console. The environment variable names below are the ones the LangChain integrations read automatically:

| Service | Environment variable | Where to get it |
|---|---|---|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | Anthropic Console → API keys |
| OpenAI | `OPENAI_API_KEY` | OpenAI platform → API keys |
| Google Gemini | `GOOGLE_API_KEY` | Google AI Studio |
| Hugging Face | `HUGGINGFACEHUB_API_TOKEN` | Hugging Face → Settings → Access tokens |
| LangSmith tracing | `LANGSMITH_API_KEY`, plus `LANGSMITH_TRACING=true` | LangSmith → Settings → API keys |

"Read automatically" means you never pass the key in code. `ChatAnthropic(model=...)` looks up `ANTHROPIC_API_KEY` in the environment by itself. While learning, set a **monthly spending limit** in each console.

### 4. The `.env` file

A `.env` file is a plain text file of `NAME=value` lines that a small library loads into the environment when your app starts:

```
# .env  (never commit this file)
ANTHROPIC_API_KEY=sk-ant-api03-...your-key...
LANGSMITH_API_KEY=lsv2_pt_...your-key...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=saree-support-bot-dev
APP_MODEL=anthropic:claude-opus-5-5
```

Commit a `.env.example` with the **same names and no values**, so teammates know what to fill in:

```
# .env.example  (commit this one)
ANTHROPIC_API_KEY=
LANGSMITH_API_KEY=
LANGSMITH_TRACING=false
LANGSMITH_PROJECT=saree-support-bot-dev
APP_MODEL=anthropic:claude-opus-5-5
```

And make sure git ignores the real one:

```
# .gitignore
.venv/
.env
__pycache__/
```

Load it at the very start of your app, before creating any model:

```python
# not-run: needs `pip install python-dotenv` and a .env file
from dotenv import load_dotenv

load_dotenv()          # reads .env from the current folder into os.environ; existing env vars win
```

`load_dotenv()` does **not** overwrite variables that are already set. That's deliberate: in production the platform sets real environment variables, and a stray `.env` file can't override them.

### 5. A settings module that fails clearly

Reading `os.environ["ANTHROPIC_API_KEY"]` all over your code gives you a cryptic `KeyError` at a random moment. Instead, read and check all configuration **in one place, at start-up**, with a clear message. A small Pydantic model does this well:

```python
import os
from pydantic import BaseModel, field_validator

class Settings(BaseModel):
    model: str = "anthropic:claude-opus-5-5"
    anthropic_api_key: str | None = None
    langsmith_tracing: bool = False
    langsmith_project: str = "default"

    @field_validator("model")
    @classmethod
    def has_provider(cls, v):
        if ":" not in v:
            raise ValueError("APP_MODEL must look like 'provider:model-name'")
        return v

    def masked(self, value):
        return "not set" if not value else value[:7] + "…" + value[-4:]

def load_settings(env=os.environ):
    return Settings(
        model=env.get("APP_MODEL", "anthropic:claude-opus-5-5"),
        anthropic_api_key=env.get("ANTHROPIC_API_KEY"),
        langsmith_tracing=env.get("LANGSMITH_TRACING", "false").lower() == "true",
        langsmith_project=env.get("LANGSMITH_PROJECT", "default"),
    )

# Simulate two environments with plain dicts, so the example is safe to run anywhere.
laptop = {"ANTHROPIC_API_KEY": "sk-ant-api03-EXAMPLEKEY1234", "LANGSMITH_TRACING": "true",
          "LANGSMITH_PROJECT": "saree-support-bot-dev"}
s = load_settings(laptop)
print(s.model, "| key:", s.masked(s.anthropic_api_key), "| tracing:", s.langsmith_tracing, "| project:", s.langsmith_project)
```

Output:

```
anthropic:claude-opus-5-5 | key: sk-ant-…1234 | tracing: True | project: saree-support-bot-dev
```

Notice the **masking**: if you ever log your settings, show only the start and end of a key. Now see the clear failure for a badly written model name:

```python
from pydantic import ValidationError

try:
    load_settings({"APP_MODEL": "claude-opus-5-5"})
except ValidationError as e:
    print(e.errors()[0]["msg"])
```

Output:

```
Value error, APP_MODEL must look like 'provider:model-name'
```

You met Pydantic validators in the [APIs course](../../apis-and-apps-fastapi-streamlit-and-docker/course.md#m4); you'll use Pydantic heavily for structured output in Module 5. (The `pydantic-settings` package can read environment variables into a model automatically; the hand-written `load_settings` above shows what it does.)

### 6. Creating the model in one place

Put model creation in one function. Then the whole app can switch models through one setting, and tests can swap in a fake:

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel

def make_chat_model(settings, fake_responses=None):
    """Return the app's chat model. Uses a fake one when testing or when no key is set."""
    if fake_responses is not None or not settings.anthropic_api_key:
        return FakeListChatModel(responses=fake_responses or ["(fake reply: no API key set)"])
    from langchain.chat_models import init_chat_model    # imported only when really needed
    return init_chat_model(settings.model, temperature=0)

no_key = load_settings({})
model = make_chat_model(no_key)
print(type(model).__name__, "->", model.invoke("Hello").content)
```

Output:

```
FakeListChatModel -> (fake reply: no API key set)
```

With a real key, the same function returns a real Claude model:

```python
# not-run: needs `pip install langchain langchain-anthropic python-dotenv` and a .env with ANTHROPIC_API_KEY
from dotenv import load_dotenv

load_dotenv()
settings = load_settings()
model = make_chat_model(settings)
print(type(model).__name__, "->", model.invoke("Reply with just: setup works").text)
```

Example output:

```
ChatAnthropic -> setup works
```

`init_chat_model("anthropic:claude-opus-5-5")` picked the `ChatAnthropic` class from the `anthropic:` prefix. You'll study it properly in [Chat Models](../03-models/chat-models.md).

### 7. A smoke test you can run without keys

The fake model gives you tests that run anywhere, including CI servers with no secrets. Here's a test of a tiny chain, in the style you'd put in `tests/test_chains.py`:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def build_greeting_chain(model):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You greet customers of {shop} in one short sentence."),
        ("human", "{name} just walked in."),
    ])
    return prompt | model | StrOutputParser()

def test_greeting_chain():
    model = make_chat_model(load_settings({}), fake_responses=["Welcome to Nalli, Meera!"])
    out = build_greeting_chain(model).invoke({"shop": "Nalli", "name": "Meera"})
    assert out == "Welcome to Nalli, Meera!"
    return "passed"

print(test_greeting_chain())
```

Output:

```
passed
```

The test checks your **wiring** (prompt variables, chain order, parser) without paying for a model call. Quality checks against a real model are a separate, slower kind of test; Module 8 shows how LangSmith runs them.

### 8. Keys in production

| Environment | Where keys come from |
|---|---|
| Your laptop | `.env` file loaded by `python-dotenv` |
| CI (GitHub Actions) | Repository secrets, exposed as environment variables to the job |
| A server or container | The platform's environment-variable settings, or a secrets manager (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, Vault) |
| Docker | `docker run --env-file .env ...` locally; never `COPY .env` into an image |

Good habits that prevent bad days:

- **One key per app and environment** (dev, staging, prod), so you can revoke one without breaking the others.
- **Rotate** keys on a schedule and whenever someone leaves the team.
- **If a key leaks, revoke it first.** Removing it from git history doesn't help; it's already been copied.
- **Don't print settings objects** that contain keys; use masking as above.
- **Turn on secret scanning** in your git host so a pushed key is caught immediately.

### 9. A start-up checklist

```mermaid
flowchart LR
    A["Activate .venv"] --> B["pip install -r requirements.txt"]
    B --> C["Copy .env.example to .env<br/>and fill in keys"]
    C --> D["load_dotenv()"]
    D --> E["load_settings()<br/>fails clearly if wrong"]
    E --> F["make_chat_model()"]
    F --> G["Run smoke test"]
```

---

## Try It Yourself

1. **Add a setting.** Add `max_tokens: int = 1024` to `Settings`, read it from `APP_MAX_TOKENS`, and show that `load_settings({"APP_MAX_TOKENS": "300"}).max_tokens` is the integer `300`.
2. **Mask safely.** What does `s.masked("")` return, and why is that better than printing an empty string?
3. **Find the leak.** A teammate's `.gitignore` contains `.env.example` but not `.env`. What goes wrong, and how do you fix it?

<details>
<summary>Show answers</summary>

**1.**

```python
class Settings2(Settings):
    max_tokens: int = 1024

def load_settings2(env=os.environ):
    base = load_settings(env).model_dump()
    return Settings2(**base, max_tokens=env.get("APP_MAX_TOKENS", 1024))

v = load_settings2({"APP_MAX_TOKENS": "300"}).max_tokens
print(v, type(v).__name__)
```

Output:

```
300 int
```

Pydantic converted the string `"300"` from the environment into an `int`. Environment variables are always strings, so this conversion (and the error if someone writes `"three hundred"`) is exactly what you want.

**2.**

```python
print(s.masked(""))
```

Output:

```
not set
```

"not set" makes a missing key obvious in logs; an empty string is easy to overlook.

**3.** The real keys in `.env` get committed and pushed, while the harmless template is hidden. Swap the entries (ignore `.env`, commit `.env.example`), **revoke the leaked keys at once**, then issue new ones.

</details>

---

## Real-World Examples

- **Startups** keep one `.env.example` in the repo and onboard new engineers by asking them to copy it and fill in personal dev keys.
- **CI pipelines** run unit tests with fake models (no secrets) on every push, and a nightly job with real keys runs quality evaluations.
- **Platform teams** issue separate provider keys per service and per environment, so a leaked staging key can be revoked without touching production.
- **Model switching**: teams set `APP_MODEL` per environment (a cheaper model in dev, a stronger one in prod) without code changes.

---

## Common Misconceptions

### "My repository is private, so a key in code is fine"

Private repos get cloned to laptops, shared with contractors, copied into logs and occasionally made public. Treat every commit as if it might become public.

### "Deleting the commit removes the leaked key"

Forks, clones and caches keep it. Revoking the key is the only fix.

### "`load_dotenv()` overrides my production settings"

By default it doesn't overwrite variables already set in the environment, which is what you want in production.

### "Tests need a real model to be useful"

Wiring tests with fake models catch most bugs (wrong variable names, wrong chain order, parser errors) instantly and for free. Use real-model evaluations for quality, separately.

---

## Interview Relevance

*"How do you manage API keys and configuration in an LLM app?"* A strong answer: keys only in environment variables, loaded from a git-ignored `.env` locally (with a committed `.env.example`) and from a secrets manager or CI secrets in production; one settings module that validates configuration at start-up and masks secrets in logs; model creation in one factory function so the model is configurable and replaceable by a fake in tests; pinned dependencies; per-environment keys, rotation, spending limits, and "revoke first" when a key leaks.

---

## Key Takeaways

- **Isolate and pin**: a virtual environment per project and a `requirements.txt` with exact versions.
- **Keys come from the environment**: `.env` (git-ignored) locally, secrets managers in production; LangChain integrations read standard names like `ANTHROPIC_API_KEY` automatically.
- **Validate configuration at start-up** in one settings module, and mask keys in any output.
- **Create the model in one function**, so you can switch models by configuration and use fakes in tests.
- **A leaked key must be revoked**, not just deleted from history.

---

**Up next:** [LLMs vs Chat Models](../03-models/llms-vs-chat-models.md)
