---
title: "Git Interview Questions Explained"
course: "Git and GitHub: Zero to Pro"
module: "11. Git and GitHub Interview Prep"
type: Article
level: Intermediate
reading_time: 40 min
---

# Git Interview Questions Explained: The Complete Guide

> 📚 **Before you start**
>
> This lesson revises the whole course. It helps most after:
>
> - [How Git Works Inside](../course.md#m3) and [Branching and Merging](../course.md#m4)
> - [Collaborating on GitHub](../course.md#m6)
> - [GitHub Actions](../07-github-actions/workflows-jobs-steps-and-runners.md) and [Security and Supply Chain](../09-security-and-supply-chain/hardening-actions-pinning-and-least-privilege.md)

## Introduction

Preparing for a Git interview by memorising commands is like preparing for a driving test by memorising the dashboard. The examiner wants to see you **drive**: understand what's happening, choose the right move, and recover calmly when something goes wrong.

Git questions show up in almost every software, data, DevOps and ML interview, usually as warm-ups ("merge versus rebase?") that quietly test depth ("so what happens to the commit hashes?"). Strong candidates answer in three layers: **what it does**, **how it works inside**, and **when they'd use it, with a trade-off**.

This lesson collects the questions interviewers actually ask, grouped from fundamentals to GitHub, Actions, security and AI tooling, with model answers, the follow-ups to expect, and the traps. The next lesson turns them into hands-on scenarios.

> 💡 **Key Insight**
>
> Nearly every Git question gets easier with one mental model: **commits are immutable snapshots linked to their parents, and branches, tags and HEAD are just movable labels pointing at them**. Merge, rebase, reset, revert and the reflog all follow from it.

---

## Core Explanation

### 1. How to Answer

For each question, aim for:

1. **One-sentence definition.**
2. **What happens inside Git** (objects, refs, hashes).
3. **When you'd use it, and the trade-off or danger.**
4. **A short example** from your experience if you have one.

Keep answers to 30 to 90 seconds and let the interviewer pull you deeper.

### 2. Fundamentals

**Q1. What's the difference between Git and GitHub?**
Git is a distributed version control tool that runs locally; every clone has the full history. GitHub is a hosting platform built around Git that adds collaboration: pull requests, reviews, issues, Actions, security features, Packages and Pages. GitLab, Bitbucket and Azure Repos are alternatives.

**Q2. What are the three areas of Git?**
The **working tree** (your files), the **staging area or index** (what will go into the next commit), and the **repository** (`.git`, the committed history). `git add` moves changes into the index; `git commit` turns the index into a commit. *Follow-up:* "Why have a staging area?" It lets you build focused commits from a messy working tree, for example with `git add -p`.

**Q3. What does "distributed" mean, and why does it matter?**
Every clone is a complete repository with full history. You can commit, branch, view history and diff offline; there's no single point of failure; and "push" and "pull" sync between equals rather than with a master server.

**Q4. `git fetch` versus `git pull`?**
`fetch` downloads new commits and updates **remote-tracking branches** (`origin/main`) without touching your work. `pull` is `fetch` followed by integrating (merge by default, or rebase with `pull.rebase=true` or `--rebase`). Many engineers fetch first, inspect, then merge or rebase deliberately.

**Q5. What should never be committed?**
Secrets (keys, tokens, `.env`), build outputs and caches, dependencies (`node_modules`, `.venv`), large binaries (use LFS or object storage), and personal IDE settings. Use `.gitignore`, and pre-commit and push protection to catch mistakes.

### 3. Internals

**Q6. What objects does Git store?**
Four: **blobs** (file contents), **trees** (directories: names, modes, and pointers to blobs and trees), **commits** (a tree, parent commit(s), author, committer, message) and **annotated tags**. Objects are stored by the hash of their content.

**Q7. How is a commit hash computed?**
It's the SHA-1 (or SHA-256 in repositories created with that format) of the object's type, size and content. For a blob:

```python
import hashlib

def git_hash_object(content: bytes, kind="blob"):
    header = f"{kind} {len(content)}\0".encode()
    return hashlib.sha1(header + content).hexdigest()

print(git_hash_object(b"hello\n"))
print(git_hash_object(b""))
```

Output:

```
ce013625030ba8dba906f756967f9e9ca394464a
e69de29bb2d1d6434b8b29ae775ad8c2e48c5391
```

These match `echo hello | git hash-object --stdin` and the well-known empty blob hash. A commit's hash covers its tree and **parent hashes**, so changing any old commit changes every hash after it. That's why history is tamper-evident and why rewriting published history is disruptive.

**Q8. What is a branch? What is HEAD?**
A branch is a **ref**: a file containing a commit hash (`.git/refs/heads/main`), which moves forward when you commit. HEAD is a pointer to your current branch (`ref: refs/heads/main`), or directly to a commit in **detached HEAD** state. Creating a branch is just writing 41 bytes, which is why branching is cheap.

**Q9. What's detached HEAD, and is it dangerous?**
HEAD points at a commit rather than a branch (after checking out a tag or hash, or during a rebase). You can look around and even commit, but those commits belong to no branch; switch away and only the reflog remembers them. Fix: `git switch -c new-branch` before leaving.

**Q10. What is the reflog?**
A local log of where HEAD and each branch pointed over time, including resets, rebases and amends. It's the safety net for "I lost my commits": `git reflog`, then `git branch rescue <hash>`. Entries expire (90 days by default for reachable entries, 30 for unreachable), and the reflog isn't pushed or cloned.

**Q11. What does `git gc` do?**
Packs loose objects into compressed packfiles with deltas, and prunes unreachable objects older than the grace period. Git runs it automatically (`gc --auto`). Unreachable commits survive until their reflog entries expire and gc prunes them.

### 4. Branching, Merging and Rewriting

**Q12. Fast-forward versus three-way merge?**
If the target branch hasn't moved since you branched, Git just moves the pointer forward (**fast-forward**), creating no new commit. If both moved, Git finds the **merge base**, combines both sets of changes and creates a **merge commit** with two parents.

```python
PARENTS = {
    "A": [], "B": ["A"], "C": ["B"],
    "D": ["C"], "E": ["D"],          # main
    "F": ["C"], "G": ["F"],          # feature
}

def ancestors(commit):
    seen, stack = set(), [commit]
    while stack:
        c = stack.pop()
        if c not in seen:
            seen.add(c)
            stack.extend(PARENTS[c])
    return seen

def merge_base(a, b):
    common = ancestors(a) & ancestors(b)
    return [c for c in common if not any(c in ancestors(o) - {o} for o in common)]

print(merge_base("E", "G"))
print(sorted(ancestors("G") - ancestors("E")))
print(sorted(ancestors("E") - ancestors("G")))
```

Output:

```
['C']
['F', 'G']
['D', 'E']
```

`C` is the merge base; the merge combines the changes from `C` to `G` with those from `C` to `E`. The last two lines are what `git log main..feature` and `git log feature..main` show.

**Q13. Merge versus rebase?**
Merge preserves history exactly and adds a merge commit; it never rewrites anything. Rebase **replays** your commits on top of another branch, creating **new commits with new hashes** for a linear history. Rule: rebase your own unpublished branches freely; don't rebase commits others have based work on. Squash-merge on GitHub is a third option that turns a PR into one commit.

**Q14. What's interactive rebase for?**
Cleaning up a branch before review: reorder, squash, fixup, reword, edit or drop commits (`git rebase -i main`). With `git commit --fixup <hash>` and `git rebase -i --autosquash`, fix-ups land in the right commit automatically.

**Q15. `reset` versus `revert` versus `restore`?**
`git restore` changes **files** (discard working-tree changes, or unstage with `--staged`). `git reset` moves the **branch pointer** (`--soft` keeps changes staged, `--mixed` keeps them unstaged, `--hard` discards them): it rewrites history, so use it only on unpublished commits. `git revert` creates a **new commit** that undoes an earlier one, safe on shared branches.

**Q16. How do you undo a merged PR on `main`?**
`git revert -m 1 <merge-commit>` (keep parent 1, the mainline), or the **Revert** button on the GitHub PR, which opens a revert PR. *Follow-up trap:* re-merging the same branch later won't bring the changes back, because Git thinks they're already merged; revert the revert first.

**Q17. What's `cherry-pick`?**
It copies the changes of one commit onto your current branch as a new commit, often to backport a fix to a release branch. Overuse leads to duplicate commits with different hashes.

**Q18. How do you resolve a merge conflict?**
Open the conflicted files, choose or combine the sides between `<<<<<<<`, `=======` and `>>>>>>>`, run tests, `git add` the files and `git commit` (or `git rebase --continue`). `git merge --abort` gets you out. `git config rerere.enabled true` remembers resolutions for repeated conflicts. Prevent conflicts with small, short-lived branches.

**Q19. `git stash`, worktrees and bisect?**
`stash` shelves uncommitted changes (`git stash push -m`, `pop`, `apply`). **Worktrees** check out another branch in a second directory from the same repository, which is handy for hotfixes and for running multiple coding agents in parallel. **bisect** binary-searches history for the commit that introduced a bug (`git bisect start`, `bad`, `good`, or `git bisect run <test>`), taking about log2(n) steps.

**Q20. `--force` versus `--force-with-lease`?**
`--force` overwrites the remote branch no matter what. `--force-with-lease` refuses if the remote has commits you haven't seen, protecting a teammate's push. Always use the lease version, and only on your own branches.

### 5. GitHub and Collaboration

**Q21. Walk me through your PR workflow.**
Branch from up-to-date `main`; small commits; push and open a (draft) PR with a clear description and linked issue; CI runs; reviewers (auto-requested by CODEOWNERS) comment; address feedback; required checks and approvals pass; merge via the agreed strategy (often squash) or a merge queue; delete the branch; deploy.

**Q22. Fork versus branch?**
Branches live in the same repository and need write access. Forks are your own copy, used to contribute without write access (typical in open source). Keep an `upstream` remote and rebase on it.

**Q23. How do you protect `main`?**
Branch protection or **rulesets**: require PRs, approvals (with CODEOWNERS review), passing status checks, up-to-date branches or a merge queue, signed commits and linear history if wanted; block force-pushes and deletion. Rulesets can apply across an organisation and to tags.

**Q24. GitHub Flow versus Git Flow versus trunk-based?**
GitHub Flow: short-lived branches off `main`, PR, deploy. Git Flow: `develop`, release and hotfix branches, suited to versioned releases but heavy. Trunk-based: tiny changes merged to `main` at least daily, behind feature flags, with strong CI. Most web teams use GitHub Flow or trunk-based.

**Q25. Squash, merge commit or rebase merge?**
Squash: one tidy commit per PR (lose individual commits). Merge commit: full history plus a record of the PR. Rebase merge: linear history keeping each commit. Teams often pick squash for clean `main` history.

**Q26. What's a merge queue?**
A queue that tests each PR **combined with everything ahead of it** before merging, so `main` never breaks from two individually green PRs that conflict logically. Workflows need the `merge_group` trigger.

### 6. Actions, Security and Supply Chain

**Q27. Explain workflows, jobs, steps and runners.**
A workflow is a YAML file in `.github/workflows/` triggered by events. It has jobs that run in parallel by default (ordered with `needs`) on runners (fresh VMs, or self-hosted machines); each job has steps that run commands or actions.

**Q28. How do you keep secrets safe in Actions?**
Store them as secrets (or environment secrets with required reviewers), pass them only to the steps that need them, prefer **OIDC** short-lived tokens for cloud access, set `permissions:` minimally, never expand untrusted input in `run:`, pin third-party actions to SHAs, and don't expose secrets to fork PRs.

**Q29. What's OIDC and why is it better than stored keys?**
The workflow requests a signed, short-lived token from GitHub describing the run (repository, branch, environment). The cloud provider trusts GitHub's issuer and exchanges the token for temporary credentials if the claims match its policy. Nothing long-lived is stored, so there's nothing to leak or rotate.

**Q30. Why pin actions to a commit SHA?**
Tags can be moved to malicious code (the 2025 `tj-actions/changed-files` compromise did exactly that). A full SHA is immutable. Dependabot updates the pins; organisation policy can require them.

**Q31. You pushed a secret. What do you do?**
Revoke and rotate it immediately; check for misuse; then optionally remove it from history with `git filter-repo`, force-push, contact GitHub Support for PR refs and caches, and have collaborators re-clone. Prevent with push protection and pre-commit scanners. (Drilled in the [next lesson](scenario-drills-broken-main-leaked-secrets-lost-work.md).)

**Q32. What's a software supply chain attack, and what does GitHub offer against it?**
Compromising something you depend on (a package, an action, a build system) rather than your code. Defences: Dependabot alerts and updates, dependency review on PRs, code scanning, secret scanning and push protection, pinned actions, least-privilege tokens, signed commits, and **artifact attestations** proving which workflow built an artifact.

### 7. AI Tools on GitHub

**Q33. How do you use AI coding assistants responsibly in a team?**
Treat AI output like a junior colleague's PR: review it, test it, and own it. Provide repository instructions (`AGENTS.md`, `.github/copilot-instructions.md`) with build, test and style rules; keep humans as required reviewers; give agents least privilege; and watch for invented APIs and insecure patterns.

**Q34. How do coding agents that open PRs fit into GitHub's controls?**
They work on their own branches, push only there, open PRs that need human review, and their workflow runs can require approval. Branch protection, CODEOWNERS and required checks apply as for any contributor; the person who asked the agent can't approve its PR for Copilot's cloud agent.

**Q35. What's MCP and the GitHub MCP server?**
The Model Context Protocol is a standard way to give AI assistants tools and data. The GitHub MCP server exposes GitHub operations (issues, PRs, code, Actions, security alerts) as tools, with toolsets and read-only modes to limit what an agent can do.

### 8. Questions to Ask Them

Good candidates ask too: *"What's your branching and release strategy? How long do PRs usually wait for review? How do you handle secrets and CI security? Do you use merge queues or feature flags? How are AI coding tools used here?"* The answers tell you a lot about engineering culture.

---

## Try It Yourself

1. Answer aloud in under 60 seconds each: Q13 (merge versus rebase), Q15 (reset versus revert) and Q29 (OIDC). Record yourself and check you covered definition, internals, and trade-off.
2. Use `git_hash_object` to compute the hash of a file containing `chai\n`, then check it with `printf 'chai\n' | git hash-object --stdin`.
3. Using `merge_base`, what's the merge base of `D` and `G`? Of `E` and `D`?
4. A teammate says "rebase is dangerous; never use it." Give a balanced answer.

<details>
<summary>Show answers</summary>

**1.** Self-check against the model answers above. Did you mention new hashes for rebase, the branch pointer for reset, and short-lived tokens for OIDC?

**2.**

```python
print(git_hash_object(b"chai\n"))
```

Output:

```
d25ef14ff6dffc8b361da02808cc81eca7f36973
```

**3.**

```python
print(merge_base("D", "G"), merge_base("E", "D"))
```

Output:

```
['C'] ['D']
```

`D` is an ancestor of `E`, so the merge base is `D` itself, and merging `E` into `D`'s branch would be a fast-forward.

**4.** Rebase rewrites commits, so rebasing **shared** history forces everyone else to recover. But rebasing your own unpushed or personal branch is safe and gives a clean, reviewable history; the reflog lets you undo a bad rebase. Use `--force-with-lease` when updating your PR branch.

</details>

---

## Real-World Examples

### Example 1: The Depth Probe

An interviewer asked a candidate "merge or rebase?" The candidate said "rebase is cleaner". Follow-up: "What happens to the commit hashes, and what if a teammate built on your branch?" The candidate who could explain new hashes and `--force-with-lease` got the offer; layer two of the answer is what's being tested.

### Example 2: Whiteboarding a Recovery

A platform team's interview asks candidates to recover a deleted branch on a shared screen. Strong candidates reach for `git reflog` or the PR's **Restore branch** button within a minute, and explain why `git gc` hadn't removed the commits yet.

### Example 3: Security Becomes Standard

Since 2025, many DevOps interviews include a short workflow file to review. Candidates are expected to spot unpinned actions, missing `permissions:`, and `${{ github.event... }}` inside `run:`.

---

## Common Misconceptions

### Misconception 1: "Interviewers want command trivia"

They want understanding and judgement. Knowing that `reset --hard` moves a branch pointer and discards changes beats memorising every flag.

### Misconception 2: "Git stores diffs"

Git stores **snapshots** (trees of blobs); packfiles use deltas only as compression.

### Misconception 3: "Deleted means gone"

Commits stay reachable via the reflog until they expire and gc prunes them, and pushed commits live on in clones, forks and caches.

### Misconception 4: "`git pull` is always safe"

It merges (or rebases) immediately, which can create surprise merge commits or conflicts. Fetching first lets you see what's coming.

---

## Interview Relevance

This whole lesson is interview relevance. How it maps to roles:

- **Software engineers:** Q1–Q26, especially merge/rebase, undoing things, PR workflow and conflict resolution.
- **DevOps and platform engineers:** add Q27–Q32 (Actions, OIDC, pinning, supply chain) and monorepo and LFS topics from module 10.
- **Data and ML engineers:** fundamentals, LFS and DVC, notebooks in Git, CI for models.
- **Senior and lead roles:** branching strategies, protecting `main`, merge queues, security policy, and how the team uses AI agents safely.

---

## Key Takeaways

- **Answer in layers**: definition, what happens inside Git, when to use it and the trade-off.
- **Commits are immutable snapshots; branches, tags and HEAD are movable pointers**: this explains merge, rebase, reset, revert and the reflog.
- **Know the safe tools for shared history** (`revert`, `--force-with-lease`) versus local clean-up tools (`reset`, interactive rebase).
- **GitHub questions** focus on PR workflow, protection rules, merge strategies and merge queues.
- **Modern interviews add Actions security, supply chain and AI-agent questions**: least privilege, OIDC, SHA pinning, secret response, and human review of agent PRs.

---

**Up next:** [Scenario Drills: Broken main, Leaked Secrets, Lost Work](scenario-drills-broken-main-leaked-secrets-lost-work.md)
