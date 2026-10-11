---
title: "Secrets, Variables and Environments"
course: "Git and GitHub: Zero to Pro"
module: "7. GitHub Actions"
type: Article
level: Intermediate
reading_time: 25 min
---

# Secrets, Variables and Environments: The Complete Guide

> 📚 **Before you start**
>
> - [Workflows, Jobs, Steps and Runners](workflows-jobs-steps-and-runners.md), for contexts and `env:`
> - [Triggers and Events](triggers-and-events.md), for why fork pull requests get less trust
> - [SSH Keys, Tokens and the GitHub CLI](../course.md#m5) (Remotes and GitHub Basics)
> - [Processes, Ports and Environment Variables](../../the-command-line-and-linux-basics/course.md#m3) (The Command Line and Linux Basics)

## Introduction

A housing society gives the watchman a master key so he can let the plumber in. Nobody writes the key's shape on the notice board. The key lives in a locked box, the watchman takes it out only when needed, and the secretary has to approve before anyone opens the water tank on the terrace.

Your workflows need keys too: an API key for a payment gateway, a token to publish a package, credentials to deploy. GitHub gives you the same three ideas as the society: **secrets** (the locked box), **variables** (the notice board, for things that aren't sensitive) and **environments** (the secretary's approval before touching production).

By the end of this article you will know where to store each kind of value, how to use them safely in workflows, how the automatic `GITHUB_TOKEN` and its permissions work, when to use a GitHub App token instead, and how environments add approvals, wait timers and branch rules to deployments.

> 💡 **Key Insight**
>
> Store **config** in variables, **credentials** in secrets, and put anything that can hurt production behind an **environment** with protection rules. Then give every job's token the **fewest permissions** it needs. Most Actions security incidents are a secret in the wrong place, or a token with more power than its job needed.

---

## Core Explanation

### 1. Secrets, Variables and the Difference

| | Secret | Variable |
|---|---|---|
| For | Passwords, API keys, tokens, private keys | Region names, feature flags, URLs, version numbers |
| Visible after saving | Never, not even to admins | Yes, anyone with access can read it |
| In logs | Masked as `***` | Printed as is |
| Context | `${{ secrets.NAME }}` | `${{ vars.NAME }}` |
| Levels | Organization, repository, environment | Organization, repository, environment |

Both live in **Settings → Secrets and variables → Actions**. Secrets are encrypted before they reach GitHub and only decrypted on the runner when a job uses them.

Naming rules: letters, numbers and underscores only; can't start with a number; can't start with `GITHUB_`. Names are case-insensitive and stored in upper case. A single secret can be up to 48 KB.

### 2. Setting Them from the Terminal

The GitHub CLI is faster than clicking through settings:

```bash
# repository secret, value typed at a hidden prompt
gh secret set PAYMENTS_API_KEY

# from a file (good for multi-line values like private keys)
gh secret set DEPLOY_KEY < ~/.ssh/deploy_key

# environment secret
gh secret set PROD_DB_PASSWORD --env production

# organization secret, shared with chosen repositories
gh secret set NPM_TOKEN --org my-company --repos "web,api"

# variables
gh variable set AWS_REGION --body ap-south-1
gh variable list
gh secret list
```

Example output:

```
NAME              UPDATED
DEPLOY_KEY        less than a minute ago
PAYMENTS_API_KEY  less than a minute ago
```

Avoid `gh secret set NAME --body "value"` with a real value: it lands in your shell history.

### 3. Using Secrets in a Workflow

Pass secrets into steps through `env:` and read them as normal environment variables:

```yaml
jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - name: Send order summary
        env:
          PAYMENTS_API_KEY: ${{ secrets.PAYMENTS_API_KEY }}
          API_BASE_URL: ${{ vars.API_BASE_URL }}
        run: python scripts/send_summary.py
```

Inside your script, read them with `os.environ` and fail early with a clear message if one is missing. A missing secret evaluates to an **empty string**, not an error, so without this check you'd get a confusing "401 Unauthorized" much later.

```python
import os

def require_env(*names):
    """Fail fast with a clear message when a workflow forgot to pass a secret."""
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
    return {n: os.environ[n] for n in names}

os.environ["PAYMENTS_API_KEY"] = "sk-live-9f8e7d6c5b4a"     # in CI, the workflow's env: sets this
config = require_env("PAYMENTS_API_KEY")
print("Loaded", list(config), "-> key ends with", config["PAYMENTS_API_KEY"][-4:])

try:
    require_env("PAYMENTS_API_KEY", "SMS_GATEWAY_TOKEN")
except SystemExit as err:
    print(err)
```

Output:

```
Loaded ['PAYMENTS_API_KEY'] -> key ends with 5b4a
Missing required environment variables: SMS_GATEWAY_TOKEN
```

Rules that keep secrets secret:

- **Use `env:`, not command-line arguments.** Arguments can show up in process listings and error messages.
- **Don't paste `${{ secrets.X }}` straight into a `run:` script**; route it through `env:` like above.
- **Secrets can't be used directly in `if:`.** Put the secret in a job-level `env:` and test the variable: `if: env.SLACK_WEBHOOK != ''`.
- **Never print them**, even "just to debug".

### 4. How Log Masking Works, and Where It Fails

The runner knows every secret value a job uses, and replaces each occurrence in the log with `***`. Here is the idea in Python:

```python
def mask(text, secrets):
    """Replace every secret value in text with ***, like the Actions log does."""
    for value in sorted(secrets, key=len, reverse=True):
        if value:
            text = text.replace(value, "***")
    return text

secret_values = ["sk-live-9f8e7d6c5b4a", "upi-merchant-4417"]
log_line = "Calling payments API with key sk-live-9f8e7d6c5b4a for upi-merchant-4417"
print(mask(log_line, secret_values))

# A transformed secret is a NEW string that the runner never registered.
import base64
encoded = base64.b64encode(b"sk-live-9f8e7d6c5b4a").decode()
print(mask(f"Authorization: Basic {encoded}", secret_values))
```

Output:

```
Calling payments API with key *** for ***
Authorization: Basic c2stbGl2ZS05ZjhlN2Q2YzViNGE=
```

Masking is exact string matching. Anything **derived** from a secret (base64, URL-encoded, a slice, a JSON blob with the secret inside) is not masked. If your step derives a sensitive value at run time, register it yourself:

```yaml
- run: |
    TOKEN=$(./scripts/exchange-token.sh)
    echo "::add-mask::$TOKEN"
    echo "TOKEN=$TOKEN" >> "$GITHUB_ENV"
```

Treat masking as a safety net, not a plan.

### 5. Who Gets Secrets, and Who Doesn't

| Situation | Secrets available? |
|---|---|
| `push`, `workflow_dispatch`, `schedule` in your repo | Yes |
| `pull_request` from a branch in the same repo | Yes |
| `pull_request` from a **fork** | No (only a read-only `GITHUB_TOKEN`) |
| Runs triggered by Dependabot | Only **Dependabot secrets**, a separate store in the same settings page |
| A **reusable workflow** you call | Only those you pass explicitly, or all with `secrets: inherit` |
| Environment secrets | Only to jobs that reference that environment, and only after its protection rules pass |

### 6. `GITHUB_TOKEN`: The Token You Get for Free

At the start of every job, GitHub creates a short-lived token for that repository and exposes it as `secrets.GITHUB_TOKEN` (also `github.token`). It expires when the job finishes. Use it to call the GitHub API, push commits, comment on pull requests or publish to GitHub Packages, without creating any personal token.

```yaml
- name: Comment on the pull request
  run: gh pr comment "$PR_URL" --body "Build passed on ${{ runner.os }} :white_check_mark:"
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    PR_URL: ${{ github.event.pull_request.html_url }}
```

**Permissions.** What the token can do is set by the `permissions:` key at workflow or job level. Anything you don't list becomes `none`.

```yaml
permissions:
  contents: read          # check out code

jobs:
  label:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write  # this job only: add labels and comments
    steps:
      - run: echo "Labelling..."
```

Scopes you'll see most often:

| Scope | Allows |
|---|---|
| `contents` | Read code; `write` to push commits, tags and releases |
| `pull-requests` | Comment, label, review pull requests |
| `issues` | Comment on and label issues |
| `packages` | Publish to GitHub Packages (ghcr.io) |
| `pages` | Deploy to GitHub Pages |
| `id-token` | Request an OIDC token (see [the OIDC lesson](oidc-deploying-to-the-cloud-without-stored-keys.md)) |
| `attestations` | Create artifact attestations |
| `security-events` | Upload code scanning results |
| `actions`, `checks`, `statuses`, `deployments` | Manage runs, check runs, commit statuses, deployments |

If you leave out `permissions:` entirely, the token gets the **default** set from repository or organization settings. Newer repositories and organizations default to read-only, but older ones may still default to read/write for everything. Always write an explicit block; it documents intent and protects you if the default changes. The [Hardening Actions](../10-security-and-supply-chain/hardening-actions-pinning-and-least-privilege.md) lesson goes further.

### 7. When `GITHUB_TOKEN` Isn't Enough: GitHub App Tokens

`GITHUB_TOKEN` only works on the current repository, and events it causes don't trigger other workflows. When you need to reach another repository, or you want a bot's pull request to run CI, the clean answer is a **GitHub App**:

1. Create a GitHub App in your organization with only the permissions you need, and install it on the target repositories.
2. Store its client ID as a variable and its private key as a secret.
3. Mint a short-lived installation token in the workflow:

```yaml
- id: app-token
  uses: actions/create-github-app-token@v3
  with:
    client-id: ${{ vars.RELEASE_BOT_CLIENT_ID }}
    private-key: ${{ secrets.RELEASE_BOT_PRIVATE_KEY }}
    owner: ${{ github.repository_owner }}
    repositories: "docs,website"

- uses: actions/checkout@v7
  with:
    repository: my-company/docs
    token: ${{ steps.app-token.outputs.token }}
```

Why not a personal access token (PAT)? A PAT acts as a **person**: it breaks when they leave, it often has far more access than the job needs, and its actions look like they were done by that human. If you must use a PAT, use a **fine-grained** one limited to specific repositories and permissions, with an expiry date.

### 8. Variables in Practice

Variables hold non-secret configuration so you can change it without editing YAML:

```yaml
env:
  AWS_REGION: ${{ vars.AWS_REGION }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - run: echo "Deploying to $AWS_REGION, feature flags = ${{ vars.FEATURE_FLAGS }}"
```

If the same name exists at several levels, the most specific wins: **environment** over **repository** over **organization**. That lets `vars.API_BASE_URL` be the staging URL in the `staging` environment and the production URL in `production`, with one workflow file.

### 9. Environments: Guard Rails for Deployments

An **environment** is a named deployment target, like `staging` or `production`, configured under **Settings → Environments**. A job opts in with `environment:`:

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.chaiwala.example
    steps:
      - run: ./deploy.sh staging
        env:
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}   # the staging environment's secret

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://chaiwala.example
    steps:
      - run: ./deploy.sh production
        env:
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}   # same name, production's value
```

Each environment can have:

- **Required reviewers**: named people or teams who must approve before the job starts. The run pauses with a "Review deployments" button. You can also **prevent self-review**, so the person who triggered the run can't approve it.
- **Wait timer**: a delay before the job starts, useful for "deploy to production 30 minutes after staging unless someone cancels".
- **Deployment branches and tags**: only allow, say, `main` and `v*` tags to deploy to production. A job from any other branch fails before it can read production secrets.
- **Custom deployment protection rules**: a GitHub App (for example a monitoring or change-management tool) that approves or rejects.
- **Environment secrets and variables** that exist only inside it.

```mermaid
flowchart LR
  B[build and test] --> S[deploy-staging<br/>environment: staging]
  S --> W{production rules}
  W -->|branch is main?| R[required reviewer approves]
  R --> T[wait timer]
  T --> P[deploy-production<br/>production secrets unlocked]
  W -->|other branch| X[rejected, secrets never exposed]
```

Environment secrets are only handed to the job **after** all its rules pass. That's what makes environments a security feature and not just a label: code on an unapproved branch never sees the production password.

Each deployment is recorded, so the repository's **Deployments** page shows what is live where and which commit put it there. Protection rules on private repositories require a paid GitHub plan.

### 10. A Checklist for Secrets

- Prefer **no secret at all**: use OIDC for cloud providers (next lesson) and `GITHUB_TOKEN` for GitHub.
- Scope secrets as **narrowly** as possible: environment over repository over organization.
- **Rotate** long-lived secrets on a schedule, and immediately when someone with access leaves.
- Keep production secrets behind an environment with required reviewers and a branch rule.
- Give every job an explicit, minimal `permissions:` block.
- If a secret leaks, **revoke it first**, then clean up. See [Removing a Leaked Secret from History](../10-security-and-supply-chain/removing-a-leaked-secret-from-history.md).

---

## Try It Yourself

1. **Classify.** Secret or variable? (a) `ap-south-1`, (b) a Razorpay API key, (c) the Slack channel name for alerts, (d) an SSH private key, (e) the Docker image name.
2. **Least privilege.** A job checks out code and comments on the pull request. Write its `permissions:` block.
3. **Conditional on a secret.** Write a step that posts to Slack only if the `SLACK_WEBHOOK` secret is set.
4. **Design.** Your team wants: anyone can deploy to staging from any branch; production only from `main`, only after one of the two tech leads approves, and the person who started the run can't approve. What do you configure?

<details>
<summary>Show answers</summary>

**1.** Variables: (a), (c), (e). Secrets: (b), (d).

**2.**

```yaml
permissions:
  contents: read
  pull-requests: write
```

**3.**

```yaml
jobs:
  notify:
    runs-on: ubuntu-latest
    env:
      SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
    steps:
      - if: env.SLACK_WEBHOOK != ''
        run: curl -sS -X POST -H 'Content-Type: application/json' -d '{"text":"Build done"}' "$SLACK_WEBHOOK"
```

**4.** Two environments. `staging`: no rules (or a branch rule allowing all branches). `production`: required reviewers = the two tech leads, "Prevent self-review" ticked, deployment branches limited to `main`. Store each environment's credentials as environment secrets with the same names, and reference `environment: production` in the deploy job.

</details>

---

## Real-World Examples

### Example 1: A Payments Startup's Release Gate

A payments startup keeps its production database password and gateway keys only as `production` environment secrets. The production job needs approval from one of three on-call engineers, can't be approved by whoever triggered it, and only runs from `main`. An intern's experimental branch can run the whole pipeline up to staging, and never touches production credentials.

### Example 2: One Workflow, Three Regions

A logistics company deploys the same service to Mumbai, Singapore and Frankfurt. Each region is an environment with its own `vars.REGION` and its own secrets, and a matrix over environment names deploys all three with one job definition.

### Example 3: Replacing a Departed Engineer's Token

A team's release workflow used a senior engineer's personal access token. When she left and her account was removed, releases broke at 11 p.m. on a Friday. They moved to a GitHub App with only `contents: write` on two repositories, and the token problem never came back.

---

## Common Misconceptions

### Misconception 1: "Masked means safe"

Masking only hides exact matches in logs. A workflow can still send a secret anywhere over the network, or print a transformed version.

### Misconception 2: "Variables are just secrets without encryption, so I can use either"

Variables are readable by anyone with repository access and appear in logs. Never put anything sensitive in them.

### Misconception 3: "Fork pull requests can use my secrets if I approve the run"

Approving a fork's run lets it run, but `pull_request` workflows from forks still get no secrets. That's intentional.

### Misconception 4: "`GITHUB_TOKEN` is an admin token"

Its power is whatever `permissions:` (or the default) gives it, limited to the current repository, and only for the job's lifetime.

---

## Interview Relevance

Secrets management is a favourite DevOps and security interview topic:

- **Where things live:** variables for config, secrets for credentials, environments for deployment targets; precedence environment > repo > org.
- **Safe use:** pass via `env:`, never print, validate presence, `::add-mask::` for derived values.
- **Token hygiene:** explicit `permissions:`, `GITHUB_TOKEN` over PATs, GitHub Apps for cross-repo work, fine-grained PATs as a last resort.
- **Deployment control:** environments with required reviewers, prevent self-review, branch rules and wait timers.

Common follow-ups:

- *"How would you stop a feature branch from deploying to production?"* Environment deployment branch rules, plus environment-scoped secrets.
- *"How do you avoid storing cloud keys at all?"* OIDC federation, covered next.

---

## Key Takeaways

- **Secrets are write-only and masked; variables are plain config.** Both exist at org, repo and environment level, most specific wins.
- **Pass secrets through `env:`** and validate them; masking is exact-match only.
- **Fork pull requests get no secrets**, and reusable workflows only get what you pass.
- **`GITHUB_TOKEN`** is per-job and limited by `permissions:`; use GitHub App tokens for cross-repo or CI-triggering work.
- **Environments** add required reviewers, self-review prevention, wait timers and branch rules, and only unlock their secrets after the rules pass.

---

**Up next:** [OIDC: Deploying to the Cloud without Stored Keys](oidc-deploying-to-the-cloud-without-stored-keys.md)
