---
title: "Branch Protection, Rulesets and CODEOWNERS"
course: "Git and GitHub: Zero to Pro"
module: "6. Collaborating on GitHub"
type: Article
level: Intermediate
reading_time: 22 min
---

# Branch Protection, Rulesets and CODEOWNERS: The Complete Guide

> 📚 **Before you start**
>
> - [Pull Requests End to End](pull-requests-end-to-end.md)
> - [Code Review that Helps](code-review-that-helps.md)
> - [GitHub Flow, Git Flow and Trunk-Based Development](github-flow-git-flow-and-trunk-based-development.md), for which branches need protecting

## Introduction

A team agrees: "Nobody pushes straight to `main`. Every change gets a review. Tests must pass." Then, at 11 p.m. before a demo, someone pushes a "quick fix" directly to `main`, the build breaks, and the demo uses yesterday's version. Agreements that rely on memory and good intentions fail exactly when people are tired and rushed.

GitHub can **enforce** your workflow instead. **Rulesets** and the older **branch protection rules** make the server reject pushes and block merges that break the rules: no direct pushes, required approvals, required passing checks, no force-pushes, no deleting `main`. A **CODEOWNERS** file routes reviews to the people who know each part of the code, and can make their approval mandatory.

By the end of this article you'll be able to explain how a server rejects pushes, protect a branch with a ruleset or a classic branch protection rule, choose the right rules (pull requests, approvals, status checks, linear history, signed commits, force-push and deletion blocking), configure bypass permissions, protect tags, write a CODEOWNERS file and predict who gets asked to review, and recognise the errors you'll see when a rule stops you.

> 💡 **Key Insight**
>
> Git servers can refuse any ref update. GitHub uses that power to turn your team's workflow into **rules checked on every push and every merge**. Use **rulesets** for new setups: they layer (several can apply at once, and the strictest wins), can target branches and tags by pattern, can be viewed by everyone with read access, and have an explicit **bypass list**. Pair them with **CODEOWNERS** so the right experts must approve changes to their areas.

---

## Core Explanation

### 1. How a Server Says No

Protection happens on the **server**, during `git push`. When the server receives your push, it checks each ref update and can reject it. Plain Git servers have a few built-in settings. On a practice server (a bare repository on the same machine), turning two on:

```bash
git -C ../server/chai-ledger.git config receive.denyNonFastForwards true
git -C ../server/chai-ledger.git config receive.denyDeletes true
git commit --amend -q -m "Second, reworded"
git push --force
git push origin --delete main
```

Example output:

```
remote: error: denying non-fast-forward refs/heads/main (you should pull first)
To file:///home/asha/projects/server/chai-ledger.git
 ! [remote rejected] main -> main (non-fast-forward)
error: failed to push some refs to 'file:///home/asha/projects/server/chai-ledger.git'

remote: error: denying ref deletion for refs/heads/main
To file:///home/asha/projects/server/chai-ledger.git
 ! [remote rejected] main (deletion prohibited)
error: failed to push some refs to 'file:///home/asha/projects/server/chai-ledger.git'
```

Even `--force` can't override the server. Notice **`[remote rejected]`**: the server refused, as opposed to `[rejected]`, where your own Git refused before sending because the push wasn't a fast-forward.

Servers can also run a **pre-receive hook**, a script that inspects every incoming update. A tiny one that blocks direct pushes to `main` gives:

```bash
git push
```

Example output:

```
remote: main is protected: open a pull request instead
To file:///home/asha/projects/server/chai-ledger.git
 ! [remote rejected] main -> main (pre-receive hook declined)
error: failed to push some refs to 'file:///home/asha/projects/server/chai-ledger.git'
```

Pushing a branch is still allowed, which is the whole idea: work arrives as branches and reaches `main` only through a reviewed pull request.

```bash
git switch -c add-c
git push -u origin add-c
```

Example output:

```
Switched to a new branch 'add-c'

To file:///home/asha/projects/server/chai-ledger.git
 * [new branch]      add-c -> add-c
branch 'add-c' set up to track 'origin/add-c'.
```

GitHub's rules work the same way from your side: the push fails with `! [remote rejected]`, and `remote:` lines name the rule that blocked it. For rulesets, the message mentions repository rule violations (error code `GH013`); for classic branch protection, a protected branch update failure (`GH006`). Read the `remote:` lines: they tell you exactly what's required, such as "Changes must be made through a pull request".

### 2. Two Systems: Rulesets and Branch Protection Rules

GitHub has two ways to protect branches. You'll meet both:

| | Branch protection rules (classic) | Rulesets (newer) |
|---|---|---|
| Where | Settings → Branches | Settings → Rules → Rulesets |
| Targets | One branch name pattern per rule | Branches **or** tags, by patterns, "default branch" or "all branches" |
| Several at once | Only one rule applies to a branch | **Layer**: all matching rulesets apply; the most restrictive combination wins |
| Turn off temporarily | Delete the rule | Set enforcement to **Disabled** (or **Evaluate** on Enterprise, to log without blocking) |
| Who's exempt | Admins (unless "Do not allow bypassing"), plus some per-setting lists | An explicit **bypass list** of roles, teams and apps |
| Visibility | Admins only | Anyone with read access can see which rules apply |
| Organisation-wide | No | Yes, on paid organisation plans: one ruleset for many repositories |

Both can coexist; GitHub applies both. For new repositories, **prefer rulesets**. Availability depends on plan: on GitHub Free, protection is available for **public** repositories; private repositories need a paid plan (Pro, Team or Enterprise).

### 3. Creating a Ruleset for main

**Settings → Rules → Rulesets → New ruleset → New branch ruleset**. Then:

1. **Name**: "Protect main".
2. **Enforcement status**: **Active**.
3. **Bypass list**: who may skip the rules. Leave it empty for maximum safety, or add a release bot or the Repository admin role. Each entry can bypass **always** or only **for pull requests** (they can merge a PR that doesn't meet the rules, but can't push directly).
4. **Target branches**: **Include default branch** (it follows a rename from `master` to `main`), or patterns like `release/**`.
5. **Rules**: tick what you need (next section).

The command line can inspect rules (it can't create them; use the web or the REST API):

```bash
gh ruleset list
gh ruleset view 42
gh ruleset check main
```

`gh ruleset check <branch>` shows every rule that applies to a branch, including organisation-level ones, which is handy when a push is rejected and you want to know why.

### 4. The Rules That Matter

| Rule | What it enforces | Typical use |
|------|------------------|-------------|
| **Restrict deletions** | Nobody can delete the branch | Always, on `main` |
| **Block force pushes** | No non-fast-forward updates | Always, on shared branches |
| **Require a pull request before merging** | No direct pushes; changes arrive via PR | Always, on `main` |
| ↳ Required approvals | Number of approving reviews (for example 1 or 2) | 1 for most teams |
| ↳ Dismiss stale approvals when new commits are pushed | Approvals reset after changes | Prevents "approve, then sneak in more" |
| ↳ Require review from Code Owners | A code owner of each changed file must approve | With CODEOWNERS (section 6) |
| ↳ Require approval of the most recent reviewable push | Someone other than the last pusher must approve | Stops self-approval via a co-author's push |
| ↳ Require conversation resolution | All review threads resolved before merging | Ensures feedback is answered |
| ↳ Allowed merge methods | Merge, squash and/or rebase | Matches your merge policy |
| **Require status checks to pass** | Named CI checks must succeed on the PR | Tests, lint, build |
| ↳ Require branches to be up to date | The PR must contain the latest `main` before merging | Catches semantic conflicts; costs reruns (a merge queue is the scalable answer) |
| **Require linear history** | No merge commits on the branch | Teams using squash or rebase merges |
| **Require signed commits** | Every commit must have a verified signature | Higher-assurance repositories |
| **Require deployments to succeed** | A deployment to an environment (for example staging) must succeed first | Deployment gates |
| **Require merge queue** | Merges go through a queue that tests each change against the latest `main` | Busy repositories ([Merge Strategies and Merge Queues](merge-strategies-and-merge-queues.md)) |
| **Require code scanning results** | Code scanning must report no alerts above a threshold | Security ([module 10](../course.md#m10)) |
| **Restrict creations / updates** | Only bypass actors can create or push to matching branches | Locking release branches |

A sensible starting ruleset for `main` on a small team: restrict deletions, block force pushes, require a pull request with one approval and stale-approval dismissal, require conversation resolution, and require the CI check (for example `test`) to pass.

**Status checks** are identified by name (a GitHub Actions job name or an external app's check). A check must have run at least once recently in the repository before you can select it. If CI is skipped for a PR (for example by a path filter), a required check never reports and the PR waits forever, a common gotcha; design workflows so required checks always run.

### 5. Classic Branch Protection Rules

You'll still see these in many repositories. **Settings → Branches → Add branch protection rule**, set a **branch name pattern** (`main`, or `release/*`), and tick options with the same meanings as the ruleset rules above, plus a few classic-only names:

- **Do not allow bypassing the above settings**: also applies the rules to administrators (without it, admins can push past them).
- **Restrict who can push to matching branches** (organisation repositories): an allow-list of people, teams or apps.
- **Allow force pushes** and **Allow deletions**: off by default once a rule exists.
- **Lock branch**: makes the branch read-only, for example an archived release line.

When only one classic rule can match a branch, GitHub picks the most specific pattern, which is one reason layered rulesets are easier to reason about.

### 6. CODEOWNERS: Who Must Review What

A **CODEOWNERS** file maps paths to owners. When a PR changes a file, GitHub automatically requests review from that file's owners, and with "Require review from Code Owners" turned on, at least one owner of each changed file must approve.

GitHub looks for the file in `.github/`, then the repository root, then `docs/`, using the first one it finds **on the PR's base branch**. Here's Asha's:

```
# Default owners for everything
*                     @asha-rao

# Billing needs a payments reviewer
/billing/             @chai-collective/payments

# Any Markdown file, anywhere
*.md                  @chai-collective/docs

# Workflows are security-sensitive
/.github/workflows/   @asha-rao @chai-collective/platform
```

Rules for reading it:

- Each line is a **pattern** followed by one or more **owners**: `@username`, `@org/team-name`, or an email address of a GitHub user.
- Patterns use mostly `.gitignore` syntax ([.gitignore and What Never to Commit](../02-version-control-from-scratch/gitignore-and-what-never-to-commit.md)): a leading `/` anchors to the repository root, a trailing `/` means a directory and everything in it, `*` matches within a path segment and `**` across segments. Negation with `!` and character ranges with `[ ]` are **not** supported.
- **The last matching pattern wins.** A file matches the most recent line that fits, not all of them. Put general rules at the top and specific ones below.
- A line with a pattern and **no owners** means "no owners" for those files, useful for exempting generated files.
- Owners must have **write access** to the repository, and teams must be visible and have write access; otherwise the line has no effect. GitHub shows errors in the file's web view.

Predicting reviewers for Asha's file:

| Changed file | Matching lines | Owner(s) requested |
|--------------|----------------|--------------------|
| `ledger.py` | `*` | @asha-rao |
| `billing/upi.py` | `*`, `/billing/` | @chai-collective/payments (last match) |
| `billing/README.md` | `*`, `/billing/`, `*.md` | @chai-collective/docs (last match wins, so payments isn't requested) |
| `.github/workflows/ci.yml` | `*`, `/.github/workflows/` | @asha-rao and @chai-collective/platform |

The `billing/README.md` row shows why order matters: if the payments team must approve *everything* under `billing/`, move the `/billing/` line below `*.md`.

Protect the CODEOWNERS file itself (give `/.github/` an owner), otherwise anyone could edit it in their PR to remove the requirement. Since changes take effect from the base branch, an edit to CODEOWNERS applies only after it merges.

### 7. Protecting Tags and Other Patterns

Tags matter for releases: if anyone can move or delete `v1.2.0`, a deploy might ship different code from what was tested. A **tag ruleset** (New ruleset → New tag ruleset) targeting `v*` with **Restrict updates** and **Restrict deletions** makes release tags immutable for everyone outside the bypass list. Similarly, a branch ruleset on `release/**` can restrict creation to release managers.

Organisations on paid plans can define **organisation rulesets** that target many repositories by name pattern or by custom property (for example "all repositories with `team: payments`"), so a security baseline applies everywhere without configuring each repository.

### 8. Living With Protection Day to Day

- **"Changes must be made through a pull request."** You committed on `main` locally. Move the commit to a branch: `git switch -c my-fix`, push it, open a PR, then reset local `main` with `git switch main` and `git reset --hard origin/main` ([Undoing Things](../04-branching-and-merging/undoing-things-restore-reset-revert-and-cherry-pick.md)).
- **Merge button disabled.** The PR page lists what's missing: approvals, checks, conversations, or "branch is out of date". Hover or expand the merge box.
- **Admins "Merge without waiting for requirements".** Use rarely, for emergencies, with a note on the PR. Better: put a break-glass procedure in the bypass list (a specific team) so it's auditable.
- **Bots that push** (release automation, dependency updates): add the GitHub App to the bypass list instead of weakening rules for everyone.
- **Audit:** rulesets have an **Insights** view listing rule evaluations, including bypasses.

---

## Try It Yourself

1. **Server-side rejection.** Create a bare repository, clone it, push a commit, then set `receive.denyNonFastForwards true` on the bare repository. Amend and force-push. Which flag tells you the server, not your client, refused?
2. **Ruleset.** In a public practice repository, create a ruleset for the default branch that blocks force pushes, restricts deletions and requires a pull request with one approval. Try `git push` directly to `main`. Read the `remote:` lines.
3. **Self-approval.** With a one-approval requirement, open a PR and try to approve it yourself. What happens?
4. **CODEOWNERS puzzle.** Given `* @a`, `/docs/ @b`, `*.py @c`, who owns `docs/build.py`, `docs/index.md`, and `app/main.py`?
5. **Tag protection.** Add a tag ruleset for `v*` that restricts deletions. Create and push `v0.1.0`, then try `git push origin --delete v0.1.0`.

<details>
<summary>Show answers</summary>

1. `! [remote rejected] main -> main (non-fast-forward)`, plus a `remote: error:` line. `[remote rejected]` means the server refused.
2. The push is rejected with `[remote rejected]`, and the `remote:` lines say the change must be made through a pull request (a repository rule violation).
3. GitHub doesn't let you approve your own pull request; the Approve option isn't available to the author. You need another person with write access.
4. `docs/build.py` → @c (`*.py` is the last match). `docs/index.md` → @b. `app/main.py` → @c.
5. The deletion is rejected by the tag ruleset; only actors on the bypass list could delete it.

</details>

---

## Real-World Examples

### Example 1: A Fintech's Main Branch

`main` requires two approvals including a code owner, dismisses stale approvals, requires the `test`, `lint` and `security-scan` checks, requires signed commits and linear history, and blocks force pushes and deletions. Only the release bot is on the bypass list.

### Example 2: An Open Source Project

Maintainers protect `main` with a ruleset requiring one maintainer approval and passing CI, and use CODEOWNERS so subsystem experts are requested automatically. External contributors don't notice the rules until a check fails, which is the point.

### Example 3: Organisation-Wide Baseline

A company with 300 repositories applies an organisation ruleset to every repository's default branch: no force pushes, no deletions, PRs required. Teams add stricter repository-level rulesets on top; the layers combine.

---

## Common Misconceptions

### Misconception 1: "Protection is a client-side setting"

It's enforced by the server. No local configuration or `--force` gets around it; only bypass permissions do.

### Misconception 2: "CODEOWNERS adds every matching owner"

Only the **last matching pattern** applies for each file. Order the file from general to specific.

### Misconception 3: "Admins are always bound by the rules"

Classic rules exempt admins unless "Do not allow bypassing" is on. With rulesets, only the bypass list is exempt, which makes exemptions explicit.

### Misconception 4: "Requiring branches to be up to date prevents all broken merges"

It helps, but on busy repositories it causes endless "update branch" reruns. A merge queue tests each PR combined with what's ahead of it, at scale.

---

## Interview Relevance

Expect these in roles involving team leadership, DevOps or platform work:

- **"How would you protect the main branch?"** Ruleset on the default branch: PRs required, approvals with stale dismissal, required checks, conversation resolution, block force pushes and deletions, minimal bypass list.
- **"What's CODEOWNERS and how does matching work?"** Path-to-owner mapping, auto review requests, required code owner review, last match wins.
- **"Rulesets versus branch protection rules?"** Layering, tag targeting, visibility, bypass lists, organisation-wide application.
- **"A required check never runs and PRs are stuck. Why?"** The workflow is filtered out (paths or branches) or the check name changed; required checks must always report.

---

## Key Takeaways

- Protection is enforced **on the server**: rejected pushes show **`[remote rejected]`** with `remote:` lines naming the rule.
- Prefer **rulesets**: they layer, target branches and tags, are visible to readers, and use an explicit **bypass list**.
- A solid baseline for `main`: **PR required, approvals with stale dismissal, required checks, conversation resolution, no force pushes, no deletions**.
- **CODEOWNERS** routes reviews by path; **the last matching pattern wins**; owners need write access; protect the file itself.
- Protect **release tags** with tag rulesets, and use **organisation rulesets** for company-wide baselines.

---

**Up next:** [Merge Strategies and Merge Queues](merge-strategies-and-merge-queues.md)
