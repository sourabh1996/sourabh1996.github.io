---
title: "The Transport Layer: stdio and Streamable HTTP"
course: Model Context Protocol (MCP)
module: "3. How MCP Components Talk"
type: Article
level: Intermediate
reading_time: 34 min
---

# The Transport Layer: stdio and Streamable HTTP: The Complete Guide

> 📚 **Before you start**
>
> - [The Data Layer: JSON-RPC Messages](the-data-layer-json-rpc-messages.md), for the messages that transports carry.
> - [HTTP Methods and Status Codes](../../production-apis-with-fastapi/course.md#m2), if POST, headers and status codes are new to you.

## Introduction

A letter can reach your grandmother in Lucknow by hand (you give it to a cousin who's travelling there) or by India Post. The words inside are the same either way. What changes is how it travels, who can read the envelope on the way, how you know it arrived, and what you do if it gets lost.

MCP has two official ways to carry its JSON-RPC messages:

- **stdio**: the host starts the server as a child process on the same machine and talks through its standard input and output. The "cousin travelling to Lucknow".
- **Streamable HTTP**: the server runs somewhere on the network, and every message is an HTTPS POST to one endpoint. The "India Post".

By the end of this lesson you'll have run a real stdio server as a subprocess and a real Streamable HTTP endpoint, both by hand, and you'll know the rules each transport adds: framing, headers, status codes, streaming, cancellation, shutdown, security and backward compatibility.

> 💡 **Key Insight**
>
> The transport changes **how messages travel**, never **what they say**. stdio frames messages as one JSON object per line over a private pipe to a local process. Streamable HTTP sends each message as its own POST to a single `/mcp` endpoint, and the server answers with either one JSON object or a short-lived event stream for that request.

---

## Core Explanation

### 1. The two transports side by side

| | stdio | Streamable HTTP |
|---|---|---|
| Where the server runs | Same machine, child process of the host | Anywhere reachable over HTTP(S) |
| Who starts it | The host, using a command from config | Already running (you deploy it) |
| Framing | One JSON message per line (newline-delimited) | One message per HTTP POST body |
| Server replies with | Lines on stdout | `application/json` or `text/event-stream` per request |
| Users per server | One | Many |
| Metadata | Only inside the JSON | JSON body **plus mirrored HTTP headers** |
| Auth | Environment variables (API keys) | OAuth 2.1 bearer tokens |
| Cancel a request | Send `notifications/cancelled` | Close that request's response stream |
| Shutdown | Close stdin, wait, then terminate | Just stop sending requests |
| Typical servers | Filesystem, local Git, local database, CLI tools | SaaS products, company-wide services |

```mermaid
flowchart LR
    subgraph Local["stdio: same machine"]
      H1["Host"] -->|"stdin: one JSON per line"| S1["Server process"]
      S1 -->|"stdout: one JSON per line"| H1
      S1 -.->|"stderr: logs"| L1["Host log file"]
    end
    subgraph Remote["Streamable HTTP: over the network"]
      H2["Host"] -->|"POST /mcp (one message)"| S2["Server"]
      S2 -->|"200 JSON, or 200 SSE stream,<br/>or 202 for a notification"| H2
    end
```

### 2. stdio: the rules

- The client launches the server as a subprocess.
- The server **reads** JSON-RPC messages from **stdin** and **writes** them to **stdout**, **one message per line**. Messages must not contain embedded newlines (normal `json.dumps` output has none).
- The server **may write anything it likes to stderr**: logs, debug output, warnings. The client may capture or ignore it and must not assume stderr output means an error.
- The server **must not write anything to stdout that isn't a valid MCP message**. One stray `print("hello")` corrupts the channel.
- All requests share one channel, so responses are matched by `id`, and notifications on subscription streams carry a `subscriptionId` in `_meta`.
- **Cancellation**: send `notifications/cancelled` with the request's id.
- **Shutdown**: the client closes the server's stdin, waits for it to exit, and only if it hangs, terminates it (`SIGTERM`, then `SIGKILL` on Linux and macOS). Servers should exit promptly when stdin closes.
- If the server dies unexpectedly, the client should restart it and retry in-flight requests, which is easy because the protocol is stateless.

### 3. A real stdio server and client (runnable)

This writes a tiny server to a temporary file, launches it with the same Python you're running, and talks to it over real pipes.

```python
import json, os, subprocess, sys, tempfile, textwrap

SERVER_CODE = textwrap.dedent('''
    import json, sys

    def log(*args):
        print(*args, file=sys.stderr, flush=True)   # stderr is for humans; stdout is the wire

    def reply(msg_id, result):
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg_id,
                                     "result": {"resultType": "complete", **result}}) + "\\n")
        sys.stdout.flush()

    log("chai-server starting")
    for line in sys.stdin:                          # one JSON-RPC message per line
        msg = json.loads(line)
        if "id" not in msg:                         # a notification: never answered
            log("notification:", msg["method"])
            continue
        if msg["method"] == "server/discover":
            reply(msg["id"], {"supportedVersions": ["2026-07-28"], "capabilities": {"tools": {}}})
        elif msg["method"] == "tools/call":
            n = msg["params"]["arguments"]["cups"]
            reply(msg["id"], {"content": [{"type": "text", "text": f"{n} cups of chai cost Rs {n * 15}"}],
                              "isError": False})
    log("stdin closed, exiting cleanly")
''')

server_path = os.path.join(tempfile.mkdtemp(), "chai_server.py")
with open(server_path, "w") as f:
    f.write(SERVER_CODE)

proc = subprocess.Popen([sys.executable, server_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, text=True)
META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {}}

def send(message):
    proc.stdin.write(json.dumps(message) + "\n")    # framing: exactly one line per message
    proc.stdin.flush()

def receive():
    return json.loads(proc.stdout.readline())

send({"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": META}})
print("<-", receive()["result"]["capabilities"])
send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
      "params": {"name": "chai_bill", "arguments": {"cups": 4}, "_meta": META}})
print("<-", receive()["result"]["content"][0]["text"])
send({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 99, "reason": "demo"}})

proc.stdin.close()                       # shutdown step 1: close the server's input
exit_code = proc.wait(timeout=5)         # step 2: wait; a real client escalates if this times out
print("exit code:", exit_code)
print("server stderr:")
print(proc.stderr.read().rstrip())
proc.stdout.close()
proc.stderr.close()
```

Output:

```
<- {'tools': {}}
<- 4 cups of chai cost Rs 60
exit code: 0
server stderr:
chai-server starting
notification: notifications/cancelled
stdin closed, exiting cleanly
```

That is a genuine MCP stdio exchange. Hosts like Claude Desktop do exactly this, with the command coming from their config file instead of `sys.executable`.

The transport binding for stdio isn't really about "standard streams": the spec notes the same newline-delimited framing works over Unix sockets or TCP. Only the process parts (launching, stderr, shutdown by closing input) are subprocess-specific.

### 4. Streamable HTTP: the rules

The server exposes **one endpoint** (the "MCP endpoint"), for example `https://mcp.kharcha.in/mcp`, that accepts **POST**.

**Sending:**

1. Every JSON-RPC message from the client is its **own POST**. The body is exactly one request or notification, never a response.
2. The client sends `Accept: application/json, text/event-stream` (it must handle both).
3. The client mirrors key body fields into **headers**:

| Header | Value comes from | Required on |
|---|---|---|
| `MCP-Protocol-Version` | `_meta` `io.modelcontextprotocol/protocolVersion` | every POST |
| `Mcp-Method` | `method` | every request |
| `Mcp-Name` | `params.name` or `params.uri` | `tools/call`, `resources/read`, `prompts/get` |
| `Mcp-Param-{Name}` | a tool argument marked with `x-mcp-header` in its schema | when that argument is present |
| `Authorization` | `Bearer <token>` | every request to a protected server |

Why duplicate data in headers? So **load balancers, gateways and firewalls** can route, rate-limit and log by method or tool without parsing JSON. Because a header and the body could disagree (an attacker might route on one and execute the other), the server **must** reject mismatches with `400` and error `-32020` (HeaderMismatch). Values that aren't plain ASCII are Base64-encoded as `=?base64?...?=`.

A real request looks like this:

```http
POST /mcp HTTP/1.1
Host: mcp.kharcha.in
Content-Type: application/json
Accept: application/json, text/event-stream
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tools/call
Mcp-Name: get_total
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...

{"jsonrpc": "2.0", "id": 7, "method": "tools/call",
 "params": {"name": "get_total", "arguments": {"category": "food", "month": "2026-10"},
            "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
                      "io.modelcontextprotocol/clientCapabilities": {}}}}
```

**Receiving:**

| Situation | Server responds |
|---|---|
| Body is a notification the server accepts | `202 Accepted`, no body |
| Body is a request, quick answer | `200`, `Content-Type: application/json`, one JSON-RPC response |
| Body is a request, with progress or log notifications first | `200`, `Content-Type: text/event-stream`: notifications for **this request**, then the final response, then the stream closes |
| Headers don't match body | `400` + `-32020` |
| Unsupported protocol version | `400` + `-32022` listing supported versions |
| Unknown method | `404` + `-32601` |
| `Origin` header present and not allowed | `403` |
| Missing or invalid token | `401` with a `WWW-Authenticate` header |
| GET or DELETE to the endpoint | `405` (they meant something in older versions) |

Server-sent events (SSE) are just a text format for a response that arrives in pieces: each event is a `data: ...` line followed by a blank line. In MCP, an SSE response stream belongs to **one request only**. Servers should send `X-Accel-Buffering: no` so proxies like nginx don't hold the events back.

**Cancellation** is beautifully simple: closing the response stream *is* the cancel signal. **Long-lived notifications** (tool list changed, resource updated) arrive on the response stream of a separate `subscriptions/listen` request.

### 5. A Streamable HTTP endpoint by hand (runnable)

We'll implement the core rules with FastAPI and exercise them with FastAPI's test client, which sends real HTTP requests to the app in memory.

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.testclient import TestClient

SUPPORTED = ["2026-07-28"]
ALLOWED_ORIGINS = {None, "https://chat.example.in"}      # None: non-browser clients send no Origin
app = FastAPI()

def rpc_error(id_, code, message, status, data=None):
    err = {"code": code, "message": message, **({"data": data} if data else {})}
    return JSONResponse({"jsonrpc": "2.0", "id": id_, "error": err}, status_code=status)

def run_tool(name, args):
    return {"content": [{"type": "text", "text": f"{args['table']} has 1,284 rows"}], "isError": False}

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    if request.headers.get("origin") not in ALLOWED_ORIGINS:          # DNS-rebinding protection
        return Response(status_code=403)
    msg = await request.json()
    if "id" not in msg:                                               # a notification
        return Response(status_code=202)
    meta = msg.get("params", {}).get("_meta", {})
    version = meta.get("io.modelcontextprotocol/protocolVersion")
    if (request.headers.get("mcp-protocol-version") != version
            or request.headers.get("mcp-method") != msg["method"]):
        return rpc_error(msg["id"], -32020, "Header mismatch", 400)
    if version not in SUPPORTED:
        return rpc_error(msg["id"], -32022, "Unsupported protocol version", 400,
                         {"supported": SUPPORTED, "requested": version})
    if msg["method"] != "tools/call":
        return rpc_error(msg["id"], -32601, "Method not found", 404)
    if request.headers.get("mcp-name") != msg["params"]["name"]:
        return rpc_error(msg["id"], -32020, "Header mismatch", 400)
    result = {"resultType": "complete", **run_tool(msg["params"]["name"], msg["params"]["arguments"])}
    token = meta.get("progressToken")
    if token is None:                                                 # quick answer: plain JSON
        return JSONResponse({"jsonrpc": "2.0", "id": msg["id"], "result": result})
    def events():                                                     # SSE stream for this request only
        for done in (50, 100):
            note = {"jsonrpc": "2.0", "method": "notifications/progress",
                    "params": {"progressToken": token, "progress": done, "total": 100}}
            yield f"data: {json.dumps(note)}\n\n"
        yield f"data: {json.dumps({'jsonrpc': '2.0', 'id': msg['id'], 'result': result})}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})

@app.get("/mcp")
async def no_get_stream():
    return Response(status_code=405)

http = TestClient(app)

def post(body, **extra_headers):
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json",
               "MCP-Protocol-Version": "2026-07-28", "Mcp-Method": body.get("method", "")}
    headers.update(extra_headers)
    return http.post("/mcp", content=json.dumps(body), headers=headers)

call = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "count_rows", "arguments": {"table": "orders"}, "_meta": META}}
r = post(call, **{"Mcp-Name": "count_rows"})
print(r.status_code, r.headers["content-type"], "|", r.json()["result"]["content"][0]["text"])
```

Output:

```
200 application/json | orders has 1,284 rows
```

Now the streaming answer, and every rejection path:

```python
streamed = json.loads(json.dumps(call))
streamed["params"]["_meta"] = {**META, "progressToken": "rows-1"}
r = post(streamed, **{"Mcp-Name": "count_rows"})
print(r.status_code, r.headers["content-type"].split(";")[0])
for event in r.text.strip().split("\n\n"):
    body = json.loads(event.removeprefix("data: "))
    label = body.get("method") or f"response id={body['id']}"
    print(f"  event: {label} {body.get('params', {}).get('progress', '')}".rstrip())

checks = {
    "lying Mcp-Name header": post(call, **{"Mcp-Name": "drop_table"}),
    "evil browser Origin": post(call, **{"Mcp-Name": "count_rows", "Origin": "https://evil.example"}),
    "notification": post({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 1}}),
    "unknown method": post({"jsonrpc": "2.0", "id": 2, "method": "pets/list", "params": {"_meta": META}}),
    "old GET stream": http.get("/mcp"),
}
for name, resp in checks.items():
    code = resp.json()["error"]["code"] if resp.content else ""
    print(f"{name:<22} -> HTTP {resp.status_code} {code}".rstrip())
```

Output:

```
200 text/event-stream
  event: notifications/progress 50
  event: notifications/progress 100
  event: response id=1
lying Mcp-Name header  -> HTTP 400 -32020
evil browser Origin    -> HTTP 403
notification           -> HTTP 202
unknown method         -> HTTP 404 -32601
old GET stream         -> HTTP 405
```

A production server adds authentication, real tools and logging, but the transport rules are exactly these.

### 6. Security rules for HTTP servers

| Rule | The attack it stops |
|---|---|
| **Validate `Origin`**; reject unknown origins with 403 | *DNS rebinding*: a malicious web page tricks your browser into calling a server on `localhost` |
| **Bind local servers to `127.0.0.1`**, not `0.0.0.0` | Other machines on the café Wi-Fi reaching your dev server |
| **Authenticate every request** (OAuth 2.1 for remote servers) | Anyone on the internet calling your tools |
| **Validate header-body consistency** (`-32020`) | Routing and policy decided on a header the server then ignores |
| **Never put secrets in `x-mcp-header` parameters** | Headers are visible to every proxy on the path |

### 7. stdio or HTTP? Choosing

```mermaid
flowchart TD
    Q1{"Does the server need the user's<br/>local files, apps or processes?"} -->|Yes| STDIO["stdio<br/>(local server)"]
    Q1 -->|No| Q2{"Will many users or devices<br/>share it?"}
    Q2 -->|Yes| HTTP["Streamable HTTP<br/>(remote, with OAuth)"]
    Q2 -->|No| Q3{"Do you want zero install<br/>for users?"}
    Q3 -->|Yes| HTTP
    Q3 -->|No| STDIO
```

Many servers ship **both**: the same tools runnable locally over stdio for developers, and hosted over HTTP for everyone else. SDKs make this a one-line switch (`mcp.run(transport="stdio")` vs `mcp.run(transport="streamable-http")` in the official Python SDK).

### 8. Old transports you'll still meet

| Era | Transport shape | Status |
|---|---|---|
| `2024-11-05` | **HTTP+SSE**: a GET opened an SSE stream, the server sent an `endpoint` event, the client POSTed messages to that second URL | Deprecated; don't build new ones |
| `2025-03-26` to `2025-11-25` | **Streamable HTTP, sessionful**: `Mcp-Session-Id` header, optional GET stream for server messages, servers could send requests on SSE, resumable streams via `Last-Event-ID`, DELETE to end a session | Replaced by the stateless form in `2026-07-28` |
| `2026-07-28` | **Streamable HTTP, stateless**: POST only, no sessions, no GET stream, `subscriptions/listen` for notifications, no resumption | Current |

A modern server receiving old-style traffic should answer GET or DELETE with `405`, ignore `Mcp-Session-Id` and ignore `Last-Event-ID`. A client that wants to support old servers tries a modern request first and falls back to the `initialize` handshake if the reply is a `400` without a recognised modern error body. The next module covers this in detail.

### 9. Custom transports

The spec allows other transports (for example WebSockets inside a company, or an in-memory pipe for tests) as long as they carry the same JSON-RPC messages and respect the lifecycle. SDKs use an **in-memory transport** for unit tests: the client and server run in the same process with no pipes at all. You'll use one in [Building an MCP Client](../course.md#m5).

---

## Try It Yourself

1. **Corrupt the pipe.** Add a line `print("debug: got message")` (to stdout!) inside the server's loop, rerun the stdio example, and predict what `receive()` does.
2. **Accept a browser origin.** Add `"http://localhost:5173"` to `ALLOWED_ORIGINS` and confirm a request with that `Origin` now succeeds.
3. **Explain the 202.** Why does a notification get `202 Accepted` with no body instead of `200` with a JSON body?

<details>
<summary>Show answers</summary>

**1.** `receive()` reads the first line, which is now `debug: got message`, and `json.loads` raises a `JSONDecodeError`. Real clients log a parse error and often drop the connection. Any debug output on a stdio server must go to stderr.

**2.**

```python
ALLOWED_ORIGINS.add("http://localhost:5173")
r = post(call, **{"Mcp-Name": "count_rows", "Origin": "http://localhost:5173"})
print(r.status_code, r.json()["result"]["isError"])
```

Output:

```
200 False
```

**3.** JSON-RPC notifications never get a response. HTTP still needs a status code, so the server says "received, nothing to return" with `202` and an empty body.

</details>

---

## Real-World Examples

- **Claude Desktop, Cursor and VS Code** launch local servers from a `command` and `args` in a JSON config file: that's stdio.
- **Remote connectors** in claude.ai, ChatGPT and IDEs take a URL such as `https://mcp.example.com/mcp`: that's Streamable HTTP, usually with OAuth.
- **Reverse proxies and API gateways** in front of MCP servers route and rate-limit using the `Mcp-Method` and `Mcp-Name` headers.
- **Serverless platforms** run stateless Streamable HTTP servers well, because no session has to stick to one instance.

---

## Common Misconceptions

### "stdio servers can log with print()"

Only to stderr. Stdout is reserved for protocol messages.

### "Streamable HTTP means one long-lived connection"

Each message is its own POST. A response may stream for the duration of that one request, and a `subscriptions/listen` request may stay open, but there's no persistent session.

### "SSE is a separate transport"

In the current spec SSE is just one way a Streamable HTTP server can format the response to a POST. The old standalone HTTP+SSE transport is deprecated.

### "Local servers are safe, so they don't need checks"

A local HTTP server can be reached by any web page through DNS rebinding unless it checks `Origin` and binds to localhost.

---

## Interview Relevance

*"What transports does MCP support and how do they differ?"* A strong answer: **stdio** (child process, newline-delimited JSON on stdin/stdout, logs on stderr, cancel with `notifications/cancelled`, shut down by closing stdin then SIGTERM/SIGKILL) and **Streamable HTTP** (one POST per message to a single endpoint, response as JSON or a per-request SSE stream, `202` for notifications, mirrored headers `MCP-Protocol-Version`, `Mcp-Method`, `Mcp-Name` validated against the body, cancel by closing the stream). Add the security points (Origin validation, localhost binding, OAuth) and the history (HTTP+SSE deprecated; sessions, GET streams and resumability removed in `2026-07-28`).

---

## Key Takeaways

- **The transport carries messages; it never changes them.**
- **stdio**: one JSON message per line, stdout only for protocol, stderr for logs, shut down by closing stdin.
- **Streamable HTTP**: one POST per message to `/mcp`; reply as JSON, a per-request SSE stream, or `202`.
- **Headers mirror the body** for routing and must match it, or the server returns `-32020`.
- **Security is part of the transport**: check `Origin`, bind local servers to localhost, authenticate remote ones.

---

**Up next:** [Using MCP in Claude Desktop and Cursor](using-mcp-in-claude-desktop-and-cursor.md)
