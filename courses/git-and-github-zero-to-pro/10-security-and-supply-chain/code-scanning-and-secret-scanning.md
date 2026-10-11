---
title: "Code Scanning and Secret Scanning"
course: "Git and GitHub: Zero to Pro"
module: "10. Security and Supply Chain"
type: Article
level: Intermediate
reading_time: 25 min
---

# Code Scanning and Secret Scanning: The Complete Guide

> 📚 **Before you start**
>
> - [Dependabot Alerts and Updates](dependabot-alerts-and-updates.md)
> - [Workflows, Jobs, Steps and Runners](../07-github-actions/workflows-jobs-steps-and-runners.md) and [Matrix Builds and Caching](../07-github-actions/matrix-builds-and-caching.md)
> - [.gitignore and What Never to Commit](../course.md#m2) (Version Control from Scratch)

## Introduction

Airport security has two different checks. The X-ray machine looks inside your bag for dangerous items, things that are harmful because of what they **are**. The ID check at the gate catches a different problem: a boarding pass that shouldn't be in the wrong hands.

Your repository needs both. **Code scanning** reads your code for dangerous patterns you wrote: SQL built from user input, unsafe deserialisation, a path that lets users read any file. **Secret scanning** looks for credentials that should never have been committed at all: API keys, tokens, private keys. One finds bugs that attackers could exploit; the other finds keys that attackers could simply use.

By the end of this article you'll know how static analysis and CodeQL work, set up code scanning with default and advanced setup, read and fix alerts (including with Copilot Autofix), plug in third-party scanners through SARIF, and use secret scanning and push protection to stop credentials from ever reaching GitHub.

> 💡 **Key Insight**
>
> The best time to catch a vulnerability is **in the pull request**, and the best time to catch a secret is **before the push lands**. Code scanning annotates PRs; push protection blocks the push. Fixing anything after it's merged, or after a secret is public, costs ten times more.

---

## Core Explanation

### 1. Static Analysis in One Picture

**Static application security testing (SAST)** analyses source code without running it. GitHub's engine is **CodeQL**: it builds a database from your code (every function, call and data flow), then runs **queries** that describe vulnerability patterns, such as "data from an HTTP request flows, unsanitised, into a SQL query".

```mermaid
flowchart LR
  SRC[Source code] --> DB[(CodeQL database<br/>AST, data flow)]
  Q[Query packs<br/>SQL injection, XSS, path traversal...] --> RUN[Run queries]
  DB --> RUN
  RUN --> SARIF[SARIF results]
  SARIF --> UI[Alerts in Security tab<br/>+ PR annotations]
```

The key idea is **taint tracking**: CodeQL follows untrusted data from a **source** (request parameters, file contents) to a **sink** (a database query, a shell command, a template), and reports when no **sanitiser** sits in between. That catches bugs a simple text search can't, across functions and files.

```python
# not-run: a vulnerable Flask route CodeQL would flag (Flask isn't installed for this course)
from flask import Flask, request
import sqlite3

app = Flask(__name__)

@app.route("/orders")
def orders():
    customer = request.args.get("customer")              # source: user input
    db = sqlite3.connect("shop.db")
    query = f"SELECT * FROM orders WHERE customer = '{customer}'"
    return {"rows": db.execute(query).fetchall()}          # sink: SQL injection
```

The fix is a parameterised query, `db.execute("SELECT * FROM orders WHERE customer = ?", (customer,))`, which CodeQL recognises as safe.

### 2. Default Setup: One Click

For most repositories, **default setup** is the right start: **Settings → Advanced Security → Code scanning → CodeQL analysis → Set up → Default**. GitHub detects the languages (Python, JavaScript/TypeScript, Java/Kotlin, C#, Go, Ruby, Swift, C/C++, GitHub Actions workflows and more), picks a query suite, and scans on pushes to the default branch, on pull requests to it, and weekly. No workflow file is added to your repository.

Code scanning is free for public repositories. For private repositories it's part of **GitHub Code Security**.

### 3. Advanced Setup: A Workflow You Control

Choose **advanced setup** when you need a custom build, extra queries, specific paths, or a schedule. GitHub creates a workflow you can edit:

```yaml
name: CodeQL

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "27 3 * * 1"      # weekly, catches new queries on old code

permissions:
  contents: read

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ubuntu-latest
    permissions:
      security-events: write   # upload results
      packages: read           # fetch query packs
      actions: read
      contents: read
    strategy:
      fail-fast: false
      matrix:
        include:
          - language: python
            build-mode: none
          - language: javascript-typescript
            build-mode: none
          - language: actions
            build-mode: none
    steps:
      - uses: actions/checkout@v7
      - uses: github/codeql-action/init@v4
        with:
          languages: ${{ matrix.language }}
          build-mode: ${{ matrix.build-mode }}
          queries: security-extended
      - uses: github/codeql-action/analyze@v4
        with:
          category: "/language:${{ matrix.language }}"
```

Details:

- **`build-mode`**: `none` for interpreted languages (and works for some compiled ones too); `autobuild` or `manual` (with your own build steps between `init` and `analyze`) for compiled languages like Java or C++.
- **`queries`**: the default suite favours high-precision results; `security-extended` adds more security queries; `security-and-quality` adds maintainability checks too.
- **`actions` language**: CodeQL can scan your **workflow files** for problems like script injection and dangerous `pull_request_target` usage, which ties directly into [Hardening Actions](hardening-actions-pinning-and-least-privilege.md).
- **`category`** keeps results from different languages separate.

A `codeql-config.yml` can add query packs, exclude queries or ignore paths such as `tests/` or vendored code.

### 4. Reading and Fixing Alerts

Alerts appear in **Security → Code scanning** and, for new problems in a pull request, as annotations on the diff with a check named after the tool. Each alert shows:

- The **rule** (for example "SQL query built from user-controlled sources"), severity and, for security rules, a security severity.
- The **path** from source to sink, step by step.
- Help text with examples of the fix.

**Copilot Autofix** suggests a fix for many code scanning alerts: an explanation and a diff you can commit to the pull request (or, for existing alerts, into a new PR). Review it like any suggested change. Autofix is available for public repositories and with GitHub Code Security.

You can **dismiss** an alert as a false positive, "won't fix" or "used in tests", with a comment. Dismissals are recorded and auditable.

### 5. Blocking Merges on Findings

To make code scanning a gate, add the **"Require code scanning results"** rule to a branch ruleset and choose the thresholds: for example, block on **security alerts of high or higher** and on **errors**. Pull requests that introduce such alerts can't merge until they're fixed or dismissed. Keep the threshold high at first; a gate that fires on every low-severity note just trains people to dismiss alerts.

### 6. Third-Party Scanners and SARIF

Any tool that outputs **SARIF** (Static Analysis Results Interchange Format, a JSON standard) can feed the same alerts UI. Upload with the CodeQL action's `upload-sarif`:

```yaml
jobs:
  bandit:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v7
      - run: pipx run --spec "bandit[sarif]" bandit -r src -f sarif -o bandit.sarif || true
      - uses: github/codeql-action/upload-sarif@v4
        with:
          sarif_file: bandit.sarif
          category: bandit
```

Linters like Ruff, container scanners like Trivy, infrastructure scanners like Checkov, and workflow linters like zizmor can all report this way, so your security findings live in one place with one triage workflow. The `|| true` lets the job continue to the upload even when the scanner exits non-zero on findings; the alerts, not the exit code, are the result.

### 7. Secret Scanning: What It Finds

**Secret scanning** checks your repository's history, issues, pull requests, discussions and wikis for credentials:

- **Provider patterns**: hundreds of token formats from GitHub and partner services (cloud providers, payment gateways, chat platforms, AI providers...). For public repositories, GitHub also **notifies the provider**, which may revoke the token automatically.
- **Non-provider patterns**: private keys, connection strings, generic API keys.
- **Generic passwords**, detected with AI (Copilot secret scanning), for passwords that don't follow any pattern.
- **Custom patterns**: your organization's internal token formats, as regular expressions.
- **Validity checks**: for supported providers, GitHub checks whether a leaked token is still **active**, so you know which alerts are urgent.

Scanners are pattern matchers at heart. A tiny illustration of the two techniques, exact formats and randomness (entropy):

```python
import math
import re
from collections import Counter

PATTERNS = {
    "GitHub personal access token": re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    "GitHub fine-grained token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{82}\b"),
    "AWS access key ID": re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Private key block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}

def entropy(s):
    """Shannon entropy in bits per character: random strings score high."""
    counts = Counter(s)
    return -sum(c / len(s) * math.log2(c / len(s)) for c in counts.values())

def scan(text):
    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append((lineno, name))
        # generic fallback: password-like assignments with a random-looking value
        m = re.search(r"(?i)(password|secret|api_key)\s*=\s*['\"]([^'\"]{12,})['\"]", line)
        if m and entropy(m.group(2)) > 3.5:
            findings.append((lineno, f"high-entropy {m.group(1).lower()}"))
    return findings

config = '''DEBUG = True
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
api_key = "change-me-later"
password = "Xq7#pL9v!Rz2@mW4"
token = "ghp_''' + "a1B2c3D4e5F6g7H8i9J0" + "k1L2m3N4o5P6" + "q7R8" + '''"
'''
for lineno, name in scan(config):
    print(f"line {lineno}: {name}")

print(round(entropy("change-me-later"), 2), round(entropy("Xq7#pL9v!Rz2@mW4"), 2))
```

Output:

```
line 2: AWS access key ID
line 4: high-entropy password
line 5: GitHub personal access token
3.32 4.0
```

(The fake token is split across string pieces so this lesson's own file doesn't contain anything that looks like a real token. `AKIAIOSFODNN7EXAMPLE` is the example key ID from AWS's documentation.) Real scanners use far better rules, but the trade-off is the same: strict patterns give few false alarms but miss unusual secrets; fuzzy rules catch more but alert on harmless strings. Provider-specific prefixes like `ghp_` and `github_pat_` exist precisely so scanners can find tokens reliably.

### 8. Push Protection: Stop It Before It Lands

Alerts after the fact still mean rotating a key. **Push protection** checks pushes and **blocks** any that contain a supported secret:

```bash
git push origin feature/payments
```

Example output:

```
remote: error: GH013: Repository rule violations found for refs/heads/feature/payments.
remote:
remote: - GITHUB PUSH PROTECTION
remote:   Resolve the following violations before pushing again
remote:
remote:   - Push cannot contain secrets
remote:
remote:     —— Stripe API Key ————————————————————————
remote:      locations:
remote:        - commit: 8a3f1c2d
remote:          path: config/settings.py:14
remote:
remote:      (?) To push, remove secret from commit(s) or follow this URL to allow the secret.
remote:      https://github.com/chai-co/orders-api/security/secret-scanning/unblock-secret/...
To github.com:chai-co/orders-api.git
 ! [remote rejected] feature/payments -> feature/payments (push declined due to repository rule violations)
```

What to do when blocked:

1. **Remove the secret from the commit**, not just from the latest file version. If it's in the last commit: edit the file to read from an environment variable, then `git commit --amend`. If it's further back: an interactive rebase to edit that commit. The [Rebase and Interactive Rebase](../course.md#m4) lesson shows how.
2. **Treat the secret as compromised anyway** if it was ever shared or pushed elsewhere, and rotate it.
3. Use the **bypass** link only for genuine false positives or test credentials, choosing a reason ("used in tests", "false positive", "I'll fix it later"). Bypasses create alerts and are audited. Organizations can enable **delegated bypass**, so a security reviewer must approve each one.

Push protection also works in the web editor and in the API, and push protection **for users** (a personal setting, on by default) protects your pushes to any public repository.

### 9. Who Gets What

| Feature | Public repositories | Private repositories |
|---|---|---|
| Secret scanning alerts and push protection | Free | GitHub Secret Protection |
| Custom patterns, validity checks, delegated bypass, AI-detected passwords | — | GitHub Secret Protection |
| Code scanning (CodeQL and SARIF uploads) | Free | GitHub Code Security |
| Copilot Autofix for code scanning | Free | GitHub Code Security |
| Dependency review | Free | GitHub Code Security |

Organization owners and security managers can also run a free **secret risk assessment** to see how many secrets are exposed across the organization's repositories.

### 10. When an Alert Fires

For a **code scanning** alert: understand the data flow, fix the root cause (parameterise, validate, encode), add a test that would have caught it, and let the alert close automatically on the next scan.

For a **secret scanning** alert, the order matters:

1. **Revoke or rotate the secret** at the provider. Now. This is the only step that actually stops misuse.
2. **Check logs** at the provider for use you don't recognise.
3. **Remove it from code** and load it from a secret store or environment variable.
4. **Decide whether to rewrite history.** Often unnecessary once the secret is revoked, but sometimes required. See [Removing a Leaked Secret from History](removing-a-leaked-secret-from-history.md).
5. **Close the alert** as revoked.

---

## Try It Yourself

1. **Fix the query.** Rewrite the vulnerable `orders()` route so CodeQL wouldn't flag it.
2. **Extend the scanner.** Add a pattern for Slack bot tokens (they start with `xoxb-`) to `PATTERNS`, and scan the line `SLACK = "xoxb-1234567890-abcdefghij"`.
3. **Pick the setup.** Default or advanced? (a) A Python web app with no special needs; (b) a C++ project that needs a custom CMake build; (c) a repo that wants Bandit results next to CodeQL's.
4. **Blocked push.** Push protection blocks your push because a test fixture contains a dummy Stripe key `sk_test_...` from Stripe's docs. What are your two options, and which is better?

<details>
<summary>Show answers</summary>

**1.**

```python
# not-run: Flask isn't installed for this course
@app.route("/orders")
def orders():
    customer = request.args.get("customer", "")
    db = sqlite3.connect("shop.db")
    rows = db.execute("SELECT id, total FROM orders WHERE customer = ?", (customer,)).fetchall()
    return {"rows": rows}
```

**2.**

```python
PATTERNS["Slack bot token"] = re.compile(r"\bxoxb-[0-9A-Za-z-]{10,}\b")
print(scan('SLACK = "xoxb-1234567890-abcdefghij"'))
```

Output:

```
[(1, 'Slack bot token')]
```

**3.** (a) default setup; (b) advanced setup with `build-mode: manual` and your CMake steps; (c) either CodeQL setup plus a separate workflow that uploads Bandit's SARIF with `upload-sarif`.

**4.** Bypass the block with the reason "used in tests", or change the fixture so it doesn't contain a realistic-looking key (for example build it at runtime or use an obviously fake placeholder). Changing the fixture is better: it keeps the history clean and avoids training the team to click bypass.

</details>

---

## Real-World Examples

### Example 1: SQL Injection Caught in Review

A developer adds a search filter built with an f-string. The CodeQL check on the pull request flags "SQL query built from user-controlled sources" with the exact path from `request.args` to `execute`. Copilot Autofix proposes a parameterised query; the developer applies it, adds a test, and the alert never reaches `main`.

### Example 2: A Key That Never Left the Laptop

An intern hard-codes a payment gateway test key while debugging and runs `git push`. Push protection blocks it with the file and line. They move the key to `.env` (already in `.gitignore`), amend the commit and push again. Nothing to rotate, nothing to clean.

### Example 3: Provider Revocation

Someone pastes a cloud access token into a public gist. Within moments, secret scanning's partner program notifies the provider, which revokes the token automatically. The owner gets an email instead of a surprise bill.

---

## Common Misconceptions

### Misconception 1: "Code scanning finds all vulnerabilities"

It finds patterns its queries describe. Business logic flaws, authorisation mistakes and misconfigurations usually need review, tests and threat modelling.

### Misconception 2: "Deleting the file removes the secret"

The secret is still in every earlier commit, every clone and possibly every fork. Rotate it first.

### Misconception 3: "Bypassing push protection is fine if I'll fix it later"

The push lands with the secret in history, and an alert opens. "Later" usually means "after it's been cloned".

### Misconception 4: "Private repos don't need secret scanning"

Private repositories get cloned to laptops, CI runners and vendors' systems, and sometimes made public by mistake. Secrets don't belong in any repository.

---

## Interview Relevance

Security interviews (and many backend ones) ask how you'd secure a codebase on GitHub:

- **SAST with CodeQL:** sources, sinks, taint tracking; default versus advanced setup; query suites; build modes; SARIF for third-party tools.
- **Gating:** PR annotations, rulesets that require code scanning results at chosen thresholds, Copilot Autofix.
- **Secrets:** provider patterns, custom patterns, validity checks, push protection with audited, delegated bypass.
- **Incident order:** revoke → check logs → remove from code → consider history rewrite → close alert.

Common follow-ups:

- *"How does push protection differ from secret scanning alerts?"* Prevention at push time versus detection after the fact.
- *"What's SARIF?"* A JSON standard for static analysis results that lets any tool report into GitHub's code scanning UI.

---

## Key Takeaways

- **Code scanning (CodeQL)** tracks untrusted data from sources to sinks and reports vulnerabilities as alerts and PR annotations.
- **Default setup** is one click; **advanced setup** gives a workflow with build modes, query suites, and `actions` workflow scanning.
- **SARIF** lets any scanner feed the same alerts; **rulesets** can block merges on high-severity findings; **Copilot Autofix** proposes fixes.
- **Secret scanning** finds provider, generic, AI-detected and custom secrets; **push protection** blocks them before they land.
- **When a secret leaks, revoke it first.** Everything else comes after.

---

**Up next:** [Signed Commits and Artifact Attestations](signed-commits-and-artifact-attestations.md)
