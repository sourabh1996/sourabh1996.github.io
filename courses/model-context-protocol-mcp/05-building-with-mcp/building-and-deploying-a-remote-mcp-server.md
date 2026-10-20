---
title: "Building and Deploying a Remote MCP Server"
course: "Model Context Protocol (MCP)"
module: "5. Building with MCP"
type: Article
level: Intermediate
reading_time: 38 min
---

# Building and Deploying a Remote MCP Server: The Complete Guide

> 📚 **Before you start**
>
> - [Building a Local MCP Server with FastMCP](building-a-local-mcp-server-with-fastmcp.md), for the kirana server we'll take online.
> - [The Transport Layer: stdio and Streamable HTTP](../03-how-mcp-components-talk/the-transport-layer-stdio-and-streamable-http.md), for the HTTP rules: one POST per message, mirrored headers, status codes.
> - [Operation and Shutdown](../04-the-mcp-lifecycle/operation-and-shutdown.md), for explicit handles and why stateless servers scale.
> - [Docker and Cloud Deployment](../../apis-and-apps-fastapi-streamlit-and-docker/course.md#m9), if Dockerfiles and cloud deploys are new to you.

## Introduction

Ramesh's kirana server works beautifully on his laptop. Then his son, who runs the second shop in Hadapsar, asks to use it too, from his phone. And the accountant wants to ask Claude about stock levels from her office. A server that lives inside one laptop, started by one Claude Desktop, can't serve them. It needs to live somewhere everyone can reach: a **remote** MCP server, reachable at a URL like `https://mcp.kirana.example.in/mcp`.

Going remote changes more than the transport. Suddenly there are **many users**, so you need to know who is calling. The server must stay up when Ramesh's laptop is off, so it runs in the cloud. It may need **several copies** (instances) to handle load, so it must not keep secrets in one process's memory. And it's on the public internet, so security stops being optional.

By the end of this lesson you'll have run a two-instance remote server behind a pretend load balancer, with API-key checks, a health endpoint and a confirmation step that survives landing on a different instance. Then you'll build the real thing with the official SDK, put it in a Docker image, deploy it to a cloud platform, and connect hosts to it.

> 💡 **Key Insight**
>
> A good remote MCP server is **an ordinary stateless web service** with one POST endpoint. Every request brings its own version, capabilities and credentials; any instance can answer it; anything that must survive between requests lives in shared storage or in signed state the client carries back. Get that right and the usual web toolbox (containers, load balancers, autoscaling, health checks) just works.

---

## Core Explanation

### 1. The shape of a remote deployment

![Clients such as Claude, IDE agents and your own agents call one HTTPS URL. At the edge, TLS, token checks and Origin checks happen, then a load balancer sends any POST to any of several stateless instances. All instances share a database for data and handles, a secret manager for API keys and the state-signing key, and logs and traces](/img/diagrams/model-context-protocol-mcp/mcp-remote-deployment.svg)
*No sessions means no sticky routing: the load balancer can send each POST anywhere.*

| Concern | Local (stdio) | Remote (Streamable HTTP) |
|---|---|---|
| Who starts it | The host, per user | You, once, on a platform |
| Users | One | Many |
| Identity | The OS user running it | A token on every request |
| Secrets | `env` in the host config | A secret manager on the platform |
| Data | Local files | A database every instance can reach |
| Scaling | Not needed | More instances behind a load balancer |
| Health | The host notices a crash | A `/health` endpoint the platform polls |
| Updates | User upgrades the package | You deploy; every user gets it |

### 2. A two-instance server you can run

Let's build the core of a remote server with FastAPI and exercise it in memory with its test client. Two instances share a "database" (a dict standing in for Postgres) and a signing key (standing in for a secret manager). A tiny round-robin load balancer sends alternate requests to alternate instances, exactly what makes session-based servers break.

The `restock` tool asks for confirmation first using the multi round-trip pattern from earlier lessons, so the confirmation **retry will land on a different instance**. To make that work, the server seals what it needs into `requestState`, signed with the shared key and bound to the caller and an expiry time, as the spec recommends.

```python
import base64, hashlib, hmac, itertools, json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.testclient import TestClient

SHARED_DB = {"rice": 40.0, "toor dal": 12.0, "sugar": 4.5}       # stands in for Postgres
API_KEYS = {"key-ramesh-123": "ramesh", "key-amit-456": "amit"}   # stands in for a secret manager
CLOCK = {"now": 1_790_000_000}                                    # a fake clock keeps output stable

def seal(state, key):
    body = base64.urlsafe_b64encode(json.dumps(state, sort_keys=True).encode()).decode()
    return body + "." + hmac.new(key, body.encode(), hashlib.sha256).hexdigest()[:24]

def unseal(token, key):
    body, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(sig, hmac.new(key, body.encode(), hashlib.sha256).hexdigest()[:24]):
        raise ValueError("requestState failed verification")
    return json.loads(base64.urlsafe_b64decode(body))

def rpc(id_, result=None, error=None, status=200):
    body = {"jsonrpc": "2.0", "id": id_}
    body.update({"result": {"resultType": "complete", **result}} if result is not None else {"error": error})
    return JSONResponse(body, status_code=status)

def make_instance(name, signing_key):
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok", "instance": name}

    @app.post("/mcp")
    async def mcp_endpoint(request: Request):
        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        user = API_KEYS.get(token)
        if user is None:
            return Response(status_code=401, headers={"WWW-Authenticate": 'Bearer realm="kirana"'})
        msg = await request.json()
        if "id" not in msg:
            return Response(status_code=202)
        if request.headers.get("mcp-protocol-version") != "2026-07-28":
            return rpc(msg["id"], error={"code": -32022, "message": "Unsupported protocol version",
                                         "data": {"supported": ["2026-07-28"]}}, status=400)
        params = msg["params"]
        args = params["arguments"]
        if params["name"] != "restock":
            return rpc(msg["id"], error={"code": -32602, "message": "Unknown tool"})
        if "inputResponses" not in params:                       # first round: ask to confirm
            state = {"user": user, "item": args["item"], "qty": args["quantity"],
                     "exp": CLOCK["now"] + 300, "tool": "restock"}
            return JSONResponse({"jsonrpc": "2.0", "id": msg["id"], "result": {
                "resultType": "input_required",
                "inputRequests": {"confirm": {"method": "elicitation/create", "params": {
                    "mode": "form", "message": f"Add {args['quantity']} kg of {args['item']}?",
                    "requestedSchema": {"type": "object", "properties": {"ok": {"type": "boolean"}},
                                        "required": ["ok"]}}}},
                "requestState": seal(state, signing_key)}})
        try:                                                     # retry: trust nothing, verify everything
            state = unseal(params["requestState"], signing_key)
        except ValueError as e:
            return rpc(msg["id"], error={"code": -32602, "message": str(e)})
        problem = ("was issued to a different user" if state["user"] != user else
                   "has expired" if state["exp"] < CLOCK["now"] else
                   "was issued for a different request" if state["item"] != args["item"] else None)
        if problem:
            return rpc(msg["id"], error={"code": -32602, "message": f"requestState {problem}"})
        if not params["inputResponses"]["confirm"]["content"]["ok"]:
            return rpc(msg["id"], {"content": [{"type": "text", "text": "Cancelled by user"}], "isError": False})
        SHARED_DB[state["item"]] += state["qty"]
        text = f"{name}: {state['item']} now {SHARED_DB[state['item']]} kg (by {user})"
        return rpc(msg["id"], {"content": [{"type": "text", "text": text}], "isError": False})

    return app

STATE_KEY = b"from-the-secret-manager"
instances = [TestClient(make_instance("instance-1", STATE_KEY)), TestClient(make_instance("instance-2", STATE_KEY))]
balancer = itertools.cycle(instances)                           # round robin, no stickiness

for inst in instances:
    print(inst.get("/health").json())
```

Output:

```
{'status': 'ok', 'instance': 'instance-1'}
{'status': 'ok', 'instance': 'instance-2'}
```

Now a client. It sends the standard headers you met in the transport lesson, and every POST goes through the round-robin balancer:

```python
META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {"elicitation": {"form": {}}}}

def post(message, api_key="key-ramesh-123", lb=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
               "MCP-Protocol-Version": "2026-07-28", "Mcp-Method": message.get("method", "")}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if message.get("method") == "tools/call":
        headers["Mcp-Name"] = message["params"]["name"]
    return next(lb or balancer).post("/mcp", content=json.dumps(message), headers=headers)

def restock_call(id_, item, qty, extra=None):
    params = {"name": "restock", "arguments": {"item": item, "quantity": qty}, "_meta": META, **(extra or {})}
    return {"jsonrpc": "2.0", "id": id_, "method": "tools/call", "params": params}

r = post(restock_call(1, "rice", 25), api_key=None)
print("no token:", r.status_code, r.headers["www-authenticate"])

first = post(restock_call(2, "rice", 25)).json()["result"]
print("round 1:", first["resultType"], "|", first["inputRequests"]["confirm"]["params"]["message"])

answer = {"inputResponses": {"confirm": {"action": "accept", "content": {"ok": True}}},
          "requestState": first["requestState"]}
second = post(restock_call(3, "rice", 25, answer)).json()["result"]
print("round 2:", second["content"][0]["text"])
```

Output:

```
no token: 401 Bearer realm="kirana"
round 1: input_required | Add 25 kg of rice?
round 2: instance-1: rice now 65.0 kg (by ramesh)
```

Round 1 was answered by one instance and round 2 by the other, and it still worked, because everything the second instance needed was in the request: the token says who is calling, and the signed `requestState` says what was being confirmed.

Now the failures a careful server must catch:

```python
replay_by_amit = post(restock_call(4, "rice", 25, answer), api_key="key-amit-456").json()
print("someone else's state:", replay_by_amit["error"]["message"])

tok = first["requestState"]
tampered = dict(answer, requestState=tok[:10] + ("A" if tok[10] != "A" else "B") + tok[11:])
print("tampered state:      ", post(restock_call(5, "rice", 25, tampered)).json()["error"]["message"])

CLOCK["now"] += 600                                              # ten minutes later
print("expired state:       ", post(restock_call(6, "rice", 25, answer)).json()["error"]["message"])
CLOCK["now"] -= 600

misconfigured = itertools.cycle([TestClient(make_instance("instance-3", b"a-different-key"))])
print("wrong key on deploy: ", post(restock_call(7, "rice", 25, answer), lb=misconfigured).json()["error"]["message"])
```

Output:

```
someone else's state: requestState was issued to a different user
tampered state:       requestState failed verification
expired state:        requestState has expired
wrong key on deploy:  requestState failed verification
```

The last line is a real production bug: one instance deployed with a different signing key fails every retry that lands on it, randomly, about half the time. **Every instance must load the same key from the same secret manager.**

### 3. The real server with the official SDK

The `MCPServer` from the previous lesson can serve Streamable HTTP instead of stdio. The tools don't change at all; only the last few lines do.

```python
# not-run: needs the `mcp` package (2.x); run with uvicorn
import os
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

mcp = MCPServer("kirana-remote", instructions="Quantities are in kg.")

@mcp.tool()
def check_stock(item: str) -> str:
    """Return how much of one item is in stock."""
    ...                                    # read from the shared database, not a dict

@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})

mcp_app = mcp.streamable_http_app(
    stateless_http=True,        # also serve handshake-era clients without per-session memory
    json_response=True,         # plain JSON replies when no streaming is needed
    host="0.0.0.0",
    transport_security=TransportSecuritySettings(
        allowed_hosts=["mcp.kirana.example.in"],
        allowed_origins=["https://mcp.kirana.example.in"],
    ),
)

class ApiKeyMiddleware:
    """Reject /mcp requests without a known API key (fine for private servers; Module 6 covers OAuth)."""
    def __init__(self, app, keys):
        self.app, self.keys = app, keys

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/mcp"):
            auth = dict(scope["headers"]).get(b"authorization", b"").decode()
            if auth.removeprefix("Bearer ") not in self.keys:
                reply = PlainTextResponse("Unauthorized", status_code=401,
                                          headers={"WWW-Authenticate": 'Bearer realm="kirana"'})
                await reply(scope, receive, send)
                return
        await self.app(scope, receive, send)

app = ApiKeyMiddleware(mcp_app, keys=set(os.environ["KIRANA_API_KEYS"].split(",")))
```

Run it locally:

```bash
KIRANA_API_KEYS=key-ramesh-123 uv run uvicorn server:app --host 0.0.0.0 --port 8080
```

What the options mean:

| Option | Why |
|---|---|
| `streamable_http_app(...)` | Returns a standard ASGI (Starlette) app serving `POST /mcp`, so any ASGI server such as `uvicorn` can run it and you can wrap it in middleware |
| `stateless_http=True` | Modern clients are always stateless. This flag also handles legacy, handshake-era clients without keeping sessions in memory, so no instance stickiness is needed for them either |
| `json_response=True` | Reply with `application/json` when a request has nothing to stream; SSE is still used when needed |
| `TransportSecuritySettings` | Checks the `Host` and `Origin` headers against your real domain, the DNS-rebinding defence from the transport lesson |
| `custom_route("/health")` | An endpoint outside MCP for the platform's health checks. Custom routes skip MCP auth, so never put data there |

For a quick local experiment without uvicorn, `mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)` serves the same app at `http://127.0.0.1:8000/mcp`. The standalone `fastmcp` package has the same idea: `mcp.run(transport="http", host="0.0.0.0", port=8000)` or `mcp.http_app()` for an ASGI app.

**API keys or OAuth?** An API key in a header is fine for a private server used by your own agents or a small team. A public server that people connect from Claude, ChatGPT or an IDE should use OAuth 2.1, so each person signs in with their own account and hosts can handle login for them. [Authorization with OAuth 2.1](../06-mcp-in-production/authorization-with-oauth-2-1.md) builds that.

### 4. Packaging it in Docker

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
USER nobody
EXPOSE 8080
CMD ["uv", "run", "--no-sync", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
```

```bash
docker build -t kirana-mcp .
docker run --rm -p 8080:8080 -e KIRANA_API_KEYS=key-ramesh-123 kirana-mcp
```

A few habits that matter more for MCP servers than for typical apps:

- Bind to `0.0.0.0` **inside** the container (so the platform can reach it), but keep `allowed_hosts` set to your real domain.
- Run as a non-root user (`USER nobody`), so a bug in a tool can't take over the container.
- Pin the `uv` image to a specific version in production instead of `latest`, and commit `uv.lock` so builds are repeatable.
- Never bake keys into the image. Pass them as environment variables from the platform's secret store.

### 5. Deploying to a cloud platform

Any platform that runs containers works, because the server is a plain stateless HTTP service. Google Cloud Run is a common choice; the Mumbai region is `asia-south1`:

```bash
gcloud run deploy kirana-mcp \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-secrets KIRANA_API_KEYS=kirana-api-keys:latest
```

Example output:

```
Building using Dockerfile and deploying container to Cloud Run service [kirana-mcp] in project [kirana-prod] region [asia-south1]
OK Building and deploying new service... Done.
Service [kirana-mcp] revision [kirana-mcp-00001-xyz] has been deployed and is serving 100 percent of traffic.
Service URL: https://kirana-mcp-abc123-el.a.run.app
```

`--allow-unauthenticated` means Google itself doesn't check identity at the front door, because **your** app checks the API key (or OAuth token). Put a custom domain such as `mcp.kirana.example.in` in front and update `allowed_hosts` to match.

| Platform | Notes |
|---|---|
| **Cloud Run, AWS App Runner, Azure Container Apps** | Containers, autoscaling to zero, managed HTTPS |
| **Fly.io, Render, Railway** | Simple container hosting with HTTPS |
| **Kubernetes** | When you already run a cluster; use a Deployment, a Service and an Ingress |
| **Cloudflare Workers** | Runs TypeScript MCP servers at the edge (with the TypeScript SDK) |
| **Serverless functions** (Lambda behind API Gateway) | Works because each POST stands alone; mind request timeouts for long tools |

One limit to plan for: platforms cap how long one HTTP request may last (often 5 to 60 minutes). Tools that run longer should return quickly with a handle and let the client check back, which is what the **Tasks** extension standardises ([What Changed in the 2026 MCP Specification](../06-mcp-in-production/what-changed-in-the-2026-mcp-specification.md)).

### 6. Testing the deployed server

Start with plain HTTP, so you can see exactly what the server says:

```bash
curl -s https://mcp.kirana.example.in/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "MCP-Protocol-Version: 2026-07-28" \
  -H "Mcp-Method: tools/list" \
  -H "Authorization: Bearer key-ramesh-123" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}'
```

Example output:

```
{"jsonrpc":"2.0","id":1,"result":{"resultType":"complete","tools":[{"name":"check_stock","description":"Return how much of one item is in stock.","inputSchema":{...}}],"ttlMs":60000,"cacheScope":"public"}}
```

Then the MCP Inspector: choose the **Streamable HTTP** transport, paste the URL, add the `Authorization` header, and click through the tools. Finally, connect a host:

- **Claude (web and desktop)**: add a custom connector with the server URL. For OAuth-protected servers Claude runs the sign-in for you.
- **Cursor, VS Code and others**: add an entry with a `url` (and headers, if your host supports them) in their MCP config, as in Module 3.
- **Your own agent**: `Client("https://mcp.kirana.example.in/mcp")` from the Python SDK, covered in the next lesson.

### 7. Operating it

Once real people depend on it, a remote server needs the same care as any production API:

| Practice | How |
|---|---|
| **Logs and traces** | Log each `Mcp-Method` and `Mcp-Name` with the user and duration. The spec reserves `traceparent` in `_meta` for OpenTelemetry trace context, so a host's trace can continue into your server |
| **Rate limits** | Per user and per tool, at the edge; the mirrored headers let a gateway do it without parsing JSON |
| **Timeouts** | A maximum duration per tool, below the platform's request limit |
| **Versioned deploys** | Roll out gradually; tool names and schemas are a public contract, so add new tools rather than changing old ones in breaking ways |
| **Caching hints** | Return sensible `ttlMs` on lists so clients don't call `tools/list` on every turn |

---

## Try It Yourself

1. **Cancel instead of confirm.** Repeat round 2 with `{"ok": False}`. What does the server return, and did the stock change?
2. **Change the item on retry.** Send the retry with the original `requestState` but `item="sugar"`. Which check stops it, and why does that matter?
3. **Why not a session?** In one paragraph, explain what would go wrong if instance 1 stored "pending confirmation for Ramesh: 25 kg rice" in a Python dict instead of sealing it into `requestState`.

<details>
<summary>Show answers</summary>

**1.**

```python
before = SHARED_DB["rice"]
first = post(restock_call(10, "rice", 5)).json()["result"]
no = {"inputResponses": {"confirm": {"action": "accept", "content": {"ok": False}}},
      "requestState": first["requestState"]}
print(post(restock_call(11, "rice", 5, no)).json()["result"]["content"][0]["text"],
      "| rice unchanged:", SHARED_DB["rice"] == before)
```

Output:

```
Cancelled by user | rice unchanged: True
```

**2.**

```python
first = post(restock_call(12, "rice", 5)).json()["result"]
swap = {"inputResponses": {"confirm": {"action": "accept", "content": {"ok": True}}},
        "requestState": first["requestState"]}
print(post(restock_call(13, "sugar", 5, swap)).json()["error"]["message"])
```

Output:

```
requestState was issued for a different request
```

The item inside the signed state is `rice`, but the retry asks for `sugar`. Binding the state to the original request's parameters stops a client from getting approval for one action and then using it for another.

**3.** The retry would usually land on a different instance, which has no such entry, so the confirmation would fail at random. Even with sticky routing, a restart or a scale-down would lose every pending confirmation. Sealing the state into the request lets any instance finish the job, at any time before it expires.

</details>

---

## Real-World Examples

- **Vendor-hosted servers** (GitHub, Atlassian, Notion, Stripe, Cloudflare and others) run remote MCP servers at a fixed URL with OAuth, so users connect without installing anything.
- **Internal company servers** sit behind the corporate identity provider and are deployed like any other microservice, often on Kubernetes.
- **Hosted MCP platforms** (Smithery's hosted connections, cloud providers' managed offerings) run your server for you and handle TLS and scaling.
- **Serverless MCP** on Cloud Run or Lambda is common for low-traffic tools, because stateless requests can scale to zero.

---

## Common Misconceptions

### "A remote server needs sessions to remember users"

The token identifies the user on every request. Workflow state goes in shared storage behind explicit handles, or in signed `requestState`.

### "HTTPS means it's secure"

HTTPS protects data in transit. You still need authentication, `Host` and `Origin` checks, rate limits and careful tools.

### "Sticky sessions on the load balancer fix everything"

They hide the problem until an instance restarts or scales down. Stateless design fixes it properly.

### "Remote servers can do anything local ones can"

A remote server can't see the user's files or local apps. Tools that need the user's machine stay local.

---

## Interview Relevance

*"How would you deploy an MCP server for many users?"* Strong answers describe Streamable HTTP on one `/mcp` endpoint, stateless instances behind a load balancer, auth on every request (API keys for private use, OAuth 2.1 for public), shared storage for data and handles, signed and bound `requestState` for multi-round flows, a shared signing key from a secret manager, `Host`/`Origin` validation, health checks, container packaging, platform request-time limits (and Tasks for long jobs), and observability through `Mcp-Method`/`Mcp-Name` headers and trace context. Mentioning the "different signing key on one instance" failure mode shows real operational experience.

---

## Key Takeaways

- **Remote MCP is a stateless web service**: one POST endpoint, auth on every request, any instance can answer any request.
- **State lives outside the process**: data and handles in a shared database, multi-round state signed, bound to the user and request, and expiring.
- **The SDK serves HTTP with a few lines**: `streamable_http_app(...)` gives an ASGI app you can wrap in middleware and run with uvicorn.
- **Package with Docker, deploy anywhere containers run**, with secrets from the platform and `allowed_hosts` set to your domain.
- **Test with curl, then the Inspector, then a host**; plan for logs, rate limits, timeouts and gradual rollouts.

---

**Up next:** [Building an MCP Client](building-an-mcp-client.md)
