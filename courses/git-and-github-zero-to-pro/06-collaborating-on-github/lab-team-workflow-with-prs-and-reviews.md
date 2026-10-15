---
title: "Lab: Team workflow with PRs and reviews"
course: "Git and GitHub: Zero to Pro"
module: "6. Collaborating on GitHub"
type: Lab
level: Intermediate
reading_time: 75 min
---

# Lab: Team Workflow with PRs and Reviews

> 📚 **Before you start**
>
> - [Pull Requests End to End](pull-requests-end-to-end.md)
> - [Code Review that Helps](code-review-that-helps.md)
> - [Issues, Labels, Milestones and Projects](issues-labels-milestones-and-projects.md)
> - [Branch Protection, Rulesets and CODEOWNERS](branch-protection-rulesets-and-codeowners.md)
> - [Merge Strategies and Merge Queues](merge-strategies-and-merge-queues.md)
> - [SSH Keys, Tokens and the GitHub CLI](../05-remotes-and-github-basics/ssh-keys-tokens-and-the-github-cli.md), with `gh auth login` done

## What You'll Build

You'll run a small team's GitHub Flow from start to finish on a real GitHub repository, `team-ledger`, playing two developers: **Asha**, who owns the repository, and **Ravi**, a teammate. Along the way you'll:

1. Create the repository with a tiny Python project and a CI check.
2. Protect `main` with a ruleset so every change needs a pull request and a green check.
3. Plan the work with labels, a milestone and two issues.
4. Open Ravi's PR, review it as Asha, and request a change.
5. Merge Asha's own PR first, which puts Ravi's PR into conflict.
6. Have Ravi fix the review comment, rebase, resolve the conflict and force-push safely.
7. Squash-merge, watch issues close automatically, and clean up both clones.

```mermaid
gitGraph
  commit id: "Initial commit"
  commit id: "billing + CI"
  branch 1-add-discounts
  commit id: "apply_discount()"
  checkout main
  branch 2-print-receipt
  commit id: "receipt()"
  checkout main
  merge 2-print-receipt id: "Add receipt() (#4)"
  checkout 1-add-discounts
  commit id: "reject bad %"
  checkout main
  merge 1-add-discounts id: "Add discounts (#3)"
```

(On GitHub both PRs are squash-merged, so `main` ends up as a straight line: the diagram shows where each change came from.)

> 💡 **Key Insight**
>
> A team workflow is **Git plus agreements, enforced by GitHub**: branches and pushes are plain Git; issues, reviews, required checks and merge buttons are GitHub. Keep asking two questions at each step: "What changed in Git (which refs moved)?" and "What changed on GitHub (which PR, issue or check state)?"

**Working alone or with a partner?** Both work. With a partner, they play Ravi on their own GitHub account (add them under **Settings → Collaborators**), and you can require one approval. Alone, you play both roles from two local clones of the same repository, with Ravi's name set as a local Git identity. GitHub won't let you approve your own pull request, so in the solo track you set required approvals to 0 and leave reviews as comments; everything else is identical.

The Git outputs below were captured with Git 2.43 against a practice server; on GitHub, your URLs and hashes will differ.

---

## Step 1: Create the Repository

Create a public repository (rulesets are free on public repositories) with a README, and clone it:

```bash
gh repo create team-ledger --public --add-readme --clone
cd team-ledger
```

Add three files. `billing.py`:

```python
PRICES = {"masala": 20, "ginger": 25, "elaichi": 25}


def bill(items):
    return sum(PRICES[name] * qty for name, qty in items)
```

`test_billing.py`, a test that needs no extra packages:

```python
# not-run: imports billing.py from the project folder
import billing

assert billing.bill([("masala", 2), ("ginger", 1)]) == 65
print("all tests passed")
```

And `.github/workflows/test.yml`, a minimal GitHub Actions workflow that runs the test on every pull request and every push to `main`. You'll learn every line in [module 7](../course.md#m7); for now it gives you a **status check** named `test`:

```yaml
name: test
on:
  pull_request:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - run: python3 test_billing.py
```

Run the test, commit and push. This is the last time anyone pushes straight to `main`:

```bash
python3 test_billing.py
git add billing.py test_billing.py .github/workflows/test.yml
git commit -m "Add billing, a test and CI"
git push
```

Example output:

```
all tests passed

[main baa159f] Add billing, a test and CI
 3 files changed, 21 insertions(+)
 create mode 100644 .github/workflows/test.yml
 create mode 100644 billing.py
 create mode 100644 test_billing.py

To https://github.com/asha-rao/team-ledger.git
   fb7f8eb..baa159f  main -> main
```

Open the **Actions** tab and wait for the `test` run to go green. A required check has to have run at least once before you can select it in Step 2.

---

## Step 2: Protect main

**Settings → Rules → Rulesets → New ruleset → New branch ruleset**:

1. Name: `Protect main`. Enforcement status: **Active**.
2. Bypass list: leave empty.
3. Target branches: **Add target → Include default branch**.
4. Rules:
   - **Restrict deletions** and **Block force pushes** (on by default).
   - **Require a pull request before merging**: required approvals **1** with a partner, **0** solo; tick **Dismiss stale pull request approvals when new commits are pushed** and **Require conversation resolution before merging**. Under **Allowed merge methods**, keep only **Squash**.
   - **Require status checks to pass**: add the `test` check.
5. **Create**.

Then, under **Settings → General → Pull Requests**, tick **Automatically delete head branches**.

Check from the terminal:

```bash
gh ruleset check main
```

It lists the rules that now apply to `main`. Optionally prove the protection works: make a throwaway commit on `main`, try `git push`, read the `[remote rejected]` line and the `remote:` explanation, then undo the commit with `git reset --hard origin/main`.

---

## Step 3: Plan the Work

Create two labels, a milestone, and two issues:

```bash
gh label create "area: billing" --color FBCA04 --description "Totals, discounts, receipts"
gh api repos/{owner}/{repo}/milestones -f title="v0.2"
gh issue create --title "Support percentage discounts" --body "Staff want to give 10% off to regulars." --label "enhancement,area: billing" --milestone "v0.2"
gh issue create --title "Print a receipt line with the total" --body "Show 'Total: Rs N' for an order." --label "enhancement,area: billing" --milestone "v0.2"
```

`gh` has no dedicated milestone command, so the second line calls the REST API directly; `{owner}` and `{repo}` are filled in from the current repository. (You can also create the milestone on the web under **Issues → Milestones**.) The issues get numbers **#1** (discounts, for Ravi) and **#2** (receipt, for Asha). Assign them on the web or with `gh issue edit 1 --add-assignee <login>`.

---

## Step 4: Ravi Opens a Pull Request

**Solo track:** make a second clone in a sibling folder and give it Ravi's identity, local to that clone only:

```bash
cd ..
gh repo clone team-ledger ravi-ledger
cd ravi-ledger
git config user.name "Ravi Kumar"
git config user.email "ravi@example.com"
```

(With a partner, they clone with their own account instead.) Ravi starts a branch named after the issue:

```bash
git switch -c 1-add-discounts
```

Example output:

```
Switched to a new branch '1-add-discounts'
```

He appends to `billing.py`:

```python
def apply_discount(total, percent):
    return total - total * percent / 100
```

and to `test_billing.py`:

```python
# not-run: continues test_billing.py
assert billing.apply_discount(200, 10) == 180
print("discount tests passed")
```

Test, commit with a closing keyword, and push:

```bash
python3 test_billing.py
git commit -am "Add apply_discount()" -m "Closes #1"
git push -u origin 1-add-discounts
```

Example output:

```
all tests passed
discount tests passed

[1-add-discounts 92b4dcc] Add apply_discount()
 2 files changed, 6 insertions(+)

To https://github.com/asha-rao/team-ledger.git
 * [new branch]      1-add-discounts -> 1-add-discounts
branch '1-add-discounts' set up to track 'origin/1-add-discounts'.
```

Open the PR, filling the title and body from the commit:

```bash
gh pr create --fill --label "area: billing" --milestone "v0.2"
```

It becomes **#3** (issues and PRs share numbers). On the PR page, watch the `test` check run, and notice the merge box: merging is blocked until requirements are met.

---

## Step 5: Asha Reviews

Back in Asha's clone, fetch and try the branch locally. Because exactly one remote has a branch called `1-add-discounts`, `git switch` creates a local tracking branch for it (`gh pr checkout 3` does the same and works for forks too):

```bash
cd ../team-ledger
git fetch
git switch 1-add-discounts
python3 -c "import billing; print(billing.apply_discount(100, 150))"
git switch main
```

Example output:

```
From https://github.com/asha-rao/team-ledger
 * [new branch]      1-add-discounts -> origin/1-add-discounts

Switched to a new branch '1-add-discounts'
branch '1-add-discounts' set up to track 'origin/1-add-discounts'.

-50.0

Switched to branch 'main'
Your branch is up to date with 'origin/main'.
```

A 150% discount gives a negative bill. On the PR's **Files changed** tab, Asha clicks the `+` beside the `def apply_discount` line and writes:

> **blocking:** `apply_discount(100, 150)` returns -50.0. Could we raise `ValueError` for percentages outside 0–100?

She clicks **Start a review**, then **Finish your review** → **Request changes** (solo track: **Comment**, since you can't request changes on your own PR), and submits. From the terminal, the review-level verdict would be:

```bash
gh pr review 3 --request-changes -b "One blocking comment on apply_discount()."
```

---

## Step 6: Asha's Own PR Lands First

Meanwhile Asha finishes issue #2. Note she branches from `main`, not from Ravi's branch:

```bash
git switch -c 2-print-receipt
```

She appends to `billing.py`:

```python
def receipt(items):
    return f"Total: Rs {bill(items)}"
```

```bash
git commit -am "Add receipt()" -m "Closes #2"
git push -u origin 2-print-receipt
gh pr create --fill
```

Example output:

```
Switched to a new branch '2-print-receipt'

[2-print-receipt 88a2076] Add receipt()
 1 file changed, 4 insertions(+)

To https://github.com/asha-rao/team-ledger.git
 * [new branch]      2-print-receipt -> 2-print-receipt
branch '2-print-receipt' set up to track 'origin/2-print-receipt'.
```

This is PR **#4**. With a partner, they approve it. When the check is green, squash-merge it (the branch is deleted automatically):

```bash
gh pr merge 4 --squash
```

Look at issue #2: it's closed, linked to PR #4. Now open PR #3: GitHub reports **This branch has conflicts that must be resolved**, because both PRs appended to the end of `billing.py`.

---

## Step 7: Ravi Responds and Resolves the Conflict

In Ravi's clone, first address the review. Edit `apply_discount` so it begins with a check:

```python
def apply_discount(total, percent):
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return total - total * percent / 100
```

```bash
cd ../ravi-ledger
git commit -am "Reject discounts outside 0-100%"
git push
```

Example output:

```
[1-add-discounts 8631609] Reject discounts outside 0-100%
 1 file changed, 2 insertions(+)

To https://github.com/asha-rao/team-ledger.git
   92b4dcc..8631609  1-add-discounts -> 1-add-discounts
```

Now bring the branch up to date with `main` by rebasing, since it's Ravi's own branch (the course's recommended conflict style, `zdiff3`, is set from module 4):

```bash
git fetch
git rebase origin/main
```

Example output:

```
From https://github.com/asha-rao/team-ledger
   baa159f..67d27f9  main       -> origin/main

Auto-merging billing.py
CONFLICT (content): Merge conflict in billing.py
error: could not apply 92b4dcc... Add apply_discount()
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
hint: You can instead skip this commit: run "git rebase --skip".
hint: To abort and get back to the state before "git rebase", run "git rebase --abort".
Could not apply 92b4dcc... Add apply_discount()
```

Look at the conflict:

```bash
git diff
```

Example output:

```
diff --cc billing.py
index 0b90d29,2005494..0000000
--- a/billing.py
+++ b/billing.py
@@@ -5,5 -5,5 +5,11 @@@ def bill(items)
      return sum(PRICES[name] * qty for name, qty in items)
  
  
++<<<<<<< HEAD
 +def receipt(items):
 +    return f"Total: Rs {bill(items)}"
++||||||| parent of 92b4dcc (Add apply_discount())
++=======
+ def apply_discount(total, percent):
+     return total - total * percent / 100
++>>>>>>> 92b4dcc (Add apply_discount())
```

During a rebase, **`HEAD` is the new base** (`main` with Asha's `receipt()`), and the other side is the commit being replayed (Ravi's `apply_discount()`). The empty base section shows both sides added code at the same place. The right answer is to keep both. Edit the file so it ends like this, with no markers:

```bash
cat billing.py
python3 test_billing.py
```

Example output:

```
PRICES = {"masala": 20, "ginger": 25, "elaichi": 25}


def bill(items):
    return sum(PRICES[name] * qty for name, qty in items)


def receipt(items):
    return f"Total: Rs {bill(items)}"


def apply_discount(total, percent):
    return total - total * percent / 100

all tests passed
discount tests passed
```

This is the first commit being replayed, so the range check isn't there yet; the second commit adds it. Mark the file resolved and continue (the editor opens with the commit message; save and close it):

```bash
git add billing.py
git rebase --continue
git log --oneline --graph -4
```

Example output:

```
[detached HEAD 9b8b624] Add apply_discount()
 2 files changed, 6 insertions(+)
Successfully rebased and updated refs/heads/1-add-discounts.

* cc56d13 Reject discounts outside 0-100%
* 9b8b624 Add apply_discount()
* 67d27f9 Add receipt() (#4)
* baa159f Add billing, a test and CI
```

Both of Ravi's commits now sit on top of Asha's merged work, with new hashes. Update the PR with a lease, which refuses if anyone else pushed to the branch since Ravi's last fetch:

```bash
git push --force-with-lease
```

Example output:

```
To https://github.com/asha-rao/team-ledger.git
 + 8631609...cc56d13 1-add-discounts -> 1-add-discounts (forced update)
```

On the PR, Ravi replies to Asha's comment ("Done in cc56d13"), and the conflict warning is gone. The `test` check runs again on the new commits.

---

## Step 8: Approve and Merge

As Asha, open the timeline entry "force-pushed the branch" and use **Compare** to see what changed (or run `git range-diff` as in [Code Review that Helps](code-review-that-helps.md)). Check the fix, then **Resolve conversation**. With a partner, submit an **Approve** review (and notice that any earlier approval would have been dismissed by the new push). When `test` is green:

```bash
gh pr merge 3 --squash
```

Check the results on GitHub:

- Issue **#1** is closed, linked to PR #3.
- The **v0.2** milestone shows 100% complete.
- `main` has one commit per PR: "Add receipt() (#4)" and "Add discounts (#3)".
- Both head branches were deleted automatically.

---

## Step 9: Clean Up Locally

In Ravi's clone:

```bash
git switch main
git pull
git fetch --prune
git branch -vv
```

Example output:

```
Switched to branch 'main'
Your branch is behind 'origin/main' by 1 commit, and can be fast-forwarded.
  (use "git pull" to update your local branch)

From https://github.com/asha-rao/team-ledger
   67d27f9..69ec285  main       -> origin/main
Updating baa159f..69ec285
Fast-forward
 billing.py      | 10 ++++++++++
 test_billing.py |  2 ++
 2 files changed, 12 insertions(+)

From https://github.com/asha-rao/team-ledger
 - [deleted]         (none)     -> origin/1-add-discounts

  1-add-discounts cc56d13 [origin/1-add-discounts: gone] Reject discounts outside 0-100%
* main            69ec285 [origin/main] Add discounts (#3)
```

`gone` confirms the remote branch was deleted after merging. Because it was a squash merge, the safe `-d` would refuse ("not fully merged"), so delete with `-D`, then confirm `main`:

```bash
git branch -D 1-add-discounts
git log --oneline
python3 test_billing.py
```

Example output:

```
Deleted branch 1-add-discounts (was cc56d13).

69ec285 Add discounts (#3)
67d27f9 Add receipt() (#4)
baa159f Add billing, a test and CI
fb7f8eb Initial commit

all tests passed
discount tests passed
```

Do the same in Asha's clone (`git switch main`, `git pull`, `git fetch --prune`, then delete `1-add-discounts` and `2-print-receipt` with `-D`).

---

## Try It Yourself

1. **CODEOWNERS.** Add `.github/CODEOWNERS` with `* @<your-login>` and `/billing.py @<partner-login>`, merge it through a PR, and turn on **Require review from Code Owners** in the ruleset. Open a PR touching `billing.py`. Who is requested?
2. **Draft first.** Open the next PR with `gh pr create --draft --fill`, push two more commits to it, then `gh pr ready`. Watch the checks run on each push.
3. **Auto-merge.** Enable **Allow auto-merge** in settings, open a PR, and run `gh pr merge --auto --squash` before the check finishes. What happens when it goes green?
4. **Break and revert.** Merge a PR that changes a price, then use the **Revert** button on the merged PR. What does GitHub create?
5. **Project board.** Create a project for the repository, add both closed issues and a new one, and set up a board grouped by Status with the "item closed" workflow.

<details>
<summary>Show answers</summary>

1. GitHub requests the owner of the last matching pattern: your partner for `billing.py`, you for other files. The PR can't merge until a code owner approves.
2. The draft can't be merged; checks run on every push regardless. `gh pr ready` switches it to ready for review.
3. The PR merges itself as soon as all requirements are met, and the branch is deleted if automatic deletion is on.
4. A new branch and a new PR containing a revert commit. It still has to pass the same rules before merging.
5. Closed issues land in Done automatically once the workflow is enabled; the new one starts in the default column.

</details>

---

## What You've Learned

- **Protecting `main`** with a ruleset turns team agreements (PRs, green checks, resolved conversations, no force pushes) into rules GitHub enforces.
- **Issues, labels and milestones** plan the work; **`Closes #n`** in commits or PR descriptions closes issues automatically on merge.
- **Reviewing** means running the code, leaving specific, labelled comments, and submitting a verdict.
- When `main` moves under an open PR, **rebase, resolve, test and `--force-with-lease`** updates it safely.
- **Squash merges** give one commit per PR on `main`; afterwards, `git pull`, `git fetch --prune` and `git branch -D` clean up.

---

**Up next:** [Workflows, Jobs, Steps and Runners](../course.md#m7), in module 7, where the CI workflow you just used gets explained line by line.
