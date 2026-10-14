---
title: "Git Hooks and pre-commit"
course: "Git and GitHub: Zero to Pro"
module: "10. Open Source and Advanced Git"
type: Article
level: Intermediate
reading_time: 25 min
---

# Git Hooks and pre-commit: The Complete Guide

> 📚 **Before you start**
>
> - [Installing and Configuring Git](../course.md#m2)
> - [Shell Scripts and cron](../../the-command-line-and-linux-basics/course.md#m3)
> - [Lab: CI that Tests and Lints a Python Project](../07-github-actions/lab-ci-that-tests-and-lints-a-python-project.md)

## Introduction

At a good restaurant, the head chef glances at every plate before it leaves the kitchen: is the garnish on, is the rim clean, is that the right table's order? It takes two seconds and catches mistakes before a customer ever sees them. Sending the plate back from the table is far more expensive.

**Git hooks** are that glance. They're scripts Git runs automatically at certain moments: before a commit is created, after you type the message, before a push. A `pre-commit` hook can format code, catch a stray `print`, refuse a private key or a 50 MB file, all in seconds and before anything leaves your laptop. CI still checks everything (it's the restaurant manager), but catching problems locally makes CI green the first time.

This lesson covers how hooks work, writing your own, sharing them with a team, and the **pre-commit framework**, the standard way to manage hooks in Python projects (and many others), including running the same checks in CI.

> 💡 **Key Insight**
>
> Hooks give **fast feedback**, not **enforcement**: anyone can skip them with `--no-verify`, and they're not cloned with the repository. Use them to make the right thing easy locally, and **repeat the same checks in CI** (with branch rules) to make them mandatory.

---

## Core Explanation

### 1. What Hooks Are

Hooks are executable files in `.git/hooks/` named after an event. A new repository contains `*.sample` examples; remove the `.sample` suffix and make the file executable to enable one. If a "pre" hook exits with a **non-zero** status, Git aborts the operation.

| Hook | Runs | Typical use |
|---|---|---|
| `pre-commit` | Before the commit is created | Format, lint, block secrets and big files |
| `prepare-commit-msg` | Before the editor opens | Pre-fill the message (e.g. the ticket ID from the branch name) |
| `commit-msg` | After you write the message (path passed as `$1`) | Enforce message conventions, add sign-offs |
| `post-commit` | After the commit | Notifications |
| `pre-push` | Before pushing (remote name and URL as arguments; refs on stdin) | Run the fast test suite; block pushing to `main` |
| `post-checkout`, `post-merge` | After switching branches or merging | Reinstall dependencies if the lock file changed |
| `pre-rebase` | Before a rebase starts | Refuse to rebase published branches |

**Server-side hooks** (`pre-receive`, `update`, `post-receive`) run on the server during a push. You can't install custom ones on GitHub.com; GitHub Enterprise Server supports pre-receive hooks. On GitHub.com their jobs are done by **rulesets**, required status checks and **secret scanning push protection** (see [Branch Protection, Rulesets and CODEOWNERS](../course.md#m6)).

### 2. Writing a Hook by Hand

A minimal `pre-commit` hook that refuses commits directly to `main`:

```bash
#!/bin/sh
# .git/hooks/pre-commit
branch=$(git symbolic-ref --short HEAD 2>/dev/null)
if [ "$branch" = "main" ]; then
  echo "pre-commit: don't commit directly to main; create a branch first." >&2
  exit 1
fi
```

```bash
chmod +x .git/hooks/pre-commit
git commit -m "fix: typo"
```

Example output:

```
pre-commit: don't commit directly to main; create a branch first.
```

Hooks can be written in any language with a shebang line. Here's the logic of a `commit-msg` hook in Python, which reads the message from the file whose path Git passes as the first argument:

```python
import re, tempfile, os

PATTERN = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([\w\-./]+\))?!?: .{1,72}$")

def commit_msg_hook(path):
    """What .git/hooks/commit-msg runs: argv[1] is the file holding the message."""
    with open(path, encoding="utf-8") as f:
        lines = [l for l in f.read().splitlines() if not l.startswith("#")]
    subject = lines[0] if lines else ""
    if subject.startswith(("Merge ", "Revert ", "fixup! ", "squash! ")):
        return 0
    if not PATTERN.match(subject):
        print(f"commit-msg: '{subject}' is not a Conventional Commit, e.g. 'fix(parser): handle empty GST'")
        return 1
    return 0

def try_message(text):
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f:
        f.write(text)
    try:
        return commit_msg_hook(f.name)
    finally:
        os.unlink(f.name)

print(try_message("feat(upi): add QR payments\n\n# Please enter the commit message\n"))
print(try_message("wip\n"))
print(try_message("Merge branch 'main' into feat/upi\n"))
```

Output:

```
0
commit-msg: 'wip' is not a Conventional Commit, e.g. 'fix(parser): handle empty GST'
1
0
```

In a real hook file you'd end with `sys.exit(commit_msg_hook(sys.argv[1]))`. Comment lines (starting with `#`) are stripped by Git before the commit is made, so the hook ignores them too, and merge or fixup messages Git writes itself are allowed through.

### 3. Sharing Hooks with a Team

`.git/hooks/` isn't part of the repository, so hooks aren't cloned. Two ways to share them:

**Option A: a versioned hooks folder.** Commit hooks to, say, `.githooks/` and point Git at it:

```bash
git config core.hooksPath .githooks
```

Each developer runs that once (put it in your setup script or `make setup`). Simple, but you write and maintain every hook yourself.

**Option B: a hook manager**, which installs hooks from a config file and fetches the tools they need: **pre-commit** (Python, language-agnostic; the most common), **prek** (a faster, compatible reimplementation of pre-commit), **Lefthook** (Go), and **Husky** (JavaScript projects).

### 4. The pre-commit Framework

pre-commit reads `.pre-commit-config.yaml`, installs each hook's tool in an isolated environment at a **pinned version**, and runs hooks only on the **staged files** by default.

```yaml
# .pre-commit-config.yaml
default_install_hook_types: [pre-commit, commit-msg]

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-merge-conflict
      - id: detect-private-key
      - id: check-added-large-files
        args: ["--maxkb=500"]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.16.10
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks

  - repo: local
    hooks:
      - id: conventional-commit
        name: Conventional Commit message
        entry: python scripts/check_commit_msg.py
        language: system
        stages: [commit-msg]
      - id: no-print
        name: No print() in library code
        entry: "print\\("
        language: pygrep
        files: ^chai_bill/
```

What's going on:

- **`rev`** pins each tool's version, so everyone (and CI) runs the same checks.
- **`pre-commit-hooks`** provides small general checks; `check-added-large-files` catches what should be in [Git LFS](git-lfs-for-large-files.md).
- **Ruff** lints (fixing what it can) and formats Python.
- **gitleaks** scans staged changes for secrets, your last line of defence before [a leaked secret](../09-security-and-supply-chain/removing-a-leaked-secret-from-history.md).
- **`repo: local`** hooks run your own scripts; `language: pygrep` is a built-in regex check; `stages:` picks the Git hook.
- **`default_install_hook_types`** makes `pre-commit install` set up both the `pre-commit` and `commit-msg` hooks.

Using it:

```bash
uv tool install pre-commit            # or: pipx install pre-commit / pip install pre-commit
pre-commit install                    # writes .git/hooks/pre-commit (and commit-msg here)
pre-commit run --all-files            # run everything on every file, e.g. when first adopting
git commit -m "feat: add UPI split"
```

Example output:

```
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...........................................(no files to check)Skipped
check toml...........................................(no files to check)Skipped
check for merge conflicts................................................Passed
detect private key.......................................................Passed
check for added large files..............................................Passed
ruff check...............................................................Failed
- hook id: ruff-check
- exit code: 1
- files were modified by this hook

Found 2 errors (2 fixed, 0 remaining).

ruff format..............................................................Passed
Detect hardcoded secrets.................................................Passed
No print() in library code...............................................Passed
```

When a hook **modifies files** (a formatter or fixer), the commit stops so you can review the changes: `git add` them and commit again.

Other everyday commands:

| Task | Command |
|---|---|
| Update all `rev`s to the latest tags | `pre-commit autoupdate` (add `--freeze` to pin commit SHAs) |
| Run one hook | `pre-commit run ruff-check --all-files` |
| Skip a specific hook once | `SKIP=gitleaks git commit -m "..."` |
| Skip all hooks (emergencies only) | `git commit --no-verify` |
| Remove the hooks | `pre-commit uninstall` |

### 5. What a Typical Pre-commit Check Does

Under the hood, many of these hooks are tiny. A combined sketch of four of them:

```python
CONFLICT = re.compile(r"^(<{7}|={7}|>{7})( |$)", re.M)
KEY = re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")

def pre_commit_checks(staged):
    """staged: {path: (size_in_bytes, text_or_None)}. Returns a list of failures."""
    failures = []
    for path, (size, text) in staged.items():
        if size > 500 * 1024:
            failures.append(f"{path}: {size // 1024} KB is over the 500 KB limit (use Git LFS?)")
        if text is None:
            continue
        if CONFLICT.search(text):
            failures.append(f"{path}: contains merge conflict markers")
        if KEY.search(text):
            failures.append(f"{path}: looks like a private key")
        bad = [n for n, line in enumerate(text.splitlines(), 1) if line != line.rstrip()]
        if bad:
            failures.append(f"{path}: trailing whitespace on line(s) {bad}")
    return failures

key_header = "-----BEGIN " + "OPENSSH PRIVATE KEY-----"
staged = {
    "chai_bill/split.py": (812, "def split(total, n):  \n    return total / n\n"),
    "notes.md": (240, "<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> feat\n"),
    "deploy/id_ed25519": (411, key_header + "\nb3BlbnNzaC1rZXk...\n"),
    "assets/menu.png": (2_400_000, None),
    "README.md": (1300, "# chai-bill\n"),
}
for failure in pre_commit_checks(staged):
    print("-", failure)
```

Output:

```
- chai_bill/split.py: trailing whitespace on line(s) [1]
- notes.md: contains merge conflict markers
- deploy/id_ed25519: looks like a private key
- assets/menu.png: 2343 KB is over the 500 KB limit (use Git LFS?)
```

Real hooks receive the staged file names as arguments (pre-commit passes them for you) and read the files from disk.

### 6. Running the Same Checks in CI

Hooks are skippable and not everyone installs them, so CI must run them too:

```yaml
# .github/workflows/pre-commit.yml
name: pre-commit
on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          persist-credentials: false
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - uses: actions/cache@v6
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ runner.os }}-${{ hashFiles('.pre-commit-config.yaml') }}
      - run: pip install pre-commit
      - run: pre-commit run --all-files --show-diff-on-failure
```

Make this a **required status check** so nothing merges without passing. Hosted alternatives such as **pre-commit.ci** run the same config on every PR and can push fixes automatically.

Keep the commit-time hooks **fast** (a few seconds): move slow things (the full test suite, type checking a big codebase) to `pre-push` (`stages: [pre-push]`) or to CI only.

### 7. Hook Etiquette and Pitfalls

- **Fast or nobody uses it.** People reach for `--no-verify` when hooks take 40 seconds.
- **Pin versions** (`rev`) and update them on purpose: run `pre-commit autoupdate` in a regular PR, or let pre-commit.ci open those PRs for you.
- **Don't surprise people**: document `pre-commit install` in CONTRIBUTING.md and your dev container's `postCreateCommand` (see [Codespaces and Dev Containers](../08-github-pages-codespaces-and-packages/codespaces-and-dev-containers.md)).
- **Hooks run code from the internet** (each `repo:`). Review new hook repositories as you would any dependency, and consider `autoupdate --freeze` to pin SHAs.
- **Coding agents** commit too: tell them in AGENTS.md to run `pre-commit run --all-files` before finishing (see [Repository Instructions](../../coding-agents-and-harness-engineering/03-coding-agents-on-github/repository-instructions-agents-md-and-custom-instructions.md)).

---

## Try It Yourself

1. Write a `pre-push` hook (shell) that runs `python -m pytest -q -x` and blocks the push if it fails.
2. Add a `repo: local` hook to the config above that fails if any file under `chai_bill/` contains `breakpoint()`.
3. Using `pre_commit_checks`, what does `{"app.py": (100, "x = 1\n=======\n")}` return?
4. A teammate says "I don't need pre-commit, CI catches everything." Give two reasons to use both.

<details>
<summary>Show answers</summary>

**1.**

```bash
#!/bin/sh
# .git/hooks/pre-push  (or .githooks/pre-push with core.hooksPath)
if ! python -m pytest -q -x; then
  echo "pre-push: tests failed; push aborted." >&2
  exit 1
fi
```

**2.**

```yaml
  - repo: local
    hooks:
      - id: no-breakpoint
        name: No breakpoint() left in code
        entry: "breakpoint\\("
        language: pygrep
        files: ^chai_bill/
```

**3.**

```python
print(pre_commit_checks({"app.py": (100, "x = 1\n=======\n")}))
```

Output:

```
['app.py: contains merge conflict markers']
```

**4.** Faster feedback (seconds locally versus minutes waiting for CI, and no "fix lint" commits cluttering history), and fewer CI minutes spent. Auto-fixers also correct problems for you instead of just failing. CI remains the enforcement.

</details>

---

## Real-World Examples

### Example 1: The Last Line of Defence

A developer pasted a cloud key into a test file to debug something. The gitleaks pre-commit hook blocked the commit with the file and line. Without it, push protection might have caught it on GitHub, but only for known secret formats, and only after it was in a local commit.

### Example 2: Ending "Fix Lint" Commits

A team's PRs were full of "fix formatting" commits after CI failures. Adopting pre-commit with Ruff, plus the same config in CI as a required check, made those commits disappear; CI time on lint dropped too.

### Example 3: Slow Hooks, Skipped Hooks

A company put its full 8-minute test suite in `pre-commit`. Within a month, everyone used `--no-verify`. Moving tests to `pre-push` (just the fast unit tests) and CI, and keeping `pre-commit` under five seconds, brought people back.

---

## Common Misconceptions

### Misconception 1: "Hooks are cloned with the repository"

They live in `.git/hooks/`, which isn't versioned. Share them with `core.hooksPath` or a hook manager, and an install step.

### Misconception 2: "Hooks enforce our rules"

`--no-verify` skips them. Enforcement belongs in CI with required checks and rulesets.

### Misconception 3: "pre-commit is only for Python"

The framework is written in Python but runs hooks for many languages (Go, Node, Rust, Docker, shell, and more).

### Misconception 4: "pre-commit checks my whole project on every commit"

By default it runs on staged files only; use `--all-files` when adopting it or in CI.

---

## Interview Relevance

Hooks and pre-commit come up in developer tooling and DevOps interviews:

- **Client versus server hooks**, and why GitHub.com uses rulesets and push protection instead of custom server hooks.
- **Sharing hooks:** `core.hooksPath` or pre-commit/Lefthook/Husky.
- **pre-commit config:** repos, `rev` pinning, local hooks, stages, `autoupdate`, `SKIP`.
- **Local hooks plus CI:** fast feedback versus enforcement.
- **Security:** secret scanning in hooks (gitleaks), private key detection, large file checks.

A common follow-up: *"How would you stop secrets being committed across a 200-person engineering org?"* Layered: pre-commit secret scanning, push protection on GitHub, secret scanning alerts, and short-lived credentials.

---

## Key Takeaways

- **Hooks are scripts in `.git/hooks/`** that run at Git events; a non-zero exit from a "pre" hook aborts the operation.
- **They aren't cloned**: share them via `core.hooksPath` or a manager such as **pre-commit**.
- **pre-commit** pins tool versions in `.pre-commit-config.yaml` and runs fast checks (Ruff, gitleaks, large files, conflict markers) on staged files.
- **Keep commit hooks fast**; put slower checks in `pre-push` or CI.
- **Run the same checks in CI as a required status check**, because anyone can skip local hooks with `--no-verify`.

---

**Up next:** [Git Interview Questions Explained](../11-git-and-github-interview-prep/git-interview-questions-explained.md)
