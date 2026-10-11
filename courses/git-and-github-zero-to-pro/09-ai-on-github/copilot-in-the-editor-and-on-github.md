---
title: "Copilot in the Editor and on GitHub"
course: "Git and GitHub: Zero to Pro"
module: "9. AI on GitHub"
type: Article
level: Beginner
reading_time: 25 min
---

# Copilot in the Editor and on GitHub: The Complete Guide

> 📚 **Before you start**
>
> - [Pull Requests End to End](../course.md#m6) and [Code Review that Helps](../course.md#m6) (Collaborating on GitHub)
> - [What is an AI Agent?](../../agentic-ai-fundamentals/02-understanding-agents/what-is-an-ai-agent.md) (Agentic AI Fundamentals), helpful for the agent features but not required

## Introduction

A senior developer pairing with a junior one does three things: finishes the obvious lines so the junior can think about the hard ones, answers "why does this break?" without judgement, and catches mistakes in review before they reach production. Most developers never get enough of that time.

**GitHub Copilot** is an AI assistant that tries to fill those roles, inside your editor, your terminal and GitHub itself. It suggests code as you type, answers questions about your codebase, edits several files at once in agent mode, summarises and reviews pull requests, and can take on whole tasks in the background (the next lesson).

This lesson is a map of Copilot as of October 2026: what each feature does, where it lives, how it's billed, how to give it good context, and, most importantly, how to use it without shipping its mistakes. By the end you'll be able to pick the right Copilot feature for a task and work with it like a careful professional.

> 💡 **Key Insight**
>
> Copilot is fast at producing **plausible** code. Plausible isn't the same as correct. Your job shifts from typing to **specifying, reviewing and testing**. Teams that get the most from AI assistants are the ones with good tests, clear instructions and real code review, because those are what turn plausible into correct.

---

## Core Explanation

### 1. The Map: Where Copilot Lives

GitHub groups Copilot's features into **assistive** features (you stay in the loop, keystroke by keystroke) and **agentic** features (Copilot works through a task on its own and asks for approval at sensitive points).

| Feature | Where | What it does |
|---|---|---|
| **Inline suggestions** | Supported IDEs | Ghost-text completions as you type |
| **Next edit suggestions** | VS Code, Xcode, Eclipse | Predicts *where* your next edit is and suggests it |
| **Copilot Chat** | IDEs, GitHub.com, GitHub Mobile, Windows Terminal | Ask questions, explain code, generate tests |
| **Agent mode** | IDEs | Edits multiple files, proposes terminal commands for your approval, iterates until done |
| **Copilot CLI** | Terminal | An agent in your terminal that edits code, runs commands and opens pull requests |
| **Pull request summaries** | GitHub.com | Writes a summary of a PR's changes and where reviewers should focus |
| **Copilot code review** | GitHub.com, IDEs | AI review comments on a pull request |
| **Copilot cloud agent** | GitHub.com and many entry points | Works on a task in the background and opens a pull request |
| **Third-party agents** | GitHub.com | Anthropic Claude and OpenAI Codex agents with the same protections |
| **Copilot in GitHub Desktop** | GitHub Desktop | Drafts commit messages from your changes |

Customisation features shape all of these: **custom instructions**, **prompt files**, **agent skills**, **custom agents**, **MCP servers**, **Copilot Spaces** (curated bundles of code and docs for context) and **Copilot Memory** (repository facts the agent and code review can reuse, in preview).

### 2. Plans and Billing in One Paragraph

Copilot has a **Free** plan with a limited allowance, free access for verified **students**, individual paid plans (**Pro**, **Pro+** and **Max**), and **Business** and **Enterprise** plans for organizations, which add policies, audit logs and content exclusion. Usage of chat, agents and premium models is measured in **GitHub AI Credits**, with a monthly allowance that depends on the plan; organizations pool their members' credits. Inline suggestions and next edit suggestions are unlimited on paid plans. Agent sessions that run on GitHub's infrastructure also use GitHub Actions minutes. Prices and allowances change, so check the plans page before choosing.

### 3. Inline Suggestions and Next Edit Suggestions

Install the Copilot extension in your editor (VS Code, Visual Studio, JetBrains IDEs, Xcode, Eclipse, Neovim and others), sign in with GitHub, and start typing. Suggestions appear as grey text:

- **Tab** accepts, **Esc** dismisses. Most editors let you accept word by word and cycle between alternatives.
- **Comments and names steer it.** A function named `split_bill_equally(total_rupees, people)` with a docstring gets far better suggestions than `def f(a, b)`.
- **Open files are context.** Copilot looks at the file you're in and related open files. Close irrelevant ones; open the module you want it to imitate.

**Next edit suggestions** go further: after you rename a parameter on line 12, Copilot predicts the matching edits on lines 30 and 41 and offers to jump there.

### 4. Chat and Agent Mode in the IDE

**Chat** is for questions and focused changes: "explain this regex", "why does this test fail?", "write pytest cases for `split_bill` including edge cases". Select code first to make it the subject. In VS Code you can attach files, folders or symbols with `#` references, and pick a model from the model picker.

**Agent mode** is for multi-step tasks: "add a `--currency` option to the CLI, update the docs and tests". The agent reads files, edits several of them, proposes terminal commands (like running tests) for you to approve, reads the output, and iterates until the task is done. You review the diff at the end and keep or discard changes.

A useful mental rule:

| Task size | Use |
|---|---|
| A line or a block | Inline suggestions |
| A question, or one function | Chat |
| A change across several files that you'll watch | Agent mode or Copilot CLI |
| A well-defined task you can hand off and review later | Cloud agent (next lesson) |

### 5. Copilot CLI

Copilot CLI brings the agent into your terminal:

```bash
npm install -g @github/copilot      # needs Node.js 22+; also via Homebrew or WinGet
copilot                             # start an interactive session (/login on first run)
```

In a session you describe a task in plain language; Copilot reads files, edits them and runs commands, asking before it uses each tool unless you've allowed it. **Shift+Tab** switches to a plan mode where it proposes a plan before writing code. Useful slash commands include `/model` (switch model), `/context` (see token usage), `/compact` (summarise the conversation to free context) and `/mcp` (list MCP servers).

For scripts and CI, run it non-interactively with `-p`, and approve exactly the tools it may use:

```bash
copilot -p "Run the test suite and summarise any failures" --allow-tool='shell(pytest)'
copilot -p "Fix the lint errors in src/" --allow-tool='write' --allow-tool='shell(ruff)' --deny-tool='shell(git push)'
```

`--deny-tool` always wins over `--allow-tool` and `--allow-all-tools`. Only start Copilot CLI in directories you trust, never your home folder, because it can read and change files under the directory you launch it from.

### 6. Copilot on GitHub.com

On the website, Copilot helps with the work around code:

- **Copilot Chat on GitHub**: ask about any repository you can see ("where is the payment retry logic?", "summarise the open issues labelled bug"). It searches the code and cites files.
- **Pull request summaries**: in the PR description box, ask Copilot to write a summary of the changes. Edit it before posting; you are the author.
- **Copilot code review**: in a pull request's **Reviewers** sidebar, click **Request** next to Copilot, or from the terminal:

```bash
gh pr create --fill --reviewer @copilot
gh pr edit 128 --add-reviewer @copilot
```

Copilot usually responds within a minute with a **Comment** review: an overview plus inline comments, often with suggested changes you can apply in one click. By default it doesn't approve or request changes, so it never satisfies or blocks your required human approvals (organizations can opt in to Copilot approvals, a preview feature). It doesn't re-review automatically after new pushes unless the repository turns on automatic code review in a ruleset with "Review new pushes".

### 7. Giving Copilot Good Context

Most bad suggestions are context failures, not intelligence failures. In order of impact:

1. **Repository instructions**: a `.github/copilot-instructions.md` or `AGENTS.md` that says how to build, test and style the project. Copilot code review also reads them, from the pull request's head branch. The whole of [Repository Instructions: AGENTS.md and Custom Instructions](repository-instructions-agents-md-and-custom-instructions.md) is about this.
2. **Clear prompts**: the goal, the constraints, the definition of done ("use Decimal for money; add tests; don't change the public API").
3. **The right files in view**: open or reference the files that matter.
4. **Examples**: "follow the pattern in `orders/service.py`".
5. **Tools via MCP**: let the agent read issues, logs or docs directly instead of you pasting them. See [The GitHub MCP Server](the-github-mcp-server.md).

### 8. Trust, but Verify

Here's a realistic suggestion for "split a bill equally". It looks fine and passes a quick glance:

```python
# A plausible-looking suggestion for "split a bill equally between people"
def split_bill_suggested(total, people):
    share = round(total / people, 2)
    return [share] * people

shares = split_bill_suggested(100, 3)
print(shares, "sum =", round(sum(shares), 2))
```

Output:

```
[33.33, 33.33, 33.33] sum = 99.99
```

A paisa disappears. A few targeted checks, which you can also ask Copilot to write, catch it immediately:

```python
# The checks you write (or ask for) before accepting it
def check_split(split):
    problems = []
    for total, people in [(100, 3), (10, 4), (0.05, 2), (999.99, 7)]:
        shares = split(total, people)
        if round(sum(shares), 2) != round(total, 2):
            problems.append(f"{total} / {people}: shares add up to {round(sum(shares), 2)}")
    return problems or ["all good"]

for line in check_split(split_bill_suggested):
    print("-", line)
```

Output:

```
- 100 / 3: shares add up to 99.99
- 0.05 / 2: shares add up to 0.06
- 999.99 / 7: shares add up to 1000.02
```

With the failing checks in hand, the fix (work in whole paise, hand out the remainder one paisa at a time) is easy to request and easy to verify:

```python
def split_bill_fixed(total, people):
    paise = round(total * 100)
    base, extra = divmod(paise, people)
    return [(base + (1 if i < extra else 0)) / 100 for i in range(people)]

print(split_bill_fixed(100, 3))
print(check_split(split_bill_fixed))
```

Output:

```
[33.34, 33.33, 33.33]
['all good']
```

Habits that keep AI-written code safe:

- **Read every line you accept.** You're the author of record.
- **Ask for tests first**, or alongside the code, and check the tests actually test the edge cases.
- **Run it.** CI is your safety net; Copilot's output goes through the same pipeline as anyone's.
- **Watch for invented APIs**: functions, flags or packages that don't exist. Check imports against the real docs. A package name that doesn't exist on PyPI today could be registered by an attacker tomorrow.
- **Never paste secrets** into prompts, and don't accept code that hard-codes keys.
- **Keep humans on approvals.** AI review comments are input to a human reviewer, not a replacement.

### 9. Privacy, Policies and Public Code

- **Duplication detection**: you (or your organization) can block suggestions that match public code, or allow them with references shown so you can check the original's licence.
- **Content exclusion** (Business and Enterprise): administrators can stop Copilot from using specific files or repositories as context, such as secrets-heavy configs or licensed third-party code.
- **Policies**: organizations decide which features and models members can use, including whether the cloud agent, third-party agents and Copilot CLI are enabled.
- **Audit logs and usage data** let administrators see adoption and agent activity.

---

## Try It Yourself

1. **Pick the feature.** Which Copilot feature fits best? (a) Rename a field across 9 files and update tests, watching each step; (b) "What does this 40-line SQL query do?"; (c) "Add input validation to all API endpoints" as a task you'll review tomorrow; (d) A second opinion on a teammate's pull request.
2. **Write a prompt.** Rewrite this weak prompt into a strong one: "make the bill code better".
3. **Find the bug.** Run `check_split` on this suggestion and explain what's wrong: `def split(total, people): return [total // people] * people`.
4. **Safe CLI.** Write a `copilot -p` command that lets it run `pytest` and edit files but never run `git push` or `rm`.

<details>
<summary>Show answers</summary>

**1.** (a) Agent mode in the IDE (or Copilot CLI); (b) Chat; (c) Copilot cloud agent; (d) Copilot code review, alongside a human reviewer.

**2.** For example: "In `src/chai_bill/billing.py`, make `split_bill` handle amounts in paise so shares always add up exactly to the total. Keep the function signature. Use `Decimal` for money. Add pytest cases for 100/3, 0.05/2 and a single person, and run the tests."

**3.**

```python
def split_floor(total, people):
    return [total // people] * people

for line in check_split(split_floor):
    print("-", line)
```

Output:

```
- 100 / 3: shares add up to 99
- 10 / 4: shares add up to 8
- 0.05 / 2: shares add up to 0.0
- 999.99 / 7: shares add up to 994.0
```

Floor division throws away the remainder (and all paise), so money vanishes on almost every input.

**4.**

```bash
copilot -p "Make the failing tests in tests/ pass" \
  --allow-tool='write' --allow-tool='shell(pytest)' \
  --deny-tool='shell(git push)' --deny-tool='shell(rm)'
```

</details>

---

## Real-World Examples

### Example 1: Test-First with Chat

A backend developer at a food-delivery startup asks Chat to "write pytest cases for the delivery-fee function, including midnight surcharges and free-delivery thresholds" before touching the function. Two generated tests fail against the current code, revealing a real bug in the midnight rule.

### Example 2: Review Load on a Busy Team

A team turns on automatic Copilot code review for every pull request. Copilot catches unused variables, missing `None` checks and inconsistent error messages, so human reviewers spend their attention on design and business logic. Required approvals still come from people.

### Example 3: Terminal Automation

A data engineer uses `copilot -p` in a scheduled job, allowed only to run the project's validation script, to summarise last night's failed data checks into a Markdown report for the team channel.

---

## Common Misconceptions

### Misconception 1: "Copilot understands my whole codebase"

It sees what's in its context: open files, references, retrieved code and instructions. Give it the right context and it does far better.

### Misconception 2: "If Copilot suggested it, it's probably correct"

It's probably plausible. Tests and review decide whether it's correct.

### Misconception 3: "Copilot code review replaces human reviewers"

By default it leaves comments only and doesn't count as an approval. It's a first pass that makes human review faster.

### Misconception 4: "AI tools mean I don't need to learn Git and GitHub deeply"

The opposite. Agents produce more branches, commits and pull requests than ever. Reviewing, reverting and untangling them needs exactly the skills in this course.

---

## Interview Relevance

Interviewers increasingly ask how you use AI tools responsibly:

- **Feature fit:** completions for flow, chat for questions, agent mode/CLI for supervised multi-file work, cloud agent for delegated tasks, code review as a first pass.
- **Context engineering:** repository instructions, precise prompts, relevant files, MCP tools.
- **Verification:** tests first, CI, reading every line, checking for invented APIs and hard-coded secrets.
- **Governance:** organization policies, content exclusion, duplication detection, audit logs.

Common follow-ups:

- *"Tell me about a time an AI suggestion was wrong."* Describe the bug, how a test or review caught it, and what you changed in your process.
- *"How do you stop an agent running dangerous commands?"* Tool approvals, deny lists (`--deny-tool`), trusted directories, and running agents in sandboxes or CI with least privilege.

---

## Key Takeaways

- **Copilot spans the editor, terminal and GitHub**: suggestions, chat, agent mode, Copilot CLI, PR summaries, code review and background agents.
- **Usage is measured in AI credits** by plan; completions and next edit suggestions are unlimited on paid plans.
- **Context is everything**: instructions files, precise prompts, the right files and MCP tools.
- **Plausible isn't correct**: write or request tests, run CI, read every line, and watch for invented APIs and secrets.
- **Copilot code review comments, humans approve**; organizations control features, models and exclusions with policies.

---

**Up next:** [Coding Agents that Open Pull Requests](coding-agents-that-open-pull-requests.md)
