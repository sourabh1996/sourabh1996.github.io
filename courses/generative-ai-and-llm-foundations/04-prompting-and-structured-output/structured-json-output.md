---
title: "Structured JSON Output"
course: "Generative AI and LLM Foundations"
module: "4. Prompting and Structured Output"
type: Article
level: Beginner
reading_time: 36 min
---

# Structured JSON Output: The Complete Guide

> 📚 **Before you start**
>
> - [Prompting Fundamentals](prompting-fundamentals.md) and [System Prompts and Roles](system-prompts-and-roles.md), for writing clear instructions and why prefill is fading.
> - [Temperature and Model Settings](../03-how-llms-work/temperature-and-model-settings.md), for how the model picks each token from a probability distribution.
> - [APIs and Apps › Validation and Schemas](../../apis-and-apps-fastapi-streamlit-and-docker/course.md#m4), for Pydantic models. A short recap is included below.

## Introduction

A hospital in Pune wants to read discharge summaries and fill in its records system: patient age, diagnosis, medicines, follow-up date. A developer writes a prompt, "Extract these fields as JSON", tests it on five summaries, and it works beautifully. It goes live. At 2 a.m. the import job crashes. The model's reply that night began with *"Sure! Here is the extracted information:"* followed by the JSON wrapped in a Markdown code fence. The parser expected a `{` as the first character and got an `S`.

This is the gap between a **human reader** and a **program**. A person shrugs off a friendly preamble or a missing comma. Code can't. Whenever an LLM's output feeds into software (a database, an API call, a dashboard, a decision), you need output that is **machine-readable and guaranteed to have the right shape**. That is **structured output**, and JSON is its common language.

By the end of this lesson you will be able to:

- Explain why free-text replies break programs, and the common ways "JSON" from a model goes wrong.
- Describe the data you need as a **JSON Schema**, generated from a Pydantic model.
- Validate model output in code, including business rules that a schema can't express.
- Climb the reliability ladder from "please reply in JSON" to **constrained decoding**, and explain how constrained decoding works inside the model.
- Use structured outputs in a real API, and design schemas that make the model's job easier.

> 💡 **Key Insight**
>
> There are two separate questions: **is the output the right shape?** and **are the values right?** Constrained decoding (an API's structured-output mode) can guarantee the first by making invalid tokens impossible. Nothing guarantees the second, so you **always validate the values in code** as well.

---

## Core Explanation

### 1. Why programs need structure

| Use | Free-text reply | Structured reply |
|---|---|---|
| Extract fields from a document | "The patient, a 64-year-old, was diagnosed with..." | `{"age": 64, "diagnosis": "..."}` |
| Classify a support ticket | "This seems to be about a refund, I think." | `{"category": "refund", "urgent": false}` |
| Route a request to the right team | "You should probably talk to billing." | `{"route": "billing"}` |
| Fill a form or call an API | A paragraph describing the booking | `{"from": "SBC", "to": "MYS", "date": "2026-10-20"}` |
| Render a UI card | A long message | `{"title": "...", "price_inr": 999}` |

The structured version can be stored, compared, counted and acted on with ordinary code, without guessing.

### 2. JSON in two minutes, and how model JSON breaks

**JSON** (JavaScript Object Notation) is a text format for data: objects in `{}` with `"key": value` pairs, lists in `[]`, strings in double quotes, numbers, `true`/`false` and `null`. Python reads it with `json.loads`.

Models produce JSON that *looks* right to a human but trips the parser in a handful of predictable ways:

```python
import json

replies = {
    "clean": '{"age": 64, "diagnosis": "type 2 diabetes"}',
    "preamble": 'Sure! Here is the JSON: {"age": 64, "diagnosis": "type 2 diabetes"}',
    "code fence": '```json\n{"age": 64, "diagnosis": "type 2 diabetes"}\n```',
    "single quotes": "{'age': 64, 'diagnosis': 'type 2 diabetes'}",
    "trailing comma": '{"age": 64, "diagnosis": "type 2 diabetes",}',
    "cut off": '{"age": 64, "diagnosis": "type 2 dia',
}

for name, text in replies.items():
    try:
        json.loads(text)
        print(f"{name:<15} parsed")
    except json.JSONDecodeError as err:
        print(f"{name:<15} FAILED: {err.msg}")
```

Output:

```
clean           parsed
preamble        FAILED: Expecting value
code fence      FAILED: Expecting value
single quotes   FAILED: Expecting property name enclosed in double quotes
trailing comma  FAILED: Illegal trailing comma before end of object
cut off         FAILED: Unterminated string starting at
```

The last one, **cut off**, happens when the reply hits `max_tokens` ([Temperature and Model Settings](../03-how-llms-work/temperature-and-model-settings.md)): always check the stop reason before parsing. And even when JSON parses, it can still be **wrong**: a missing field, `"age": "sixty-four"` instead of a number, or an extra field nobody asked for. Parsing only checks the syntax. To check the content you need a schema.

### 3. A schema: the contract for the output

A **JSON Schema** is a JSON document that describes what valid data looks like: which fields exist, their types, which are required, and which values are allowed. It is the contract between your prompt, the model and your code.

You rarely write a schema by hand in Python. You write a **Pydantic** model, and Pydantic generates the schema. Quick recap, since Pydantic is taught properly in [Validation and Schemas](../../apis-and-apps-fastapi-streamlit-and-docker/course.md#m4): a Pydantic model is a class whose attributes have types; creating or validating one checks every value against those types and raises a clear error if something doesn't fit.

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field

class Medicine(BaseModel):
    name: str = Field(description="Medicine name as written, e.g. 'Metformin'")
    dose: str = Field(description="Dose and frequency, e.g. '500 mg twice daily'")

class DischargeSummary(BaseModel):
    patient_age: int = Field(description="Age in years")
    diagnosis: str = Field(description="Main diagnosis in plain words")
    severity: Literal["mild", "moderate", "severe"]
    medicines: list[Medicine]
    follow_up_date: Optional[str] = Field(description="YYYY-MM-DD, or null if not mentioned")

schema = DischargeSummary.model_json_schema()
print(json.dumps(schema["properties"]["severity"]))
print(json.dumps(schema["properties"]["follow_up_date"]))
print("required:", schema["required"])
```

Output:

```
{"enum": ["mild", "moderate", "severe"], "title": "Severity", "type": "string"}
{"anyOf": [{"type": "string"}, {"type": "null"}], "description": "YYYY-MM-DD, or null if not mentioned", "title": "Follow Up Date"}
required: ['patient_age', 'diagnosis', 'severity', 'medicines', 'follow_up_date']
```

Look at what the schema captures: `severity` may only be one of three words (an **enum**), `follow_up_date` may be a string or `null`, and every field is required, so the model must say `null` explicitly rather than silently skip a field. The `description` text travels with the schema to the model, so descriptions double as instructions.

### 4. Validating what comes back

With the model class in hand, one call parses **and** checks a reply:

```python
from pydantic import ValidationError

good = '''{"patient_age": 64, "diagnosis": "type 2 diabetes", "severity": "moderate",
          "medicines": [{"name": "Metformin", "dose": "500 mg twice daily"}],
          "follow_up_date": "2026-11-02"}'''

bad = '''{"patient_age": "sixty-four", "diagnosis": "type 2 diabetes", "severity": "medium",
         "medicines": [], "follow_up_date": null}'''

record = DischargeSummary.model_validate_json(good)
print(record.patient_age, record.medicines[0].name, record.follow_up_date)

try:
    DischargeSummary.model_validate_json(bad)
except ValidationError as err:
    for e in err.errors():
        print(f"{'.'.join(map(str, e['loc']))}: {e['msg']}")
```

Output:

```
64 Metformin 2026-11-02
patient_age: Input should be a valid integer, unable to parse string as an integer
severity: Input should be 'mild', 'moderate' or 'severe'
```

These error messages are precise enough to send back to the model ("`severity`: Input should be 'mild', 'moderate' or 'severe'") and ask it to fix its answer. You'll build exactly that **validate-and-repair loop** in the [lab](lab-reliable-json-extraction.md).

### 5. The reliability ladder

There are four ways to get JSON from a model, each more reliable than the last.

![A four-step ladder for getting JSON from an LLM: asking in the prompt, adding examples with validation and retry, JSON mode which guarantees valid JSON syntax, and schema-constrained decoding which guarantees the schema. A bar beneath all four steps says the values are always checked in code: stop reason, business rules, values found in the source, and human review when stakes are high](/img/diagrams/generative-ai-and-llm-foundations/json-reliability-ladder.svg)
*Climb as high as your model and API allow. Whatever rung you reach, keep validating the values in code.*

| Rung | How | What's guaranteed | Typical failure |
|---|---|---|---|
| **1. Ask in the prompt** | "Reply with only JSON matching this schema" | Nothing | Preambles, code fences, missing fields |
| **2. Ask + examples + validate + retry** | Few-shot examples, parse and validate, re-ask with the errors | Nothing per call, but failures are caught and usually fixed | Extra latency and cost on retries |
| **3. JSON mode** | An API setting that forces syntactically valid JSON | Valid JSON syntax | Right syntax, wrong fields or types |
| **4. Schema-constrained decoding** | An API setting that takes your schema ("structured outputs", "strict" tools) | Output matches the schema | Values can still be wrong; refusals and truncation |

Rungs 1 and 2 work with any model, including small open models. Rungs 3 and 4 need support from the API or the inference server. Most major providers now support rung 4 on their current models.

### 6. How constrained decoding works

Rung 4 sounds like magic: how can an API *guarantee* the model follows a schema? The answer comes straight from [Temperature and Model Settings](../03-how-llms-work/temperature-and-model-settings.md). At every step the model produces a probability for every token, and a sampler picks one. **Constrained decoding** adds one step before sampling: it works out which tokens could still lead to valid output, and sets the probability of every other token to zero.

Here is the idea at toy scale. The schema allows only `{"sentiment": "positive"}`, `{"sentiment": "negative"}` or `{"sentiment": "neutral"}`. Our pretend model, like a chatty real one, would most like to start with "Sure":

```python
import numpy as np

VOCAB = ["Sure", "!", '{"sentiment": "', "positive", "negative", "neutral", '"}', "I", "think"]

def model_logits(generated):
    """A pretend model's scores. It loves chatty openings and is unsure about the label."""
    if not generated:
        return np.array([3.0, 0.5, 1.5, 0.2, 0.2, 0.2, 0.1, 2.0, 0.5])
    if generated[-1] == '{"sentiment": "':
        return np.array([0.1, 0.1, 0.1, 1.2, 0.3, 1.4, 0.1, 0.5, 0.2])
    return np.array([0.5, 1.0, 0.1, 0.1, 0.1, 0.1, 2.5, 0.3, 0.3])

def allowed_next(generated):
    """What the schema permits next: open the object, pick a label, then close it."""
    if not generated:
        return {'{"sentiment": "'}
    if generated[-1] == '{"sentiment": "':
        return {"positive", "negative", "neutral"}
    if generated[-1] in {"positive", "negative", "neutral"}:
        return {'"}'}
    return set()                                     # finished

def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()

def generate(constrained):
    generated = []
    for _ in range(3):
        logits = model_logits(generated)
        if constrained:
            allowed = allowed_next(generated)
            logits = np.where([t in allowed for t in VOCAB], logits, -np.inf)
        probs = softmax(logits)
        token = VOCAB[int(np.argmax(probs))]          # greedy, to keep the demo deterministic
        generated.append(token)
    return "".join(generated)

print("unconstrained:", generate(constrained=False))
print("constrained:  ", generate(constrained=True))
```

Output:

```
unconstrained: Sure"}"}
constrained:   {"sentiment": "neutral"}
```

Without constraints, the model's favourite tokens produce garbage. With the mask, the only tokens that can be chosen are ones that keep the output valid, so the result **must** match the schema. Notice what the mask did *not* do: it didn't decide between "positive" and "neutral". The model's own probabilities still chose "neutral". **Constrained decoding controls the shape; the model still controls the content.**

Real systems turn the full JSON Schema into a grammar and track, token by token, which continuations are legal. That compilation is why the first request with a new schema can be slightly slower.

### 7. Structured outputs in a real API

With Anthropic's Messages API, you pass the schema in `output_config`, and the reply's text block is guaranteed to be JSON matching it:

```python
# not-run: needs the anthropic package and an API key
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Extract the fields from this discharge summary:\n<summary>...</summary>"}],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "patient_age": {"type": "integer"},
                    "diagnosis": {"type": "string"},
                    "severity": {"type": "string", "enum": ["mild", "moderate", "severe"]},
                },
                "required": ["patient_age", "diagnosis", "severity"],
                "additionalProperties": False,
            },
        }
    },
)
print(response.stop_reason)
print(next(b.text for b in response.content if b.type == "text"))
```

Example output:

```
end_turn
{"patient_age":64,"diagnosis":"type 2 diabetes with high blood pressure","severity":"moderate"}
```

`"additionalProperties": False` means "no fields other than these", and the API requires it on every object in the schema. The Python SDK can also take a Pydantic model directly and hand you back a validated object:

```python
# not-run: needs the anthropic package and an API key
response = client.messages.parse(
    model="claude-opus-5-5",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Extract the fields from this discharge summary:\n<summary>...</summary>"}],
    output_format=DischargeSummary,
)
record = response.parsed_output          # a DischargeSummary instance
print(record.severity, [m.name for m in record.medicines])
```

Example output:

```
moderate ['Metformin', 'Telmisartan']
```

Things to know about schema-constrained output (details vary by provider; check the docs for your model):

- **Not every JSON Schema feature is enforced.** Anthropic's structured outputs, for example, don't support number ranges (`minimum`, `maximum`) or string lengths; the Python SDK removes such constraints from the schema it sends and checks them in your code instead. Recursive schemas aren't supported either.
- **Refusals and truncation still happen.** If the stop reason is `refusal` or `max_tokens`, the output may not match the schema. Check the stop reason first, exactly as in the [lab](../03-how-llms-work/lab-your-first-llm-api-call.md).
- **Tools have a strict mode too.** When a model calls a tool, the tool's inputs are JSON as well; marking a tool `strict` constrains its inputs to the tool's schema. You'll use this in [Function Calling Step by Step](../../agentic-ai-fundamentals/04-tools-and-function-calling/function-calling-step-by-step.md).
- **Other providers offer the same idea.** OpenAI calls it Structured Outputs (a JSON Schema response format with a strict setting), and Google's Gemini API accepts a response schema. Open-model servers offer grammar-constrained generation as well.

### 8. What structure can't guarantee: validate the values

A schema says `"amount_inr"` is a number. It can't say the number is the one printed on the invoice. Constrained models still hallucinate **values**: a plausible date that isn't in the document, an amount from the wrong line, a name with a typo. So production code adds **business-rule validation** on top of the schema. Pydantic's `field_validator` is the natural place:

```python
from datetime import date
from pydantic import field_validator

class UpiPayment(BaseModel):
    payee: str
    amount_inr: float
    paid_on: date
    upi_ref: str

    @field_validator("amount_inr")
    @classmethod
    def amount_is_sensible(cls, v):
        if not 0 < v <= 100_000:
            raise ValueError("UPI payments here must be between ₹0 and ₹1,00,000")
        return v

    @field_validator("paid_on")
    @classmethod
    def not_in_future(cls, v):
        if v > date(2026, 10, 14):                      # in real code: date.today()
            raise ValueError("payment date is in the future")
        return v

    @field_validator("upi_ref")
    @classmethod
    def ref_is_12_digits(cls, v):
        if not (v.isdigit() and len(v) == 12):
            raise ValueError("UPI reference must be 12 digits")
        return v

candidates = [
    '{"payee": "Sharma Kirana", "amount_inr": 450, "paid_on": "2026-10-12", "upi_ref": "629184735201"}',
    '{"payee": "Sharma Kirana", "amount_inr": 4500000, "paid_on": "2026-12-01", "upi_ref": "62918"}',
]
for text in candidates:
    try:
        p = UpiPayment.model_validate_json(text)
        print("valid:", p.payee, p.amount_inr, p.paid_on)
    except ValidationError as err:
        print("rejected:", [e["msg"].removeprefix("Value error, ") for e in err.errors()])
```

Output:

```
valid: Sharma Kirana 450.0 2026-10-12
rejected: ['UPI payments here must be between ₹0 and ₹1,00,000', 'payment date is in the future', 'UPI reference must be 12 digits']
```

The second candidate is perfectly valid JSON with the right types. Only the business rules catch that it's nonsense. A good extraction pipeline also checks values **against the source**: does the extracted UPI reference actually appear in the original text? That one check catches a large share of hallucinated values. You'll add it in the lab.

### 9. Designing schemas the model can fill well

The schema is also part of the prompt, so design it for the model as well as for your code.

| Tip | Why | Example |
|---|---|---|
| **Use clear field names and descriptions** | Names and descriptions are instructions | `follow_up_date` with "YYYY-MM-DD, or null if not mentioned" beats `fud` |
| **Use enums for categories** | The model can't invent a new label | `"severity": ["mild", "moderate", "severe"]` |
| **Allow "not found"** | Without a way to say "missing", a required field invites a made-up value | `Optional[str]` with "null if not mentioned" |
| **Put evidence before the answer** | Tokens are generated in order, so earlier fields become context for later ones | A `quote` field before `amount_inr`; a short `reasoning` field before `category` |
| **Keep nesting shallow** | Deep, complex schemas are harder to fill and to validate | Prefer a list of flat objects to five levels of nesting |
| **Don't ask for what code can compute** | Models make arithmetic slips ([Where LLMs Fail](../03-how-llms-work/where-llms-fail.md)) | Extract line items; compute the total in Python |
| **Version the schema** | Downstream code depends on it | `InvoiceV2`, with a changelog |

The "evidence before the answer" tip deserves a concrete look, because it uses what you know about how generation works:

```python
class TicketTriage(BaseModel):
    evidence: str = Field(description="The sentence from the ticket that shows what the problem is")
    category: Literal["refund", "delivery", "account", "other"]
    urgent: bool = Field(description="True only if the customer is charged twice or cannot access their account")

print(list(TicketTriage.model_json_schema()["properties"]))
```

Output:

```
['evidence', 'category', 'urgent']
```

Field order in the schema becomes the order the model writes them. By the time it writes `category`, it has already copied the relevant sentence, so the label is based on the text, and a person reviewing the result can see why.

---

## Try It Yourself

1. **Repair the easy cases.** Write a function `loose_json(text)` that strips a leading preamble and a Markdown code fence by taking the text from the first `{` to the last `}`, then parses it. Test it on the `"preamble"` and `"code fence"` replies from section 2.
2. **Schema for a train booking.** Write a Pydantic model `BookingRequest` with `from_station` and `to_station` (strings), `travel_date` (a `date`), `travel_class` (one of `"SL"`, `"3A"`, `"2A"`, `"1A"`) and `passengers` (an `int`). Validate `{"from_station": "SBC", "to_station": "MAS", "travel_date": "2026-10-20", "travel_class": "3AC", "passengers": 2}` and print the error.
3. **Constrain to a different label.** In the constrained-decoding demo, change `model_logits` so that after the opening token, `"negative"` has the highest score. Run the constrained generation again.

<details>
<summary>Show answers</summary>

**1.**

```python
def loose_json(text):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found")
    return json.loads(text[start:end + 1])

print(loose_json(replies["preamble"]))
print(loose_json(replies["code fence"]))
```

Output:

```
{'age': 64, 'diagnosis': 'type 2 diabetes'}
{'age': 64, 'diagnosis': 'type 2 diabetes'}
```

This rescues the two most common rung-1 failures. It can't fix single quotes, trailing commas or truncation, which is why you validate and retry, or better, use constrained decoding.

**2.**

```python
class BookingRequest(BaseModel):
    from_station: str
    to_station: str
    travel_date: date
    travel_class: Literal["SL", "3A", "2A", "1A"]
    passengers: int

try:
    BookingRequest.model_validate_json('{"from_station": "SBC", "to_station": "MAS", "travel_date": "2026-10-20", "travel_class": "3AC", "passengers": 2}')
except ValidationError as err:
    print(err.errors()[0]["loc"], err.errors()[0]["msg"])
```

Output:

```
('travel_class',) Input should be 'SL', '3A', '2A' or '1A'
```

Everyone says "3AC", but the schema says "3A". With an enum in a constrained schema, the model could only have produced one of the four allowed codes.

**3.**

```python
original_logits = model_logits

def model_logits(generated):
    if generated and generated[-1] == '{"sentiment": "':
        return np.array([0.1, 0.1, 0.1, 0.3, 2.0, 0.4, 0.1, 0.5, 0.2])
    return original_logits(generated)

print(generate(constrained=True))
```

Output:

```
{"sentiment": "negative"}
```

The mask kept the shape fixed; the model's own preference picked the label.

</details>

---

## Real-World Examples

- **Document processing** in banks, insurers and hospitals extracts fields from forms, claims and reports into schemas, with business-rule validation and human review for low-confidence records.
- **E-commerce catalogues** turn supplier descriptions into structured product attributes (size, material, colour) using enums that match the site's filters.
- **Support desks** classify and route tickets with a schema of category, urgency and a short evidence quote, which feeds dashboards and queues.
- **Agents** depend on structured output constantly: every tool call is a JSON object that must match the tool's schema, which is why providers added strict modes for tool inputs.

---

## Common Misconceptions

### "Asking for JSON in the prompt is enough"

It works most of the time, which is the dangerous part. At scale, "most of the time" means failures every day. Validate everything, and use constrained decoding where available.

### "Structured outputs mean the data is correct"

They guarantee the **shape**. Values can still be invented or copied from the wrong place. Validate business rules and check values against the source.

### "If the schema is strict, I don't need to handle errors"

Refusals, truncation at `max_tokens`, network failures and unsupported schema features all still happen. Check the stop reason and keep the error handling.

### "Making every field required improves quality"

Required fields with no way to say "not found" push the model to invent values. Allow `null` (or an explicit "unknown") for anything that might be missing.

---

## Interview Relevance

*"How do you get reliable structured output from an LLM?"* A strong answer walks the ladder: clear instructions with the schema and examples; parse and validate with a schema library such as Pydantic; retry with the validation errors; JSON mode for syntax; and schema-constrained decoding (structured outputs or strict tool use) to guarantee the shape. It explains constrained decoding as masking invalid tokens at each step, and stresses that semantic correctness still needs business-rule checks, source grounding and human review for high-stakes fields. Bonus points for schema design: enums, nullable fields, evidence fields before answers, computing totals in code, and checking the stop reason before parsing.

---

## Key Takeaways

- **Programs need structure**: free text breaks parsers, and "almost JSON" is not JSON.
- **A JSON Schema is the contract**; generate it from a Pydantic model and validate every reply against it.
- **Climb the ladder**: prompt, then validate and retry, then JSON mode, then schema-constrained decoding.
- **Constrained decoding masks invalid tokens**, so the shape is guaranteed while the model still chooses the content.
- **Shape is not truth**: validate values with business rules and against the source, and check the stop reason first.
- **Design schemas for the model**: clear names, enums, nullable fields, evidence first, no arithmetic.

---

**Up next:** [Lab: Reliable JSON extraction](lab-reliable-json-extraction.md)
