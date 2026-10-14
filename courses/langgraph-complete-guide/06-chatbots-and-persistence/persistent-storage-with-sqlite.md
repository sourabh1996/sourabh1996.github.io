---
title: "Persistent Storage with SQLite"
course: LangGraph Complete Guide
module: "6. Chatbots and Persistence"
type: Article
level: Intermediate
reading_time: 26 min
---

# Persistent Storage with SQLite: The Complete Guide

> 📚 **Before you start**
>
> - [Persistence and Checkpointers](persistence-and-checkpointers.md) and [Threads, Fault Tolerance and Resuming](threads-fault-tolerance-and-resuming.md), for what a checkpointer stores and why.
> - [Databases: SQL and NoSQL](../../databases-sql-and-nosql/course.md), helpful but optional, for SQL basics.

## Introduction

`InMemorySaver` is like writing your shop's accounts on a whiteboard. It's quick and perfect for practice, but the moment someone wipes the board (the Python process stops), everything is gone. Restart your chatbot, redeploy your app, or just close the notebook, and every conversation disappears.

The fix is to write the checkpoints somewhere that outlives the process. The simplest such place is **SQLite**: a full SQL database stored in a **single file**, with a driver built into Python's standard library and no server to install. LangGraph's `SqliteSaver` stores every checkpoint in that file, so a chatbot can be stopped, restarted and pick up every conversation exactly where it left off.

In this lesson you'll learn how to install and use `SqliteSaver`, what it writes to the database, how to list conversations for a UI, how to see the "survives a restart" effect for yourself, and when SQLite stops being the right choice.

> 💡 **Key Insight**
>
> Switching from memory to disk is a **one-line change**: compile with `SqliteSaver(conn)` instead of `InMemorySaver()`. Everything else (threads, `get_state`, history, resuming, `delete_thread`) works the same, because every checkpointer implements the same interface. What changes is that the snapshots now live in a file that survives restarts.

---

## Core Explanation

### 1. Why SQLite for a first durable checkpointer

| | `InMemorySaver` | `SqliteSaver` | `PostgresSaver` |
|---|---|---|---|
| Survives restart | No | **Yes** | Yes |
| Setup | None | `pip install` one package | A database server |
| Storage | Python memory | One `.db` file | Database server |
| Concurrent writers | One process | One writer at a time | Many |
| Best for | Tests, demos | Local apps, prototypes, single-machine tools, Streamlit apps | Production web services |

SQLite is a great fit for the Streamlit chatbot you'll build in the lab: one machine, one file, real persistence.

### 2. Installing and connecting

The SQLite checkpointer is a separate package (it isn't installed with `langgraph`):

```bash
pip install langgraph-checkpoint-sqlite
```

There are two ways to create it. The first opens a connection yourself and passes it in, which suits long-running apps:

```python
# not-run: needs `pip install langgraph-checkpoint-sqlite`
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

conn = sqlite3.connect("chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)
chatbot = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "asha"}}
chatbot.invoke({"messages": [("user", "Hi, I'm Asha")]}, config)
```

`check_same_thread=False` lets the connection be used from threads other than the one that created it. Web frameworks and Streamlit often run your code on different threads, so you'll almost always want it.

The second creates and closes the connection for you with a context manager, which suits scripts and tests:

```python
# not-run: needs `pip install langgraph-checkpoint-sqlite`
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("chatbot.db") as checkpointer:
    chatbot = builder.compile(checkpointer=checkpointer)
    chatbot.invoke({"messages": [("user", "Hi, I'm Asha")]}, {"configurable": {"thread_id": "asha"}})
```

Pass `":memory:"` instead of a filename to get an in-memory SQLite database for tests.

The tables are created automatically on first use. Now stop the program, start it again, and ask a follow-up:

```python
# not-run: a second run of the program, after a restart
conn = sqlite3.connect("chatbot.db", check_same_thread=False)
chatbot = builder.compile(checkpointer=SqliteSaver(conn))
state = chatbot.get_state({"configurable": {"thread_id": "asha"}})
print([m.content for m in state.values["messages"]])
```

Example output:

```
["Hi, I'm Asha", 'Hello Asha! How can I help?']
```

The conversation came back from the file. Nothing else in the graph changed.

### 3. What's inside the file

`SqliteSaver` creates two tables. You never need to write to them yourself, but knowing their shape helps with debugging and with building UIs:

```sql
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint BLOB,
    metadata BLOB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);
-- plus a "writes" table for pending writes (outputs of nodes in an unfinished step)
```

- One row in **`checkpoints`** per snapshot: the ids you met in `StateSnapshot.config`, the parent link, and the serialised state and metadata as binary blobs.
- **`writes`** holds the pending writes that make resuming after a failure possible.

You can peek with any SQLite tool:

```bash
sqlite3 chatbot.db "SELECT thread_id, COUNT(*) FROM checkpoints GROUP BY thread_id;"
```

Example output:

```
asha|4
ravi|2
```

Because the state is stored as a binary blob, query it through LangGraph (`get_state`, `get_state_history`), not with SQL.

### 4. Seeing "survives a restart" without the package

`langgraph-checkpoint-sqlite` isn't installed on this site's test machine, so here's a runnable experiment that shows the same effect with Python's built-in `sqlite3`. It's a deliberately simplified stand-in: it saves only the **latest messages** of each thread as JSON, whereas `SqliteSaver` stores **every checkpoint** in its own format. But it makes the before-and-after of a restart concrete.

First, a chatbot with `InMemorySaver`, and a helper that copies a thread's messages into a SQLite file:

```python
import json, os, sqlite3, tempfile
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import messages_from_dict, messages_to_dict
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver

llm = FakeListChatModel(responses=["Hello Asha! How can I help?", "You told me your name is Asha."])

def chatbot(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}

def build_app():
    b = StateGraph(MessagesState)
    b.add_node(chatbot)
    b.add_edge(START, "chatbot")
    b.add_edge("chatbot", END)
    return b.compile(checkpointer=InMemorySaver())

DB_PATH = os.path.join(tempfile.mkdtemp(), "demo_chat.db")

def save_thread(app, thread_id):
    messages = app.get_state({"configurable": {"thread_id": thread_id}}).values["messages"]
    with sqlite3.connect(DB_PATH) as db:
        db.execute("CREATE TABLE IF NOT EXISTS conversations (thread_id TEXT PRIMARY KEY, messages TEXT)")
        db.execute("INSERT OR REPLACE INTO conversations VALUES (?, ?)",
                   (thread_id, json.dumps(messages_to_dict(messages))))

app = build_app()
cfg = {"configurable": {"thread_id": "asha"}}
app.invoke({"messages": [("user", "Hi, I'm Asha")]}, cfg)
save_thread(app, "asha")
print("saved", len(app.get_state(cfg).values["messages"]), "messages to", os.path.basename(DB_PATH))
```

Output:

```
saved 2 messages to demo_chat.db
```

Now "restart": throw the app and its in-memory checkpointer away, build a fresh one, and see what it remembers:

```python
del app
app = build_app()                                   # a brand-new process would look like this
print("fresh app remembers:", app.get_state(cfg).values)

with sqlite3.connect(DB_PATH) as db:
    row = db.execute("SELECT messages FROM conversations WHERE thread_id = ?", ("asha",)).fetchone()
restored = messages_from_dict(json.loads(row[0]))
app.update_state(cfg, {"messages": restored})        # load the saved conversation into the thread

reply = app.invoke({"messages": [("user", "What's my name?")]}, cfg)
print([m.content for m in reply["messages"]])
```

Output:

```
fresh app remembers: {}
["Hi, I'm Asha", 'Hello Asha! How can I help?', "What's my name?", 'You told me your name is Asha.']
```

With `InMemorySaver` alone, the restart wiped the thread. With the conversation stored in a file, the bot carried on. `SqliteSaver` gives you that automatically, for every checkpoint, on every step, with no `save_thread` or `update_state` calls.

### 5. Listing conversations for a UI

A chat app's sidebar needs the list of threads. The portable way works with any checkpointer:

```python
# not-run: with a SqliteSaver called checkpointer
thread_ids = {c.config["configurable"]["thread_id"] for c in checkpointer.list(None)}
```

This walks every checkpoint, which is fine for hundreds of threads but slow for many thousands. A direct query on the `checkpoints` table is faster:

```python
# not-run: with the same sqlite3 connection the SqliteSaver uses
rows = conn.execute("SELECT DISTINCT thread_id FROM checkpoints").fetchall()
```

Most real apps go one step further and keep a small **table of their own** next to the checkpointer's, with what the UI needs: a title, the owner, timestamps. The checkpointer stores the conversation; your table stores the list:

```python
with sqlite3.connect(DB_PATH) as db:
    db.execute("""CREATE TABLE IF NOT EXISTS threads (
                      thread_id TEXT PRIMARY KEY, user_id TEXT, title TEXT, updated_at TEXT)""")
    db.executemany("INSERT OR REPLACE INTO threads VALUES (?, ?, ?, ?)", [
        ("asha-1", "asha", "Goa trip budget", "2026-10-09 18:20"),
        ("asha-2", "asha", "Chai recipes", "2026-10-11 08:05"),
        ("ravi-1", "ravi", "Resume review", "2026-10-10 21:40"),
    ])
    for row in db.execute("SELECT thread_id, title FROM threads WHERE user_id = ? "
                          "ORDER BY updated_at DESC", ("asha",)):
        print(row)
```

Output:

```
('asha-2', 'Chai recipes')
('asha-1', 'Goa trip budget')
```

Update `updated_at` whenever the user sends a message, and delete the row together with `checkpointer.delete_thread(thread_id)` when they delete a chat.

### 6. Async apps: `AsyncSqliteSaver`

If your graph runs with `ainvoke`/`astream` (FastAPI, async Streamlit code, MCP tools), use the async version. It's in the same package and uses `aiosqlite`:

```python
# not-run: needs `pip install langgraph-checkpoint-sqlite`
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async def main():
    async with AsyncSqliteSaver.from_conn_string("chatbot.db") as checkpointer:
        chatbot = builder.compile(checkpointer=checkpointer)
        await chatbot.ainvoke({"messages": [("user", "Hi")]}, {"configurable": {"thread_id": "asha"}})
```

Use the sync saver with sync calls and the async saver with async calls.

### 7. Practical limits and good habits

- **One writer at a time.** SQLite locks the file while writing. That's fine for one app process serving a few users; it becomes a bottleneck for a busy web service with several workers. Then switch to `PostgresSaver`; your graph code doesn't change.
- **One machine.** The file lives on one disk. Containers that get replaced on each deploy need a mounted volume, or the file is lost with the container.
- **The file grows.** Every super-step adds a checkpoint. Delete threads users no longer need (`delete_thread`), consider `durability="exit"` for short runs where intermediate history isn't useful, and run SQLite's `VACUUM` occasionally to reclaim space.
- **It holds every conversation.** Keep the file out of version control (add `*.db` to `.gitignore`), restrict access, and follow the checkpoint package's advice to restrict deserialisation in production (`LANGGRAPH_STRICT_MSGPACK=true`).
- **Back it up** like any database: copy the file while the app is stopped, or use SQLite's online backup.

---

## Try It Yourself

1. **Count rows.** Using the `conversations` table from section 4, save a second thread `"ravi"` with one exchange (reuse `build_app` and a fresh `llm`). Then count the rows in `conversations`.
2. **Delete a chat.** Write `delete_chat(thread_id)` that removes the thread's row from both `conversations` and `threads`. Call it for `"asha-1"` and list Asha's remaining threads.
3. **Pick the checkpointer.** For each app, choose `InMemorySaver`, `SqliteSaver` or `PostgresSaver`: (a) unit tests for a graph, (b) a Streamlit chatbot you run on your laptop, (c) a customer support API running on four servers.

<details>
<summary>Show answers</summary>

**1.**

```python
llm = FakeListChatModel(responses=["Namaste Ravi!"])
app2 = build_app()
app2.invoke({"messages": [("user", "Hi, I'm Ravi")]}, {"configurable": {"thread_id": "ravi"}})
save_thread(app2, "ravi")
with sqlite3.connect(DB_PATH) as db:
    print(db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0])
```

Output:

```
2
```

**2.**

```python
def delete_chat(thread_id):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("DELETE FROM conversations WHERE thread_id = ?", (thread_id,))
        db.execute("DELETE FROM threads WHERE thread_id = ?", (thread_id,))
    # with a real checkpointer, also: checkpointer.delete_thread(thread_id)

delete_chat("asha-1")
with sqlite3.connect(DB_PATH) as db:
    print(db.execute("SELECT thread_id, title FROM threads WHERE user_id = 'asha'").fetchall())
```

Output:

```
[('asha-2', 'Chai recipes')]
```

**3.** (a) `InMemorySaver`: fast, nothing to clean up. (b) `SqliteSaver`: one file, survives restarts. (c) `PostgresSaver`: many processes writing at once on different machines.

</details>

---

## Real-World Examples

- **Personal and internal tools** (a Streamlit assistant for your team, a desktop app) use `SqliteSaver` so chats survive restarts with zero infrastructure.
- **Prototypes** start on SQLite and move to Postgres before launch by swapping the checkpointer line.
- **Edge and offline apps** (a field-sales assistant on a laptop) keep conversations in a local SQLite file and sync summaries later.

---

## Common Misconceptions

### "`SqliteSaver` comes with LangGraph"

It's a separate package: `pip install langgraph-checkpoint-sqlite`.

### "I can read the conversation with SQL"

The state is stored as serialised blobs. Read it with `get_state` and `get_state_history`.

### "SQLite is a toy database"

It's a robust, widely deployed database. Its limits are about concurrent writers and being on one machine, not reliability.

### "Moving to Postgres means rewriting the graph"

Only the checkpointer line changes.

---

## Interview Relevance

*"How do you persist LangGraph conversations across restarts?"* Use a durable checkpointer: `SqliteSaver` for single-machine apps, `PostgresSaver` for production services (or the managed persistence of a LangSmith Deployment). Mention `check_same_thread=False`, the async variants, listing threads (checkpointer `list`, or your own threads table), deleting threads, and that the graph code is unchanged.

---

## Key Takeaways

- `pip install langgraph-checkpoint-sqlite`, then compile with **`SqliteSaver(sqlite3.connect("x.db", check_same_thread=False))`** or use **`SqliteSaver.from_conn_string`**.
- The file has **`checkpoints`** and **`writes`** tables; state is stored as blobs, read via LangGraph.
- Conversations **survive restarts**; nothing else about the graph changes.
- Keep a small **threads table** of your own for titles and owners in a UI.
- SQLite means **one machine, one writer at a time**; move to **Postgres** for multi-server production.

---

**Up next:** [Lab: Chatbot UI with Streamlit, streaming and saved chats](lab-chatbot-ui-with-streamlit-streaming-and-saved-chats.md)
