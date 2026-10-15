---
title: "Scenario Drills: Broken main, Leaked Secrets, Lost Work"
course: "Git and GitHub: Zero to Pro"
module: "11. Git and GitHub Interview Prep"
type: Article
level: Advanced
reading_time: 40 min
---

# Scenario Drills: Broken main, Leaked Secrets, Lost Work: The Complete Guide

> 📚 **Before you start**
>
> - [Git Interview Questions Explained](git-interview-questions-explained.md)
> - [The Reflog and Garbage Collection](../course.md#m3) and [Undoing Things](../course.md#m4)
> - [Removing a Leaked Secret from History](../09-security-and-supply-chain/removing-a-leaked-secret-from-history.md)

## Introduction

Fire drills at school felt silly: line up, walk down the stairs, stand in the playground. But the point was that on the day of a real alarm, nobody would have to **think**; their feet would already know the way.

Git emergencies work the same way. When `main` is red ten minutes before a release, or a teammate says "I think I just deleted a week of work", panic makes people reach for `--force` and make things worse. Engineers who have rehearsed the recovery stay calm, because they know Git almost never truly loses committed work, and they know the safe order of moves.

This lesson is a set of drills. Each one gives you the **situation**, the **first thing to do**, the **commands**, **why they work**, and **how to explain it in an interview**. Practise them in a throwaway repository until they're boring.

> 💡 **Key Insight**
>
> In every incident: **stop the damage first, then recover, then prevent**. And remember that **committed work is almost always recoverable** (reflog, dangling objects, other clones, GitHub's PR and activity history), while a **pushed secret is never fully recoverable**, so it's rotated, not hidden.

---

## Core Explanation

### 1. The Incident Framework

Use this shape for every scenario, at work and in interviews:

1. **Contain**: stop things getting worse (pause merges, revoke the key, stop running commands that rewrite history).
2. **Communicate**: tell the team what's happening and who's on it.
3. **Recover**: restore a good state with the **least destructive** tool.
4. **Verify**: tests pass, the right commits are there, the secret no longer works.
5. **Prevent**: a blameless note on what happened and which guardrail would have stopped it.

Before any risky recovery, take a free backup: `git branch backup/before-fix` (a branch costs nothing).

### 2. Drill: `main` Is Broken After a Merge

**Situation:** A PR merged 20 minutes ago; CI on `main` is red and deploys are blocked.

**Contain:** tell the team not to merge on top; if you use a merge queue, it will pause naturally.

**Recover:** prefer **revert** (safe on shared history) over a quick fix you haven't tested:

- On GitHub, open the merged PR and click **Revert**. It creates a branch and a PR that undoes it; merge it once CI passes.
- Or from the command line:

```bash
git switch main && git pull
git log --first-parent --oneline -5
```

Example output:

```
a71c3e2 Merge pull request #418 from chai-co/feat/upi-qr
5be0d91 Merge pull request #417 from chai-co/fix/rounding
```

```bash
git switch -c revert-418
git revert -m 1 a71c3e2          # keep parent 1 (main's side) and undo the PR's changes
git push -u origin revert-418
gh pr create --fill --title "Revert #418: broke main"
```

**Why `-m 1`:** a merge commit has two parents; `-m 1` says "the mainline is parent 1, undo what parent 2 brought in". If the PR was squash-merged, it's a normal commit and plain `git revert <sha>` works.

**Afterwards:** the author fixes the branch and opens a new PR. Remember that re-merging the original branch won't reapply reverted changes; revert the revert, or cherry-pick onto a fresh branch.

**Prevent:** required status checks; "require branches to be up to date" or, better, a **merge queue** (so two PRs that are green separately can't break `main` together); flaky tests fixed or quarantined.

**Interview line:** "Revert first to restore a known-good state, then fix forward without time pressure. Then find out why CI didn't catch it, often a missing required check or two PRs merging without being tested together."

### 3. Drill: A Secret Is in a Pushed Commit

**Situation:** Secret scanning alerts on an API key in `config/settings.py`, pushed an hour ago.

**Contain:** **revoke and rotate the key now.** Everything else waits. Check the provider's logs for use since the push.

**Recover:** decide whether to rewrite history (sensitive personal data or an unrotatable secret: yes; a revoked key: optional). If yes, use `git filter-repo --sensitive-data-removal` with `--replace-text` or `--invert-paths --path`, force-push with `--mirror`, contact GitHub Support for PR refs and cached views, and have everyone re-clone. The full procedure is in [Removing a Leaked Secret from History](../09-security-and-supply-chain/removing-a-leaked-secret-from-history.md).

**Close the alert** as revoked in the Security tab, with a note.

**Prevent:** push protection, a gitleaks pre-commit hook, `.env` in `.gitignore`, and OIDC instead of long-lived cloud keys.

**Variation, secret printed in Actions logs:** rotate it, delete the affected workflow run logs (**Delete all logs** on the run page, or `gh run delete <run-id>` for the whole run), and find out how it escaped masking (often it was transformed, e.g. base64-encoded).

**Interview line:** "A pushed secret is compromised. Rotate first; rewriting history is clean-up, and it can't reach forks or other people's clones anyway."

### 4. Drill: "I Ran `git reset --hard` and Lost My Commits"

**Situation:** On `feat/upi`, you ran `git reset --hard origin/main` to "start fresh" and your two commits vanished.

**Recover:** the **reflog** remembers where HEAD was:

```bash
git reflog -5
```

Example output:

```
9c41e07 HEAD@{0}: reset: moving to origin/main
e5a0b13 HEAD@{1}: commit: feat(upi): QR code payments
7d2c9aa HEAD@{2}: commit: feat(upi): add payment model
3f18c42 HEAD@{3}: checkout: moving from main to feat/upi
9c41e07 HEAD@{4}: pull: Fast-forward
```

The entry just **before** the reset is the state you want. A tiny script shows the reasoning:

```python
reflog = """\
9c41e07 HEAD@{0}: reset: moving to origin/main
e5a0b13 HEAD@{1}: commit: feat(upi): QR code payments
7d2c9aa HEAD@{2}: commit: feat(upi): add payment model
3f18c42 HEAD@{3}: checkout: moving from main to feat/upi
9c41e07 HEAD@{4}: pull: Fast-forward
"""

def before_last(reflog_text, action):
    entries = [line.split(" ", 2) for line in reflog_text.splitlines()]
    for i, (sha, ref, message) in enumerate(entries):
        if message.startswith(action):
            return entries[i + 1][0], entries[i + 1][2]
    return None

print(before_last(reflog, "reset:"))
```

Output:

```
('e5a0b13', 'commit: feat(upi): QR code payments')
```

```bash
git reset --hard e5a0b13          # or: git reset --hard HEAD@{1}
# safer alternative that touches nothing current:
git branch rescue/upi e5a0b13
```

Right after a reset, rebase or merge, `ORIG_HEAD` also points at where you were: `git reset --hard ORIG_HEAD`.

**What can't be recovered:** **uncommitted** changes discarded by `reset --hard` or `git restore`. If they had been **staged** (`git add`), their blobs exist as dangling objects and `git fsck --lost-found` writes them to `.git/lost-found/other/`, without file names. Commit (or stash) early and often.

**Interview line:** "Commits aren't deleted by reset; the branch pointer just moves. The reflog keeps the old positions for 90 days by default, so I find the entry before the reset and point a branch at it."

### 5. Drill: A Dropped Stash or Deleted Branch

**Deleted local branch:** Git prints the hash when it deletes:

```bash
git branch -D feat/upi
```

Example output:

```
Deleted branch feat/upi (was e5a0b13).
```

`git branch feat/upi e5a0b13` brings it back. Lost the message? `git reflog` shows the branch's last commits.

**Deleted branch on GitHub:** the merged or closed PR page has a **Restore branch** button. Otherwise, anyone with a clone can push it back: `git push origin e5a0b13:refs/heads/feat/upi`.

**Dropped or cleared stash:** stashes are commits, so they become dangling commits you can find:

```bash
git fsck --no-reflog | grep "dangling commit"
```

Example output:

```
dangling commit 4b8e2f19c0a3d6e7f8a9b0c1d2e3f4a5b6c7d8e9
```

```bash
git show --stat 4b8e2f19        # check it's your stash (message "WIP on ...")
git stash apply 4b8e2f19
```

**Interview line:** "Branches and stashes are pointers to commits. Deleting the pointer leaves the commit until garbage collection, so I find it via the reflog or `git fsck` and point something at it again."

### 6. Drill: Someone Force-Pushed Over Shared Work

**Situation:** Your teammate's commits disappeared from `release/2.4` after someone ran `git push --force` from an old local copy.

**Contain:** ask everyone **not to pull** the branch yet (pulling would make their copies match the bad state; their reflogs still help, but it's messier).

**Recover:** the lost commits exist in at least one place:

- **The teammate's local clone**: their branch or reflog still has them.
- **Anyone who fetched before the force-push**: `git reflog show origin/release/2.4` shows where their remote-tracking branch used to point.
- **GitHub**: the repository's **Activity** view lists pushes to each branch, including force pushes, with the before and after commits.

```bash
git reflog show origin/release/2.4 -3
```

Example output:

```
3c9d0e1 refs/remotes/origin/release/2.4@{0}: fetch: forced-update
b72f4a8 refs/remotes/origin/release/2.4@{1}: fetch: fast-forward
5e01c2d refs/remotes/origin/release/2.4@{2}: fetch: fast-forward
```

```bash
git switch -c restore-release b72f4a8
git log --oneline 3c9d0e1..b72f4a8           # the commits the force-push removed
```

Then combine the two histories if the force-push also added something new (merge or cherry-pick), and push the repaired branch with `--force-with-lease` or through a PR.

**Prevent:** block force-pushes on shared branches with **rulesets**; teach `--force-with-lease` (which would have refused, since the remote had commits the pusher hadn't fetched).

**Interview line:** "A force-push only moves the remote's pointer. The old commits are still in clones, remote-tracking reflogs and GitHub's activity history. Then I'd add a ruleset blocking force-pushes."

### 7. Drill: Committed to the Wrong Branch

**Situation:** You made three commits on `main` locally that should be on a feature branch, and haven't pushed.

```bash
git branch feat/gst-report               # new branch at your current commit (keeps the 3 commits)
git reset --hard origin/main             # move main back to match the remote
git switch feat/gst-report
```

Already pushed to a shared `main`? Don't rewrite it; revert, or let the commits stand and open a follow-up PR.

**On the wrong feature branch instead:** `git switch right-branch && git cherry-pick <sha1> <sha2>`, then remove them from the wrong branch with `git reset --hard HEAD~2` (if unpushed) or `git revert`.

### 8. Drill: A Rebase Went Wrong

**During the rebase**, with confusing conflicts: `git rebase --abort` returns you exactly to where you started.

**After a finished rebase** that dropped or mangled commits: `git reset --hard ORIG_HEAD` (immediately afterwards), or find the pre-rebase commit in the reflog (look for the entry before `rebase (start)`) and reset to it.

If you've already force-pushed the bad result to your PR branch, fix it locally and push again with `--force-with-lease`.

### 9. Drill: Which Commit Broke It?

**Situation:** The bill PDF export worked in last month's release (`v2.3.0`) but not now; there are 200 commits in between.

```bash
git bisect start
git bisect bad HEAD
git bisect good v2.3.0
git bisect run python -m pytest -q tests/test_pdf_export.py
```

Example output:

```
...
4d7e1a2c is the first bad commit
commit 4d7e1a2c
    refactor(pdf): switch to new font loader
bisect found first bad commit
```

```bash
git bisect reset
```

Binary search halves the range each step:

```python
import math

def bisect(commits, is_bad):
    """commits[0] is known good, commits[-1] is known bad."""
    good, bad = 0, len(commits) - 1
    steps = 0
    while bad - good > 1:
        mid = (good + bad) // 2
        steps += 1
        verdict = "bad" if is_bad(commits[mid]) else "good"
        if verdict == "bad":
            bad = mid
        else:
            good = mid
    return commits[bad], steps

commits = [f"c{n:03d}" for n in range(1, 201)]
print(bisect(commits, lambda c: c >= "c137"))
print(math.ceil(math.log2(len(commits) - 1)))
```

Output:

```
('c137', 8)
8
```

Eight test runs instead of up to 199. `git bisect run` treats exit code 0 as good, 1 to 127 (except 125) as bad, and 125 as "can't test this commit, skip it".

### 10. Drill: The Push Is Rejected

| Message | Meaning | Fix |
|---|---|---|
| `! [rejected] main -> main (fetch first)` or `(non-fast-forward)` | The remote has commits you don't | `git pull --rebase` (or fetch and merge), then push. Never force a shared branch. |
| `GH013: Repository rule violations found` | A ruleset blocks it (direct push to `main`, unsigned commits, etc.) | Push a branch and open a PR, or sign commits |
| `GH001: Large files detected` / file exceeds 100 MB | A file over GitHub's limit is in your commits | Remove it from the unpushed commits (amend or `git lfs migrate import`) and use LFS |
| `GH013: ... Push cannot contain secrets` | Push protection found a secret | Remove it from the commits (amend or interactive rebase) and rotate it if it was real |
| `Permission denied (publickey)` / 403 | Authentication or access problem | Check `ssh -T git@github.com`, `gh auth status`, token scopes, SSO authorisation |

### 11. Drill: A Compromised Action

**Situation:** A third-party action your workflows use is reported compromised.

1. **Contain**: block it with the organisation's allowed-actions policy (`!owner/action@*`) or disable affected workflows.
2. **Assess**: search for uses across the organisation, and review recent runs' logs for exfiltrated data.
3. **Rotate** every secret those workflows could access; revoke cloud sessions if OIDC roles were reachable.
4. **Recover**: remove the action or pin it to a verified-clean commit SHA.
5. **Prevent**: pin all actions to SHAs with Dependabot updates, `permissions: {}` by default, and environment-scoped secrets (see [Hardening Actions](../09-security-and-supply-chain/hardening-actions-pinning-and-least-privilege.md)).

### 12. Practising Safely

Create a scratch repository and break it on purpose:

```bash
mkdir drill && cd drill && git init -b main
for n in 1 2 3 4 5; do echo "line $n" >> notes.txt; git add notes.txt; git commit -qm "commit $n"; done
git reset --hard HEAD~3          # "lose" three commits
git reflog                       # now get them back
```

Time yourself on each drill until recovery takes under two minutes.

---

## Try It Yourself

1. A merged PR (merge commit `a71c3e2`) broke `main`. Write the two commands that create the revert commit on a new branch.
2. Using `before_last`, which commit would you restore if the reflog's newest entry were `rebase (finish): returning to refs/heads/feat/upi` and you searched for `"rebase (start)"` in this reflog?

   ```text
   1aa2bb3 HEAD@{0}: rebase (finish): returning to refs/heads/feat/upi
   1aa2bb3 HEAD@{1}: rebase (pick): feat(upi): QR code payments
   0ff9e88 HEAD@{2}: rebase (start): checkout main
   e5a0b13 HEAD@{3}: commit: feat(upi): QR code payments
   ```

3. How many `git bisect` steps do you need for roughly 1,000 commits?
4. In an interview: "You accidentally force-pushed `main` and two colleagues' commits disappeared. Talk me through it."

<details>
<summary>Show answers</summary>

**1.**

```bash
git switch -c revert-418 origin/main
git revert -m 1 a71c3e2
```

**2.**

```python
rebased = """\
1aa2bb3 HEAD@{0}: rebase (finish): returning to refs/heads/feat/upi
1aa2bb3 HEAD@{1}: rebase (pick): feat(upi): QR code payments
0ff9e88 HEAD@{2}: rebase (start): checkout main
e5a0b13 HEAD@{3}: commit: feat(upi): QR code payments
"""
print(before_last(rebased, "rebase (start)"))
```

Output:

```
('e5a0b13', 'commit: feat(upi): QR code payments')
```

`e5a0b13` is the branch tip before the rebase began; `git reset --hard e5a0b13` (or `ORIG_HEAD` right after the rebase) restores it.

**3.**

```python
print(math.ceil(math.log2(1000)))
```

Output:

```
10
```

**4.** Contain: tell everyone not to pull `main`, pause merges. Recover: find the pre-push tip (a colleague's clone, `git reflog show origin/main` on any machine that fetched before, or GitHub's Activity view), restore it on a branch, merge in anything legitimately new, and update `main` through an admin-approved push or PR. Verify CI and the colleagues' commits. Prevent: a ruleset that blocks force-pushes on `main`, and `--force-with-lease` as the team default.

</details>

---

## Real-World Examples

### Example 1: Revert, Then Breathe

An e-commerce team's checkout broke at 7 pm during a sale. The on-call engineer clicked **Revert** on the guilty PR, merged it after CI, and had checkout working in twelve minutes. The fix forward went out the next morning, reviewed properly.

### Example 2: The Reflog Saves a Week

A developer cleaned up with `git reset --hard` on the wrong branch and lost five days of local commits. A senior colleague spent two minutes on `git reflog` and `git branch rescue <sha>`. The team now covers the reflog in onboarding.

### Example 3: A Force-Push and a Ruleset

After a force-push wiped a day of commits from `develop`, recovered from a colleague's clone, the platform team added an organisation ruleset blocking force-pushes and deletions on all default and release branches. It hasn't happened since.

---

## Common Misconceptions

### Misconception 1: "If it's not on any branch, it's gone"

Unreachable commits live until their reflog entries expire and garbage collection prunes them, typically weeks.

### Misconception 2: "Fixing forward is always faster than reverting"

A rushed, untested fix can break things twice. Revert to a known-good state first, unless the fix is trivial and certain.

### Misconception 3: "Deleting the commit removes the secret"

The secret was exposed the moment it was pushed. Rotation is the only real fix.

### Misconception 4: "`git push --force` is how you fix a rejected push"

It overwrites other people's work. Rejected pushes usually mean "integrate first": fetch, rebase or merge, then push.

---

## Interview Relevance

Scenario questions are where interviewers separate people who've used Git from people who understand it:

- **Broken `main`:** revert (`-m 1` for merges), merge queues, required checks.
- **Leaked secret:** rotate first, then filter-repo, Support, re-clone, push protection.
- **Lost work:** reflog, `ORIG_HEAD`, `git fsck` for dangling commits and blobs, PR **Restore branch**.
- **Force-push damage:** remote-tracking reflogs, colleagues' clones, the Activity view, rulesets.
- **Regression hunting:** `git bisect run`, log2(n) steps.
- **Supply chain incident:** block, assess, rotate, re-pin.

Use the framework out loud: *contain, communicate, recover, verify, prevent*. Interviewers listen for calm sequencing and the instinct to make a backup branch before risky moves.

---

## Key Takeaways

- **Contain, communicate, recover, verify, prevent**: and make a backup branch before any risky recovery.
- **Broken `main`?** Revert first (`git revert -m 1` or the PR's **Revert** button), fix forward calmly, add merge queues and required checks.
- **Leaked secret?** Rotate immediately; history clean-up is secondary.
- **Lost commits, branches or stashes?** They're usually still there: `git reflog`, `ORIG_HEAD`, `git fsck`, **Restore branch**, colleagues' clones.
- **Practise in a scratch repository** until bisect, reflog recovery and reverting merges are muscle memory.

---

**Up next:** You've finished Git and GitHub: Zero to Pro. Head back to the [course overview](../course.md) to review any module, or put your skills to work in [Coding Agents and Harness Engineering](../../coding-agents-and-harness-engineering/course.md).
