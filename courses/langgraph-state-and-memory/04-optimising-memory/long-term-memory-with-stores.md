---
title: "Long-Term Memory with Stores"
course: LangGraph State and Memory
module: "4. Optimising Memory"
type: Article
level: Intermediate
reading_time: 32 min
---

# Long-Term Memory with Stores: The Complete Guide

> 📚 **Before you start**
>
> - [The LangGraph State System](../02-state-fundamentals/the-langgraph-state-system.md), for runtime context and the map of where data lives.
> - [Agents with Memory](../../langgraph-fundamentals/04-workflows-and-agents/agents-with-memory.md), for short-term memory with checkpointers and threads.
> - [Summarising Long Conversations](summarising-long-conversations.md), since summaries and stores solve different halves of the memory problem.
> - [RAG Building Blocks in LangChain](../../retrieval-augmented-generation-rag/course.md#m3) in the RAG course (vector stores and embeddings), helpful but optional, for section 6.

## Introduction

A good hotel remembers you. You stayed once in March and mentioned you're vegetarian and prefer a room away from the lift. In October you book again, through a different website, and the room is on a quiet corridor and the welcome snack is paneer, not chicken. Nobody re-read your March emails. The hotel kept a small **guest profile**, separate from any one booking, and looked it up when you returned.

A LangGraph checkpointer is like the folder for one booking: it remembers everything about **one thread**, and a new thread starts empty. For an assistant to remember "Asha is vegetarian" across all her chats, it needs a guest profile: a **store**. A store is a database of small JSON documents organised by **namespace** (for example, one per user), that any thread and any node can read and write.

In this lesson you'll learn the store API (`put`, `get`, `search`, `delete`, `list_namespaces`), connect a store to a graph, give a chatbot memory that follows a user across threads, add **semantic search** so memories can be found by meaning, and decide what kinds of memory to keep and when to write them.

> 💡 **Key Insight**
>
> Checkpoints are keyed by **thread**; store items are keyed by **namespace and key**, which you choose. That one difference is what makes long-term memory possible: put a user's facts under `(user_id, "memories")`, and every conversation that knows the `user_id` can find them, while other users' namespaces stay separate.

---

## Core Explanation

### 1. Short-term vs long-term memory

| | Checkpointer (short-term) | Store (long-term) |
|---|---|---|
| Keyed by | `thread_id` (plus checkpoint id) | `namespace` tuple + `key` |
| Holds | The full graph state after every step | Whatever JSON documents you decide to save |
| Written by | LangGraph, automatically | Your nodes (or tools), explicitly |
| Shared across threads? | No | Yes |
| Typical content | The current conversation | User profile, preferences, past outcomes, learned instructions |

```mermaid
flowchart LR
    subgraph T1["Thread: chat on Monday"]
      A1["messages..."]
    end
    subgraph T2["Thread: chat on Friday"]
      A2["messages..."]
    end
    ST[("Store<br/>(asha, memories)<br/>(ravi, memories)")]
    T1 -->|"write: vegetarian"| ST
    ST -->|"read: vegetarian"| T2
```

### 2. The store API

`InMemoryStore` keeps everything in a Python dictionary, perfect for learning and tests. Every value is a **dictionary**; every item lives at a **namespace** (a tuple of strings) and a **key** (a string):

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

store.put(("asha", "memories"), "diet", {"text": "Asha is vegetarian"})
store.put(("asha", "memories"), "city", {"text": "Asha lives in Pune"})
store.put(("ravi", "memories"), "diet", {"text": "Ravi eats everything except mushrooms"})

item = store.get(("asha", "memories"), "diet")
print(item.namespace, item.key, item.value)
print("timestamps:", type(item.created_at).__name__, type(item.updated_at).__name__)
print(store.get(("asha", "memories"), "phone"))
```

Output:

```
('asha', 'memories') diet {'text': 'Asha is vegetarian'}
timestamps: datetime datetime
None
```

An `Item` carries `namespace`, `key`, `value`, and `created_at` / `updated_at` timestamps. Getting a missing key returns `None`, not an error.

`put` on an existing key **replaces** the value (and updates `updated_at`); `delete` removes it:

```python
store.put(("asha", "memories"), "city", {"text": "Asha moved to Bengaluru"})
print(store.get(("asha", "memories"), "city").value)

store.delete(("ravi", "memories"), "diet")
print(store.get(("ravi", "memories"), "diet"))
```

Output:

```
{'text': 'Asha moved to Bengaluru'}
None
```

### 3. Namespaces and search

A namespace works like a folder path. `search` takes a namespace **prefix** and returns items in it and below it; `list_namespaces` shows the folders:

```python
store.put(("asha", "trips"), "goa-2026", {"text": "Goa trip in December, budget ₹40,000", "type": "trip"})
store.put(("asha", "trips"), "kerala-2025", {"text": "Kerala backwaters, loved the houseboat", "type": "trip"})

print(store.list_namespaces())
print(store.list_namespaces(prefix=("asha",)))
print([i.key for i in store.search(("asha", "memories"))])
print(sorted(i.key for i in store.search(("asha",))))
```

Output:

```
[('asha', 'memories'), ('asha', 'trips'), ('ravi', 'memories')]
[('asha', 'memories'), ('asha', 'trips')]
['diet', 'city']
['city', 'diet', 'goa-2026', 'kerala-2025']
```

`search` can also **filter** on values and page through results with `limit` and `offset`:

```python
print([i.key for i in store.search(("asha",), filter={"type": "trip"})])
print(len(store.search(("asha",), limit=2)))
```

Output:

```
['goa-2026', 'kerala-2025']
2
```

Common namespace designs:

| Namespace | Holds |
|---|---|
| `(user_id, "memories")` | Facts about one user |
| `(user_id, "preferences")` | One profile document with settings |
| `(org_id, user_id, "memories")` | Multi-tenant apps; search `(org_id,)` for org-wide analytics |
| `("agent", "instructions")` | Instructions the agent has learned, shared by all users |

### 4. Connecting a store to a graph

Pass the store to `compile(store=...)`. Nodes reach it through the **runtime**: declare a `runtime: Runtime[YourContext]` parameter and use `runtime.store`. The user's id comes from the runtime context, so a node can't be tricked into reading another user's namespace through the conversation:

```python
from dataclasses import dataclass
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.runtime import Runtime

@dataclass
class UserContext:
    user_id: str

model_prompts = []

def chatbot(state: MessagesState, runtime: Runtime[UserContext]):
    ns = (runtime.context.user_id, "memories")
    facts = [item.value["text"] for item in runtime.store.search(ns)]
    system = SystemMessage("You are a travel assistant. Known facts about the user: "
                           + ("; ".join(facts) if facts else "none"))
    model_prompts.append(system.content)
    return {"messages": [llm.invoke([system] + state["messages"])]}

def remember(state: MessagesState, runtime: Runtime[UserContext]):
    """A deliberately simple memory writer: save messages that start with 'Remember:'."""
    text = state["messages"][-2].content            # the user's latest message
    if text.lower().startswith("remember:"):
        fact = text.split(":", 1)[1].strip().rstrip(".")
        key = f"fact-{len(runtime.store.search((runtime.context.user_id, 'memories'))) + 1}"
        runtime.store.put((runtime.context.user_id, "memories"), key, {"text": fact})
    return {}

b = StateGraph(MessagesState, context_schema=UserContext)
b.add_node(chatbot)
b.add_node(remember)
b.add_edge(START, "chatbot")
b.add_edge("chatbot", "remember")
b.add_edge("remember", END)

memory_store = InMemoryStore()
app = b.compile(checkpointer=InMemorySaver(), store=memory_store)
```

The checkpointer gives each chat its thread; the store gives each user their memories. Now two separate threads for Meera:

```python
llm = FakeListChatModel(responses=[
    "Noted! I'll keep that in mind.",
    "How about Udaipur? Lots of great vegetarian thalis.",
])
meera = UserContext(user_id="meera")

app.invoke({"messages": [("user", "Remember: I am vegetarian and hate long bus rides.")]},
           {"configurable": {"thread_id": "meera-chat-1"}}, context=meera)

reply = app.invoke({"messages": [("user", "Suggest a weekend trip.")]},
                   {"configurable": {"thread_id": "meera-chat-2"}}, context=meera)

print(reply["messages"][-1].content)
print("model was told:", model_prompts[-1])
print("thread 2 has", len(reply["messages"]), "messages")
```

Output:

```
How about Udaipur? Lots of great vegetarian thalis.
model was told: You are a travel assistant. Known facts about the user: I am vegetarian and hate long bus rides
thread 2 has 2 messages
```

Thread 2 started empty (two messages: the question and the answer), yet the model was told about the earlier fact, because it came from the store. A different user sees nothing of Meera's:

```python
llm = FakeListChatModel(responses=["Sure, what kind of places do you like?"])
app.invoke({"messages": [("user", "Suggest a weekend trip.")]},
           {"configurable": {"thread_id": "kabir-chat-1"}}, context=UserContext(user_id="kabir"))
print("model was told:", model_prompts[-1])
print(memory_store.list_namespaces())
```

Output:

```
model was told: You are a travel assistant. Known facts about the user: none
[('meera', 'memories')]
```

An older style of access, still supported, is a parameter annotated `store: BaseStore` (from `langgraph.store.base`); LangGraph injects the compiled store. The `Runtime` parameter is the current recommendation because it also gives you the context and stream writer in one object.

### 5. Writing memories: what and when

The `remember` node above is a toy. In a real app, deciding **what is worth remembering** is a model's job. A typical approach asks a model for structured output, for example a list of facts to add or update, and writes each one:

```python
# not-run: needs `pip install langchain-anthropic` and ANTHROPIC_API_KEY
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic

class Memory(BaseModel):
    key: str        # short stable id, e.g. "diet" or "home_city"
    text: str       # the fact, in one sentence

class MemoryUpdate(BaseModel):
    memories: list[Memory]

extractor = ChatAnthropic(model="claude-opus-5-5").with_structured_output(MemoryUpdate)

def extract_memories(state: MessagesState, runtime: Runtime[UserContext]):
    existing = [i.value["text"] for i in runtime.store.search((runtime.context.user_id, "memories"))]
    update = extractor.invoke([
        SystemMessage("Extract durable facts about the user worth remembering in future chats. "
                      f"Existing memories: {existing}. Reuse a key to update a fact."),
        *state["messages"][-6:],
    ])
    for m in update.memories:
        runtime.store.put((runtime.context.user_id, "memories"), m.key, {"text": m.text})
    return {}
```

Choosing stable **keys** (`"diet"`, `"home_city"`) lets a later `put` **update** a fact ("moved to Bengaluru") instead of piling up contradictions.

**When** to write is a design decision too:

| Approach | How | Trade-off |
|---|---|---|
| **In the hot path** | A node in the graph writes memories during the conversation (like `remember`) | Memories are available immediately; adds latency and cost to every turn |
| **In the background** | A separate job processes finished or idle threads and writes memories | No latency for the user; memories appear a little later |
| **As a tool** | The agent gets a `save_memory` tool and decides itself | Flexible; depends on the model choosing well |

### 6. Semantic search: finding memories by meaning

Listing every memory works for a handful. With hundreds, you want the ones **relevant to the current question**. Give the store an **index** with an embedding function, and `search` accepts a `query` and returns items ranked by similarity.

A real app uses an embedding model. To keep this lesson offline, here's a tiny hand-made embedding: each dimension counts words from one topic. It's crude, but it behaves like the real thing for our examples:

```python
TOPICS = {
    "food": {"vegetarian", "food", "eat", "eats", "thali", "spicy", "dosa", "biryani", "allergic", "peanuts"},
    "travel": {"trip", "travel", "train", "flight", "bus", "beach", "hills", "weekend", "goa"},
    "money": {"budget", "₹", "cheap", "expensive", "salary", "upi", "spend"},
    "work": {"office", "meeting", "manager", "deadline", "laptop", "work"},
}

def toy_embed(texts: list[str]) -> list[list[float]]:
    vectors = []
    for text in texts:
        words = text.lower().replace(",", " ").replace(".", " ").split()
        vectors.append([sum(w in vocab for w in words) + 0.01 for vocab in TOPICS.values()])
    return vectors

print(toy_embed(["I love spicy dosa", "Weekend trip to Goa on a budget"]))
```

Output:

```
[[2.01, 0.01, 0.01, 0.01], [0.01, 3.01, 1.01, 0.01]]
```

An embedding function for the store takes a list of strings and returns one vector (list of floats) per string. Configure the index with the number of dimensions, the function, and which fields of each value to embed:

```python
semantic = InMemoryStore(index={"dims": 4, "embed": toy_embed, "fields": ["text"]})

memories = {
    "m1": "Asha is vegetarian and loves spicy food",
    "m2": "Asha prefers trains over flights for travel",
    "m3": "Asha's monthly travel budget is ₹15,000",
    "m4": "Asha has a deadline at the office every Friday",
    "m5": "Asha is allergic to peanuts",
}
for key, text in memories.items():
    semantic.put(("asha", "memories"), key, {"text": text})

for query in ["What should I eat tonight?", "Plan a cheap weekend trip"]:
    hits = semantic.search(("asha", "memories"), query=query, limit=2)
    print(query, "->", [(h.key, round(h.score, 2)) for h in hits])
```

Output:

```
What should I eat tonight? -> [('m5', 1.0), ('m1', 1.0)]
Plan a cheap weekend trip -> [('m3', 0.95), ('m2', 0.9)]
```

The food question found the vegetarian and peanut-allergy memories; the trip question found the budget and travel memories. Each result has a `score` (higher is more similar). A few practical details:

- Items saved with `put(..., index=False)` are stored but **not embedded**; they won't rank in semantic search.
- `fields` chooses what to embed. Embed the human-readable text, not ids or timestamps.
- You can combine `query` with `filter` to rank only within, say, `{"type": "trip"}`.

With a real embedding model it's the same configuration:

```python
# not-run: needs `pip install langchain langchain-openai` and OPENAI_API_KEY
from langchain.embeddings import init_embeddings
from langgraph.store.memory import InMemoryStore

embeddings = init_embeddings("openai:text-embedding-3-small")
store = InMemoryStore(index={"dims": 1536, "embed": embeddings, "fields": ["text"]})
```

Any LangChain embeddings object works as `embed`, as does your own function.

### 7. Using semantic memories in the graph

The chatbot now retrieves only the relevant memories for the latest question, instead of all of them:

```python
def relevant_chatbot(state: MessagesState, runtime: Runtime[UserContext]):
    question = state["messages"][-1].content
    hits = runtime.store.search((runtime.context.user_id, "memories"), query=question, limit=2)
    facts = "; ".join(h.value["text"] for h in hits)
    model_prompts.append(facts)
    return {"messages": [llm.invoke([SystemMessage(f"Relevant facts: {facts}")] + state["messages"])]}

b = StateGraph(MessagesState, context_schema=UserContext)
b.add_node("chatbot", relevant_chatbot)
b.add_edge(START, "chatbot")
smart = b.compile(checkpointer=InMemorySaver(), store=semantic)

llm = FakeListChatModel(responses=["Try a vegetarian thali, and skip anything with peanuts."])
smart.invoke({"messages": [("user", "What should I eat tonight?")]},
             {"configurable": {"thread_id": "asha-food"}}, context=UserContext(user_id="asha"))
print(model_prompts[-1])
```

Output:

```
Asha is allergic to peanuts; Asha is vegetarian and loves spicy food
```

The work-deadline memory never reached the model: fewer tokens, and less chance of the model mentioning something irrelevant.

### 8. Kinds of memory

Memory research borrows terms from psychology. They're a useful checklist for what an assistant might keep:

| Kind | Meaning | Example in a store |
|---|---|---|
| **Semantic** | Facts | `(user, "memories")`: "vegetarian", "lives in Pune" |
| **Episodic** | Past experiences | `(user, "episodes")`: "Last refund took 3 tries; worked when we asked for the UPI ref" |
| **Procedural** | How to behave | `("agent", "instructions")`: an updated system prompt the agent refines from feedback |

Facts are the most common. Episodes are often used as few-shot examples. Procedural memory means the agent edits its own instructions, which is powerful and needs careful review.

### 9. Stores in production

`InMemoryStore` disappears when the process exits. For real apps use a database-backed store with the same API:

```python
# not-run: needs `pip install langgraph-checkpoint-postgres "psycopg[binary,pool]"` and a database
from langgraph.store.postgres import PostgresStore
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://postgres:postgres@localhost:5432/langgraph"
with PostgresStore.from_conn_string(DB_URI) as store, PostgresSaver.from_conn_string(DB_URI) as saver:
    store.setup()          # create tables, once
    saver.setup()
    app = builder.compile(checkpointer=saver, store=store)
```

When deployed with LangSmith Deployment (the Agent Server), a Postgres-backed store is provided for you. Whatever the backend:

- **Respect deletion requests.** "Forget me" means deleting the user's namespaces in the store **and** their threads in the checkpointer.
- **Don't store secrets** (passwords, OTPs, full card numbers) as memories.
- **Show users what you remember** when you can. A memory that's wrong is worse than none.

---

## Try It Yourself

1. **A profile document.** Instead of many memory items, keep one document per user at `(user_id, "profile")`, key `"main"`, with fields `diet`, `city`, `language`. Write `update_profile(store, user_id, **changes)` that merges changes into the existing profile.
2. **Forget me.** Write `forget_user(store, user_id)` that deletes every item in every namespace starting with `user_id`. Test it on `store` from section 2 for `"asha"`.
3. **Filtered semantic search.** Add a `"category"` field (`"health"` or `"preference"`) to the five semantic memories and search for "food" restricted to `{"category": "health"}`.

<details>
<summary>Show answers</summary>

**1.**

```python
def update_profile(store, user_id, **changes):
    item = store.get((user_id, "profile"), "main")
    profile = dict(item.value) if item else {}
    profile.update(changes)
    store.put((user_id, "profile"), "main", profile)
    return profile

profiles = InMemoryStore()
update_profile(profiles, "asha", diet="vegetarian", city="Pune")
print(update_profile(profiles, "asha", city="Bengaluru", language="Marathi"))
```

Output:

```
{'diet': 'vegetarian', 'city': 'Bengaluru', 'language': 'Marathi'}
```

A profile is easy to show and edit; a collection of items scales to many unrelated facts. Many apps use both.

**2.**

```python
def forget_user(store, user_id):
    removed = 0
    for ns in store.list_namespaces(prefix=(user_id,)):
        for item in store.search(ns):
            if tuple(item.namespace) == ns:
                store.delete(ns, item.key)
                removed += 1
    return removed

print(forget_user(store, "asha"), "items removed")
print("left for asha:", store.search(("asha",)))
```

Output:

```
4 items removed
left for asha: []
```

The check `item.namespace == ns` avoids deleting the same item twice when one namespace is a prefix of another. (`InMemoryStore` may keep listing a namespace after its last item is deleted, as `('ravi', 'memories')` did in section 3, so check for items rather than namespaces.) In production, also delete the user's checkpointer threads with `delete_thread`.

**3.**

```python
categories = {"m1": "preference", "m2": "preference", "m3": "preference", "m4": "preference", "m5": "health"}
for key, text in memories.items():
    semantic.put(("asha", "memories"), key, {"text": text, "category": categories[key]})
hits = semantic.search(("asha", "memories"), query="food", filter={"category": "health"})
print([(h.key, h.value["text"]) for h in hits])
```

Output:

```
[('m5', 'Asha is allergic to peanuts')]
```

</details>

---

## Real-World Examples

- **Personal assistants** remember dietary needs, home city and preferred languages across every chat.
- **Customer support agents** keep a per-customer record of past issues ("their router was replaced in June") so a new ticket starts with context.
- **Coding assistants** store per-repository conventions ("this project uses pytest and ruff") under a namespace for the repo, shared by every session.
- **Tutoring apps** track which topics a student struggled with and bring them up again a week later.

---

## Common Misconceptions

### "The checkpointer is long-term memory"

It's per thread. A new thread starts empty. Cross-thread memory needs a store (or your own database).

### "Store everything the user says"

That recreates the long-conversation problem in a database. Store durable, useful facts with stable keys, and update them.

### "Semantic search needs a vector database"

The store's index handles it; `InMemoryStore` and `PostgresStore` both support it. A separate vector database is for large document collections (RAG), not usually for user memories.

### "The user id can come from the conversation"

Take it from authenticated runtime context. Otherwise a user could type "I'm user 42" and read someone else's memories.

---

## Interview Relevance

*"How do you give a LangGraph agent memory across conversations?"* Short-term memory is the checkpointer per thread; long-term memory is a `BaseStore` (`InMemoryStore`, `PostgresStore`) passed to `compile(store=...)`, accessed in nodes via `runtime.store`, organised by namespace such as `(user_id, "memories")`, with `put`, `get`, `search` and `delete`. Mention semantic search with an embedding index, stable keys for updates, hot-path vs background writing, and deletion and privacy.

*"What would you store, and how would you retrieve it?"* Durable facts and preferences (semantic), useful past episodes, maybe learned instructions; retrieve by relevance with `search(query=...)` and a small `limit` so prompts stay short.

---

## Key Takeaways

- A **store** holds JSON documents by **namespace + key**, shared across threads; a checkpointer holds state per thread.
- The API: **`put`** (insert or replace), **`get`**, **`search`** (prefix, `filter`, `limit`, `query`), **`delete`**, **`list_namespaces`**.
- Compile with **`store=`**, access it via **`runtime.store`**, and take the **user id from runtime context**.
- Add an **index** (`dims`, `embed`, `fields`) for **semantic search**; any embedding function works, even offline toys.
- Decide **what** to remember (stable keys), **when** to write (hot path or background), and honour **deletion**.

---

**Up next:** [Lab: Keep a long chat under budget](lab-keep-a-long-chat-under-budget.md)
