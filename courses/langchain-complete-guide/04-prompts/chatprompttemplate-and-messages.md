---
title: "ChatPromptTemplate and Messages"
course: LangChain Complete Guide
module: "4. Prompts"
type: Article
level: Intermediate
reading_time: 27 min
---

# ChatPromptTemplate and Messages: The Complete Guide

> 📚 **Before you start**
>
> - [Prompt Templates](prompt-templates.md), for templates, prompt values and partials.
> - [LangChain Components](../02-langchain-foundations/langchain-components.md), where you first met the message classes.
> - [System Prompts and Roles](../../generative-ai-and-llm-foundations/04-prompting-and-structured-output/system-prompts-and-roles.md), for what each role is for.

## Introduction

At a railway enquiry counter, three voices matter. The **rule book** pinned behind the clerk ("never promise a confirmed berth from the waiting list"), the **passenger** at the window, and the **clerk's own earlier replies** ("I told you it's RAC 4"). A good clerk keeps them apart: the rule book outranks the passenger, and what the clerk said a minute ago shapes what they say next.

Chat models work the same way, with **messages** that carry a **role**: system (the rule book), human (the passenger), AI (the clerk's earlier replies) and tool (results your code fetched). In the last lesson, `PromptTemplate` produced a single block of text, which a chat model receives as one human message. That's fine for simple tasks, but real apps need a system message with rules, then the user's message, sometimes example exchanges, and later the whole conversation.

`ChatPromptTemplate` is the template for that: a list of role-tagged message templates, filled from one dict, producing a list of messages. This lesson covers the message classes in depth, every way to build a `ChatPromptTemplate`, how it differs from fixed messages, few-shot chat examples, images in prompts, and the mistakes people make.

> 💡 **Key Insight**
>
> A `ChatPromptTemplate` is a **list of message templates**, one per role. Invoking it fills every slot from the same dict and returns a list of real messages. Write the rules in the system message, put user data in the human message, and the model gets a clean, role-separated conversation every time.

---

## Core Explanation

### 1. Messages in depth

Every message in `langchain_core.messages` has a **type** (role) and **content**, plus some optional fields:

| Class | `type` | Written by | Extra fields worth knowing |
|---|---|---|---|
| `SystemMessage` | `system` | You (rules, persona, format) | |
| `HumanMessage` | `human` | The user | `name` (to tell several users apart) |
| `AIMessage` | `ai` | The model | `tool_calls`, `usage_metadata`, `response_metadata` |
| `ToolMessage` | `tool` | Your code (a tool's result) | `tool_call_id` linking it to the request |

```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

conversation = [
    SystemMessage("You are an IRCTC enquiry assistant. Never promise a confirmed berth."),
    HumanMessage("My PNR shows RL WL 7. Will it confirm?"),
    AIMessage("WL 7 on a remote-location quota often moves, but I can't promise confirmation."),
    HumanMessage("What are my chances by Friday?"),
]
for m in conversation:
    print(f"{m.type:>6} | {m.content}")
```

Output:

```
system | You are an IRCTC enquiry assistant. Never promise a confirmed berth.
 human | My PNR shows RL WL 7. Will it confirm?
    ai | WL 7 on a remote-location quota often moves, but I can't promise confirmation.
 human | What are my chances by Friday?
```

Content doesn't have to be a single string. A message can hold a **list of content blocks**, for example text plus an image. This is how you send a photo of a ticket or a screenshot to a model that can see:

```python
photo_question = HumanMessage(content=[
    {"type": "text", "text": "Read the PNR number from this ticket photo."},
    {"type": "image", "url": "https://example.com/ticket-photo.jpg"},
])
print([block["type"] for block in photo_question.content])
```

Output:

```
['text', 'image']
```

Image blocks can also carry the picture's bytes as base64 (`"base64": ..., "mime_type": "image/jpeg"`) instead of a URL. Each provider package converts these standard blocks into its own API format.

### 2. Your first `ChatPromptTemplate`

`ChatPromptTemplate.from_messages` takes a list of `(role, template_text)` pairs:

```python
from langchain_core.prompts import ChatPromptTemplate

enquiry = ChatPromptTemplate.from_messages([
    ("system", "You are an enquiry assistant at {station}. Reply in {language}. "
               "Never promise a confirmed berth."),
    ("human", "{question}"),
])
print(enquiry.input_variables)

pv = enquiry.invoke({"station": "Howrah Junction", "language": "Bengali",
                     "question": "Is the 12301 Rajdhani on time today?"})
print(type(pv).__name__)
for m in pv.to_messages():
    print(f"{type(m).__name__:>13} | {m.content}")
```

Output:

```
['language', 'question', 'station']
ChatPromptValue
SystemMessage | You are an enquiry assistant at Howrah Junction. Reply in Bengali. Never promise a confirmed berth.
 HumanMessage | Is the 12301 Rajdhani on time today?
```

![A chat prompt template in three columns: inputs (partials such as the date, variables such as station and language, the chat history and the new question) feed a template of a system message, a MessagesPlaceholder and a human message, which produces a prompt value of a SystemMessage, the history's Human and AI messages, and the new HumanMessage, ready for any chat model](/img/diagrams/langchain-complete-guide/prompt-templates.svg)
*One dict of inputs fills every message template. The history slot is covered in the next lesson.*

The role names accepted in the tuples:

| You write | Becomes |
|---|---|
| `"system"` | `SystemMessage` |
| `"human"` or `"user"` | `HumanMessage` |
| `"ai"` or `"assistant"` | `AIMessage` |
| `"placeholder"` | A slot for a list of messages (next lesson) |

The result is a `ChatPromptValue`. Its `to_messages()` gives the list for a chat model; `to_string()` flattens it for an LLM-interface model (with the "System:"/"Human:" labels you saw in [LLMs vs Chat Models](../03-models/llms-vs-chat-models.md)).

### 3. Into a model

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser

model = FakeListChatModel(responses=["১২৩০১ রাজধানী আজ সময়মতো চলছে।"])
chain = enquiry | model | StrOutputParser()
print(chain.invoke({"station": "Howrah Junction", "language": "Bengali",
                    "question": "Is the 12301 Rajdhani on time today?"}))
```

Output:

```
১২৩০১ রাজধানী আজ সময়মতো চলছে।
```

(The fake replies "The 12301 Rajdhani is running on time today" in Bengali.) Swap the fake for a real chat model and nothing else changes.

### 4. Template tuples vs fixed message objects

You can mix `(role, text)` tuples with ready-made message objects in `from_messages`. The difference is important:

- A **tuple** is a **template**: `{...}` inside it is a slot to fill.
- A **message object** is **fixed**: its content is used exactly as written, braces and all.

```python
mixed = ChatPromptTemplate.from_messages([
    SystemMessage("Reply only with JSON like {\"status\": \"on time\"}."),   # fixed: braces are literal
    ("human", "Status of train {train}?"),                                    # template: {train} is a slot
])
print(mixed.input_variables)
for m in mixed.invoke({"train": "12951"}).to_messages():
    print(m.content)
```

Output:

```
['train']
Reply only with JSON like {"status": "on time"}.
Status of train 12951?
```

That's a neat way to include text with lots of braces (JSON examples, code) without escaping. It also matters for security: **user-written text should never become a template**. If you built a message tuple from user text, a user typing `{station}` would create a slot. Keep user text in values, or in fixed message objects.

### 5. Message prompt template classes

Under the hood, each tuple becomes a **message prompt template** object. You can create them explicitly, which you'll see in older code and in the docs:

```python
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate

explicit = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("You are an enquiry assistant at {station}."),
    HumanMessagePromptTemplate.from_template("{question}"),
])
print([type(m).__name__ for m in explicit.messages])
```

Output:

```
['SystemMessagePromptTemplate', 'HumanMessagePromptTemplate']
```

The tuple shorthand produces the same objects, so most code just uses tuples.

### 6. Partials, combining and reuse

Everything you learned for `PromptTemplate` works here too:

```python
base = ChatPromptTemplate.from_messages([
    ("system", "You are an enquiry assistant at {station}. Today is {date}."),
])
howrah_today = base.partial(station="Howrah Junction", date="17 Oct 2026")

with_question = howrah_today + ChatPromptTemplate.from_messages([("human", "{question}")])
print(with_question.input_variables)
for m in with_question.invoke({"question": "Where is the cloak room?"}).to_messages():
    print(f"{m.type:>6} | {m.content}")
```

Output:

```
['question']
system | You are an enquiry assistant at Howrah Junction. Today is 17 Oct 2026.
 human | Where is the cloak room?
```

Adding chat templates appends their message lists. You can also add a single tuple or message object with `+`. A common pattern is one shared "house rules" system template, partially filled once per deployment and combined with task-specific templates.

### 7. Few-shot examples as messages

For chat models, examples work best as **real example exchanges**: a human message followed by the AI reply you want. `FewShotChatMessagePromptTemplate` turns a list of example dicts into those message pairs:

```python
from langchain_core.prompts import FewShotChatMessagePromptTemplate

examples = [
    {"query": "Train 12301 kab aayegi?", "intent": "running_status"},
    {"query": "Tatkal kitne baje khulta hai?", "intent": "booking_rules"},
    {"query": "Mera refund kab milega?", "intent": "refund"},
]
example_pair = ChatPromptTemplate.from_messages([("human", "{query}"), ("ai", "{intent}")])
few_shot = FewShotChatMessagePromptTemplate(examples=examples, example_prompt=example_pair)

classifier = ChatPromptTemplate.from_messages([
    ("system", "Classify the passenger's message as running_status, booking_rules or refund. "
               "Reply with the label only."),
    few_shot,
    ("human", "{query}"),
])
for m in classifier.invoke({"query": "PNR confirm hoga kya?"}).to_messages():
    print(f"{m.type:>6} | {m.content}")
```

Output:

```
system | Classify the passenger's message as running_status, booking_rules or refund. Reply with the label only.
 human | Train 12301 kab aayegi?
    ai | running_status
 human | Tatkal kitne baje khulta hai?
    ai | booking_rules
 human | Mera refund kab milega?
    ai | refund
 human | PNR confirm hoga kya?
```

Notice the Hinglish queries: few-shot examples are a quick way to show a model the real mix of languages your users write in. The model sees three completed exchanges and continues the pattern with a single label.

### 8. Images and other content in templates

Message templates can contain content blocks with slots, so a template can carry an image URL chosen at run time:

```python
vision = ChatPromptTemplate.from_messages([
    ("system", "You read Indian railway tickets and extract the PNR."),
    ("human", [
        {"type": "text", "text": "Extract the PNR from this {ticket_kind}."},
        {"type": "image", "url": "{image_url}"},
    ]),
])
print(vision.input_variables)
msg = vision.invoke({"ticket_kind": "e-ticket", "image_url": "https://example.com/t.jpg"}).to_messages()[1]
print(msg.content)
```

Output:

```
['image_url', 'ticket_kind']
[{'type': 'text', 'text': 'Extract the PNR from this e-ticket.'}, {'type': 'image', 'url': 'https://example.com/t.jpg'}]
```

Only send image blocks to models that accept images; the model's documentation (or its `profile`) tells you which inputs it supports.

### 9. A checklist for good chat prompts

| Put this | In this message | Why |
|---|---|---|
| Role, rules, output format, things never to do | **System** | Highest authority; stays the same across turns |
| The user's question or document | **Human** | It's data from the user, kept separate from your rules |
| Worked examples | **Human/AI pairs** (few-shot) | The model copies the pattern of its "own" earlier replies |
| Earlier turns | **Placeholder** for history | Next lesson |
| Tool results | **Tool** messages | Module 7 |

---

## Try It Yourself

1. **Translate a template.** Turn this `PromptTemplate` into a `ChatPromptTemplate` with a proper system message: `"You are a polite assistant for Chennai Metro. Answer in Tamil. Question: {question}"`. Print the messages for "Where is the nearest station to Marina Beach?".
2. **Fixed vs template.** Why does this raise an error, and how would you fix it with a fixed message? `ChatPromptTemplate.from_messages([("system", 'Reply as {"ok": true}'), ("human", "{q}")]).invoke({"q": "hi"})`
3. **Few-shot tone.** Build a chat prompt with two example pairs that turn formal sentences into friendly WhatsApp-style ones, then show the messages for `"Kindly confirm your attendance at the meeting."`

<details>
<summary>Show answers</summary>

**1.**

```python
metro = ChatPromptTemplate.from_messages([
    ("system", "You are a polite assistant for Chennai Metro. Answer in Tamil."),
    ("human", "{question}"),
])
for m in metro.invoke({"question": "Where is the nearest station to Marina Beach?"}).to_messages():
    print(f"{m.type:>6} | {m.content}")
```

Output:

```
system | You are a polite assistant for Chennai Metro. Answer in Tamil.
 human | Where is the nearest station to Marina Beach?
```

The rules are now in the system message, separate from the user's question.

**2.**

```python
try:
    ChatPromptTemplate.from_messages([("system", 'Reply as {"ok": true}'), ("human", "{q}")]).invoke({"q": "hi"})
except Exception as e:
    print(type(e).__name__)

fixed = ChatPromptTemplate.from_messages([SystemMessage('Reply as {"ok": true}'), ("human", "{q}")])
print(fixed.invoke({"q": "hi"}).to_messages()[0].content)
```

Output:

```
KeyError
Reply as {"ok": true}
```

In a tuple, `{"ok": true}` is read as a template slot named `"ok": true`, which was never provided. Making it a fixed `SystemMessage` keeps the braces literal (doubling them to `{{"ok": true}}` also works).

**3.**

```python
tone = ChatPromptTemplate.from_messages([
    ("system", "Rewrite formal sentences as short, friendly WhatsApp messages."),
    FewShotChatMessagePromptTemplate(
        examples=[{"formal": "Please be informed that the office will remain closed tomorrow.",
                   "casual": "Heads up, office is shut tomorrow!"},
                  {"formal": "Your presence at the function is requested.",
                   "casual": "Do come for the function!"}],
        example_prompt=ChatPromptTemplate.from_messages([("human", "{formal}"), ("ai", "{casual}")]),
    ),
    ("human", "{formal}"),
])
print(len(tone.invoke({"formal": "Kindly confirm your attendance at the meeting."}).to_messages()), "messages")
```

Output:

```
6 messages
```

One system message, two example pairs (four messages) and the new human message.

</details>

---

## Real-World Examples

- **Customer-support bots** use a system message with policy rules and tone, a few-shot block of ideal replies, the chat history, and the new customer message.
- **Classification and routing** (which department should handle this email?) uses few-shot chat examples so the model replies with a bare label.
- **Document assistants** put retrieved passages in a clearly labelled human message ("Here are the relevant policy sections: …") separate from the system rules.
- **Insurance and KYC apps** send photos of documents as image blocks inside a templated human message.

---

## Common Misconceptions

### "The system message is just the first human message"

Models are trained to treat system messages as higher-priority instructions. Putting rules in a human message weakens them, and putting user data in the system message can let that data act as instructions.

### "`ChatPromptTemplate` sends the template to the model"

It sends the **filled messages**. The template, its variable names and its partials never reach the model.

### "Every message in `from_messages` is a template"

Only tuples and message-template objects are. Message objects like `SystemMessage(...)` are inserted exactly as written.

### "Few-shot examples should go in the system message as text"

That works, but example human/AI pairs usually work better for chat models, because the model then imitates its own "previous" replies directly.

---

## Interview Relevance

*"How do you build prompts for chat models in LangChain?"* A strong answer: use `ChatPromptTemplate.from_messages` with `(role, template)` tuples (system, human/user, ai/assistant, placeholder); `invoke` returns a `ChatPromptValue` that gives a list of `SystemMessage`/`HumanMessage`/`AIMessage` objects. Explain message classes and content blocks (text, images), template tuples vs fixed message objects (literal braces, and never templating user text), partials and `+`, `FewShotChatMessagePromptTemplate` for examples as message pairs, and the guideline of rules in system, user data in human, history in a placeholder and tool results in tool messages.

---

## Key Takeaways

- **Messages have roles**: system (rules), human (user), AI (model), tool (results); content can be text or a list of blocks such as images.
- **`ChatPromptTemplate.from_messages`** builds a list of role-tagged templates; `invoke` returns a `ChatPromptValue` of real messages.
- **Tuples are templates, message objects are fixed**: use fixed messages for literal braces, and never turn user text into template text.
- **Partials, `+` and few-shot message pairs** work just like with `PromptTemplate`.
- **Rules go in the system message, data in the human message**, examples as human/AI pairs.

---

**Up next:** [MessagesPlaceholder and Chat History](messagesplaceholder-and-chat-history.md)
