---
title: "Structured Output with Pydantic and JSON Schema"
course: LangChain Complete Guide
module: "5. Structured Output and Output Parsers"
type: Article
level: Intermediate
reading_time: 30 min
---

# Structured Output with Pydantic and JSON Schema: The Complete Guide

> 📚 **Before you start**
>
> - [Structured Output with TypedDict](structured-output-with-typeddict.md), for `with_structured_output`, `include_raw` and `method`, and the `scripted()` helper.
> - [Pydantic Models](../../apis-and-apps-fastapi-streamlit-and-docker/course.md#m4) in the APIs course, helpful but optional: this lesson explains everything it uses.

## Introduction

A chartered accountant's office in Ahmedabad scans hundreds of supplier invoices every month. A model reads each one and fills in vendor name, GSTIN, invoice date, line items and totals. Last lesson's `TypedDict` would hand back whatever the model wrote, including a GSTIN with 14 characters instead of 15, an amount written as `"12,400/-"`, or line items that don't add up to the total. In accounting, a silently wrong number is worse than no number.

**Pydantic** is the standard Python library for exactly this problem: you describe data as a class with typed fields and rules, and every object created from it is **checked and converted** on the way in. `with_structured_output` accepts a Pydantic class, sends its JSON Schema to the model, and returns a validated object, or tells you clearly what was wrong.

This lesson covers Pydantic for structured output end to end: fields, descriptions and constraints; nested models; custom validators, including cross-field checks like "line items must add up to the total"; what happens when validation fails and how to recover; and plain **JSON Schema** dictionaries, for when your schema comes from somewhere other than Python code.

> 💡 **Key Insight**
>
> With a Pydantic schema, the **model proposes and Pydantic disposes**: the model fills the fields, and Pydantic converts types and enforces every rule you wrote before your code sees the data. Rules the provider can't enforce during generation (ranges, patterns, sums) are still enforced, so bad data becomes a clear error instead of a silent bug.

---

## Core Explanation

### 1. Pydantic in five minutes

A Pydantic **model** is a class that inherits from `BaseModel`. Each field has a type, and optionally a default and rules set with `Field(...)`:

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field, ValidationError

class LineItem(BaseModel):
    description: str = Field(description="What was supplied")
    quantity: int = Field(gt=0, description="Number of units")
    unit_price: float = Field(gt=0, description="Price per unit in rupees, excluding GST")

item = LineItem(description="A4 paper ream", quantity="10", unit_price=245)
print(item)
print(type(item.quantity).__name__, item.quantity * item.unit_price)
```

Output:

```
description='A4 paper ream' quantity=10 unit_price=245.0
int 2450.0
```

Two things happened. The string `"10"` was **converted** to the integer `10` (Pydantic coerces sensible values), and `245` became `245.0` because the field is a `float`. Now break a rule:

```python
try:
    LineItem(description="Toner", quantity=0, unit_price="free")
except ValidationError as e:
    for err in e.errors():
        print(f"{err['loc'][0]:<11} {err['msg']}")
```

Output:

```
quantity    Input should be greater than 0
unit_price  Input should be a valid number, unable to parse string as a number
```

Every problem is reported at once, with the field name. That's the behaviour you want between a model and your accounts.

### 2. Pydantic with `with_structured_output`

The offline helper from the last two lessons again:

```python
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langchain_core.utils.function_calling import convert_to_openai_tool

class ScriptedChatModel(FakeMessagesListChatModel):
    """A scripted chat model that accepts tools/schemas, so structured output runs offline."""
    def bind_tools(self, tools, **kwargs):
        return self.bind(tools=[convert_to_openai_tool(t) for t in tools], **kwargs)

def scripted(name, args):
    return ScriptedChatModel(responses=[AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": "call_1"}])])
```

Now a full invoice schema. Docstrings and `Field(description=...)` go into the schema the model sees:

```python
class Invoice(BaseModel):
    """A supplier invoice extracted from a scanned document."""
    vendor: str = Field(description="Supplier's business name")
    gstin: str = Field(pattern=r"^[0-9]{2}[A-Z0-9]{13}$", description="15-character GSTIN of the supplier")
    invoice_date: str = Field(description="Invoice date as YYYY-MM-DD")
    items: list[LineItem] = Field(min_length=1, description="Every line item on the invoice")
    gst_rate: Literal[0, 5, 12, 18, 28] = Field(description="GST rate in percent")
    total: float = Field(description="Grand total in rupees including GST")
    notes: Optional[str] = Field(default=None, description="Anything unusual, else null")

model = scripted("Invoice", {
    "vendor": "Shree Stationers", "gstin": "24ABCDE1234F1Z5", "invoice_date": "2026-10-03",
    "items": [{"description": "A4 paper ream", "quantity": 10, "unit_price": 245},
              {"description": "Toner cartridge", "quantity": 2, "unit_price": 1800}],
    "gst_rate": 18, "total": 7139.0,
})
invoice = model.with_structured_output(Invoice).invoke("<text of the scanned invoice>")
print(type(invoice).__name__, "|", invoice.vendor, "|", len(invoice.items), "items |", invoice.items[1].unit_price)
```

Output:

```
Invoice | Shree Stationers | 2 items | 1800.0
```

You get an `Invoice` object, with nested `LineItem` objects inside, all validated. (The `scripted` model returns the exact tool call a real model would send; with a real model, only the model line changes.)

### 3. What the model sees

Pydantic generates the JSON Schema, including descriptions, enums and the nested item schema:

```python
import json

params = convert_to_openai_tool(Invoice)["function"]["parameters"]
print("required:", params["required"])
print("gstin:   ", json.dumps(params["properties"]["gstin"]))
print("gst_rate:", json.dumps(params["properties"]["gst_rate"]))
print("items:   ", json.dumps(params["properties"]["items"])[:110] + "...")
```

Output:

```
required: ['vendor', 'gstin', 'invoice_date', 'items', 'gst_rate', 'total']
gstin:    {"description": "15-character GSTIN of the supplier", "pattern": "^[0-9]{2}[A-Z0-9]{13}$", "type": "string"}
gst_rate: {"description": "GST rate in percent", "enum": [0, 5, 12, 18, 28], "type": "integer"}
items:    {"description": "Every line item on the invoice", "items": {"properties": {"description": {"description": "Wha...
```

The model receives the pattern and the enum as hints. Whether the provider **enforces** them during generation varies (constrained decoding usually supports types, required fields and enums well, and patterns or number ranges less consistently). That's fine: Pydantic enforces all of them afterwards.

### 4. Custom validators: rules a schema can't express

Some rules involve logic: normalise a value, or check that fields agree with each other. Pydantic has two kinds of validator:

- `@field_validator("field")` checks or cleans **one field**.
- `@model_validator(mode="after")` checks the **whole object** once all fields are set.

For invoices: normalise the GSTIN to upper case before checking it, and make sure the line items plus GST add up to the stated total (within a rupee, for rounding):

```python
from pydantic import field_validator, model_validator

class CheckedInvoice(Invoice):
    """A supplier invoice extracted from a scanned document, with arithmetic checks."""

    @field_validator("gstin", mode="before")
    @classmethod
    def clean_gstin(cls, v):
        return v.replace(" ", "").upper() if isinstance(v, str) else v

    @model_validator(mode="after")
    def totals_add_up(self):
        subtotal = sum(i.quantity * i.unit_price for i in self.items)
        expected = round(subtotal * (1 + self.gst_rate / 100), 2)
        if abs(expected - self.total) > 1:
            raise ValueError(f"items + {self.gst_rate}% GST = {expected}, but total says {self.total}")
        return self

good = scripted("CheckedInvoice", {
    "vendor": "Shree Stationers", "gstin": "24abcde1234f1z5", "invoice_date": "2026-10-03",
    "items": [{"description": "A4 paper ream", "quantity": 10, "unit_price": 245},
              {"description": "Toner cartridge", "quantity": 2, "unit_price": 1800}],
    "gst_rate": 18, "total": 7139.0,
}).with_structured_output(CheckedInvoice).invoke("<invoice text>")
print(good.gstin, good.total)
```

Output:

```
24ABCDE1234F1Z5 7139.0
```

The lower-case GSTIN was cleaned before the pattern check, and the arithmetic passed (2,450 + 3,600 = 6,050, plus 18% = 7,139).

### 5. When validation fails

Now the model misreads a digit: the total says 7,193 instead of 7,139. What does the chain do?

```python
misread = scripted("CheckedInvoice", {
    "vendor": "Shree Stationers", "gstin": "24ABCDE1234F1Z5", "invoice_date": "2026-10-03",
    "items": [{"description": "A4 paper ream", "quantity": 10, "unit_price": 245},
              {"description": "Toner cartridge", "quantity": 2, "unit_price": 1800}],
    "gst_rate": 18, "total": 7193.0,
})
try:
    misread.with_structured_output(CheckedInvoice).invoke("<invoice text>")
except Exception as e:
    print(type(e).__name__)
    print(e.errors()[0]["msg"])
```

Output:

```
ValidationError
Value error, items + 18% GST = 7139.0, but total says 7193.0
```

The chain **raised**: no wrong total reached your accounts. In a batch job you usually don't want one bad invoice to crash the run, so use `include_raw=True`, which never raises for parsing problems and hands you the error instead:

```python
out = misread.with_structured_output(CheckedInvoice, include_raw=True).invoke("<invoice text>")
print("parsed:", out["parsed"])
print("error type:", type(out["parsing_error"]).__name__)
print("model said total =", out["raw"].tool_calls[0]["args"]["total"])
```

Output:

```
parsed: None
error type: ValidationError
model said total = 7193.0
```

Now your code can decide: send the invoice to a human review queue, or **ask the model again** with the error message, which often fixes it. Here's a small repair loop:

```python
from langchain_core.messages import HumanMessage

def extract_with_repair(model_factory, text, schema, attempts=2):
    messages = [HumanMessage(text)]
    for attempt in range(1, attempts + 1):
        out = model_factory(attempt).with_structured_output(schema, include_raw=True).invoke(messages)
        if out["parsing_error"] is None:
            return out["parsed"], attempt
        problem = out["parsing_error"].errors()[0]["msg"]
        messages.append(HumanMessage(f"Your previous answer was invalid: {problem}. Re-read the invoice and fix it."))
    return None, attempts

def model_factory(attempt):
    # 1st attempt misreads the total; 2nd attempt (after the error message) gets it right.
    total = 7193.0 if attempt == 1 else 7139.0
    return scripted("CheckedInvoice", {**misread.responses[0].tool_calls[0]["args"], "total": total})

inv, used = extract_with_repair(model_factory, "<invoice text>", CheckedInvoice)
print(f"fixed on attempt {used}: total = {inv.total}")
```

Output:

```
fixed on attempt 2: total = 7139.0
```

This "validate, explain the error, retry" loop is the same repair loop you built by hand in [Lab: Reliable JSON Extraction](../../generative-ai-and-llm-foundations/04-prompting-and-structured-output/lab-reliable-json-extraction.md), now with Pydantic doing the checking. Two retries is plenty; after that, send it to a human.

### 6. Extracting many records: a list wrapper

`with_structured_output` returns one object. To extract a variable number of things (every person in a news story, every transaction in a bank SMS dump), wrap a list in a model:

```python
class Transaction(BaseModel):
    amount: float = Field(description="Amount in rupees")
    kind: Literal["debit", "credit"]
    counterparty: str = Field(description="Merchant or person, as written")

class TransactionList(BaseModel):
    """All transactions found in a batch of bank SMS messages."""
    transactions: list[Transaction]

sms = """Rs 450.00 debited from A/c XX1234 to SWIGGY on 15-10. 
Rs 25,000 credited to A/c XX1234 by NEFT from ACME PAYROLL.
Rs 1,299 debited for NETFLIX autopay."""
txns = scripted("TransactionList", {"transactions": [
    {"amount": 450, "kind": "debit", "counterparty": "SWIGGY"},
    {"amount": 25000, "kind": "credit", "counterparty": "ACME PAYROLL"},
    {"amount": 1299, "kind": "debit", "counterparty": "NETFLIX"},
]}).with_structured_output(TransactionList).invoke(sms)

spent = sum(t.amount for t in txns.transactions if t.kind == "debit")
print(len(txns.transactions), "transactions | spent ₹", spent)
```

Output:

```
3 transactions | spent ₹ 1749.0
```

### 7. JSON Schema dictionaries

Sometimes the schema isn't Python code: it comes from a config file, a database, another team's API spec, or a form builder in your product. `with_structured_output` also accepts a **JSON Schema** as a plain dict. It needs a `title` (used as the name) and should have a `description`:

```python
complaint_schema = {
    "title": "Complaint",
    "description": "A customer complaint about a delivery",
    "type": "object",
    "properties": {
        "order_id": {"type": "string", "description": "Order number like OD123..."},
        "issue": {"type": "string", "enum": ["late", "damaged", "wrong_item", "missing"]},
        "wants_refund": {"type": "boolean"},
    },
    "required": ["order_id", "issue", "wants_refund"],
}

result = scripted("Complaint", {"order_id": "OD4471", "issue": "damaged", "wants_refund": True}
                  ).with_structured_output(complaint_schema).invoke("OD4471 arrived with a cracked screen, I want my money back")
print(type(result).__name__, result)
```

Output:

```
dict {'order_id': 'OD4471', 'issue': 'damaged', 'wants_refund': True}
```

Like `TypedDict`, a JSON Schema dict returns a plain `dict` and is **not validated** by LangChain. If the schema comes from outside, you can validate results with a JSON Schema validator library, or build a Pydantic model from it.

### 8. Comparing the three schema types

| | `TypedDict` | Pydantic `BaseModel` | JSON Schema `dict` |
|---|---|---|---|
| Result type | `dict` | Model instance | `dict` |
| Run-time validation | No | **Yes** (types, constraints, validators) | No |
| Type conversion (`"10"` → `10`) | No | **Yes** | No |
| Descriptions | `Annotated[..., "desc"]`, docstring | `Field(description=...)`, docstring | `"description"` keys |
| Custom logic | No | `field_validator`, `model_validator` | No |
| Best for | Simple dicts, quick prototypes, streaming | **Anything important** | Schemas defined outside Python |

### 9. Tips for schemas models fill well

- **Describe every field**, including units ("in rupees"), formats ("YYYY-MM-DD") and what to do when unknown ("null if not mentioned").
- **Use enums (`Literal`)** for categories; free-text categories drift ("Billing", "billing issue", "payments").
- **Make fields optional when the text may not contain them**, or the model will invent values to fill required fields.
- **Keep nesting shallow** and names obvious; deeply nested schemas are harder for models.
- **Validate business rules in validators** (sums, date ranges, catalogue lookups), not in the prompt alone.
- **Set `method="json_schema"`** for providers that support native structured output when format reliability matters, and keep `include_raw=True` in batch jobs so one failure doesn't stop the run.

---

## Try It Yourself

1. **A PAN field.** Add a field `pan: str` with the pattern `^[A-Z]{5}[0-9]{4}[A-Z]$` to a small `Supplier` model, plus a `mode="before"` validator that strips spaces and upper-cases it. Validate `"abcde 1234 f"`.
2. **Cross-field rule.** Write a `TrainTicket` model with `departure: str` and `arrival: str` (both `"HH:MM"`) and `overnight: bool`. Add a model validator that raises if arrival is earlier than departure and `overnight` is `False`.
3. **No-crash batch.** Run `with_structured_output(CheckedInvoice, include_raw=True)` over a list of two scripted models (one good, one misread) and print how many were accepted and how many sent to review.

<details>
<summary>Show answers</summary>

**1.**

```python
class Supplier(BaseModel):
    name: str
    pan: str = Field(pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$")

    @field_validator("pan", mode="before")
    @classmethod
    def clean(cls, v):
        return v.replace(" ", "").upper()

print(Supplier(name="Shree Stationers", pan="abcde 1234 f").pan)
```

Output:

```
ABCDE1234F
```

**2.**

```python
class TrainTicket(BaseModel):
    departure: str
    arrival: str
    overnight: bool

    @model_validator(mode="after")
    def times_make_sense(self):
        if self.arrival < self.departure and not self.overnight:
            raise ValueError("arrival is before departure but overnight is False")
        return self

print(TrainTicket(departure="22:10", arrival="06:45", overnight=True).arrival)
try:
    TrainTicket(departure="22:10", arrival="06:45", overnight=False)
except ValidationError as e:
    print(e.errors()[0]["msg"])
```

Output:

```
06:45
Value error, arrival is before departure but overnight is False
```

(Comparing `"HH:MM"` strings works because they're zero-padded.)

**3.**

```python
good_args = dict(misread.responses[0].tool_calls[0]["args"], total=7139.0)
models = [scripted("CheckedInvoice", good_args), misread]
accepted, review = [], []
for m in models:
    out = m.with_structured_output(CheckedInvoice, include_raw=True).invoke("<invoice>")
    (accepted if out["parsing_error"] is None else review).append(out)
print(len(accepted), "accepted,", len(review), "sent to review")
```

Output:

```
1 accepted, 1 sent to review
```

</details>

---

## Real-World Examples

- **Accounts-payable automation** extracts invoices into Pydantic models with GSTIN patterns and arithmetic validators; failures go to a human queue.
- **Insurance claims** are extracted from forms and doctors' notes with strict enums for claim types and date-range validators.
- **FastAPI services** reuse the same Pydantic models as their response schema, so the API contract and the LLM contract are one definition.
- **Bank and fintech apps** turn transaction SMS into typed records with list-wrapper schemas for spending insights.

---

## Common Misconceptions

### "If the provider enforces the schema, Pydantic validation is redundant"

Providers enforce shape (types, required fields, enums) well, but not always patterns, ranges or cross-field logic, and never your business rules. Pydantic checks all of it.

### "A validation error means the model is useless for this task"

Usually one retry with the error message fixes it. Measure your first-try and after-retry success rates before deciding.

### "Required fields make extraction more complete"

They make it more **invented**. If the text may not contain a value, make the field optional with a description saying when to leave it null.

### "JSON Schema dicts and Pydantic behave the same"

They produce similar schemas for the model, but only Pydantic validates and converts the result.

---

## Interview Relevance

*"How do you make LLM extraction production-safe?"* A strong answer: define a Pydantic model with typed fields, `Field` descriptions and constraints (`gt`, `pattern`, `min_length`), `Literal` enums, optional fields for absent data, nested models and list wrappers; call `model.with_structured_output(Model)` (ideally `method="json_schema"` where supported) to get validated instances; add `field_validator`/`model_validator` for normalisation and cross-field rules; use `include_raw=True` to capture `parsing_error` without crashing, then retry with the error message or route to human review; use JSON Schema dicts when schemas come from outside Python, remembering they aren't validated. Mention that constrained decoding guarantees shape, not truth.

---

## Key Takeaways

- **Pydantic models are validated schemas**: types are converted, constraints and validators enforced, errors reported per field.
- **`with_structured_output(PydanticModel)`** returns a model instance (with nested objects), or raises a `ValidationError`.
- **Validators** handle normalisation (`mode="before"`) and cross-field rules (`model_validator`), which providers can't enforce.
- **Recover, don't crash**: `include_raw=True` exposes `parsing_error`; retry with the error message or send to review.
- **JSON Schema dicts** work for externally defined schemas and return unvalidated dicts, like `TypedDict`.

---

**Up next:** [StrOutputParser](stroutputparser.md)
