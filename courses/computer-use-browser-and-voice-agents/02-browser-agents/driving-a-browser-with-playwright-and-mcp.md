---
title: "Driving a Browser with Playwright and MCP"
course: "Computer-Use, Browser and Voice Agents"
module: "2. Browser Agents"
type: Article
level: Advanced
reading_time: 35 min
---

# Driving a Browser with Playwright and MCP: The Complete Guide

> 📚 **Before you start**
>
> - [DOM, Accessibility Tree or Screenshots?](dom-accessibility-tree-or-screenshots.md), for accessibility snapshots and element references.
> - [What is MCP?](../../model-context-protocol-mcp/course.md#m2), [Hosts, Clients and Servers](../../model-context-protocol-mcp/course.md#m2) and [The Data Layer: JSON-RPC Messages](../../model-context-protocol-mcp/course.md#m3), because one way to give an agent a browser is an MCP server.
> - [Function Calling Step by Step](../../agentic-ai-fundamentals/04-tools-and-function-calling/function-calling-step-by-step.md), for `tool_use` and `tool_result` blocks.

## Introduction

When a cricket broadcaster shows Hawk-Eye, nobody is drawing the ball's path by hand. Cameras capture the ball, software tracks it, and the umpire only asks one question: "Was it hitting the stumps?" There is a clean split between **the machinery that sees and moves** and **the person who decides**.

A browser agent needs the same split. The model decides ("add Amul Butter to the cart"); something else must actually open Chromium, find the right button, click it, wait for the cart to update and report back. That machinery is almost always **Playwright**, Microsoft's open-source browser automation library. In this lesson you will:

- Drive a real Chromium with Playwright from Python: open a page, read its accessibility snapshot, fill, click and wait.
- Give that browser to an agent in the three ways used today: the **Playwright MCP server**, **Anthropic's browser use toolset** backed by your own executor, and **your own function tools**.
- Put the first safety checks into the harness, starting with where the browser is allowed to go.

> 💡 **Key Insight**
>
> Playwright is the hands; the model is the brain; **your harness sits between them**. Whether the tools arrive over MCP or as a toolset in the API request, every click passes through code you control, which is where you enforce allowlists, approvals and step limits.

---

## Core Explanation

### 1. Playwright in five ideas

Playwright controls Chromium, Firefox and WebKit through each browser's automation protocol. It has official libraries for Python, Node.js, Java and .NET. Five ideas cover most of what an agent needs:

| Idea | What it means | Why agents care |
|---|---|---|
| **Browser → context → page** | A *browser* process holds *contexts*; each context is like a fresh incognito profile with its own cookies and storage; each context holds *pages* (tabs) | One isolated context per agent task keeps sessions apart and leaves no personal cookies around |
| **Headless or headed** | Headless runs with no visible window; headed shows the window | Headless for servers and CI; headed when a human wants to watch or take over |
| **Locators** | A recipe for finding an element, re-evaluated every time it's used: `get_by_role("button", name="Add")`, `get_by_label("Search")`, `get_by_text(...)` | Role and name locators match the accessibility tree the model reads |
| **Auto-waiting** | Before clicking, Playwright waits until the element is attached, visible, stable, enabled and able to receive the click | Removes most "clicked too early" flakiness |
| **Web-first assertions** | `expect(locator).to_have_text(...)` retries until the condition holds or a timeout passes | The harness can verify that an action really worked |

### 2. A first script against a local page

We'll use an interactive version of the Sharma Kirana Store page, served from your own machine. Typing in the search box filters the list; clicking **Add** updates the cart after a deliberate 400 ms delay, like a slow server. The relevant HTML:

```html
<label>Search groceries <input type="search" id="q"></label>
<ul id="items">
  <li data-name="Amul Butter 100 g">Amul Butter 100 g, ₹58
    <button aria-label="Add Amul Butter 100 g">Add</button></li>
  ...
</ul>
<p id="status" role="status"></p>
```

Notice that each button now has an `aria-label` that names the product, fixing the "three identical Add buttons" trap from the previous lesson. To serve the folder: `python -m http.server 8765`.

```python
# not-run: needs `pip install playwright` and `playwright install chromium`
import re
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.goto("http://127.0.0.1:8765/kirana.html")
    print("title:", page.title())

    page.get_by_label("Search groceries").fill("butter")
    print(page.get_by_role("list").aria_snapshot())

    page.get_by_role("button", name="Add Amul Butter 100 g").click()
    cart = page.get_by_role("link", name=re.compile("Cart"))
    print("cart right after click:", cart.text_content())

    expect(page.get_by_role("status")).to_have_text("Amul Butter 100 g added")
    print("cart after waiting:", cart.text_content())
    browser.close()
```

Example output:

```
title: Sharma Kirana Store
- list:
  - listitem:
    - text: Amul Butter 100 g, ₹58
    - button "Add Amul Butter 100 g": Add
cart right after click: Cart (0)
cart after waiting: Cart (1)
```

Three things in that output matter for agents:

1. **The snapshot reflects the live page.** After filtering, only one list item remains, because hidden elements leave the accessibility tree.
2. **A click is not a result.** Right after the click the cart still says `Cart (0)`. If an agent observed the page immediately, it would think the click failed and might click again, adding two packets of butter. Waiting for evidence (`to_have_text`) and only then observing is a habit your harness must have.
3. **Locators by role and name** are exactly what the model sees in the snapshot, so translating a model's choice into a Playwright action is direct.

### 3. Three ways to hand the browser to an agent

![A layered diagram: the model at the top proposes an action; the harness layer holds the agent loop, a policy and approval gate, and a secret store; below, two options for browser tools, the Playwright MCP server or your own executor for Anthropic's browser toolset; at the bottom, an isolated Chromium context talking HTTP to the website, whose text is untrusted](/img/diagrams/computer-use-browser-and-voice-agents/browser-agent-stack.svg)
*Every route to the browser passes through your harness. The website at the bottom is untrusted input.*

| Route | Who defines the tools | Who runs Playwright | Best for |
|---|---|---|---|
| **Playwright MCP server** | Microsoft's server (`browser_navigate`, `browser_snapshot`, `browser_click` and more) | The MCP server process | Any MCP host: Claude Code, Codex, Cursor, Claude Desktop, your own MCP client |
| **Anthropic browser use toolset** (`browser_toolset_20260801`) | Anthropic fixes the member tools and their schemas | Your executor | Apps built directly on the Claude Messages API |
| **Your own function tools** | You | Your code | Narrow, high-volume tasks where you want only three or four tools |

The rest of the lesson shows each one, with the shared harness checks at the end.

### 4. Route A: the Playwright MCP server

The Playwright MCP server wraps Playwright behind the Model Context Protocol. Your MCP host starts it as a subprocess over stdio. The standard client configuration is:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless", "--isolated"]
    }
  }
}
```

In Claude Code the one-liner is `claude mcp add playwright npx @playwright/mcp@latest`. `--isolated` keeps the browser profile in memory so nothing is saved to disk between sessions.

Here is what an agent actually exchanges with the server. These are real results from version 0.0.83 driving the kirana page in headless Chromium. First the agent calls `browser_snapshot`:

```json
{"jsonrpc": "2.0", "id": 4, "method": "tools/call",
 "params": {"name": "browser_snapshot", "arguments": {}}}
```

Example output:

```
### Page
- Page URL: http://127.0.0.1:8765/kirana.html
- Page Title: Sharma Kirana Store
### Snapshot
- generic [active] [ref=e1]:
  - heading "Sharma Kirana Store" [level=1] [ref=e2]
  - link "Cart (0)" [ref=e3] [cursor=pointer]:
    - /url: "#cart"
  - generic [ref=e4]:
    - text: Search groceries
    - searchbox "Search groceries" [ref=e5]
  - list [ref=e6]:
    - listitem [ref=e7]:
      - text: Tata Tea Gold 500 g, ₹285
      - button "Add Tata Tea Gold 500 g" [ref=e8]: Add
    - listitem [ref=e9]:
      - text: Aashirvaad Atta 5 kg, ₹245
      - button "Add Aashirvaad Atta 5 kg" [ref=e10]: Add
    - listitem [ref=e11]:
      - text: Amul Butter 100 g, ₹58
      - button "Add Amul Butter 100 g" [ref=e12]: Add
  - status
```

It's the same accessibility snapshot you met in the last lesson, with `[ref=eN]` tags added by the server. The model picks a ref and calls `browser_click`:

```json
{"name": "browser_click",
 "arguments": {"element": "Add button for Amul Butter", "target": "e12"}}
```

Example output:

```
### Ran Playwright code
await page.getByRole('button', { name: 'Add Amul Butter 100 g' }).click();
### Page
- Page URL: http://127.0.0.1:8765/kirana.html
- Page Title: Sharma Kirana Store
### Snapshot
- [Snapshot](.playwright-mcp/page-2026-10-18T03-31-45-693Z.yml)
```

Look at three design choices in these results:

- **`target` is required, `element` is a human-readable description.** The server's schema says `element` is used "to obtain permission to interact with the element", so a host can show a person *"Click: Add button for Amul Butter?"* rather than *"Click e12?"*.
- **The server shows the Playwright code it ran**, translated from the ref into a role-and-name locator. That is useful for debugging and for turning an exploratory session into a repeatable test.
- **Big snapshots go to files.** After a click, the new snapshot was written to a `.yml` file and only its path returned, instead of flooding the context window. This is the "return just enough" principle from the context engineering course, built into the server.

The server offers about two dozen tools in this version. The ones agents use most:

| Tool | Purpose |
|---|---|
| `browser_navigate`, `browser_navigate_back` | Go to a URL, or back |
| `browser_snapshot` | Accessibility snapshot with refs |
| `browser_click`, `browser_type`, `browser_fill_form`, `browser_select_option`, `browser_hover`, `browser_press_key` | Act on elements by ref |
| `browser_wait_for` | Wait for text to appear or disappear, or for a time |
| `browser_take_screenshot` | An image of the page or an element |
| `browser_tabs` | List, open, switch and close tabs |
| `browser_console_messages`, `browser_network_requests` | Debugging views of the page |
| `browser_evaluate` | Run JavaScript in the page (powerful, so treat it as dangerous) |

Useful command-line options include `--headless`, `--isolated`, `--storage-state` (load saved cookies into an isolated context), `--allowed-origins` and `--blocked-origins`, `--caps=vision` (adds coordinate-based mouse tools for screenshot-driven use), `--secrets` (a dotenv file of secrets, covered in [Logins, Flaky Pages and Safety](logins-flaky-pages-and-safety.md)) and `--port` to serve over HTTP instead of stdio.

Two warnings straight from the project. Its documentation says plainly that Playwright MCP **is not a security boundary**, and its own help text says the origin allow and block lists don't serve as one either and don't affect redirects. Treat them as guard rails for a cooperative agent, and put real isolation around the browser (Module 3 covers that). For coding agents that only need a few browser checks, the project also offers a **Playwright CLI** that an agent calls through its shell; it avoids loading two dozen tool schemas and large snapshots into context.

### 5. Route B: Anthropic's browser use toolset

If you build directly on the Claude Messages API, Anthropic provides a **client toolset**: one entry in `tools` that declares a fixed set of browser member tools. Anthropic defines their names and schemas; **your application executes every call** against its own browser automation, for example Playwright.

```python
# not-run: needs the anthropic package, an API key and a browser executor
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=2048,
    tools=[{"type": "browser_toolset_20260801"}],
    messages=[{"role": "user", "content": "Open http://127.0.0.1:8765/kirana.html and add Amul Butter to the cart."}],
)
for block in response.content:
    if block.type == "tool_use":
        print(block.toolset_name, block.name, block.input)
```

Example output:

```
browser navigate {'url': 'http://127.0.0.1:8765/kirana.html'}
```

The shapes to know:

- Each call is a `tool_use` block whose `name` is the member (such as `navigate`, `read_page`, `left_click`, `type`, `form_input`, `screenshot`) and whose `toolset_name` is `"browser"`. Dispatch on both, because the computer use toolset in Module 3 shares member names like `screenshot`.
- `read_page` returns the accessibility tree as text with reference tags like `button "Search" [ref_4]`. Claude points at an element with a target such as `{"type": "ref", "ref": "ref_4"}` or, for pixel actions, `{"type": "coordinate", "x": 640, "y": 210}`.
- Your executor assigns the refs and keeps the ref-to-element map. When a ref goes stale after navigation, return an error telling Claude to read the page again.
- Every result echoes `"toolset_name": "browser"`. When Claude sends several calls in one turn (a **batch**), run them in order, stop at the first failure, and answer each later call with an error result whose text is exactly `Not executed: an earlier action in this turn failed.`
- Risky members are **off by default**: `javascript_exec`, `file_upload`, `read_console` and `read_network`. You enable one through the entry's `configs`, for example `{"type": "browser_toolset_20260801", "configs": {"file_upload": {"enabled": True}}}`.

Here is the dispatch-and-batch logic of an executor, run against a small fake page so you can see the exact results it sends back. A real executor would call Playwright inside each handler.

```python
FAKE_REFS = {"ref_1": 'searchbox "Search groceries"', "ref_2": 'button "Add Amul Butter 100 g"'}

def run_member(name, tool_input):
    """Pretend executor: returns result text, or raises an error the model should see."""
    if name == "navigate":
        return f"Navigated to {tool_input['url']}"
    if name == "read_page":
        return "\n".join(f"{desc} [{ref}]" for ref, desc in FAKE_REFS.items())
    if name == "left_click":
        ref = tool_input["target"]["ref"]
        if ref not in FAKE_REFS:
            raise LookupError(f"Error: {ref} is stale or not found on the current page. "
                              "Re-read the page to get fresh references.")
        return f"Clicked {FAKE_REFS[ref]}"
    raise ValueError(f"Unknown or unimplemented member: {name}")

def run_batch(tool_uses):
    """Run browser calls in order; after the first failure, answer the rest as not executed."""
    results, failed = [], False
    for call in tool_uses:
        result = {"type": "tool_result", "tool_use_id": call["id"], "toolset_name": "browser"}
        if failed:
            result |= {"is_error": True, "content": "Not executed: an earlier action in this turn failed."}
        else:
            try:
                result["content"] = run_member(call["name"], call["input"])
            except Exception as error:
                result |= {"is_error": True, "content": str(error)}
                failed = True
        results.append(result)
    return results

batch = [
    {"id": "toolu_1", "name": "left_click", "input": {"target": {"type": "ref", "ref": "ref_9"}}},
    {"id": "toolu_2", "name": "left_click", "input": {"target": {"type": "ref", "ref": "ref_2"}}},
]
for r in run_batch(batch):
    print(r["tool_use_id"], "error" if r.get("is_error") else "ok", "|", r["content"])
```

Output:

```
toolu_1 error | Error: ref_9 is stale or not found on the current page. Re-read the page to get fresh references.
toolu_2 error | Not executed: an earlier action in this turn failed.
```

The second click was never attempted. That is deliberate: if the first click failed, the page is not in the state the model planned for, and blindly continuing could click something else entirely.

### 6. Route C: your own small set of tools

For a narrow job, such as an agent that only fills one kind of form, three or four custom tools can beat a 30-member toolset: fewer tokens per request, fewer wrong choices. A typical minimal set, written as Claude tool definitions:

```json
[
  {"name": "read_page", "description": "Return the page's accessibility snapshot with refs like [e5]. Call after every action.",
   "input_schema": {"type": "object", "properties": {}}},
  {"name": "fill", "description": "Type text into the textbox with this ref, replacing what is there.",
   "input_schema": {"type": "object", "properties": {"ref": {"type": "string"}, "text": {"type": "string"}},
                    "required": ["ref", "text"]}},
  {"name": "click", "description": "Click the element with this ref. Submitting or paying needs human approval.",
   "input_schema": {"type": "object", "properties": {"ref": {"type": "string"}}, "required": ["ref"]}}
]
```

You'll build exactly this in [Lab: A browser agent that fills a form](lab-a-browser-agent-that-fills-a-form.md).

### 7. The harness checks every route needs

Whichever route you choose, some checks belong in your code, not in the prompt. The first is **where the browser may go**. Anthropic's browser use documentation recommends re-checking the destination in your `navigate` handler, accepting only `http` and `https`, treating a URL without a scheme as `https`, parsing URLs with a real parser instead of string prefixes, and blocking loopback, link-local and private address ranges unless you need them. Link-local matters because `169.254.169.254` is where cloud servers expose their instance credentials; a page that tricks an agent into visiting it could leak them.

```python
import ipaddress
from urllib.parse import urlsplit

ALLOWED_HOSTS = {"127.0.0.1", "shop.example.in"}

def check_navigation(url):
    """Return (ok, reason). Runs in the harness before every navigate call."""
    if url in ("back", "forward", "reload"):
        return True, "history action"
    parts = urlsplit(url)
    if not parts.scheme or "." in parts.scheme:     # "shop.example.in/cart" has no real scheme
        parts = urlsplit("https://" + url)
    if parts.scheme not in ("http", "https"):
        return False, f"scheme {parts.scheme!r} is not allowed"
    host = parts.hostname or ""
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_link_local or (ip.is_private and not ip.is_loopback):
            return False, f"{host} is a private or link-local address"
    except ValueError:
        pass                                        # a name, not an IP address
    if host not in ALLOWED_HOSTS:
        return False, f"{host} is not on the allowlist"
    return True, "ok"

for url in ["http://127.0.0.1:8765/kirana.html", "shop.example.in/cart", "file:///etc/passwd",
            "javascript:alert(1)", "https://evil.example.com/steal", "http://169.254.169.254/latest/", "back"]:
    print(f"{url:<38} -> {check_navigation(url)}")
```

Output:

```
http://127.0.0.1:8765/kirana.html      -> (True, 'ok')
shop.example.in/cart                   -> (True, 'ok')
file:///etc/passwd                     -> (False, "scheme 'file' is not allowed")
javascript:alert(1)                    -> (False, "scheme 'javascript' is not allowed")
https://evil.example.com/steal         -> (False, 'evil.example.com is not on the allowlist')
http://169.254.169.254/latest/         -> (False, '169.254.169.254 is a private or link-local address')
back                                   -> (True, 'history action')
```

We allowed `127.0.0.1` on purpose because our test page lives there; in production you would usually block loopback too. Remember that a page can also redirect after you navigate, so the same check should run again on the final URL, and the strongest version of this rule lives at the network layer (a proxy or firewall), which Module 3 sets up.

The other checks, covered in the next lessons, are: approval before consequential clicks (submit, pay, send, delete, accept terms), secrets that never enter the model's context, a step limit, and treating page text as untrusted.

---

## Try It Yourself

1. **Spot the flaky agent.** In the Playwright example, the agent reads the cart immediately after clicking and sees `Cart (0)`. Describe what a naive agent might do next, and two different fixes.
2. **Extend the guard.** Add a rule to `check_navigation` that blocks any URL whose path contains `/checkout/pay` unless an `approved` flag is passed.
3. **Batch semantics.** Run `run_batch` with a batch where the first call is a valid `read_page` and the second is an unknown member `teleport`. What does each result say?

<details>
<summary>Show answers</summary>

**1.** A naive agent would conclude the click failed and click **Add** again, ending with two packets of butter. Fixes: (a) after any click, wait for evidence of change, such as the status text or a network response, before observing (`expect(...).to_have_text(...)` or MCP's `browser_wait_for`); (b) make the tool return the *new* state after a short settle period, and tell the model in the tool description that cart updates can take a moment. A good harness does both.

**2.**

```python
def check_navigation_with_pay(url, approved=False):
    ok, reason = check_navigation(url)
    if ok and "/checkout/pay" in urlsplit(url if "://" in url else "https://" + url).path and not approved:
        return False, "payment pages need human approval"
    return ok, reason

print(check_navigation_with_pay("https://shop.example.in/checkout/pay"))
print(check_navigation_with_pay("https://shop.example.in/checkout/pay", approved=True))
```

Output:

```
(False, 'payment pages need human approval')
(True, 'ok')
```

**3.**

```python
for r in run_batch([{"id": "toolu_3", "name": "read_page", "input": {}},
                    {"id": "toolu_4", "name": "teleport", "input": {}}]):
    print(r["tool_use_id"], "error" if r.get("is_error") else "ok", "|", r["content"])
```

Output:

```
toolu_3 ok | searchbox "Search groceries" [ref_1]
button "Add Amul Butter 100 g" [ref_2]
toolu_4 error | Unknown or unimplemented member: teleport
```

The unknown member becomes an error result rather than crashing the agent loop, so the model can recover.

</details>

---

## Real-World Examples

- **Coding agents verify their own UI work** by connecting the Playwright MCP server: after editing a React form they open it, read the snapshot, fill it, and check the success message.
- **Test teams** use the code that Playwright MCP prints for each action as a starting point for permanent end-to-end tests.
- **Product teams building on the Claude API** use the browser use toolset with an executor running in a container per user session, so each user's browsing is isolated.
- **Browser automation platforms** such as Browserbase run fleets of remote Chromium instances that any of these routes can connect to over the Chrome DevTools Protocol, so the agent's browser never runs on a laptop.

---

## Common Misconceptions

### "The MCP server makes the browser safe"

It translates tool calls into Playwright actions. Its own documentation says it is not a security boundary. Isolation, network rules and approvals are your job.

### "If the click succeeded, the task step succeeded"

A click only means the event fired. Pages update asynchronously; always look for evidence of the intended change before deciding what to do next.

### "More browser tools make a smarter agent"

Every tool schema costs tokens on every request and gives the model another way to choose wrongly. Pick the smallest toolset that covers the task, and keep powerful members like JavaScript execution off unless you need them.

### "The model writes Playwright code"

In these routes the model chooses from fixed tools with refs; your harness or the MCP server runs Playwright. Agents that write and run automation code exist, but that is the code-execution pattern, with its own sandboxing needs.

---

## Interview Relevance

*"How would you give an LLM agent control of a browser?"* A strong answer names Playwright as the automation layer (contexts for isolation, role-based locators, auto-waiting), then compares the delivery routes: the Playwright MCP server for any MCP host, a provider toolset such as Anthropic's `browser_toolset_20260801` with your own executor, or a few custom function tools. It explains refs from accessibility snapshots, batch execution that stops at the first failure, and waiting for evidence after actions. It finishes with harness controls: URL scheme and host allowlists re-checked after redirects, blocking private and link-local addresses, risky tools disabled by default, human approval for consequential actions, and isolation because the MCP server itself is not a security boundary.

---

## Key Takeaways

- **Playwright is the hands**: contexts isolate sessions, role-and-name locators match what the model reads, and auto-waiting removes most timing bugs.
- **Three routes to the agent**: Playwright MCP server, Anthropic's browser use toolset with your executor, or a few custom tools.
- **Refs connect the model to elements**; executors keep the map and reject stale refs with a clear error.
- **A click is not a result**: wait for evidence, then observe.
- **Safety lives in the harness**: navigation allowlists, blocked private addresses, risky tools off by default, approvals in code.

---

**Up next:** [Browser Agent Libraries](browser-agent-libraries.md)
