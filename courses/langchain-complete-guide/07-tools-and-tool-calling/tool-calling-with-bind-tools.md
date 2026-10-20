---
title: "Tool Calling with bind_tools"
course: LangChain Complete Guide
module: "7. Tools and Tool Calling"
type: Article
level: Intermediate
reading_time: 32 min
---

# Tool Calling with bind_tools

> 📚 **Before you start**
>
> - [Custom Tools: @tool, StructuredTool and BaseTool](custom-tools-tool-structuredtool-and-basetool.md), for building tools.
> - [Chat Models](../03-models/chat-models.md), for `AIMessage`, `tool_calls` and message lists.
> - [Why Structured Output Matters](../05-structured-output-and-output-parsers/why-structured-output-matters.md), where you saw that structured output uses tool calling underneath.

## Introduction

Think of a hotel concierge in Delhi. A guest asks "Should I go to India Gate this evening?". The concierge doesn't know the answer offhand, so they check the weather app and the air-quality index, then reply: "It'll be 31°C and clear, but the AQI is 285, which is poor. Go after 7 pm with a mask, or try the Delhi Metro Museum instead." The concierge decided **which** apps to check, **looked**, and **answered** using what they found.

Tool calling gives a chat model the same ability. You attach tools to the model with **`bind_tools`**. The model decides whether a tool would help and replies with **tool calls** (which tool, which arguments). Your code runs them and sends the results back as **`ToolMessage`s**, and the model writes the answer. That request, run, return, answer cycle is the **tool-calling loop**, and it's the heart of every agent.

This lesson builds the loop by hand, one message at a time, then as a reusable function. You'll also see parallel tool calls, forcing a tool with `tool_choice`, what goes wrong and how to guard against it, and how `create_agent` and LangGraph automate the same loop.

> 💡 **Key Insight**
>
> Tool calling is a **conversation protocol**: `HumanMessage` → `AIMessage` with `tool_calls` → one `ToolMessage` per call (matched by `tool_call_id`) → `AIMessage` with the answer. The model never executes anything. Your loop does, which is exactly where you add validation, limits, logging and human approval.

---

## Core Explanation

### 1. The tools and a stand-in model

Two tools for the concierge:

```python
from langchain_core.tools import tool

WEATHER = {"delhi": "31°C, clear", "bengaluru": "24°C, light drizzle", "mumbai": "29°C, humid, cloudy"}
AQI = {"delhi": 285, "bengaluru": 62, "mumbai": 118}

@tool
def get_weather(city: str) -> str:
    """Get the current weather for an Indian city."""
    return WEATHER.get(city.lower(), f"No weather data for {city}.")

@tool
def get_aqi(city: str) -> str:
    """Get the current air quality index (AQI) for an Indian city. Above 200 is poor."""
    value = AQI.get(city.lower())
    return f"AQI {value}" if value is not None else f"No AQI data for {city}."

tools = [get_weather, get_aqi]
tools_by_name = {t.name: t for t in tools}
print(list(tools_by_name))
```

Output:

```
['get_weather', 'get_aqi']
```

To run the loop offline we need a model that behaves like a tool-calling model: it receives the tool schemas from `bind_tools`, requests tools whose keywords appear in the question, and once it has tool results, writes an answer from them. A real model makes these decisions far more cleverly; the protocol is identical:

```python
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool

class ConciergeModel(BaseChatModel):
    """Offline stand-in for a tool-calling chat model."""
    @property
    def _llm_type(self):
        return "concierge"

    def bind_tools(self, tools, tool_choice=None, **kwargs):
        schemas = [convert_to_openai_tool(t) for t in tools]
        return self.bind(tools=schemas, tool_choice=tool_choice, **kwargs)

    def _generate(self, messages, stop=None, run_manager=None, tools=None, tool_choice=None, **kwargs):
        last = messages[-1]
        if isinstance(last, ToolMessage):                       # results are in: answer
            results = [m.content for m in messages if isinstance(m, ToolMessage)]
            reply = AIMessage(content="Here's what I found: " + "; ".join(results) + ".")
        else:
            available = {s["function"]["name"] for s in tools or []}
            q = last.content.lower()
            city = next((c for c in WEATHER if c in q), "delhi")
            wanted = [n for n, words in {"get_weather": ["weather", "rain", "hot", "go "], "get_aqi": ["aqi", "air", "pollution", "go "]}.items()
                      if n in available and any(w in q for w in words)]
            if tool_choice not in (None, "auto", "any") and tool_choice in available:
                wanted = [tool_choice]
            elif tool_choice == "any" and not wanted and available:
                wanted = [sorted(available)[0]]
            calls = [{"name": n, "args": {"city": city.title()}, "id": f"call_{i}"} for i, n in enumerate(wanted)]
            reply = AIMessage(content="" if calls else "Happy to help with your Delhi plans!", tool_calls=calls)
        return ChatResult(generations=[ChatGeneration(message=reply)])

model = ConciergeModel()
```

### 2. `bind_tools`: give the model its tools

`bind_tools` converts each tool to the provider's schema format and attaches the schemas to every request the model makes. It returns a new runnable; the original model is unchanged:

```python
from langchain_core.runnables import RunnableBinding

model_with_tools = model.bind_tools(tools)
print(isinstance(model_with_tools, RunnableBinding), type(model_with_tools).__name__)
print([s["function"]["name"] for s in model_with_tools.kwargs["tools"]])
```

Output:

```
True _ChatModelBinding
['get_weather', 'get_aqi']
```

It's a `RunnableBinding` (chat models use a small subclass of it): the model plus fixed extra arguments, the `.bind()` you met in module 6. With a real provider it looks the same:

```python
# not-run: needs `pip install langchain langchain-anthropic` and ANTHROPIC_API_KEY
from langchain.chat_models import init_chat_model

llm = init_chat_model("anthropic:claude-opus-5-5", temperature=0)
llm_with_tools = llm.bind_tools([get_weather, get_aqi])
```

`bind_tools` accepts LangChain tools, Pydantic models, TypedDicts, plain functions and raw JSON schema dicts, converting each one.

### 3. Step 1: the model asks for tools

```python
from langchain_core.messages import HumanMessage

messages = [HumanMessage("Should I go to India Gate in Delhi this evening?")]
ai_msg = model_with_tools.invoke(messages)
print("content:", repr(ai_msg.content))
for call in ai_msg.tool_calls:
    print(call)
```

Output:

```
content: ''
{'name': 'get_weather', 'args': {'city': 'Delhi'}, 'id': 'call_0', 'type': 'tool_call'}
{'name': 'get_aqi', 'args': {'city': 'Delhi'}, 'id': 'call_1', 'type': 'tool_call'}
```

The reply has **empty content** and two **tool calls**. Each tool call is a dict:

| Key | Meaning |
|---|---|
| `name` | Which tool to run |
| `args` | Arguments as a dict, already parsed from the model's JSON |
| `id` | A unique id; the result must carry the same id |
| `type` | Always `"tool_call"` |

Real models sometimes also include text ("Let me check the weather and air quality."). Your code should look at `tool_calls`, not at whether `content` is empty. If the model produced arguments that couldn't be parsed as JSON, they appear in `ai_msg.invalid_tool_calls` instead, with an error message.

The model asked for **two** tools at once. That's a **parallel tool call**: the calls don't depend on each other, so you can run them together.

### 4. Step 2: run the tools

Find each tool by name and invoke it **with the whole tool call**. That returns a `ToolMessage` with the matching `tool_call_id`:

```python
messages.append(ai_msg)
for call in ai_msg.tool_calls:
    tool_msg = tools_by_name[call["name"]].invoke(call)
    print(repr(tool_msg))
    messages.append(tool_msg)
```

Output:

```
ToolMessage(content='31°C, clear', name='get_weather', tool_call_id='call_0')
ToolMessage(content='AQI 285', name='get_aqi', tool_call_id='call_1')
```

### 5. Step 3: send the results back

The model now gets the whole conversation: the question, its own tool request, and the results:

```python
final = model_with_tools.invoke(messages)
print([type(m).__name__ for m in messages])
print(final.content)
print("more tool calls?", bool(final.tool_calls))
```

Output:

```
['HumanMessage', 'AIMessage', 'ToolMessage', 'ToolMessage']
Here's what I found: 31°C, clear; AQI 285.
more tool calls? False
```

No more tool calls, so this is the answer. (A real model would write something closer to the concierge's advice; the stand-in just lists the facts.)

Message order matters. Providers check that every tool call in an `AIMessage` is followed by a `ToolMessage` with the same id before the next model turn. Dropping one, or sending a `ToolMessage` without the `AIMessage` that requested it, makes the provider reject the request.

### 6. The loop as a function

Real questions can need several rounds (look something up, then use the result to look up something else). Wrap the steps in a loop with a safety limit:

```python
def run_with_tools(question, model, tools, max_rounds=5, verbose=True):
    lookup = {t.name: t for t in tools}
    bound = model.bind_tools(tools)
    messages = [HumanMessage(question)]
    for round_no in range(1, max_rounds + 1):
        ai = bound.invoke(messages)
        messages.append(ai)
        if not ai.tool_calls:                          # the model answered
            return ai.content, messages
        for call in ai.tool_calls:
            if verbose:
                print(f"  round {round_no}: {call['name']}({call['args']})")
            tool = lookup.get(call["name"])
            if tool is None:                           # the model invented a tool
                messages.append(ToolMessage(f"Unknown tool {call['name']}", tool_call_id=call["id"], status="error"))
            else:
                messages.append(tool.invoke(call))
    return "Stopped: too many tool rounds.", messages

answer, history = run_with_tools("How is the air in Bengaluru today?", model, tools)
print(answer)
print(len(history), "messages")
```

Output:

```
  round 1: get_aqi({'city': 'Bengaluru'})
Here's what I found: AQI 62.
4 messages
```

Every agent framework contains a loop like this. Notice the guards, all of which matter with real models:

- **`max_rounds`** stops a model that keeps calling tools forever.
- **Unknown tool names** get an error `ToolMessage` instead of a crash.
- **Each call keeps its id**, so the protocol stays valid.

In production you'd also catch tool exceptions (or use `handle_tool_error`, from the last lesson), log every call, and require approval before risky tools.

Questions that need no tool skip the loop entirely:

```python
answer, history = run_with_tools("Thanks, that's all!", model, tools)
print(answer, "|", len(history), "messages")
```

Output:

```
Happy to help with your Delhi plans! | 2 messages
```

### 7. `tool_choice`: let the model decide, or force it

By default the model chooses whether to call a tool (`"auto"`). You can force it:

| `tool_choice` | Effect |
|---|---|
| `"auto"` (default) | The model may answer directly or call tools |
| `"any"` | The model must call at least one tool |
| `"get_aqi"` (a tool name) | The model must call that tool |

```python
forced = model.bind_tools(tools, tool_choice="get_aqi")
print(forced.invoke([HumanMessage("Tell me about Mumbai")]).tool_calls)
```

Output:

```
[{'name': 'get_aqi', 'args': {'city': 'Mumbai'}, 'id': 'call_0', 'type': 'tool_call'}]
```

Forcing a tool is how `with_structured_output` works on the tool-calling route: the schema is bound as a tool and the model is forced to call it, so the "tool call" is your structured data. Use `"any"` or a name when a tool call is the only acceptable response, for example a classifier step.

Most providers also accept `parallel_tool_calls=False` in `bind_tools` to make the model request one tool at a time, useful when tools have side effects that must happen in order.

### 8. Streaming tool calls

When you stream a tool-calling model, tool calls arrive in pieces as `tool_call_chunks` on each `AIMessageChunk` (the name first, then the arguments JSON a few characters at a time). Adding chunks together with `+`, as you did for text in [Chat Models](../03-models/chat-models.md), assembles complete `tool_calls`. UIs use this to show "Checking the weather..." as soon as the tool name arrives.

### 9. From your loop to agents

You've now built the core of an agent by hand. LangChain 1.x packages this loop as **`create_agent`**: give it a model, tools and a system prompt, and it runs the loop (with tool error handling, `return_direct`, memory via a checkpointer, and middleware for things like summarisation or human approval):

```python
# not-run: needs `pip install langchain langchain-anthropic` and ANTHROPIC_API_KEY
from langchain.agents import create_agent

agent = create_agent(
    model="anthropic:claude-opus-5-5",
    tools=[get_weather, get_aqi],
    system_prompt="You are a helpful Delhi hotel concierge. Check weather and air quality before advising outings.",
)
result = agent.invoke({"messages": [{"role": "user", "content": "Should I go to India Gate this evening?"}]})
print(result["messages"][-1].text)
```

Example output:

```
It's a clear 31°C evening, but Delhi's AQI is 285, which is in the poor range. If you go, wear an N95 mask and keep the visit short, ideally after 7 pm. If anyone in your group has asthma, consider an indoor option like the National Museum instead.
```

`create_agent` is built on LangGraph, and its result contains the full message list you built manually above. The [LangGraph course](../../langgraph-complete-guide/course.md) builds this loop as an explicit graph (a model node, a `ToolNode` and a conditional edge), which gives you control over every step: pausing for approval, routing between tools, and persisting the conversation.

---

## Try It Yourself

1. **Trace the messages.** Run `run_with_tools("Weather and AQI in Mumbai?", model, tools, verbose=False)` and print the type of every message in the history along with, for tool messages, the `tool_call_id`.
2. **Add a tool.** Write a `@tool get_metro_status(line: str) -> str` that returns `"Running normally"`. Bind three tools to the stand-in model. Does it ever call the new tool? Why not, and what would make a real model call it?
3. **Guard the loop.** Make a model that always calls `get_weather` (bind with `tool_choice="get_weather"`, and never let it answer). What does `run_with_tools` return with `max_rounds=3`? (Hint: write a subclass whose `bind_tools` ignores the `tool_choice` you pass and always forces `get_weather`.)

<details>
<summary>Show answers</summary>

**1.**

```python
_, hist = run_with_tools("Weather and AQI in Mumbai?", model, tools, verbose=False)
for m in hist:
    print(f'{type(m).__name__} {getattr(m, "tool_call_id", "")}'.strip())
```

Output:

```
HumanMessage
AIMessage
ToolMessage call_0
ToolMessage call_1
AIMessage
```

**2.**

```python
@tool
def get_metro_status(line: str) -> str:
    """Get the current service status of a Delhi Metro line, e.g. Yellow Line."""
    return "Running normally"

ans, _ = run_with_tools("Is the Yellow Line metro running in Delhi?", model, [get_weather, get_aqi, get_metro_status], verbose=True)
print(ans)
```

Output:

```
Happy to help with your Delhi plans!
```

The stand-in only knows keyword rules for weather and AQI, so it never picks the metro tool. A real model reads every tool's description and would call `get_metro_status` for this question. That's why descriptions matter.

**3.**

```python
class StubbornModel(ConciergeModel):
    def bind_tools(self, tools, tool_choice=None, **kwargs):
        return super().bind_tools(tools, tool_choice="get_weather", **kwargs)

    def _generate(self, messages, stop=None, run_manager=None, tools=None, tool_choice=None, **kwargs):
        call = {"name": "get_weather", "args": {"city": "Delhi"}, "id": f"call_{len(messages)}"}
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="", tool_calls=[call]))])

ans, hist = run_with_tools("Weather?", StubbornModel(), tools, max_rounds=3, verbose=False)
print(ans, "|", len(hist), "messages")
```

Output:

```
Stopped: too many tool rounds. | 7 messages
```

Without `max_rounds`, this would loop until you ran out of money or patience.

</details>

---

## Real-World Examples

- **Travel and hospitality assistants** call weather, AQI, traffic and booking tools in parallel and combine the results into one recommendation.
- **Fintech support bots** call account tools (balance, recent transactions) with the user id set by the app, then explain the result in plain language.
- **Classifier steps** bind a single schema with `tool_choice` forced, which is how `with_structured_output` works on many providers.
- **Production agents** wrap the loop with logging of every tool call and argument, so a wrong answer can be traced to the tool result that caused it.

---

## Common Misconceptions

### "bind_tools makes the model run my functions"

It only sends schemas. The model returns requests; your code or an agent runs the tools.

### "An empty `content` means something went wrong"

A tool-calling reply often has empty content. Check `tool_calls`.

### "One question means one tool call"

Models may request several tools at once (parallel) or across several rounds. Your loop must handle both.

### "I can drop tool messages from history to save tokens"

Every tool call must be followed by its `ToolMessage` before the next model turn, or the provider rejects the request. Trim whole rounds, never half of one.

---

## Interview Relevance

*"Walk me through tool calling in LangChain."* A strong answer: define tools; `model.bind_tools(tools)` attaches their JSON schemas to requests (returning a `RunnableBinding`); the model replies with an `AIMessage` whose `tool_calls` list has `name`, `args`, `id`; your code runs each with `tool.invoke(tool_call)`, which returns a `ToolMessage` with the same `tool_call_id`; append the AI message and all tool messages and call the model again; repeat until there are no tool calls. Mention parallel calls, `tool_choice` (`auto`, `any`, a tool name) and `parallel_tool_calls=False`, `invalid_tool_calls`, streaming `tool_call_chunks`, loop guards (max rounds, unknown tools, error messages), and that `create_agent` and LangGraph's `ToolNode` automate this loop.

---

## Key Takeaways

- **`bind_tools`** attaches tool schemas to every request; the model only *requests* calls.
- **`AIMessage.tool_calls`** holds `name`, `args`, `id`; invoking a tool with a call returns a matching `ToolMessage`.
- **The loop**: model → tool calls → tool messages → model, until no tool calls remain.
- **Guard the loop**: max rounds, unknown tools, error messages, logging, approval for risky actions.
- **`tool_choice`** forces tools; it's how structured output works underneath.
- **`create_agent` and LangGraph** automate the same loop.

![The tool-calling loop. Define: a Python function becomes a tool schema, and bind_tools sends the schemas with every request. Call: a HumanMessage goes to the model, which answers directly or requests tools in AIMessage.tool_calls; your code runs the tool and returns a ToolMessage with the matching tool_call_id to the model. Answer: when no more tools are needed, a final grounded AIMessage.](/img/diagrams/langchain-complete-guide/tool-calling-loop.svg)

---

**Up next:** [Injected Tool Arguments](injected-tool-arguments.md)
