---
title: "Docker MCP Catalog and Toolkit"
course: "Model Context Protocol (MCP)"
module: "5. Building with MCP"
type: Article
level: Intermediate
reading_time: 30 min
---

# Docker MCP Catalog and Toolkit: The Complete Guide

> 📚 **Before you start**
>
> - [Open MCP Registries (Smithery)](open-mcp-registries-smithery.md), for registries and the risks of running other people's servers.
> - [Building an MCP Client](building-an-mcp-client.md), for how a host merges tools from several servers.
> - [Docker and Cloud Deployment](../../apis-and-apps-fastapi-streamlit-and-docker/course.md#m9), for images, containers and `docker run`.

## Introduction

When a new tenant moves into a flat in Mumbai, the society doesn't hand them keys to every flat and the building's electrical room. They get their own flat, their own meter and a gate pass. If they turn out to be trouble, the damage stays inside their walls.

Local MCP servers, as you've run them so far, get the opposite deal. `npx some-server` or `uvx some-server` runs with **your** user account: it can read your home folder, your SSH keys and your browser profile, open network connections anywhere, and use as much CPU as it likes. You also need the right Node or Python version installed for each one, and every host (Claude Desktop, Cursor, VS Code) needs its own copy of the config.

Docker's MCP tools apply the "own flat, own meter" idea to MCP servers:

- The **Docker MCP Catalog** is a curated set of MCP servers packaged as container images.
- The **MCP Toolkit** in Docker Desktop lets you pick servers, configure them and their secrets once, and group them into **profiles**.
- The **MCP Gateway** (`docker mcp gateway run`) is a single MCP server that your hosts connect to; behind it, it runs each selected server in its own container and routes calls to the right one.

By the end of this lesson you'll understand why containers suit MCP servers, how the catalog, toolkit, profiles and gateway fit together, the exact CLI commands to set them up and connect a host, how to containerise your own server, and how a gateway applies policy to every call (you'll build a small one).

> 💡 **Key Insight**
>
> The Docker MCP Gateway is **an MCP server made of MCP servers**. Your host sees one server with all the tools from a profile; behind it, every real server runs in an isolated container with limited CPU, memory and file access, and the gateway can inspect each call on the way in and out. Isolation plus one choke point is what makes trying many third-party servers reasonably safe.

---

## Core Explanation

### 1. The pieces

![On the left, hosts such as Claude Desktop, Cursor and VS Code each have one config entry: docker mcp gateway run --profile web-dev. In the middle, the MCP Gateway reads the profile, lists merged tools, checks calls for secrets and routes each call. On the right, each server from the profile (GitHub, Playwright, a custom internal server) runs in its own container with 1 CPU, 2 GB memory and no host files unless mounted. Below, the Docker MCP Catalog and a company catalog supply signed images](/img/diagrams/model-context-protocol-mcp/docker-mcp-gateway.svg)
*Hosts know one server. The gateway knows the profile. Each real server lives in its own container.*

| Piece | What it is | Where |
|---|---|---|
| **Docker MCP Catalog** | Hundreds of MCP servers (Docker's docs say 300+) packaged as container images, with versions, provenance and security updates | Docker Hub's MCP section; the Catalog tab in Docker Desktop |
| **`mcp` namespace on Docker Hub** | Images Docker builds itself, digitally signed, each with an SBOM (a list of everything inside the image) | `hub.docker.com/u/mcp` |
| **MCP Toolkit** | The management UI in Docker Desktop: browse, enable, configure, connect clients | Docker Desktop (the current UI is in 4.62 and later) |
| **Profiles** | Named sets of servers and their settings, for example `web-dev` with GitHub and Playwright | Docker Desktop or `docker mcp profile ...` |
| **MCP Gateway** | One MCP server that hosts connect to; runs and routes to the servers in a profile | `docker mcp gateway run` |
| **Custom catalogs** | Your organisation's own list of approved servers, shared as an OCI artifact | `docker mcp catalog ...` |

### 2. Why containers suit MCP servers

| Problem with `npx`/`uvx` servers | What the container gives you |
|---|---|
| Runs as you, with access to all your files | No host file access unless you explicitly mount a folder |
| Unlimited CPU and memory | Each tool container is limited to 1 CPU and 2 GB of memory |
| Needs the right Node or Python on your machine | The image carries its own runtime |
| Unknown build: what's actually in that npm package? | Docker-built images in the `mcp` namespace are signed and come with an SBOM |
| Secrets pasted into each host's config | Secrets configured once in the toolkit and injected into the container |
| A different config in every host | One gateway entry in every host |

Isolation doesn't fix everything. A server that legitimately needs your GitHub token can still misuse **that** token, and a poisoned tool description still reaches your model. Containers shrink the blast radius; they don't make a malicious server trustworthy.

### 3. Setting it up from the command line

Everything in the Docker Desktop UI has a CLI equivalent under `docker mcp`. A typical setup for a web developer:

```bash
# See what's in Docker's catalog
docker mcp catalog server ls mcp/docker-mcp-catalog

# Create a profile and add two servers from the catalog
docker mcp profile create --name web-dev
docker mcp profile server add web-dev \
  --server catalog://mcp/docker-mcp-catalog/github-official \
  --server catalog://mcp/docker-mcp-catalog/playwright

# Check it
docker mcp profile server ls --filter profile=web-dev

# Per-server settings (the keys are defined by each server)
docker mcp profile config web-dev --get-all
```

Then connect your hosts. For clients the toolkit knows, one command writes the config:

```bash
docker mcp client connect vscode --profile web-dev     # writes .vscode/mcp.json in the current folder
echo ".vscode/mcp.json" >> .gitignore                  # it's user-specific; keep it out of Git
```

For any host that takes a JSON config (Claude Desktop, Cursor and others), the gateway is just a stdio server whose command is `docker`:

```json
{
  "mcpServers": {
    "docker-gateway": {
      "command": "docker",
      "args": ["mcp", "gateway", "run", "--profile", "web-dev"]
    }
  }
}
```

Restart the host and you'll see the GitHub and Playwright tools, all coming through one server entry. Behind the scenes the gateway pulls the images, starts containers as needed and forwards each `tools/call` to the right one.

```mermaid
sequenceDiagram
    participant H as Host (Claude Desktop)
    participant G as MCP Gateway
    participant C1 as github container
    participant C2 as playwright container
    H->>G: launch docker mcp gateway run --profile web-dev
    H->>G: tools/list
    G->>C1: tools/list
    G->>C2: tools/list
    G-->>H: merged list
    H->>G: tools/call (a GitHub tool)
    G->>G: check the call (secrets, policy)
    G->>C1: tools/call
    C1-->>G: result
    G->>G: check the result
    G-->>H: result
```

### 4. Profiles for different projects and teams

A profile is a named bundle: which servers, which settings. Use one per project or role, so a data project's agent doesn't see your production deployment tools.

```bash
docker mcp profile list
docker mcp profile show web-dev

# Share a profile with your team through a registry (credentials are NOT included)
docker mcp profile push web-dev registry.example.com/profiles/web-dev:v1
docker mcp profile pull registry.example.com/profiles/team-standard:latest

# Or through a file in the repository
docker mcp profile export web-dev .docker/mcp-profile.json
docker mcp profile import .docker/mcp-profile.json
```

Since credentials never travel with a shared profile, each teammate configures their own tokens. That's deliberate: a profile says *which* tools, not *whose* access.

### 5. Custom catalogs: an approved list for your company

An organisation can publish its own catalog: start from Docker's, remove what isn't approved, add internal servers, and push it to the company's registry.

```bash
# Start from Docker's catalog
docker mcp catalog tag mcp/docker-mcp-catalog registry.example.com/mcp/company-tools:latest

# Remove a server that isn't approved
docker mcp catalog server remove registry.example.com/mcp/company-tools:latest --name <server-name>

# Add internal servers (your own images)
docker mcp catalog server add registry.example.com/mcp/company-tools:latest \
  --server docker://registry.example.com/mcp/internal-api:latest \
  --server docker://registry.example.com/mcp/data-pipeline:latest

# Publish it; teammates pull it
docker mcp catalog push registry.example.com/mcp/company-tools:latest
docker mcp catalog pull registry.example.com/mcp/company-tools:latest

# Run a gateway straight from a catalog with chosen servers
docker mcp gateway run --catalog registry.example.com/mcp/company-tools:latest \
  --servers internal-api --servers data-pipeline
```

To get a server into Docker's **public** catalog, you contribute it through the `docker/mcp-registry` repository on GitHub; after approval it appears within about a day. That's a different list from the official MCP Registry you met two lessons ago, although both can describe the same server.

### 6. Containerising your own server

Any stdio server can run in a container, as long as the container keeps stdin open. Here's the kirana server from earlier lessons:

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY server.py .
USER nobody
LABEL io.modelcontextprotocol.server.name="io.github.kirana-dev/kirana"
ENTRYPOINT ["uv", "run", "--no-sync", "server.py"]
```

The `LABEL` is how the official MCP Registry verifies that an image belongs to the server name you publish (from the registries lesson).

```bash
docker build -t kirana-mcp:1.0.0 .
```

A host can run it directly, without the gateway, using flags that recreate the toolkit's safety defaults:

```json
{
  "mcpServers": {
    "kirana": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--cpus", "1", "--memory", "2g",
               "--read-only", "--network", "none", "kirana-mcp:1.0.0"]
    }
  }
}
```

| Flag | Why |
|---|---|
| `-i` | Keep stdin open; stdio servers read their messages from it |
| `--rm` | Delete the container when the host closes it |
| `--cpus 1 --memory 2g` | The same limits the toolkit uses |
| `--read-only` | The container can't modify its own filesystem |
| `--network none` | No network at all, for servers that don't need it (kirana's stock lives in the container; a real one would mount a data folder) |

Let's write a small helper that builds this command from a server's needs, so the safe defaults are the easy path and every exception is explicit:

```python
def docker_command(image, *, needs_network=False, mounts=(), env_names=(), cpus=1, memory="2g"):
    args = ["run", "-i", "--rm", "--cpus", str(cpus), "--memory", memory, "--read-only"]
    if not needs_network:
        args += ["--network", "none"]
    for host_path, container_path, mode in mounts:
        if mode not in ("ro", "rw"):
            raise ValueError("mount mode must be 'ro' or 'rw'")
        args += ["-v", f"{host_path}:{container_path}:{mode}"]
    for name in env_names:                     # pass the NAME only; the value comes from the host's env
        args += ["-e", name]
    return ["docker"] + args + [image]

print(" ".join(docker_command("kirana-mcp:1.0.0")))
print(" ".join(docker_command("notes-mcp:2.1.0", mounts=[("/Users/ramesh/notes", "/data", "ro")])))
print(" ".join(docker_command("mcp/github:latest", needs_network=True, env_names=["GITHUB_TOKEN"])))
```

Output:

```
docker run -i --rm --cpus 1 --memory 2g --read-only --network none kirana-mcp:1.0.0
docker run -i --rm --cpus 1 --memory 2g --read-only --network none -v /Users/ramesh/notes:/data:ro notes-mcp:2.1.0
docker run -i --rm --cpus 1 --memory 2g --read-only -e GITHUB_TOKEN mcp/github:latest
```

Two details matter. Every mount has to state its mode, so read-write access is a visible choice, and you mount only the folder the server needs. And `-e GITHUB_TOKEN` with no `=value` tells Docker to copy the value from the environment of whoever launches the container, so the token never sits in the config file.

### 7. Inside the gateway: one server made of many

The gateway's job is the host's job from the client lesson (merge, prefix, route), plus **inspection** of every call. Docker's toolkit, for example, blocks tool requests and responses that contain sensitive data such as secrets. Let's build a small gateway with the same shape: backends are plain functions here (in Docker they're containers), and an interceptor checks arguments on the way in and results on the way out.

```python
import json, re

SECRET_PATTERNS = {
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}

def find_secret(value):
    text = json.dumps(value)
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            return label
    return None

def github_backend(tool, args):
    if tool == "create_issue":
        return f"Created issue #412: {args['title']}"
    if tool == "read_file":
        return "PORT=8080\nDEPLOY_KEY=ghp_abcdefghijklmnopqrstuvwxyz123456"   # a careless .env file

def notes_backend(tool, args):
    return f"Saved note: {args['text']}"

class MiniGateway:
    def __init__(self, profile):
        self.routes = {}
        for server, (backend, tools) in profile.items():
            for tool in tools:
                self.routes[f"{server}__{tool}"] = (server, backend, tool)
        self.audit = []

    def tools_list(self):
        return sorted(self.routes)

    def call(self, name, args):
        server, backend, tool = self.routes[name]
        leak = find_secret(args)
        if leak:
            self.audit.append((name, f"blocked request: {leak}"))
            return {"isError": True, "text": f"Blocked: the arguments contain a {leak}."}
        result = backend(tool, args)
        leak = find_secret(result)
        if leak:
            self.audit.append((name, f"blocked response: {leak}"))
            return {"isError": True, "text": f"Blocked: the result contained a {leak} and was withheld."}
        self.audit.append((name, "ok"))
        return {"isError": False, "text": result}

gateway = MiniGateway({
    "github": (github_backend, ["create_issue", "read_file"]),
    "notes": (notes_backend, ["save_note"]),
})
print("tools:", gateway.tools_list())
print(gateway.call("github__create_issue", {"title": "Login button misaligned on mobile"}))
print(gateway.call("notes__save_note", {"text": "my token is ghp_ZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"}))
print(gateway.call("github__read_file", {"path": ".env"}))
print("audit:", gateway.audit)
```

Output:

```
tools: ['github__create_issue', 'github__read_file', 'notes__save_note']
{'isError': False, 'text': 'Created issue #412: Login button misaligned on mobile'}
{'isError': True, 'text': 'Blocked: the arguments contain a GitHub token.'}
{'isError': True, 'text': 'Blocked: the result contained a GitHub token and was withheld.'}
audit: [('github__create_issue', 'ok'), ('notes__save_note', 'blocked request: GitHub token'), ('github__read_file', 'blocked response: GitHub token')]
```

The second call shows the gateway stopping a model (or a prompt-injected instruction) from copying a token into a notes server, and the third shows it withholding a secret that a server returned by accident. Real gateways use far better detectors than three regular expressions, but the placement is the point: **one choke point sees every call to every server**, so policy and audit live in one place instead of in each host.

### 8. Where the Docker tools fit

| You want to... | Use |
|---|---|
| Try popular servers safely on your laptop | Catalog + Toolkit + gateway, one profile per project |
| Give a team the same set of tools | A shared profile (pushed to a registry or committed as a file) |
| Restrict a company to approved servers | A custom catalog, and gateways run from it |
| Ship your own server so it runs anywhere | A container image (stdio with `docker run -i`, or HTTP as in the remote lesson) |
| Serve many users over the network | A remote server deployment, not the local gateway |

---

## Try It Yourself

1. **A data-analysis profile.** Write the `docker mcp` commands to create a profile called `data-lab` with two servers from Docker's catalog of your choice, and the JSON a host needs to use it.
2. **A tighter command.** Use `docker_command` to build the command for an image `pdf-reader-mcp:0.4.0` that needs to read `/Users/priya/Downloads` but nothing else, and no network.
3. **Extend the gateway.** Add an allow-list to `MiniGateway` so only tools named in `allowed` can be called, and show a blocked call.

<details>
<summary>Show answers</summary>

**1.** For example, with two servers from the catalog listing (names vary; check `docker mcp catalog server ls`):

```bash
docker mcp profile create --name data-lab
docker mcp profile server add data-lab \
  --server catalog://mcp/docker-mcp-catalog/<server-one> \
  --server catalog://mcp/docker-mcp-catalog/<server-two>
```

```json
{"mcpServers": {"data-lab": {"command": "docker", "args": ["mcp", "gateway", "run", "--profile", "data-lab"]}}}
```

**2.**

```python
print(" ".join(docker_command("pdf-reader-mcp:0.4.0", mounts=[("/Users/priya/Downloads", "/data", "ro")])))
```

Output:

```
docker run -i --rm --cpus 1 --memory 2g --read-only --network none -v /Users/priya/Downloads:/data:ro pdf-reader-mcp:0.4.0
```

**3.**

```python
class AllowListGateway(MiniGateway):
    def __init__(self, profile, allowed):
        super().__init__(profile)
        self.allowed = set(allowed)

    def call(self, name, args):
        if name not in self.allowed:
            self.audit.append((name, "blocked: not on allow-list"))
            return {"isError": True, "text": f"{name} is not approved for this profile."}
        return super().call(name, args)

strict = AllowListGateway({"github": (github_backend, ["create_issue", "read_file"])},
                          allowed=["github__create_issue"])
print(strict.call("github__read_file", {"path": "README.md"}))
print(strict.call("github__create_issue", {"title": "Add Hindi translations"}))
```

Output:

```
{'isError': True, 'text': 'github__read_file is not approved for this profile.'}
{'isError': False, 'text': 'Created issue #412: Add Hindi translations'}
```

</details>

---

## Real-World Examples

- **Developers** use the Docker MCP Toolkit to try new servers from the catalog without installing Node or Python versions, and connect Claude Desktop, Cursor and VS Code to the same profile.
- **Teams** commit an exported profile to the repository so everyone's coding agent sees the same tools for that project.
- **Companies** publish a custom catalog of approved servers and point employees' gateways at it.
- **Server authors** ship images with the `io.modelcontextprotocol.server.name` label so the same image can be listed in the official MCP Registry and pulled by Docker tools.

---

## Common Misconceptions

### "A container makes a malicious server safe"

It limits what the server can reach on your machine. It doesn't stop it misusing the credentials you give it, or poisoning your model with its tool descriptions.

### "The gateway is a different protocol"

To your host, the gateway is an ordinary MCP server over stdio. To each container, it's an ordinary MCP client.

### "Sharing a profile shares my tokens"

Profiles don't include credentials. Each person configures their own.

### "The Docker catalog and the official MCP Registry are the same list"

They're separate catalogs with different submission processes. Many servers appear in both.

---

## Interview Relevance

*"How would you let developers use third-party MCP servers safely?"* A strong answer covers running servers in containers (no host files by default, CPU and memory limits, read-only mounts, no network unless needed), signed images with SBOMs, a gateway as one choke point that merges and routes tools, inspects requests and responses for secrets and logs every call, profiles per project, a custom catalog of approved servers, and the limits of isolation (credential misuse, tool poisoning). Mentioning `docker mcp gateway run --profile` and `docker mcp client connect` shows hands-on familiarity.

---

## Key Takeaways

- **The catalog provides servers as container images**; Docker-built ones in the `mcp` namespace are signed and come with an SBOM.
- **The toolkit and profiles** let you choose and configure servers once and group them per project.
- **The gateway is one MCP server in front of many containers**; hosts need a single `docker mcp gateway run --profile ...` entry.
- **Containers shrink the blast radius**: no host files by default, 1 CPU and 2 GB per tool container, explicit mounts and secrets.
- **A gateway is a policy choke point**: merge, route, block secrets, allow-list and audit in one place.

---

**Up next:** [Lab: Build and connect your own MCP server](lab-build-and-connect-your-own-mcp-server.md)
