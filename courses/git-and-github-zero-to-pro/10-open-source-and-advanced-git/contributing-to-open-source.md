---
title: "Contributing to Open Source"
course: "Git and GitHub: Zero to Pro"
module: "10. Open Source and Advanced Git"
type: Article
level: Intermediate
reading_time: 25 min
---

# Contributing to Open Source: The Complete Guide

> 📚 **Before you start**
>
> - [Forks, Upstreams and Remotes](../course.md#m5)
> - [Pull Requests End to End](../course.md#m6) and [Code Review that Helps](../course.md#m6)
> - [Rebase and Interactive Rebase](../course.md#m4)

## Introduction

Think of a big neighbourhood Ganesh pandal. Nobody "owns" it the way a shop owner owns a shop, yet it runs smoothly every year because a small committee coordinates, hundreds of volunteers pitch in, and there are clear unwritten rules: ask the committee before you rearrange the stage, don't wander off with the donation box, and turn up on the day you promised.

Open source projects work the same way. A few **maintainers** decide what goes in, many **contributors** send changes, and each project writes its rules down in files such as `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`. Contributing well is less about brilliant code and more about following those rules: picking the right issue, talking before building, sending a small, tested, well-described pull request, and responding to review graciously.

This lesson walks you through the whole journey, from finding your first issue to getting a pull request merged, including the parts beginners trip on: syncing your fork, DCO sign-offs and CLAs, CI that won't run on your PR, and the etiquette of using AI tools on someone else's project.

> 💡 **Key Insight**
>
> Maintainers are volunteers with limited time. Every contribution costs them **review time**. The contributors who get merged are the ones who make that review **cheap**: small changes, discussed first, matching the project's style, with tests and a clear description.

---

## Core Explanation

### 1. Why Contribute?

- **Learning from real code**, reviewed by experienced engineers, for free.
- **A public portfolio.** A merged PR to a known project is concrete proof of skill for interviews.
- **Fixing what you use.** The bug that annoys you probably annoys others.
- **Programmes that pay or mentor:** Google Summer of Code, Outreachy, LFX Mentorship, and in India GirlScript Summer of Code, plus October's Hacktoberfest for a first push.

Contributions aren't only code: documentation, translations, triaging issues, reproducing bugs, answering questions and reviewing PRs are all valued, and are often the best way in.

### 2. Choosing a Project and an Issue

Pick a project you **actually use**; you'll understand its problems and stay motivated. Then check its health:

| Signal | Where to look |
|---|---|
| Active maintainers | Recent commits and releases; are issues and PRs answered within weeks? |
| Welcoming to newcomers | `CONTRIBUTING.md`, a code of conduct, labels like `good first issue` or `help wanted` |
| Clear licence | A `LICENSE` file (see [Licenses in Plain English](licenses-in-plain-english.md)) |
| Contribution rules | DCO or CLA requirement, commit style, AI-assistance policy |

Finding beginner-friendly issues:

- The repository's **Issues** tab, filtered with `label:"good first issue"`.
- `https://github.com/OWNER/REPO/contribute`, which lists a project's good first issues.
- GitHub search across projects: `is:issue is:open label:"good first issue" language:python`.

```bash
gh issue list --repo OWNER/REPO --label "good first issue" --state open
```

### 3. Read the Rules Files

Before writing code, read:

- **`CONTRIBUTING.md`**: how to set up the dev environment, run tests, name branches and format commits; whether to open an issue first.
- **`CODE_OF_CONDUCT.md`**: how to behave and how to report problems. The Contributor Covenant is the most common.
- **Issue and PR templates** in `.github/`: what information maintainers expect.
- **`SECURITY.md`**: never report a vulnerability in a public issue; follow this file instead (often GitHub private vulnerability reporting).
- **`AGENTS.md` or AI policy**: some projects ask you to disclose AI assistance, or don't accept AI-generated PRs at all.

### 4. Talk Before You Build

Comment on the issue: what you plan to change and roughly how. For anything bigger than a typo, wait for a maintainer to agree. This avoids the classic heartbreak of a 500-line PR closed with "we don't want this feature" or "someone else is already on it".

Good claim comment:

~~~markdown
I'd like to take this. My plan: treat an empty GST field as zero in
`parse_bill()` and add a test for it. I'll have a PR up this week.
~~~

If you go quiet for weeks, say so, so someone else can pick it up.

### 5. The Fork-and-Branch Workflow

```bash
gh repo fork chai-co/chai-bill --clone      # fork on GitHub and clone your fork
cd chai-bill
git remote -v                                # origin = your fork, upstream = original
git switch -c fix/empty-gst-field            # one branch per change
```

`gh repo fork --clone` sets up both remotes for you. Done by hand, it's `git remote add upstream https://github.com/chai-co/chai-bill.git`.

Keep your branch current with upstream (rebase keeps the history tidy for review):

```bash
git fetch upstream
git rebase upstream/main
git push --force-with-lease                  # update your PR branch safely
```

Never commit to your fork's `main`; keep it as a clean mirror of upstream so you can start each new branch from it.

### 6. Making the Change

- Follow the project's style and run its formatter and linter (often through `pre-commit`; see [Git Hooks and pre-commit](git-hooks-and-pre-commit.md)).
- Add or update **tests**, and **docs** if behaviour changes.
- Keep the diff **focused**: no drive-by reformatting of unrelated files.
- Write commit messages the way the project does. Many use **Conventional Commits** (`fix(parser): ...`), which also drive changelogs and version bumps (see [Maintaining a Project](maintaining-a-project-templates-releases-and-semver.md)).

### 7. Sign-offs: DCO and CLA

Projects need to know you have the right to contribute your code:

- **DCO (Developer Certificate of Origin)**: you certify that you wrote the code (or have the right to submit it) by adding a `Signed-off-by:` line to each commit. `git commit -s` adds it, using your configured `user.name` and `user.email`. A DCO check on the PR fails if any commit lacks it.
- **CLA (Contributor Licence Agreement)**: a legal agreement you sign once (often by clicking through a bot's link on your first PR) that grants the project rights to your contribution. Companies sometimes need their legal team to sign a corporate CLA.

Forgot to sign off? Fix the commits and force-push:

```bash
git commit --amend --no-edit -s                 # last commit only
git rebase --signoff upstream/main              # every commit on the branch
git push --force-with-lease
```

Many projects automate checks like these. Here's a small checker for Conventional Commit subjects and DCO sign-offs:

```python
import re

CONVENTIONAL = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([\w\-./]+\))?!?: \S")

def check_commit(message, author_email):
    subject, *rest = message.splitlines()
    problems = []
    if not CONVENTIONAL.match(subject):
        problems.append("subject is not 'type(scope): description'")
    if len(subject) > 72:
        problems.append(f"subject is {len(subject)} chars (max 72)")
    if "Signed-off-by:" not in message:
        problems.append("missing DCO sign-off (use git commit -s)")
    elif not re.search(rf"^Signed-off-by: .+ <{re.escape(author_email)}>$", message, re.M):
        problems.append("sign-off email does not match the commit author")
    return problems

good = """fix(parser): handle empty GST field

Empty strings crashed Decimal(). Treat them as zero.

Fixes #142

Signed-off-by: Asha Rao <asha@example.com>"""
print(check_commit(good, "asha@example.com"))

bad = """Fixed stuff"""
for p in check_commit(bad, "asha@example.com"):
    print("-", p)

wrong = """docs: fix typo in README

Signed-off-by: Asha Rao <asha.rao@work.example>"""
print(check_commit(wrong, "asha@example.com"))
```

Output:

```
[]
- subject is not 'type(scope): description'
- missing DCO sign-off (use git commit -s)
['sign-off email does not match the commit author']
```

The last case is common: your Git email is your work address but your sign-off was written for your personal one. Check `git config user.email` in the repository.

### 8. Opening the Pull Request

```bash
git push -u origin fix/empty-gst-field
gh pr create --repo chai-co/chai-bill --fill --draft
```

A good description:

~~~markdown
## What
Treat an empty GST field as zero in `parse_bill()`.

## Why
Fixes #142: uploading a bill with a blank GST column crashed with
`decimal.InvalidOperation`.

## How I tested
- Added `test_empty_gst_is_zero`
- `pytest -q` passes locally (182 passed)

## Notes
I used an AI assistant to draft the test; I've reviewed and run it.
~~~

Things that surprise first-timers:

- **CI may not run yet.** For first-time contributors, maintainers often have to click **Approve and run workflows** before Actions runs on a fork PR. That's a security feature, not a rejection.
- **Allow edits by maintainers** (a checkbox on PRs from forks) lets maintainers push small fixes to your branch. Leave it on.
- **Draft first** if you want early feedback; mark it ready when tests pass.
- **`Fixes #142`** in the description closes the issue when the PR merges.

### 9. Review, Patience and Etiquette

- Reply to every comment, either with a change or a short explanation. Resolve threads only when the reviewer is satisfied (or the project says you can).
- Push follow-up commits (or amend and force-push with `--force-with-lease` if the project prefers a tidy history; some squash on merge anyway).
- **Wait politely.** A gentle ping after a week or two is fine; daily pings aren't.
- If the PR is declined, ask what would make it acceptable, and thank them anyway. Your next PR will be reviewed by the same people.
- **AI tools:** you're responsible for every line. Don't submit code you can't explain, don't flood projects with generated PRs, and follow the project's disclosure policy.

### 10. After the Merge

- Delete your branch and sync your fork's `main` (`gh repo sync` or `git fetch upstream && git switch main && git merge --ff-only upstream/main && git push`).
- Pick up a slightly bigger issue next time. Regular contributors often become reviewers, then maintainers.

---

## Try It Yourself

1. Find three open `good first issue`s in a Python project you use. For each, write the one-line "claim" comment you'd post.
2. Your PR's DCO check fails on two of five commits. Which single command fixes all of them, and what do you run next?
3. Using `check_commit`, what does `feat: add UPI payment support` with no sign-off return?
4. Your fork's `main` has three commits that upstream doesn't. Why is that a problem, and how do you avoid it?

<details>
<summary>Show answers</summary>

**1.** Something like: "I'd like to work on this. Plan: (one sentence). Expect a PR within a week." Check that nobody else has claimed it first.

**2.** `git rebase --signoff upstream/main`, then `git push --force-with-lease`.

**3.**

```python
print(check_commit("feat: add UPI payment support", "asha@example.com"))
```

Output:

```
['missing DCO sign-off (use git commit -s)']
```

**4.** Every new branch you create from your `main` will carry those commits into your PRs, and syncing with upstream will create merge conflicts. Keep `main` identical to upstream, and do all work on feature branches.

</details>

---

## Real-World Examples

### Example 1: Documentation as a Door

A student fixed a broken example in a popular data library's docs. The PR was merged in two days. A month later, a maintainer tagged her on a related bug, and her third PR was a real feature, reviewed by the same people who now knew her.

### Example 2: The PR That Should Have Been an Issue

A developer spent a weekend adding a plugin system to a small CLI tool and opened a 2,000-line PR. The maintainer closed it: it didn't fit the project's goals. A comment on the issue tracker first would have saved the weekend, or turned it into a smaller, welcome change.

### Example 3: Corporate CLA Delay

An engineer's first PR to a cloud SDK sat for three weeks because the CLA bot needed his employer's corporate agreement. Teams that contribute regularly get the corporate CLA signed once, ahead of time.

---

## Common Misconceptions

### Misconception 1: "I need to be an expert to contribute"

Docs fixes, bug reproductions and tests are valuable and beginner-friendly. Expertise comes from contributing.

### Misconception 2: "No response means my PR is bad"

Maintainers are busy volunteers. Silence usually means "not yet". A polite ping after a week or two is normal.

### Misconception 3: "The DCO is a legal contract like a CLA"

The DCO is a per-commit statement that you have the right to submit the code; a CLA is a separate signed agreement that may grant the project additional rights.

### Misconception 4: "Hacktoberfest means quantity matters"

Projects reject low-effort PRs, and many mark them as spam. One useful PR beats ten whitespace changes.

---

## Interview Relevance

Open source experience comes up in behavioural and technical rounds:

- **Describe a contribution:** the problem, how you discussed it, how you handled review feedback.
- **Fork workflow:** origin versus upstream, rebasing on upstream, `--force-with-lease`.
- **Collaboration skills:** reading CONTRIBUTING.md, writing PR descriptions, responding to review.
- **Legal basics:** DCO versus CLA, licence compatibility.

A common follow-up: *"A maintainer asked for a big change you disagreed with. What did you do?"* Explain your reasoning once, briefly, then defer to the maintainer: it's their project.

---

## Key Takeaways

- **Pick projects you use** and issues labelled for newcomers; **read CONTRIBUTING.md, the code of conduct and SECURITY.md** first.
- **Talk before you build**: claim and discuss issues, especially anything non-trivial.
- **Fork, branch, rebase on upstream**, keep your fork's `main` clean, and update PRs with `--force-with-lease`.
- **Sign off (`git commit -s`) or sign the CLA** as the project requires; follow its commit style.
- **Make review cheap**: small focused diffs, tests, a clear description, patience, and honesty about AI assistance.

---

**Up next:** [Licenses in Plain English](licenses-in-plain-english.md)
