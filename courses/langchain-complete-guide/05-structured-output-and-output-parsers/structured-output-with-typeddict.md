---
title: "Structured Output with TypedDict"
course: LangChain Complete Guide
module: "5. Structured Output and Output Parsers"
type: Article
level: Intermediate
reading_time: 24 min
---

# Structured Output with TypedDict: The Complete Guide

> 📚 **Before you start**
>
> - [Why Structured Output Matters](why-structured-output-matters.md), for schemas, the two routes and the `ScriptedChatModel` used to run examples offline.
> - Type hints from [Python Programming](../../python-programming/course.md#m7).

## Introduction

A wedding caterer in Jaipur receives enquiries on WhatsApp: *"Hi, need food for 250 guests on 12 Dec at Rambagh, pure veg, Rajasthani + some Chinese, budget around 1200 per plate."* The owner wants every enquiry turned into a row in a spreadsheet: guests, date, venue, veg or not, cuisines, budget. That's a classic structured-output job, and the shape is simple: a handful of named fields.

Python already has a lightweight way to describe "a dict with these keys and these types": **`TypedDict`**. LangChain's `with_structured_output` accepts a `TypedDict` directly, sends its shape to the model as a schema, and returns a plain `dict`. No new library, no classes with methods, just a type description.

This lesson teaches `TypedDict` from scratch, how to add descriptions and optional fields with `Annotated`, how nested and list fields work, what the model actually receives, and the one big limitation you must know: **a `TypedDict` is never checked at run time**.

> 💡 **Key Insight**
>
> A `TypedDict` is a **description of a dict's shape for type checkers and for the model**, not a validator. `with_structured_output(MyTypedDict)` gives the model the schema and returns a plain `dict`; if you need guaranteed types and value rules at run time, use Pydantic (next lesson).

---

## Core Explanation

### 1. TypedDict in plain Python

A `TypedDict` declares the keys a dictionary should have and the type of each value:

```python
from typing import TypedDict

class Enquiry(TypedDict):
    guests: int
    event_date: str
    venue: str
    pure_veg: bool

e: Enquiry = {"guests": 250, "event_date": "2026-12-12", "venue": "Rambagh", "pure_veg": True}
print(type(e).__name__, e["guests"])
```

Output:

```
dict 250
```

The value is an ordinary `dict`. The class only exists so that tools (your editor, `mypy`) and now LangChain know what keys and types to expect. Python itself does **not** check it:

```python
wrong: Enquiry = {"guests": "two hundred fifty", "venue": 42}     # no error at run time!
print(wrong)
```

Output:

```
{'guests': 'two hundred fifty', 'venue': 42}
```

A type checker would complain about that line, but the program runs happily. Keep this in mind; it matters later.

### 2. Using a TypedDict with `with_structured_output`

We'll use the same offline helper as the previous lesson: a scripted model that accepts schemas and returns the tool call a real model would produce.

```python
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.utils.function_calling import convert_to_openai_tool

class ScriptedChatModel(FakeMessagesListChatModel):
    """A scripted chat model that accepts tools/schemas, so structured output runs offline."""
    def bind_tools(self, tools, **kwargs):
        return self.bind(tools=[convert_to_openai_tool(t) for t in tools], **kwargs)

def scripted(name, args):
    """A model that will 'fill' schema `name` with `args`."""
    return ScriptedChatModel(responses=[AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": "call_1"}])])

model = scripted("Enquiry", {"guests": 250, "event_date": "2026-12-12", "venue": "Rambagh", "pure_veg": True})
extractor = model.with_structured_output(Enquiry)

msg = ("Hi, need food for 250 guests on 12 Dec at Rambagh, pure veg, "
       "Rajasthani + some Chinese, budget around 1200 per plate.")
result = extractor.invoke(msg)
print(type(result).__name__)
print(result)
```

Output:

```
dict
{'guests': 250, 'event_date': '2026-12-12', 'venue': 'Rambagh', 'pure_veg': True}
```

The result is a plain `dict`, ready for `csv.DictWriter`, a database insert or a pandas `DataFrame`. With a real model, only the model line changes:

```python
# not-run: needs `pip install langchain langchain-anthropic` and ANTHROPIC_API_KEY
from langchain.chat_models import init_chat_model

model = init_chat_model("anthropic:claude-opus-5-5", temperature=0)
extractor = model.with_structured_output(Enquiry)
print(extractor.invoke(msg))
```

Example output:

```
{'guests': 250, 'event_date': '2026-12-12', 'venue': 'Rambagh', 'pure_veg': True}
```

### 3. What the model actually receives

`with_structured_output` converts your `TypedDict` into a JSON Schema and sends it to the provider (as a tool definition, or as a native response schema). You can see that schema yourself:

```python
import json
spec = convert_to_openai_tool(Enquiry)["function"]
print("name:       ", spec["name"])
print("description:", repr(spec["description"][:48]) + " ...")
print("properties: ", json.dumps(spec["parameters"]["properties"]))
print("required:   ", spec["parameters"]["required"])
```

Output:

```
name:        Enquiry
description: 'dict() -> new empty dictionary\ndict(mapping) -> ' ...
properties:  {"guests": {"type": "integer"}, "event_date": {"type": "string"}, "venue": {"type": "string"}, "pure_veg": {"type": "boolean"}}
required:    ['guests', 'event_date', 'venue', 'pure_veg']
```

Look closely at the description. Our class had no docstring, so the schema picked up the docstring of Python's built-in `dict` type: the model is told this schema is about "dict() -> new empty dictionary". That's a real, easy-to-miss bug. And nothing tells the model what format `event_date` should use, whether `venue` is a hall name or a city, or what `pure_veg` means for "veg with egg". **The model only knows what the schema tells it.** Field names help, but descriptions help much more.

### 4. Adding descriptions with a docstring and `Annotated`

Two things improve the schema:

- The class **docstring** becomes the schema's description.
- `Annotated[type, default, "description"]` attaches a description (and optionally a default) to each field. Use `...` as the "default" to mean "required, no default".

```python
from typing import Annotated, Literal, Optional

class CateringEnquiry(TypedDict):
    """A catering enquiry extracted from a customer's WhatsApp message."""
    guests: Annotated[int, ..., "Number of guests expected"]
    event_date: Annotated[str, ..., "Event date in YYYY-MM-DD format; assume the next such date"]
    venue: Annotated[str, ..., "Name of the venue or area, as written by the customer"]
    food_type: Annotated[Literal["veg", "non-veg", "jain", "mixed"], ..., "Overall food preference"]
    cuisines: Annotated[list[str], ..., "Cuisines requested, e.g. Rajasthani, Chinese"]
    budget_per_plate: Annotated[Optional[int], None, "Budget in rupees per plate, if mentioned"]

schema = convert_to_openai_tool(CateringEnquiry)["function"]
print(schema["description"])
for name, spec in schema["parameters"]["properties"].items():
    print(f"{name:<17} {json.dumps(spec)}")
print("required:", schema["parameters"]["required"])
```

Output:

```
A catering enquiry extracted from a customer's WhatsApp message.
guests            {"description": "Number of guests expected", "type": "integer"}
event_date        {"description": "Event date in YYYY-MM-DD format; assume the next such date", "type": "string"}
venue             {"description": "Name of the venue or area, as written by the customer", "type": "string"}
food_type         {"description": "Overall food preference", "enum": ["veg", "non-veg", "jain", "mixed"], "type": "string"}
cuisines          {"description": "Cuisines requested, e.g. Rajasthani, Chinese", "type": "array", "items": {"type": "string"}}
budget_per_plate  {"description": "Budget in rupees per plate, if mentioned", "type": "integer"}
required: ['guests', 'event_date', 'venue', 'food_type', 'cuisines']
```

Every field now carries an instruction, `food_type` is restricted to four values (an **enum**), `cuisines` is a list, and `budget_per_plate` is optional (it has a default, so it's not in `required`). The model will fill this far more accurately.

| You want | Write |
|---|---|
| A required field | `name: type` or `name: Annotated[type, ..., "desc"]` |
| A described field | `Annotated[type, ..., "description"]` |
| An optional field | `Annotated[Optional[type], None, "description"]` |
| A fixed set of values | `Literal["a", "b", "c"]` |
| A list | `list[str]`, `list[int]` |
| A nested object | Another `TypedDict` as the type (next section) |

### 5. Nested and list fields

Real data has structure inside structure. A wedding has several events (mehendi, sangeet, reception), each with its own guests and food:

```python
class Event(TypedDict):
    """One function within the wedding."""
    name: Annotated[str, ..., "e.g. mehendi, sangeet, reception"]
    guests: Annotated[int, ..., "Guests for this function"]
    food_type: Annotated[Literal["veg", "non-veg", "jain", "mixed"], ..., "Food preference"]

class WeddingEnquiry(TypedDict):
    """A multi-event wedding catering enquiry."""
    family_name: Annotated[str, ..., "Family or contact name"]
    events: Annotated[list[Event], ..., "Every function mentioned, in order"]

model = scripted("WeddingEnquiry", {
    "family_name": "Rathore",
    "events": [
        {"name": "mehendi", "guests": 80, "food_type": "veg"},
        {"name": "sangeet", "guests": 150, "food_type": "mixed"},
        {"name": "reception", "guests": 400, "food_type": "mixed"},
    ],
})
wedding = model.with_structured_output(WeddingEnquiry).invoke(
    "Rathore family here. Mehendi 80 people veg, sangeet 150 veg+non-veg, reception 400 both.")
total = sum(ev["guests"] for ev in wedding["events"])
print(wedding["family_name"], "|", len(wedding["events"]), "events |", total, "plates")
```

Output:

```
Rathore | 3 events | 630 plates
```

A list of nested objects is how you extract "many things from one text": every event in a message, every line item on an invoice, every person in a news article.

### 6. The catch: no run-time validation

Here's what happens when the model makes a mistake, such as writing the guest count as words and inventing a food type:

```python
sloppy = scripted("CateringEnquiry", {
    "guests": "around 250", "event_date": "12 Dec", "venue": "Rambagh",
    "food_type": "pure veg", "cuisines": "Rajasthani",
})
result = sloppy.with_structured_output(CateringEnquiry).invoke(msg)
print(result)
print(type(result["guests"]).__name__, "|", type(result["cuisines"]).__name__)
```

Output:

```
{'guests': 'around 250', 'event_date': '12 Dec', 'venue': 'Rambagh', 'food_type': 'pure veg', 'cuisines': 'Rajasthani'}
str | str
```

Every value is wrong for the schema, and **nothing complained**. With providers that enforce the schema natively (constrained decoding), these particular mistakes are much less likely, but LangChain itself doesn't check `TypedDict` results. If your code then does `result["guests"] * 1200`, you get a string repeated 1,200 times instead of a budget.

You have two options:

1. **Validate yourself** with a small check before using the data.
2. **Use Pydantic** instead, which validates and converts automatically. That's the next lesson, and the usual choice for anything important.

A minimal check looks like this:

```python
def check_enquiry(d):
    problems = []
    if not isinstance(d.get("guests"), int):
        problems.append(f"guests should be an integer, got {d.get('guests')!r}")
    if d.get("food_type") not in {"veg", "non-veg", "jain", "mixed"}:
        problems.append(f"food_type {d.get('food_type')!r} is not allowed")
    if not isinstance(d.get("cuisines"), list):
        problems.append("cuisines should be a list")
    return problems

for p in check_enquiry(result):
    print("-", p)
```

Output:

```
- guests should be an integer, got 'around 250'
- food_type 'pure veg' is not allowed
- cuisines should be a list
```

Writing these checks by hand for every schema is exactly the work Pydantic does for you.

### 7. Seeing the raw reply: `include_raw=True`

When something looks wrong, you want to see what the model actually sent. `include_raw=True` returns a dict with three keys: the raw `AIMessage`, the parsed result, and any parsing error:

```python
model = scripted("Enquiry", {"guests": 120, "event_date": "2026-11-02", "venue": "Amer", "pure_veg": False})
out = model.with_structured_output(Enquiry, include_raw=True).invoke("120 people at Amer on 2 Nov, non-veg ok")
print(sorted(out))
print("tool call:", out["raw"].tool_calls[0]["name"], out["raw"].tool_calls[0]["args"])
print("parsed:", out["parsed"])
print("error:", out["parsing_error"])
```

Output:

```
['parsed', 'parsing_error', 'raw']
tool call: Enquiry {'guests': 120, 'event_date': '2026-11-02', 'venue': 'Amer', 'pure_veg': False}
parsed: {'guests': 120, 'event_date': '2026-11-02', 'venue': 'Amer', 'pure_veg': False}
error: None
```

The raw message also carries `usage_metadata` (tokens), so `include_raw=True` is how you log cost for structured calls.

### 8. Choosing the method

`with_structured_output` takes a `method` argument that picks how the schema reaches the model:

| `method` | How it works | Notes |
|---|---|---|
| `"function_calling"` | The schema is sent as a tool the model must call | Works with every tool-calling model; the default for several providers |
| `"json_schema"` | The provider's native structured-output feature (constrained decoding) | Strongest format guarantee where supported (Anthropic, OpenAI, Google and others) |
| `"json_mode"` | The model is told to output valid JSON; the schema goes in your prompt | Older feature; weakest of the three |

```python
# not-run: needs `pip install langchain-anthropic` and ANTHROPIC_API_KEY
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-opus-5-5", temperature=0)
extractor = model.with_structured_output(CateringEnquiry, method="json_schema")   # native structured output
```

Defaults differ by provider and change over time, so if format reliability matters, set `method` explicitly and check the provider page in the LangChain docs.

### 9. When to choose TypedDict

| Choose TypedDict when… | Choose Pydantic when… |
|---|---|
| You want plain dicts (for JSON, CSV, a DataFrame) | You want objects with attributes and methods |
| The schema is simple and you'll check values yourself | You need automatic type conversion and validation |
| You're streaming partial results (dicts stream naturally) | You need custom rules (ranges, patterns, cross-field checks) |
| You don't want a Pydantic dependency in that code | You already use Pydantic (FastAPI, settings) |

---

## Try It Yourself

1. **Describe it.** Write a `TypedDict` called `TrainBooking` with `from_station`, `to_station`, `travel_date` (YYYY-MM-DD) and `travel_class` (one of `SL`, `3A`, `2A`, `1A`), each with an `Annotated` description. Print the `required` list from its schema.
2. **Optional field.** Add `passengers: Annotated[Optional[int], None, "Number of passengers, if given"]` and confirm it is not required.
3. **Validate a result.** Use `scripted("TrainBooking", {...})` to return `travel_class="AC 3 tier"`, then write a check that flags the bad class.

<details>
<summary>Show answers</summary>

**1.**

```python
class TrainBooking(TypedDict):
    """A train booking request."""
    from_station: Annotated[str, ..., "Departure station name"]
    to_station: Annotated[str, ..., "Arrival station name"]
    travel_date: Annotated[str, ..., "Date in YYYY-MM-DD"]
    travel_class: Annotated[Literal["SL", "3A", "2A", "1A"], ..., "Coach class code"]

print(convert_to_openai_tool(TrainBooking)["function"]["parameters"]["required"])
```

Output:

```
['from_station', 'to_station', 'travel_date', 'travel_class']
```

**2.**

```python
class TrainBooking2(TrainBooking):
    passengers: Annotated[Optional[int], None, "Number of passengers, if given"]

print("passengers" in convert_to_openai_tool(TrainBooking2)["function"]["parameters"]["required"])
```

Output:

```
False
```

(Subclassing a `TypedDict` adds fields to it.)

**3.**

```python
booking = scripted("TrainBooking", {"from_station": "Pune", "to_station": "Nagpur",
                                    "travel_date": "2026-11-05", "travel_class": "AC 3 tier"}
                   ).with_structured_output(TrainBooking).invoke("Pune to Nagpur 5 Nov AC 3 tier")
if booking["travel_class"] not in {"SL", "3A", "2A", "1A"}:
    print("bad class:", booking["travel_class"])
```

Output:

```
bad class: AC 3 tier
```

With a `Literal`, a provider using native structured output would normally force one of the four codes, but your code shouldn't rely on that without a check.

</details>

---

## Real-World Examples

- **Lead capture**: WhatsApp and email enquiries for caterers, decorators and wedding planners are extracted into dicts and appended to a Google Sheet or CRM.
- **Data pipelines**: analysts extract fields from thousands of documents into dicts and load them straight into pandas.
- **Quick prototypes**: TypedDict schemas are fast to write while exploring what fields are extractable, before hardening with Pydantic.
- **Streaming UIs** show partially filled dicts while the model is still writing.

---

## Common Misconceptions

### "TypedDict validates the data"

It doesn't, not in Python and not in LangChain. It describes the shape. Validate yourself or use Pydantic.

### "Field names are enough for the model"

Names help, but descriptions, enums and formats in `Annotated` make a big difference to accuracy, especially for dates, units and categories.

### "`Optional` means the model may skip it, so leave it out of the docs"

Optional fields still need descriptions, and ideally a rule for when to leave them empty ("only if the customer mentions a budget"), otherwise the model may invent values.

### "with_structured_output always uses tool calling"

It depends on the `method` and the provider's default. Native JSON-schema mode is available for many providers and gives stronger format guarantees.

---

## Interview Relevance

*"How do you use TypedDict for structured output in LangChain, and what are its limits?"* A strong answer: define a `TypedDict` (docstring as description, `Annotated[type, default_or_..., "description"]` per field, `Literal` for enums, `Optional` with a default for optional fields, nested `TypedDict`s and lists for complex data); `model.with_structured_output(MyTypedDict)` converts it to JSON Schema, sends it via function calling or native JSON schema (`method=`), and returns a plain `dict`. `include_raw=True` returns raw, parsed and parsing_error for debugging and token logging. Limitation: no run-time validation or type coercion, so validate manually or use Pydantic for important data.

---

## Key Takeaways

- **A `TypedDict` describes a dict's keys and types**; the result of `with_structured_output(TypedDict)` is a plain `dict`.
- **Descriptions matter**: use a docstring and `Annotated[type, ..., "description"]`; use `Literal` for fixed values and `Optional` with a default for optional fields.
- **Nest TypedDicts and use lists** to extract many records from one text.
- **No run-time validation**: wrong types pass through silently unless you check them, or switch to Pydantic.
- **`include_raw=True` and `method=`** give you the raw reply for debugging and control over how the schema is enforced.

---

**Up next:** [Structured Output with Pydantic and JSON Schema](structured-output-with-pydantic-and-json-schema.md)
