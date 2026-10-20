---
title: "Subagents, Slash Commands and Plugins"
course: "Coding Agents and Harness Engineering"
module: "4. What a Harness Is"
type: Article
level: Advanced
reading_time: 32 min
---

# Subagents, Slash Commands and Plugins: The Complete Guide

> 📚 **Before you start**
>
> - [Permissions, Hooks and Approval Modes](permissions-hooks-and-approval-modes.md), because subagents and plugins carry their own tools, permissions and hooks
> - [Offloading Context to Files and Scratchpads](../../context-engineering-and-agent-memory/03-just-in-time-context/offloading-context-to-files-and-scratchpads.md), whose section on sub-agents explains why isolating heavy reading saves the main context
> - [Skills vs MCP vs Subagents vs Prompts](../../tools-agent-skills-and-code-execution/course.md#m4) (Tools, Agent Skills and Code Execution), which compares these extension types in general; this lesson shows how coding agents implement them
> - [Orchestrator and Subagents](../../multi-agent-systems-and-agent-protocols/course.md#m2) (Multi-Agent Systems and Agent Protocols), for the general multi-agent pattern

## Introduction

A head chef in a busy Bengaluru restaurant doesn't chop every onion. She sends one assistant to check the cold store and report what's left, another to prepare the chutneys exactly as the recipe card says, and she keeps her own attention on the plates going out. The assistants come back with short answers ("12 kg paneer, no coriander"), not a tour of the cold store. The kitchen also has laminated recipe cards anyone can call up by name ("make the Sunday thali"), and when the restaurant opens a second branch, the whole kit of recipes, assistants' roles and kitchen rules is packed up and shipped together.

Coding agents have the same three tools. **Subagents** are assistants with their own fresh context and limited tools, who come back with a summary. **Slash commands** are saved prompts and workflows you trigger by name. **Plugins** package subagents, commands, skills, hooks and MCP servers into one installable unit that a whole team can share.

By the end of this lesson you'll know when a subagent helps and when it just burns tokens, how to define subagents in Claude Code, Codex and Gemini CLI, how built-in subagents like `Explore` work, how to run subagents in parallel and in isolated worktrees, how custom commands work (and why in Claude Code they've merged into skills), and how plugins and marketplaces package all of it.

> 💡 **Key Insight**
>
> A subagent's real product is a **clean context**: it does the messy reading or the narrow job in its own window and hands back only the conclusion. Use one when the *work* is big but the *answer* is small, or when you want a fresh, unbiased pair of eyes. Commands and plugins are about **reuse**: write a good workflow once, and share it with everyone.

---

## Core Explanation

### 1. What a subagent is, mechanically

When the main agent delegates, the harness starts a **new agent loop** with:

- its own **system prompt** (the subagent definition's body), not the main conversation's history;
- its own **tool list**, often narrower (an explorer can read but not edit);
- optionally its own **model**, permission mode, hooks, MCP servers and skills;
- a **task description** written by the main agent.

The subagent works until it's done and returns a final message. **Only that message** goes back into the main context. All its file reads and command output stay in its own transcript.

```mermaid
sequenceDiagram
  participant M as Main agent (your session)
  participant H as Harness
  participant S as Explore subagent (fresh context, read-only tools)
  M->>H: Agent tool: "Find every place we parse dates; report file:line and format"
  H->>S: new loop: subagent system prompt + task
  loop 40 tool calls, 60k tokens of file contents
    S->>H: Grep / Glob / Read
    H-->>S: results
  end
  S-->>H: "7 parsers found: (list). 3 use day-first format."
  H-->>M: the 1-paragraph summary only
```

### 2. When a subagent helps, and when it hurts

```python
def main_context_cost(task_reads_tokens, summary_tokens, use_subagent, overhead=3_000):
    """Tokens added to the MAIN context, and total tokens processed."""
    if use_subagent:
        return summary_tokens, task_reads_tokens + summary_tokens + overhead
    return task_reads_tokens, task_reads_tokens

for name, reads, summary in [("find all date parsers", 60_000, 600),
                             ("read one 200-line file", 2_500, 2_000)]:
    for sub in (False, True):
        main, total = main_context_cost(reads, summary, sub)
        print(f"{name:<24} subagent={str(sub):<5}  main context +{main:>6,}  total processed {total:>6,}")
```

Output:

```
find all date parsers    subagent=False  main context +60,000  total processed 60,000
find all date parsers    subagent=True   main context +   600  total processed 63,600
read one 200-line file   subagent=False  main context + 2,500  total processed  2,500
read one 200-line file   subagent=True   main context + 2,000  total processed  7,500
```

Two lessons from four lines:

- **Subagents protect the main context; they don't save total tokens.** The date-parser search keeps 59,400 tokens out of your session, but costs slightly *more* overall.
- **For small jobs they're pure overhead.** Reading one file through a subagent triples the cost for almost no context saving.

| Use a subagent | Don't |
|---|---|
| Wide searches and investigations ("where is X used?") | Reading one or two known files |
| A **fresh-eyes review** of a diff, without the reasoning that produced it | Tasks needing the whole conversation's nuance |
| A narrow role with **restricted tools** (read-only explorer, test-only writer) | Tightly coupled edits to the same files as the main agent |
| **Parallel** independent tasks (one per module) | Work where every step depends on the previous |
| A cheaper or faster **model** for simple jobs | When latency matters more than context |

### 3. Built-in subagents

You get useful subagents without writing any:

| Tool | Built-ins | Notes |
|---|---|---|
| Claude Code | `Explore` (fast, read-only search), `Plan` (research during plan mode), `general-purpose` | `Explore` and `Plan` start without your `CLAUDE.md` to stay fast and cheap; Claude asks `Explore` for a thoroughness level (quick, medium, very thorough) |
| Codex | `default`, `worker` (implementation and fixes), `explorer` (read-heavy exploration) | A custom agent with the same name overrides the built-in |
| Gemini CLI | `codebase_investigator`, `generalist`, `cli_help` (plus a `browser_agent`, off by default) | Enabled by default |

Prompting for them is plain language: *"Use a subagent to find every caller of `split_bill` and summarise how each uses it."*

### 4. Defining your own subagents

**Claude Code**: a Markdown file in `.claude/agents/` (project) or `~/.claude/agents/` (personal). Only `name` and `description` are required; the body is the subagent's system prompt:

```markdown
---
name: test-reviewer
description: Reviews test changes in a diff. Use after tests are added or modified, before committing.
tools: Read, Grep, Glob, Bash
disallowedTools: Edit, Write
model: sonnet
maxTurns: 20
---

You review tests, not production code. For each changed test file:
1. Check every new test has exact expected values, not just "is not None" or "> 0".
2. Flag tests whose expected values were changed in the same diff as the code they test.
3. Flag new skip markers.
Run `python -m pytest -q` once. Report findings as file:line, problem, suggested fix.
Report only problems that would let a bug through. No style comments.
```

Other useful fields: `permissionMode`, `skills` (preloaded in full), `mcpServers`, `hooks`, `memory` (persistent memory across sessions), `background: true`, `effort`, and `isolation: worktree`, which gives the subagent its own temporary git worktree so its edits can't collide with yours (Module 5 builds on this). Claude Code silently skips a file whose front matter has no `name`, a name containing `:`, or no `description`, so a typo can make your agent vanish; `claude --debug` shows why.

**Codex**: one TOML file per agent in `.codex/agents/` (or `~/.codex/agents/`). Required fields are `name`, `description` and `developer_instructions`:

```toml
# .codex/agents/test-reviewer.toml
name = "test-reviewer"
description = "Reviews test changes in a diff before committing."
developer_instructions = """
You review tests, not production code. Flag weak assertions, tests changed alongside the code
they test, and new skip markers. Report file:line, problem, fix. No style comments.
"""
model_reasoning_effort = "high"
```

A Codex custom agent can't override `sandbox_mode`, `approval_policy` or `mcp_servers`; those come from the parent session, so a subagent can't grant itself more power than you gave the session.

**Gemini CLI**: Markdown with front matter in `.gemini/agents/*.md`, with `name`, `description`, and optional `tools`, `model`, `max_turns` (default 30) and `timeout_mins` (default 10).

The **description is the routing signal**: the main agent decides whether to delegate by reading it, exactly as with skills. Say *what it does and when to use it*. A toy router shows why vague descriptions lose:

```python
import re

AGENTS = {
    "test-reviewer": "Reviews test changes in a diff. Use after tests are added or modified, before committing.",
    "db-migrator": "Writes and checks database migrations with alembic. Use for any schema change.",
    "helper": "Helps with things.",
}

def words(text):
    return set(re.findall(r"[a-z]+", text.lower())) - {"a", "the", "for", "with", "use", "any", "in", "and"}

def route(task):
    scores = {name: len(words(task) & words(desc)) for name, desc in AGENTS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "(no delegation)", scores

for task in ["Check the tests I modified before committing", "Add a column for GST number to the schema",
             "Make it better"]:
    choice, scores = route(task)
    print(f"{task:<46} -> {choice:<16} {scores}")
```

Output:

```
Check the tests I modified before committing   -> test-reviewer    {'test-reviewer': 4, 'db-migrator': 0, 'helper': 0}
Add a column for GST number to the schema      -> db-migrator      {'test-reviewer': 0, 'db-migrator': 1, 'helper': 0}
Make it better                                 -> (no delegation)  {'test-reviewer': 0, 'db-migrator': 0, 'helper': 0}
```

Real models match meaning, not words, but the lesson holds: `helper` never wins anything, and a delegation decision is only as good as the descriptions. (The wording rules from [Writing Descriptions that Trigger Correctly](../../tools-agent-skills-and-code-execution/course.md#m4) apply unchanged.)

### 5. Running subagents: foreground, background, parallel, isolated

| Pattern | How | Watch out for |
|---|---|---|
| **Foreground** | Main agent waits for the result | Simple; blocks the session |
| **Background** | Subagent runs while you keep working (`background: true` in Claude Code) | Results arrive later; don't edit the same files meanwhile |
| **Parallel fan-out** | Several subagents on independent pieces at once | Total cost multiplies; merge conflicts if pieces overlap |
| **Worktree isolation** | Each subagent edits in its own git worktree (`isolation: worktree`) | Changes must be merged back; setup per worktree |
| **Fork** | A subagent that starts with a **copy** of the current conversation | Inherits context (and its biases); useful for "try another approach" |

Claude Code's bundled `/batch <instruction>` skill is the fan-out pattern packaged: it researches the codebase, splits a large change into 5 to 30 independent units, and gives each to a subagent in its own worktree. Beyond subagents, Claude Code also has experimental **agent teams** (several full sessions with shared tasks and messaging) and **dynamic workflows** (a script Claude writes to orchestrate many subagents). These are multi-agent orchestration, which [Multi-Agent Systems and Agent Protocols](../../multi-agent-systems-and-agent-protocols/course.md) covers in general and [Parallel Agents with Worktrees](../05-long-running-agents/parallel-agents-with-worktrees.md) applies to coding.

### 6. Slash commands: saved workflows you trigger by name

Every coding agent has **built-in** commands. A few in Claude Code that you'll use constantly:

| Command | Does |
|---|---|
| `/init` | Generate a starter `CLAUDE.md` for the project |
| `/context` | Show what's using the context window |
| `/compact [focus]` | Summarise the conversation to free space |
| `/clear` | Start a fresh conversation |
| `/rewind` | Restore code and/or conversation to an earlier point |
| `/permissions`, `/hooks`, `/sandbox` | Inspect and change the controls from the previous lesson |
| `/plugin` | Browse, install and manage plugins |
| `/code-review` | Review the current diff (or a PR) in a fresh subagent |
| `/goal <condition>` | Keep working across turns until a condition is met |

**Custom commands** are your own reusable prompts. In Claude Code, custom commands have **merged into skills**: a file at `.claude/commands/fix-issue.md` and a skill at `.claude/skills/fix-issue/SKILL.md` both create `/fix-issue`. Skills add supporting files and let Claude load them automatically when relevant; for a workflow that should only run when *you* ask, set `disable-model-invocation: true`:

```markdown
---
name: fix-issue
description: Fix a GitHub issue end to end
disable-model-invocation: true
argument-hint: "<issue-number>"
---

Fix GitHub issue $ARGUMENTS:
1. Read it with `gh issue view $ARGUMENTS`.
2. Explore the relevant code; write a short plan in PLAN.md and stop for my approval.
3. After approval, implement with tests; run `python -m pytest -q` until green.
4. Commit with a message referencing the issue, push a branch, and open a draft PR.
```

Typing `/fix-issue 212` substitutes `212` for `$ARGUMENTS`. Other agents have the same idea in their own format: **Gemini CLI** reads TOML commands from `.gemini/commands/` with a `prompt` field and a `{{args}}` placeholder (`git/commit.toml` becomes `/git:commit`), and **Copilot** has prompt files in `.github/prompts/*.prompt.md`.

A tiny version of what the harness does when you type a command:

```python
COMMANDS = {
    "fix-issue": "Fix GitHub issue $ARGUMENTS:\n1. Read it with `gh issue view $ARGUMENTS`.\n2. Plan, then stop for approval.",
    "review-tests": "Use the test-reviewer subagent on the current diff.",
}

def expand(user_input):
    if not user_input.startswith("/"):
        return user_input
    name, _, args = user_input[1:].partition(" ")
    if name not in COMMANDS:
        return f"Unknown command /{name}"
    body = COMMANDS[name]
    if args and "$ARGUMENTS" not in body:
        body += f"\n\nARGUMENTS: {args}"          # the documented fallback when there's no placeholder
    return body.replace("$ARGUMENTS", args)

print(expand("/fix-issue 212"))
print("---")
print(expand("/review-tests focus on refunds"))
```

Output:

```
Fix GitHub issue 212:
1. Read it with `gh issue view 212`.
2. Plan, then stop for approval.
---
Use the test-reviewer subagent on the current diff.

ARGUMENTS: focus on refunds
```

Commands are **guides** in the vocabulary of the first lesson: they make good practice the path of least resistance. A team that has `/fix-issue` will plan and test more consistently than one that relies on everyone typing good prompts.

### 7. Plugins: packaging the whole kit

Once a team has subagents, commands, skills, hooks and MCP servers it likes, copying them repo to repo gets messy. A **plugin** packages them as one versioned, installable unit. A Claude Code plugin is a directory:

```
chai-team-plugin/
├── .claude-plugin/
│   └── plugin.json            # name (required), description, version
├── skills/
│   └── fix-issue/SKILL.md     # becomes /chai-team-plugin:fix-issue
├── agents/
│   └── test-reviewer.md       # becomes chai-team-plugin:test-reviewer
├── hooks/
│   └── hooks.json             # e.g. format after every edit
├── scripts/
│   └── format.sh              # referenced as ${CLAUDE_PLUGIN_ROOT}/scripts/format.sh
└── .mcp.json                  # MCP servers the plugin starts
```

```json
{
  "name": "chai-team-plugin",
  "description": "Chai Co. engineering workflow: issue fixing, test review, formatting hooks",
  "version": "1.4.0"
}
```

Plugins are distributed through **marketplaces**: a repository with a `.claude-plugin/marketplace.json` that lists plugins and where to fetch them. Claude Code adds Anthropic's official marketplace automatically; you add others yourself:

```bash
claude plugin marketplace add anthropics/claude-plugins-official
/plugin install commit-commands@claude-plugins-official          # inside a session
claude plugin install chai-team-plugin@chai-co --scope project     # from the shell, for this repo
claude --plugin-dir ./chai-team-plugin                             # load a local plugin while developing it
```

Other agents converged on the same idea: Codex has plugins and skills, Gemini CLI had **extensions**, and Google's Antigravity CLI calls them plugins too.

Three things to know before installing any plugin:

- **It runs as you.** Hooks and MCP servers from a plugin execute with your permissions. Read a plugin (especially its hooks and scripts) before installing it, as you would any dependency; [Supply Chain: Malicious MCP Servers and Skills](../../agent-security-and-safety/course.md#m3) goes deeper.
- **It costs context in every session.** The name and description of every skill, agent and command a plugin adds are in the model's context on every turn while it's enabled. Disable plugins you don't use.
- **Pin versions** for team plugins, so an update doesn't change everyone's agent behaviour overnight.

```python
def plugin_context_cost(plugins):
    """Rough per-turn cost of always-visible names + descriptions (about 60 tokens each)."""
    return {name: items * 60 for name, items in plugins.items()}

installed = {"chai-team-plugin": 6, "giant-everything-plugin": 85, "commit-commands": 3}
costs = plugin_context_cost(installed)
for name, tokens in sorted(costs.items(), key=lambda kv: -kv[1]):
    print(f"{name:<24} ~{tokens:>5,} tokens on every turn")
```

Output:

```
giant-everything-plugin  ~5,100 tokens on every turn
chai-team-plugin         ~  360 tokens on every turn
commit-commands          ~  180 tokens on every turn
```

(The 60-token figure is a rough illustration; Claude Code's `/plugin` shows a context-cost estimate for official-marketplace plugins, and `/context` shows the real numbers in your session.)

### 8. Choosing the right extension

| You want | Use |
|---|---|
| Knowledge every task needs | Instruction file (`AGENTS.md`, `CLAUDE.md`) |
| A procedure some tasks need, loaded on demand | Skill |
| A procedure you trigger by name | Command (a skill with `disable-model-invocation: true` in Claude Code) |
| Heavy reading or a fresh, restricted helper | Subagent |
| Something that must *always* happen | Hook |
| An outside system (issues, browser, database) | MCP server |
| All of the above, shared across repos and people | Plugin |

---

## Try It Yourself

1. **Worth it?** Use `main_context_cost` for a task that reads 15,000 tokens and returns a 4,000-token answer. Would you use a subagent?
2. **Fix the description.** Rewrite `helper`'s description so the router sends "Make it better" somewhere sensible, or argue why it shouldn't be delegated at all.
3. **Write a command.** Create a `COMMANDS` entry `release-notes` that takes a tag (`/release-notes v1.4.0`) and asks the agent to summarise merged PRs since that tag. Expand it.
4. **Audit a plugin.** List four things you'd check in a plugin before running `claude plugin install` for your whole team.

<details>
<summary>Show answers</summary>

**1.**

```python
print(main_context_cost(15_000, 4_000, False), main_context_cost(15_000, 4_000, True))
```

Output:

```
(15000, 15000) (4000, 22000)
```

It saves 11,000 tokens of main context for 7,000 extra total. Worth it if the session is long and context is precious, or if you want a fresh-eyes view; otherwise probably not. A large answer shrinks the benefit, so ask the subagent for a tighter summary.

**2.** "Make it better" names no task, so the right outcome is *no* delegation: the main agent should ask what "better" means. A good `helper` would instead be specific, for example "Refactors one function for readability without changing behaviour. Use when asked to tidy or simplify a named function."

**3.**

```python
COMMANDS["release-notes"] = ("Summarise pull requests merged since $ARGUMENTS. Run "
                             "`git log $ARGUMENTS..HEAD --merges --oneline`, group by label, "
                             "write RELEASE_NOTES.md and stop.")
print(expand("/release-notes v1.4.0"))
```

Output:

```
Summarise pull requests merged since v1.4.0. Run `git log v1.4.0..HEAD --merges --oneline`, group by label, write RELEASE_NOTES.md and stop.
```

**4.** Its hooks and scripts (what runs automatically, with your permissions); its MCP servers (what they connect to, what credentials they need); how many skills/agents/commands it adds (context cost, name clashes); who publishes and maintains it, and whether you can pin a version.

</details>

---

## Real-World Examples

- **A large Python monorepo team** defined an `explorer` subagent on a cheaper model for all codebase questions, keeping their main sessions short; their Opus sessions read far fewer files directly.
- **A platform team** publishes an internal plugin marketplace. New repos install the team plugin with `--scope project`, which brings the `fix-issue` command, a test-reviewer subagent, formatting hooks and the internal docs MCP server in one step.
- **An open source project** uses the writer/reviewer pattern with a reviewer subagent that has only `Read`, `Grep` and `Glob`, so it can't "fix" what it's supposed to judge.

---

## Common Misconceptions

### "Subagents make agents cheaper"

They make the **main context** cleaner. Total tokens usually go up. You're buying focus, not savings.

### "A subagent knows what we discussed"

A normal subagent starts fresh with only its definition and the task text. If it needs a decision from the conversation, the main agent must put it in the task (or you use a fork).

### "Commands and skills are completely different things"

In Claude Code they're now the same mechanism; the difference is who triggers them (you by name, or the model by description).

### "Plugins from a marketplace are vetted and safe"

A marketplace is a catalogue. Plugins run with your permissions; review them like any dependency.

---

## Interview Relevance

*"When would you use a subagent?"* A strong answer: when the work is large but the answer small (wide searches), when you need a fresh unbiased reviewer, when a role needs restricted tools or a different model, or for parallel independent tasks; not for small or tightly coupled work. Explain that subagents isolate context but increase total tokens, that delegation depends on the description, and that isolation (worktrees) prevents edit collisions. Show you know the formats (Claude Code `.claude/agents/*.md`, Codex `.codex/agents/*.toml`) and that a subagent can't escalate beyond the parent's sandbox and permissions.

*"How do you share agent setup across a team?"* Portable instruction files and skills in the repo, commands for common workflows, and a versioned plugin from an internal marketplace for hooks, subagents and MCP servers, reviewed like any dependency.

---

## Key Takeaways

- **Subagents give a fresh, focused context** and return only a summary; they protect the main context but cost more total tokens.
- **Use them for wide searches, fresh-eyes review, restricted roles and parallel work**; skip them for small or coupled tasks.
- **Definitions are Markdown or TOML with a name, description and system prompt**; the description drives delegation; `isolation: worktree` prevents collisions.
- **Slash commands are saved workflows**; in Claude Code they've merged into skills (`$ARGUMENTS`, `disable-model-invocation`).
- **Plugins package skills, agents, hooks and MCP servers** for sharing via marketplaces; they run as you and cost context every turn.

---

**Up next:** [Sandboxes: Containers, MicroVMs and Hosted Sandboxes](sandboxes-containers-microvms-and-hosted-sandboxes.md)
