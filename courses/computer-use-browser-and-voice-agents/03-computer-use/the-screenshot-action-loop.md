---
title: "The Screenshot-Action Loop"
course: "Computer-Use, Browser and Voice Agents"
module: "3. Computer Use"
type: Article
level: Advanced
reading_time: 35 min
---

# The Screenshot-Action Loop: The Complete Guide

> 📚 **Before you start**
>
> - [DOM, Accessibility Tree or Screenshots?](../02-browser-agents/dom-accessibility-tree-or-screenshots.md), for what a screenshot costs and what it shows that structure doesn't.
> - [Driving a Browser with Playwright and MCP](../02-browser-agents/driving-a-browser-with-playwright-and-mcp.md), for toolsets, executors and batch results.
> - [Lab: A browser agent that fills a form](../02-browser-agents/lab-a-browser-agent-that-fills-a-form.md), for the harness pattern of checks before every action.

## Introduction

Think of a relative abroad helping your father over a video call to file his income tax return on an old desktop. They can't touch the keyboard. They see his screen, and they say things like: "Click the blue button at the top right. Now type your PAN in the second box. Press Tab. Wait, the page is loading. Okay, now scroll down." Each instruction is based on what they see right now; after each one they look again.

That is computer use. The model sees **screenshots** of a whole desktop, not a web page's structure, and answers with **mouse and keyboard actions at pixel coordinates**. Your code performs them, takes a new screenshot, and the cycle repeats. Because it works on pixels, it can operate anything a person can: Tally, Excel, a legacy Java billing app, a remote desktop, a game, or a browser.

In this lesson you will learn the loop end to end, read the current computer-use APIs from Anthropic, OpenAI and Google, get coordinate scaling right (the most common bug in every first implementation), and handle batched actions safely.

> 💡 **Key Insight**
>
> In computer use **the model works in the screenshot's coordinate space, and your executor works in the screen's.** Every screenshot you send is resized to fit the model's limits, so every coordinate that comes back must be mapped back before you click. Get the scale wrong and the agent confidently clicks the button next to the one it meant.

---

## Core Explanation

### 1. The loop

![On the left the model looks at a screenshot and writes actions such as left_click at 512, 342, type Chai at 5, key ctrl+s. On the right, inside a VM, the executor maps coordinates back to the screen, checks each action against policy and approval, moves the mouse and presses keys, lets the screen settle, captures the real screen, resizes it to fit the model's limits and sends it back](/img/diagrams/computer-use-browser-and-voice-agents/screenshot-action-loop.svg)
*The model never touches the machine. Everything on the right is your code, running inside an isolated VM.*

Each turn:

1. **Capture** the screen at its real resolution.
2. **Resize** it to fit the model's image limits, and remember the scale factor.
3. **Send** it to the model, with the task and the history.
4. The model replies with one or more **actions**: click here, type this, press that key, scroll, wait, take another screenshot, zoom into a region.
5. **Map** each coordinate back to real screen pixels.
6. **Check** each action against your policy, and ask a human for consequential ones.
7. **Perform** the action with an input tool such as `xdotool` (Linux), PyAutoGUI, or Playwright's mouse and keyboard for a browser window.
8. **Wait** for the screen to settle, then go back to step 1.

The loop ends when the model replies with no actions (it thinks the task is done), when a step or cost limit is reached, or when a human stops it.

Compared with browser agents from Module 2, three things change:

| | Browser agent | Computer-use agent |
|---|---|---|
| Observation | Accessibility tree with refs, screenshots when needed | Screenshots (plus zoom) |
| Action target | A ref the harness maps to an element | A pixel coordinate |
| Scope | One browser | Any app on the desktop, including the browser, file manager and terminal |
| Typical cost per step | Hundreds to a few thousand text tokens | One image per screenshot, often more than a thousand tokens |
| Main failure | Missing or misleading structure | Misreading small text, clicking slightly off target, acting before the screen updates |

### 2. Anthropic's computer use toolset

On the Claude API, computer use is a **client toolset**: one entry in `tools` declares a fixed set of member tools; your application executes every call. The current version is `computer_toolset_20260801`, which needs no beta header. (Older beta versions, `computer_20251124` and `computer_20250124`, remain for some models and platforms; they use a single `computer` tool with an `action` field instead of separate members.)

```python
# not-run: needs the anthropic package, an API key, and an executor connected to a real or virtual screen
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=4096,
    tools=[{"type": "computer_toolset_20260801"}],
    messages=[{"role": "user", "content": "Open the chat app and tell Ravi I'm running 10 minutes late."}],
)
for block in response.content:
    if block.type == "tool_use":
        print(block.toolset_name, block.name, block.input)
```

Example output:

```
computer screenshot {}
```

A sensible first move: the model can't act on a screen it hasn't seen. The member tools in this version:

| Member | Input | What your executor does |
|---|---|---|
| `screenshot` | none | Capture the display and return it as an image |
| `zoom` | `region: [x0, y0, x1, y1]` | Capture that region at full resolution, scaled to the usual screenshot size, to read small text |
| `left_click`, `right_click`, `middle_click`, `double_click`, `triple_click` | `coordinate: [x, y]` (optional), `text` for modifier keys such as `"ctrl+shift"` (optional) | Click at the coordinate, or at the cursor if omitted |
| `left_click_drag` | `start_coordinate`, `coordinate` | Press, drag, release |
| `mouse_move` | `coordinate` | Move without clicking (hover) |
| `left_mouse_down`, `left_mouse_up` | none | Fine-grained drags |
| `cursor_position` | none | Report the cursor position as text |
| `scroll` | `scroll_direction` (`up`, `down`, `left`, `right`), `scroll_amount`, optional `coordinate` | Scroll with the wheel |
| `type` | `text` | Type literal text at the keyboard focus |
| `key` | `text` such as `"Return"`, `"ctrl+s"`, `"alt+Tab"`, optional `repeat` | Press a key or combination |
| `hold_key` | `text`, `duration` (seconds) | Hold keys down |
| `wait` | `duration` (seconds) | Pause while something loads |

The shapes of a turn, which you have already seen for the browser toolset:

- Each call is a `tool_use` block whose `name` is the member and whose `toolset_name` is `"computer"`. The `input` holds only that member's parameters.
- You answer **every** `tool_use` with a `tool_result` that echoes `"toolset_name": "computer"`. Screenshot and zoom results carry an image; other members can return short text such as `"OK"`.
- Claude often sends a **batch**: for example click, type, press Return, screenshot. Run them in order and stop at the first failure; later blocks get an error result with the exact text `Not executed: an earlier computer action in this turn failed.`
- Coordinates are in **screenshot pixels**, origin at the top left. Zoom regions are expressed in the full screenshot's space too.
- The toolset adds roughly 4,500 input tokens to each request, and every screenshot is billed as image input. Two related client tools often sit beside it: the bash tool and the text editor tool, so the agent can use a terminal or edit files directly instead of clicking through a GUI.

### 3. Coordinate scaling: the bug everyone writes once

The API does not resize your screenshots; an image above the model's limits is simply rejected. According to Anthropic's documentation, current models (Opus 4.7 and later, including all models that support the toolset) accept a long edge up to 2576 pixels and up to 4,784 visual tokens, counted as `ceil(w/28) × ceil(h/28)`. Earlier models accept a long edge of 1568 pixels and about 1.15 megapixels. So you pick a scale factor per screen:

```python
import math

LIMITS = {
    "current Claude models": {"long_edge": 2576, "max_tiles": 4784},   # Opus 4.7 and later
    "earlier Claude models": {"long_edge": 1568, "max_pixels": 1_150_000},
}

def fits(w, h, limit):
    if max(w, h) > limit["long_edge"]:
        return False
    if "max_tiles" in limit:
        return math.ceil(w / 28) * math.ceil(h / 28) <= limit["max_tiles"]
    return w * h <= limit["max_pixels"]

def scale_for(screen_w, screen_h, limit):
    """Largest scale (never above 1) whose resized screenshot fits the model's image limits."""
    scale = min(1.0, limit["long_edge"] / max(screen_w, screen_h))
    while not fits(int(screen_w * scale), int(screen_h * scale), limit):
        scale -= 0.001
    return round(scale, 3)

for screen in [(1280, 800), (1920, 1080), (2560, 1600)]:
    for name, limit in LIMITS.items():
        s = scale_for(*screen, limit)
        print(f"{screen[0]}x{screen[1]} for {name:<22} scale {s:<6} -> send {int(screen[0]*s)}x{int(screen[1]*s)}")
```

Output:

```
1280x800 for current Claude models  scale 1.0    -> send 1280x800
1280x800 for earlier Claude models  scale 1.0    -> send 1280x800
1920x1080 for current Claude models  scale 1.0    -> send 1920x1080
1920x1080 for earlier Claude models  scale 0.745  -> send 1430x804
2560x1600 for current Claude models  scale 0.945  -> send 2419x1512
2560x1600 for earlier Claude models  scale 0.529  -> send 1354x846
```

Now the bug. Imagine a 2560 by 1600 screen with Tally open. "Create Voucher" sits just below "Delete Voucher". The model looks at the **resized** screenshot and answers in its coordinates:

```python
# A fake desktop, in real screen pixels: (left, top, right, bottom)
WIDGETS = {
    "Tally: Delete Voucher": (1400, 660, 1700, 730),
    "Tally: Create Voucher": (1400, 740, 1700, 800),
    "Excel: Save":           (300, 120, 420, 180),
}

def what_is_at(x, y):
    for name, (left, top, right, bottom) in WIDGETS.items():
        if left <= x <= right and top <= y <= bottom:
            return name
    return "empty desktop"

SCALE = scale_for(2560, 1600, LIMITS["current Claude models"])

def model_click_for(target):
    """Pretend model: it sees the *resized* screenshot, so it answers in screenshot coordinates."""
    left, top, right, bottom = WIDGETS[target]
    return [round((left + right) / 2 * SCALE), round((top + bottom) / 2 * SCALE)]

def execute_click_buggy(coordinate):
    return what_is_at(*coordinate)                                   # forgot to undo the resize

def execute_click(coordinate):
    x, y = coordinate
    return what_is_at(round(x / SCALE), round(y / SCALE))            # back to real screen pixels

coordinate = model_click_for("Tally: Create Voucher")
print("model says left_click at", coordinate)
print("buggy executor clicked:  ", execute_click_buggy(coordinate))
print("correct executor clicked:", execute_click(coordinate))
```

Output:

```
model says left_click at [1465, 728]
buggy executor clicked:   Tally: Delete Voucher
correct executor clicked: Tally: Create Voucher
```

The buggy executor used the model's numbers as if they were screen pixels and hit the button above the intended one: a *delete*, not a create. The fix is one division, but it must be in every action handler that takes a coordinate (`left_click`, `scroll`, `mouse_move`, `left_click_drag`, `zoom`).

Two more sources of the same bug:

- **High-density displays.** On a Mac Retina screen, the screenshot is in physical pixels but mouse APIs usually work in logical points, a factor of 2 apart. Either capture at the logical size or divide coordinates by the device pixel ratio as well.
- **Multiple monitors.** Capture one display and keep the mouse on it, or the origin shifts.

Anthropic's guidance on resolution: for general desktop work use something like 1024 by 768 or 1280 by 720, for web apps 1280 by 800 or 1366 by 768, and avoid going above 1920 by 1080. Smaller screens mean cheaper screenshots and bigger targets; `zoom` covers the cases where text is too small to read.

### 4. Batches, approvals and the state of the screen

A batch can complete a consequential action in one turn: click the contact, click the message box, type, press **Return**. If you approve "the turn" you miss that **Return** sends the message. The documentation's advice is to check before **each** block runs. And the check must look at the **state of the environment**, because `key Return` is harmless in a search box and consequential in a chat box.

```python
class FakeDesktop:
    """A chat app on a 1280x800 screen. Pressing Return in the message box sends the message."""
    BOXES = {"contact: Ravi": (20, 140, 300, 200), "message box": (340, 720, 1180, 770)}

    def __init__(self):
        self.focus, self.chat, self.draft, self.sent = None, None, "", []

    def element_at(self, x, y):
        for name, (l, t, r, b) in self.BOXES.items():
            if l <= x <= r and t <= y <= b:
                return name
        return None

    def left_click(self, coordinate):
        target = self.element_at(*coordinate)
        if target is None:
            raise RuntimeError(f"nothing clickable at {coordinate}")
        self.focus = target
        if target.startswith("contact: "):
            self.chat = target.split(": ")[1]
        return "OK"

    def type(self, text):
        if self.focus != "message box":
            raise RuntimeError("keyboard focus is not on a text box")
        self.draft += text
        return "OK"

    def key(self, text):
        if text == "Return" and self.focus == "message box":
            self.sent.append((self.chat, self.draft))
            self.draft = ""
        return "OK"

    def screenshot(self):
        # A real executor captures and resizes a PNG. We return a stand-in image block.
        return [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}}]

def is_consequential(block, desktop):
    """Judge from the environment's state, not from the action's name alone."""
    return block["name"] == "key" and block["input"].get("text") == "Return" and desktop.focus == "message box"

def run_computer_batch(blocks, desktop, ask_human):
    results, failed = [], False
    for block in blocks:
        result = {"type": "tool_result", "tool_use_id": block["id"], "toolset_name": "computer"}
        if failed:
            result |= {"is_error": True, "content": "Not executed: an earlier computer action in this turn failed."}
        elif is_consequential(block, desktop) and ask_human(desktop) != "y":
            result |= {"is_error": True, "content": "The user declined this action."}
            failed = True
        else:
            try:
                result["content"] = getattr(desktop, block["name"])(**block["input"])
            except Exception as error:
                result |= {"is_error": True, "content": str(error)}
                failed = True
        results.append(result)
    return results

# One assistant turn, shaped like the computer use toolset's tool_use blocks
turn = [
    {"id": "toolu_01", "name": "left_click", "toolset_name": "computer", "input": {"coordinate": [160, 170]}},
    {"id": "toolu_02", "name": "left_click", "toolset_name": "computer", "input": {"coordinate": [760, 745]}},
    {"id": "toolu_03", "name": "type", "toolset_name": "computer", "input": {"text": "Running 10 minutes late"}},
    {"id": "toolu_04", "name": "key", "toolset_name": "computer", "input": {"text": "Return"}},
    {"id": "toolu_05", "name": "screenshot", "toolset_name": "computer", "input": {}},
]

def ask(desktop):
    print(f'   [approval] Send "{desktop.draft}" to {desktop.chat}? -> y')
    return "y"

desktop = FakeDesktop()
for r in run_computer_batch(turn, desktop, ask_human=ask):
    content = r["content"] if isinstance(r["content"], str) else f'[image block, {r["content"][0]["source"]["media_type"]}]'
    print(r["tool_use_id"], "error" if r.get("is_error") else "ok   ", content)
print("sent:", desktop.sent)
```

Output:

```
   [approval] Send "Running 10 minutes late" to Ravi? -> y
toolu_01 ok    OK
toolu_02 ok    OK
toolu_03 ok    OK
toolu_04 ok    OK
toolu_05 ok    [image block, image/png]
sent: [('Ravi', 'Running 10 minutes late')]
```

The approval prompt appeared while block `toolu_04` was about to run (it prints before the result lines because results are printed at the end). Note what the gate used: the executor's knowledge of **which element has focus** and **what the draft says**. Pure action names would never have caught it.

### 5. OpenAI's computer tool

OpenAI offers computer use through the Responses API. You add `{"type": "computer"}` to `tools`; the model returns `computer_call` items, each with an ordered `actions` array (such as a `click` with `x`, `y` and `button`, then a `type` with `text`) and a `call_id`. You perform the actions and send back a `computer_call_output` carrying a fresh screenshot, chaining turns with `previous_response_id`. The action types are `click`, `double_click`, `drag`, `move`, `scroll`, `keypress`, `type`, `wait` and `screenshot`. Only some OpenAI models support the tool; check the model's page for computer use in its tools list.

```python
# not-run: needs the openai package, an API key, a model whose page lists computer use, and an executor
import base64
from openai import OpenAI

client = OpenAI()
MODEL = "a-model-that-supports-computer-use"

response = client.responses.create(
    model=MODEL,
    tools=[{"type": "computer"}],
    input="Open the chat app and tell Ravi I'm running 10 minutes late.",
)
while True:
    calls = [item for item in response.output if item.type == "computer_call"]
    if not calls:
        break
    call = calls[0]
    for action in call.actions:          # run them in order, with your own policy checks
        perform(action)                  # your executor: click, type, keypress, scroll, ...
    png = capture_screenshot()           # your executor
    response = client.responses.create(
        model=MODEL,
        tools=[{"type": "computer"}],
        previous_response_id=response.id,
        input=[{
            "type": "computer_call_output",
            "call_id": call.call_id,
            "output": {"type": "computer_screenshot",
                       "image_url": "data:image/png;base64," + base64.b64encode(png).decode(),
                       "detail": "original"},
        }],
    )
print(response.output_text)
```

OpenAI's guide also notes that a `computer_call` with status `completed` means the model finished *writing* the call, not that anything happened on screen, and that pending safety checks should stop your program until a human approves. It points to partner environments (Browserbase, Browser Use, Daytona, E2B Desktop) and a sample app with Playwright and PyAutoGUI executors.

### 6. Google's Gemini computer use

The Gemini API offers a computer use tool with an `environment` setting for browser, desktop or mobile. Two design choices differ from the others:

**Normalised coordinates.** The model answers with `x` and `y` from 0 to 999 on a virtual 1000 by 1000 grid, regardless of screen size. Your executor converts them:

```python
def from_normalized(x, y, screen_w, screen_h):
    """Gemini-style coordinates run from 0 to 999 on each axis, whatever the screen size."""
    return round(x / 1000 * screen_w), round(y / 1000 * screen_h)

for screen in [(1440, 900), (1280, 800)]:
    print(screen, "->", from_normalized(500, 500, *screen), from_normalized(999, 0, *screen))
```

Output:

```
(1440, 900) -> (720, 450) (1439, 0)
(1280, 800) -> (640, 400) (1279, 0)
```

This removes the resize bookkeeping, but you must still use the real screen size, including any device pixel ratio.

**Safety decisions on each call.** A function call can carry a `safety_decision` such as `require_confirmation`; your app must ask the user, and only then send the result back with a safety acknowledgement. Built-in actions can be excluded, and you can add your own functions, for example a `yield_to_user` tool that hands control to a person.

### 7. The three APIs side by side

| | Anthropic | OpenAI | Google Gemini |
|---|---|---|---|
| How you enable it | `{"type": "computer_toolset_20260801"}` in Messages API `tools` | `{"type": "computer"}` in Responses API `tools` | Computer use tool with an `environment` (browser, desktop, mobile) |
| What the model returns | One `tool_use` block per action, member name as tool name; batches allowed | `computer_call` with an ordered `actions` array | Function calls for predefined UI actions |
| Coordinates | Screenshot pixels | Screenshot pixels | Normalised 0 to 999 |
| What you return | `tool_result` per block, echoing `toolset_name`; images for screenshot and zoom | `computer_call_output` with a screenshot | Function results with a screenshot |
| Built-in safety signal | Classifiers scan screenshots for prompt injection | Pending safety checks that need human approval | Per-call `safety_decision`, optional injection detection |
| Who executes actions | You | You | You |

The last row is the one that matters most: **in every case, your code moves the mouse**, so your code decides what is allowed.

### 8. Practical tips from real deployments

| Tip | Why |
|---|---|
| Prefer keyboard shortcuts and typing over long click sequences | Fewer coordinates, fewer misses |
| Tell the model to take a screenshot after each meaningful step and check the result | It catches its own mistakes before building on them |
| Add explicit `wait` or settle time after opening apps or pages | Acting on a half-drawn screen is the commonest cause of wrong clicks |
| Keep `zoom` enabled | Small text such as file names and tab titles is where screenshots fail |
| Give a bash or editor tool when the task is really about files | Editing a CSV through a spreadsheet GUI is slow and error-prone |
| Cap steps and cost, and log every screenshot with its actions | Long tasks wander; logs make failures debuggable |

---

## Try It Yourself

1. **Scale for an old laptop.** Compute the scale factor and image size for a 1366 by 768 screen for both model families. Does it need resizing at all?
2. **Retina fix.** A Mac screenshot is 2880 by 1800 physical pixels; mouse coordinates are in points (1440 by 900). The screenshot was resized with scale 0.894 before sending. The model asks to click `[1287, 804]` in screenshot space. Where should the mouse click, in points?
3. **Decline the send.** Rerun the chat batch with a human who answers `"n"`. Which blocks run, and is anything sent?

<details>
<summary>Show answers</summary>

**1.**

```python
for name, limit in LIMITS.items():
    s = scale_for(1366, 768, limit)
    print(name, s, int(1366 * s), int(768 * s))
```

Output:

```
current Claude models 1.0 1366 768
earlier Claude models 1.0 1366 768
```

No resizing is needed: 1366 by 768 fits both limits.

**2.**

```python
scale, device_pixel_ratio = 0.894, 2
x, y = 1287, 804
print(round(x / scale / device_pixel_ratio), round(y / scale / device_pixel_ratio))
```

Output:

```
720 450
```

Undo the resize (back to physical pixels), then divide by the device pixel ratio (to points).

**3.**

```python
desktop = FakeDesktop()
results = run_computer_batch(turn, desktop, ask_human=lambda d: "n")
for r in results:
    print(r["tool_use_id"], "error" if r.get("is_error") else "ok   ", r["content"])
print("sent:", desktop.sent, "| draft still in the box:", repr(desktop.draft))
```

Output:

```
toolu_01 ok    OK
toolu_02 ok    OK
toolu_03 ok    OK
toolu_04 error The user declined this action.
toolu_05 error Not executed: an earlier computer action in this turn failed.
sent: [] | draft still in the box: 'Running 10 minutes late'
```

The first three actions run, the send is declined, and the screenshot is not executed because an earlier action in the turn failed. Nothing is sent; the draft stays in the box for the human to review. On the next turn the model learns from the error result that the user declined.

</details>

---

## Real-World Examples

- **Back-office automation** in finance and logistics teams drives desktop accounting and ERP software that has no API, in virtual machines, with approvals before postings.
- **QA for native apps** uses computer-use agents to click through desktop and mobile builds the way a tester would, logging screenshots for every step.
- **Coding agents** use computer use to look at the running app they built, for example to check that a chart renders correctly, something no test assertion captures well.
- **Accessibility research** uses the same perception models to describe interfaces to people who can't see them.

---

## Common Misconceptions

### "Computer use sends the model a video of the screen"

It sends still screenshots, one per observation, when your executor captures them. Anything that happens between screenshots, such as a toast message that disappears, the model never sees.

### "The model can click precisely anywhere"

Models are good but not pixel-perfect, and small targets on huge screens are hard. Lower resolutions, zoom, keyboard shortcuts and verification screenshots all improve accuracy.

### "If the API accepted my screenshot, coordinates are fine"

The API never checks that you mapped coordinates back. A wrong scale factor produces clicks that land consistently off-target, sometimes on a dangerous neighbour.

### "Computer use is the best way to automate a web app"

For web pages, structure-based browser tools are cheaper and more reliable. Anthropic itself recommends its browser use tool for webpage-only tasks. Use computer use when the task spans desktop apps or the page is visual.

---

## Interview Relevance

*"Walk me through how a computer-use agent works."* A strong answer describes the loop (capture, resize, send, receive actions, map coordinates, check policy, execute, settle, repeat), names the action set (clicks, drags, typing, keys, scroll, wait, screenshot, zoom), explains batching with stop-at-first-failure, and shows coordinate scaling with a formula, including device pixel ratio. It compares Anthropic's toolset (screenshot-pixel coordinates, `tool_use` per action), OpenAI's `computer_call` with action arrays, and Gemini's normalised 0 to 999 coordinates with per-call safety decisions. It ends with safety: your executor performs every action, so approvals are checked per action using the environment's state, and the whole thing runs in an isolated VM (the next lesson).

---

## Key Takeaways

- **The loop is screenshot in, actions out**, with your executor doing everything on the machine.
- **Scale coordinates back** from screenshot space to screen pixels in every handler, and mind Retina ratios.
- **Batches need per-action checks**, judged from the environment's state, not the action's name.
- **The three big APIs differ in shape, not in principle**: Anthropic's toolset, OpenAI's `computer_call`, Gemini's normalised coordinates.
- **Prefer structure when you can**: browser tools for web pages, shell and editor tools for files, computer use for everything else.

---

**Up next:** [Running Desktop Agents Safely in VMs](running-desktop-agents-safely-in-vms.md)
