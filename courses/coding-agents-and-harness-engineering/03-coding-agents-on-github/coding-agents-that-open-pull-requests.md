---
title: "Coding Agents that Open Pull Requests"
course: "Coding Agents and Harness Engineering"
module: "3. Coding Agents on GitHub"
type: Article
level: Intermediate
reading_time: 30 min
---

# Coding Agents that Open Pull Requests: The Complete Guide

> 📚 **Before you start**
>
> - [Copilot in the Editor and on GitHub](copilot-in-the-editor-and-on-github.md)
> - [Pull Requests End to End](../../git-and-github-zero-to-pro/course.md#m6) and [Branch Protection, Rulesets and CODEOWNERS](../../git-and-github-zero-to-pro/course.md#m6) (Collaborating on GitHub)
> - [Workflows, Jobs, Steps and Runners](../../git-and-github-zero-to-pro/07-github-actions/workflows-jobs-steps-and-runners.md), because the agent's environment is set up with a workflow file
> - [What is an AI Agent?](../../agentic-ai-fundamentals/02-understanding-agents/what-is-an-ai-agent.md) (Agentic AI Fundamentals)

## Introduction

Imagine handing a well-written ticket to a new team member at 6 p.m.: "the bill split loses a paisa; fix it in `billing.py`, add tests, don't change the API." The next morning there's a pull request waiting, with a description of what they did, the tests they ran, and commits you can review line by line. You comment "please also handle zero people"; an hour later the fix is pushed.

That's the workflow of a **cloud coding agent**. You assign it an issue or describe a task, it works on its own in a temporary cloud environment, and it delivers a **draft pull request** that goes through exactly the same review, CI and branch protection as a human's work. On GitHub, the built-in one is **Copilot cloud agent** (earlier docs and blog posts call it Copilot coding agent), and since GitHub's **Agent HQ** announcement in October 2025, third-party agents from Anthropic (Claude) and OpenAI (Codex) can be assigned work the same way.

By the end of this article you'll know how these agents work end to end, every way to start them, how to prepare a repository so they succeed (setup steps, firewall, MCP servers, secrets), the security protections built in, how to iterate on their pull requests, their limits and costs, and how to write tasks that agents can actually finish.

> 💡 **Key Insight**
>
> A coding agent is only as good as the **task**, the **environment** and the **review** around it. Pull requests are the right container for agent work because they bring all three: a written goal, CI that runs the real checks, and a human who approves. Treat the agent like a fast new teammate whose work always needs review, never like a merge button.

---

## Core Explanation

### 1. IDE Agents versus Cloud Agents

| | Agent mode / Copilot CLI | Cloud coding agent |
|---|---|---|
| Runs on | Your machine | An ephemeral cloud environment GitHub manages |
| You | Watch and approve step by step | Hand off and review the result |
| Output | Changes in your working tree | Commits on a branch and a draft pull request |
| Best for | Exploratory or interactive work | Well-defined tasks: bugs, tests, small features, refactors, docs |
| Parallelism | One session at a time, in practice | Many tasks at once, each in its own environment |

### 2. The Lifecycle of an Agent Task

```mermaid
sequenceDiagram
  actor Dev as Developer
  participant GH as GitHub
  participant Ag as Cloud agent
  participant CI as CI workflows
  Dev->>GH: Assign issue to Copilot (or prompt in Agents tab)
  GH->>Ag: Start session in ephemeral environment
  Ag->>Ag: Run copilot-setup-steps, explore repo, plan
  Ag->>GH: Push commits to a copilot/ branch, open draft PR
  Ag->>Ag: Edit, run tests and linters, self-review, security checks
  Ag->>GH: Update PR description, request review
  Dev->>GH: Click "Approve and run workflows"
  GH->>CI: Run required checks
  Dev->>GH: Review, comment "@copilot handle zero people"
  GH->>Ag: New session on the same branch
  Ag->>GH: Push follow-up commit
  Dev->>GH: Approve (a different person from the requester) and merge
```

### 3. Starting a Task

Copilot cloud agent is available on all paid Copilot plans, in repositories on GitHub (not those owned by managed user accounts, or where an admin has disabled it). You can start it from many places:

- **An issue:** open the issue, click **Assignees**, choose **Copilot**. The "Assign to Copilot" dialog lets you add an optional prompt with extra context, pick the repository and **base branch**, choose a **custom agent**, and choose a **model** (and reasoning level where supported).
- **The Agents tab** in a repository, the agents panel (the agents icon in the top navigation bar), or `github.com/copilot/agents`: pick a repository, type the task, press Enter.
- **Copilot Chat** on GitHub, the **dashboard**, a **new repository**, or a **failing Actions run** ("fix this").
- **IDEs** (VS Code, JetBrains, Eclipse, Visual Studio), **GitHub Mobile** and **Raycast**.
- **The GitHub CLI:**

```bash
gh agent-task create "Make split_bill() shares add up exactly; add tests" --base main --follow
gh agent-task list
gh agent-task view 57 --log
```

  These commands need GitHub CLI 2.80.0 or later and are in public preview.

- **The REST API** and **the GitHub MCP server**, so another agent can delegate to Copilot.
- **Integrations** with Jira, Slack, Microsoft Teams, Azure Boards and Linear.
- **Automations:** sessions that start on a schedule or in response to repository events, such as an issue being opened.

When Copilot starts on your comment or issue, a 👀 reaction appears, and a "Copilot has started work" event shows in the timeline.

### 4. What the Agent Does While It Works

Inside its environment, the agent:

1. Clones the repository and runs your **setup steps** (section 6).
2. Reads the issue, your prompt, repository **instructions** and relevant code.
3. Plans, edits files, runs tests and linters, and iterates on failures.
4. Runs **validation tools** by default: CodeQL for code security issues, a check of new dependencies against the GitHub Advisory Database (malware and high or critical vulnerabilities), secret scanning, and a second opinion from Copilot code review. It tries to fix what they find before finishing. Repository admins can turn individual tools off under **Settings → Copilot → Cloud agent**.
5. Pushes commits to its branch and keeps the pull request description up to date, then requests your review.

You can follow along in the **session logs**, opened from the pull request or the Agents tab. Teammates with access can view shared sessions. Each commit message links back to the session that produced it.

### 5. Built-in Protections

GitHub designed the agent so its work can't bypass your normal controls:

| Protection | What it means |
|---|---|
| **Only writers can trigger it** | Only users with write access can assign tasks; comments from other users are never shown to the agent |
| **One branch only** | It pushes to a new `copilot/...` branch, or to the existing PR branch it was mentioned on, using simple pushes only |
| **Branch protection applies** | Rulesets, required checks and reviews all still apply; incompatible rules can block it unless admins add Copilot as a bypass actor |
| **Draft PRs, human merges** | It can't mark a PR ready, approve or merge |
| **No self-approval** | The person who asked for the PR can't approve it; if the repo requires approvals, an agent PR needs one more independent approval |
| **Workflows wait** | CI on its pushes waits until someone with write access clicks **Approve and run workflows** (admins can change this) |
| **Restricted internet** | An integrated firewall limits network access (section 7) |
| **Hidden-text filtering** | Hidden characters and HTML comments in issues and PRs aren't passed to it, a defence against hidden prompt injection |
| **Auditable** | Commits are authored by Copilot with the requester as co-author, signed and shown as Verified; session logs and audit log events are kept |

The "workflows wait" rule matters more than it looks. An agent PR can change files under `.github/workflows/`. If CI ran automatically, unreviewed code would run with your Actions secrets and token. Look at workflow changes before you click approve.

### 6. Preparing the Environment: `copilot-setup-steps.yml`

The agent works in an ephemeral environment powered by GitHub Actions. By default it tries to discover and install your dependencies itself, which is slow and error-prone. Tell it exactly how, with a special workflow file on the **default branch** at `.github/workflows/copilot-setup-steps.yml`:

```yaml
name: "Copilot Setup Steps"

# Lets you test the setup from the Actions tab and on changes to this file.
on:
  workflow_dispatch:
  push:
    paths: [.github/workflows/copilot-setup-steps.yml]
  pull_request:
    paths: [.github/workflows/copilot-setup-steps.yml]

jobs:
  # The job MUST be called copilot-setup-steps.
  copilot-setup-steps:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      contents: read
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_PASSWORD: postgres
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
          cache: pip
      - name: Install project and dev tools
        run: python -m pip install -e ".[test]" ruff
      - name: Prepare the database
        run: python scripts/create_test_db.py
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/postgres
```

Rules for this file:

- It must contain a single job named exactly **`copilot-setup-steps`**, and it only takes effect from the **default branch**.
- Only these job keys are honoured: `steps`, `permissions`, `runs-on`, `services`, `snapshot` and `timeout-minutes` (at most 59). Anything else is ignored. Any `fetch-depth` you give `actions/checkout` is overridden.
- If a step fails, the agent skips the rest of the steps and starts work from whatever state the environment is in.
- `runs-on` can name a **larger runner** for heavy builds (Ubuntu x64 and Windows x64 are supported, macOS isn't) or an ephemeral **self-hosted** runner set (for example via Actions Runner Controller), in which case you must turn off the integrated firewall and control network access yourself.

Because it's a normal workflow, you can run it from the Actions tab to check it works before the agent ever uses it.

### 7. Network Access, Secrets and MCP Servers

**Firewall.** By default the agent's internet access is restricted to an allowlist that covers common package registries and the services it needs. If your build downloads from somewhere else (a private package index, a model hub), add it to the custom allowlist in **Settings → Copilot → Cloud agent**. Keep the list short: every allowed host is a place a prompt-injected agent could send data.

**Secrets and variables.** Give the agent credentials through **Settings → Secrets and variables → Agents** (repository) or the same path in organization settings. They're exposed as environment variables to the setup steps and the tools the agent runs, and masked in session logs. Actions, Codespaces and Dependabot secrets are **not** passed to the agent.

**MCP servers** give the agent extra tools, such as your issue tracker, error monitoring or internal docs. The **GitHub MCP server** is on by default, with a token that can only **read** the current repository. Add others as JSON under **Settings → Copilot → MCP servers**:

```json
{
  "mcpServers": {
    "sentry": {
      "type": "http",
      "url": "https://mcp.sentry.example/mcp",
      "headers": { "Authorization": "Bearer $COPILOT_MCP_SENTRY_TOKEN" },
      "tools": ["get_issue", "search_issues"]
    },
    "docs": {
      "type": "local",
      "command": "npx",
      "args": ["-y", "@chai-co/docs-mcp"],
      "env": { "DOCS_API_KEY": "$COPILOT_MCP_DOCS_API_KEY" },
      "tools": ["*"]
    }
  }
}
```

Only Agents secrets whose names start with **`COPILOT_MCP_`** can be referenced in this configuration. List specific `tools` rather than `"*"` when you can: the agent uses tools autonomously, without asking you first.

### 8. Iterating on the Pull Request

Review an agent's pull request like any other, then steer it with comments:

- Comment **`@copilot`** with what to change, on the PR or as review comments on specific lines. Copilot pushes commits to the same branch by default; ask explicitly if you want a separate pull request.
- Batch your feedback into one review rather than many single comments, so it works on everything at once.
- Only people with write access get a response.
- If the task went wrong from the start, close the PR and start a fresh, better-specified task rather than coaching it through a bad approach.

When you're satisfied: approve and run workflows, wait for green checks, get the required approval from someone other than the requester, mark ready for review, and merge.

### 9. Third-Party Agents: Claude and Codex

Through Agent HQ, the **Anthropic Claude** and **OpenAI Codex** coding agents run on GitHub with the same security protections as Copilot cloud agent (third-party agents are in public preview). To use them:

1. An admin (or you, on a personal Pro, Pro+ or Max plan) enables **"Allow Claude coding agent"** or **"Allow Codex coding agent"** in the Copilot cloud agent policy settings. This installs the agent's GitHub App.
2. Start a task by selecting the agent below the prompt box in the **Agents** tab, by **assigning** an existing issue to it, or from VS Code and GitHub Mobile.
3. Ask for changes on its pull requests by mentioning it in a comment, `@AGENT_NAME`.

Sessions consume GitHub Actions minutes and AI credits like Copilot's own agent. The practical upshot: you can give different agents different tasks, or the same task, and compare the pull requests.

### 10. Custom Agents

A **custom agent** is a specialised version of the cloud agent with its own instructions and tool set, defined as a Markdown file in `.github/agents/` with the `.agent.md` extension:

```markdown
---
name: test-writer
description: Writes and improves pytest tests without changing production code
tools: ["read", "search", "edit", "shell"]
---

You only add or improve tests under tests/. Never edit files under src/.
Use pytest parametrize for tables of cases. Money is always Decimal.
Run `python -m pytest -q` before finishing and include the summary in the PR description.
```

`description` is required; `name` defaults to the file name. `tools` limits what it can use (omit it to allow everything), `mcp-servers` gives it its own MCP servers, and `target` can restrict it to `vscode` or `github-copilot`. Organizations can share agents from the `agents/` folder of their `.github` (or `.github-private`) repository. You pick a custom agent from the agent dropdown when assigning an issue or starting a task.

### 11. Limits and Costs

- **One repository per task**: changes are limited to the repository named when the task starts.
- **One branch, one pull request** per task.
- **59 minutes** maximum per session.
- Only repositories **hosted on GitHub**.
- Sessions consume **GitHub Actions minutes** and **AI credits** according to your plan.

### 12. Writing Tasks Agents Can Finish

The most important skill is writing the task. A vague issue gets a confident, wrong pull request. Here's a quick heuristic check you could even run as an issue-form bot:

```python
import re

CHECKS = {
    "states the goal": lambda t: len(t.split()) >= 12,
    "names files or areas": lambda t: bool(re.search(r"[\w/]+\.(py|ts|js|md|yml|sql)\b|src/|tests/", t)),
    "has acceptance criteria": lambda t: bool(re.search(r"(?im)^\s*(- \[ \]|acceptance|done when)", t)),
    "says how to test": lambda t: bool(re.search(r"pytest|npm test|make test|run the tests", t, re.I)),
    "sets limits": lambda t: bool(re.search(r"(?i)\b(don't|do not|only|without)\b", t)),
}

def agent_readiness(issue_text):
    passed = [name for name, check in CHECKS.items() if check(issue_text)]
    missing = [name for name in CHECKS if name not in passed]
    return len(passed), missing

vague = "Fix the bill bug"
good = """Bill splitting loses a paisa when the total doesn't divide evenly.
In src/chai_bill/billing.py, make split_bill() return shares that add up exactly.
Do not change the function signature.
Done when:
- [ ] split_bill(100, 3) returns 33.34, 33.33, 33.33
- [ ] new cases in tests/test_billing.py pass with pytest
"""
for name, text in [("vague", vague), ("good", good)]:
    score, missing = agent_readiness(text)
    print(f"{name}: {score}/{len(CHECKS)} missing={missing}")
```

Output:

```
vague: 0/5 missing=['states the goal', 'names files or areas', 'has acceptance criteria', 'says how to test', 'sets limits']
good: 5/5 missing=[]
```

Good agent tasks are like good tickets for a new joiner: **the goal, where to look, what "done" means, how to verify it, and what not to touch.** Good candidates: well-scoped bugs, adding tests, small features with clear behaviour, dependency upgrades with failing tests to fix, documentation, and mechanical refactors. Poor candidates: vague redesigns, work needing production access, and changes that need judgement calls only a human stakeholder can make.

---

## Try It Yourself

1. **Rewrite the task.** Turn "dark mode doesn't work" into an agent-ready issue, and check it with `agent_readiness`.
2. **Setup steps.** Write a `copilot-setup-steps.yml` job for a Node 22 project that uses `npm ci` and needs Redis running.
3. **Who approves?** Priya assigned an issue to Copilot. The repository requires one approval. Can Priya approve the resulting PR? What happens if she's the only maintainer?
4. **Spot the risk.** An agent PR modifies `.github/workflows/deploy.yml` to add a step that `curl`s an unfamiliar URL. What protects you, and what should you do?

<details>
<summary>Show answers</summary>

**1.**

```python
issue = """Dark mode loses the user's choice after a page reload.
In site/src/theme.ts, save the chosen theme to localStorage and read it on load.
Only change theme.ts and its tests; do not add dependencies.
Done when:
- [ ] reloading keeps the chosen theme
- [ ] npm test passes, including a new test in site/src/theme.test.ts
"""
print(agent_readiness(issue))
```

Output:

```
(5, [])
```

**2.**

```yaml
name: "Copilot Setup Steps"
on: workflow_dispatch
jobs:
  copilot-setup-steps:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    services:
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version: 22
          cache: npm
      - run: npm ci
```

**3.** No. The person who asked the agent to create the PR can't approve it. Another person with write access must approve; a solo maintainer would need to adjust the rule (for example, the ruleset setting for extra approvals on agent PRs) or add a second reviewer.

**4.** CI doesn't run until someone with write access clicks "Approve and run workflows", so the new step hasn't run yet. Don't approve the workflows. Ask the agent (or do it yourself) to remove the step, and investigate where that URL came from, since it may indicate prompt injection from issue text, a dependency or a web page.

</details>

---

## Real-World Examples

### Example 1: Clearing the Test Backlog

A payments team had 60 small "add tests for X" issues. They wrote a `test-writer` custom agent that may only edit `tests/`, then assigned ten issues a day to it. Reviewers merged most within minutes because the diffs were small, confined and covered by CI.

### Example 2: Fix the Failing Run

A developer sees a red nightly build caused by a deprecated API in a dependency upgrade. From the failed run, they ask Copilot to fix it. A draft PR arrives with the migration and passing tests; a teammate approves it.

### Example 3: Comparing Agents

An open source maintainer assigns the same tricky parser bug to Copilot and to the Claude agent. One PR is cleaner; the other has a better test. The maintainer merges one and cherry-picks the test from the other.

---

## Common Misconceptions

### Misconception 1: "The agent merges its own work"

It can't mark PRs ready, approve or merge. A human always does, and not the person who requested it.

### Misconception 2: "It has full internet and all my secrets"

Network access is firewalled to an allowlist, and it only gets Agents secrets you explicitly add. Actions secrets aren't passed to it.

### Misconception 3: "A better model fixes vague tasks"

Clear goals, acceptance criteria and setup steps matter more than model choice for most tasks.

### Misconception 4: "Agent PRs need lighter review because they pass CI"

CI only checks what your tests cover. Review agent PRs at least as carefully as a new contributor's, especially changes to workflows, dependencies and security-sensitive code.

---

## Interview Relevance

Expect questions like "how would you introduce coding agents to a team safely?":

- **Workflow:** issue or prompt → agent works in an ephemeral environment → draft PR on its own branch → CI → human review → merge.
- **Environment as code:** `copilot-setup-steps.yml` (one job named `copilot-setup-steps`, limited keys, default branch), firewall allowlist, Agents secrets, MCP servers with `COPILOT_MCP_` secrets.
- **Controls:** write-access triggers only, branch protection, no self-approval, workflow approval, validation tools, audit logs.
- **Task design:** goal, location, acceptance criteria, test command, limits.
- **Ecosystem:** third-party agents (Claude, Codex) and custom agents.

Common follow-ups:

- *"What's the prompt injection risk?"* Malicious text in issues, code or fetched pages can steer the agent; mitigations are hidden-text filtering, a firewall, limited tools and secrets, workflow approval and human review.
- *"When wouldn't you use a cloud agent?"* Vague or judgement-heavy work, tasks needing production access, or anything you can't verify with tests and review.

---

## Key Takeaways

- **Cloud coding agents turn tasks into draft pull requests**, so their work flows through your normal CI and review.
- **Start tasks from issues, the Agents tab, chat, IDEs, `gh agent-task`, the API, MCP or automations**; iterate with `@copilot` comments.
- **Prepare the environment** with `copilot-setup-steps.yml`, a tight firewall allowlist, Agents secrets and MCP servers.
- **Protections are built in**: writers-only triggers, one branch, no self-approval, workflow approval, validation tools, signed and auditable commits.
- **Third-party (Claude, Codex) and custom agents** extend the same model; **well-written tasks** matter more than anything else.

---

**Up next:** [Repository Instructions: AGENTS.md and Custom Instructions](repository-instructions-agents-md-and-custom-instructions.md)
