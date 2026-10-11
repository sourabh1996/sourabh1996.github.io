---
title: "Removing a Leaked Secret from History"
course: "Git and GitHub: Zero to Pro"
module: "10. Security and Supply Chain"
type: Article
level: Advanced
reading_time: 25 min
---

# Removing a Leaked Secret from History: The Complete Guide

> 📚 **Before you start**
>
> - [How Git Works Inside](../course.md#m3): commits, hashes, refs and the reflog
> - [Rebase and Interactive Rebase](../course.md#m4) and [Undoing Things](../course.md#m4)
> - [Code Scanning and Secret Scanning](code-scanning-and-secret-scanning.md)

## Introduction

It's 11 at night. You pushed a quick fix, and an email arrives: *"Secret scanning found a Stripe API key in chai-co/chai-bill."* Your stomach drops. Somewhere in yesterday's commit is `settings.py` with the live payment key in it, and the repository is public.

The instinct is to delete the line, commit, and push. That does nothing useful. Git remembers **every** version of every file: the key is still in the old commit, in every clone, in every fork, and possibly in GitHub's cached views of the pull request. Bots scrape public GitHub for keys continuously; leaked cloud keys are often abused within minutes.

This lesson gives you the correct order of operations: **revoke first**, then decide whether history needs cleaning, then rewrite it properly with `git filter-repo`, push, and handle the parts you don't control (pull request refs, forks, caches, teammates' clones). Finally, we set up the guardrails so it doesn't happen again.

> 💡 **Key Insight**
>
> Once a secret is pushed, **treat it as stolen**. Rotating the credential is the fix; rewriting history is the clean-up. Do them in that order, because rewriting takes hours of coordination and the attacker needs minutes.

---

## Core Explanation

### 1. Step Zero: Revoke and Rotate

Before touching Git:

1. **Revoke or rotate the credential** at its source (Stripe dashboard, AWS IAM, GitHub token settings, database password). Issue a new one and put it in a secret store, never in code.
2. **Check for abuse.** Look at the provider's logs for activity using the leaked key since the moment it was pushed.
3. **Tell the right people.** Your security team, and if customer data could have been accessed, whoever handles incident reporting.

GitHub's own documentation says that if the data is a secret, rotating it may be enough on its own. After rotation, the string in history is a dead key. You might still remove it, for hygiene, to stop alerts, or because the data itself is sensitive (personal data, a private certificate you can't rotate, internal hostnames), but the urgency is gone.

### 2. Why "Delete and Commit" Doesn't Work

```bash
git log --oneline -- settings.py
```

Example output:

```
d1fb774 Read key from env
391835f Add payment config
```

```bash
git show 391835f:settings.py
```

Example output:

```
PAYMENT_KEY = "sk_live_...."
```

The fix commit `d1fb774` changed the **current** file, but `391835f` still contains the key, and its hash is baked into every later commit's parent chain. The only way to remove it is to create **new** commits that never contained it, which changes the hash of that commit and every commit after it. That's a history rewrite, and everybody who has the old history has to move to the new one.

Finding every place a string appears:

```bash
git log --all -S "sk_live_" --oneline         # commits that added or removed the string
git grep "sk_live_" $(git rev-list --all)      # every commit whose files contain it
```

### 3. The Tool: `git filter-repo`

`git filter-repo` is the tool recommended by both the Git project and GitHub's documentation (the old `git filter-branch` is slow and easy to misuse). GitHub's guide requires version **2.47 or later**, for the `--sensitive-data-removal` flag, which fetches all refs including pull request refs, and reports what you'll need for GitHub Support.

```bash
# install (one of)
brew install git-filter-repo
python3 -m pip install --user git-filter-repo
```

Always work in a **fresh clone**. filter-repo refuses to run in a clone that doesn't look fresh, to protect your unpushed work.

```bash
git clone https://github.com/chai-co/chai-bill
cd chai-bill
```

**Option A: delete a whole file from all history.**

```bash
git filter-repo --sensitive-data-removal --invert-paths --path config/.env
```

`--path` selects paths; `--invert-paths` means "keep everything **except** these". Use the full path from the repository root, and add more `--path` arguments if the file ever lived elsewhere.

**Option B: replace the secret text but keep the file.** Write an expressions file, **outside** the repository so you don't commit it:

~~~text
sk_live_51HxQ9pZ==>PAYMENT_KEY_REMOVED
regex:password\s*=\s*\S+==>password = REMOVED
db.internal.chai.example
~~~

Each line is a literal string (or `regex:` pattern), optionally followed by `==>` and its replacement. A line without `==>` is replaced with `***REMOVED***`.

```bash
git filter-repo --sensitive-data-removal --replace-text ../passwords.txt
```

`--replace-text` only works on text files; for a binary file containing a secret, remove the whole file with Option A.

### 4. What the Rewrite Does to Hashes

A small simulation of `--replace-text` shows why every later commit changes, even ones that never contained the secret:

```python
import hashlib, re

def parse_rules(text):
    rules = []
    for line in text.strip().splitlines():
        find, sep, repl = line.partition("==>")
        repl = repl if sep else "***REMOVED***"
        if find.startswith("regex:"):
            rules.append((re.compile(find[6:]), repl))
        else:
            rules.append((re.compile(re.escape(find.removeprefix("literal:"))), repl))
    return rules

def scrub(content, rules):
    for pattern, repl in rules:
        content = pattern.sub(repl, content)
    return content

def commit_id(parent, files, message):
    data = parent + message + "".join(f"{p}\0{c}" for p, c in sorted(files.items()))
    return hashlib.sha1(data.encode()).hexdigest()[:7]

def rewrite(history, rules):
    old_parent = new_parent = ""
    for message, files in history:
        old = commit_id(old_parent, files, message)
        clean = {p: scrub(c, rules) for p, c in files.items()}
        new = commit_id(new_parent, clean, message)
        status = "changed" if old != new else "same   "
        print(f"{old} -> {new}  {status}  {message}")
        old_parent, new_parent = old, new

key = "sk_live_" + "51Hx" + "Q9pZ"   # a short fake key, built in pieces
history = [
    ("Add README", {"README.md": "# chai-bill"}),
    ("Add payment config", {"README.md": "# chai-bill", "settings.py": f'PAYMENT_KEY = "{key}"'}),
    ("Read key from env", {"README.md": "# chai-bill", "settings.py": 'PAYMENT_KEY = os.environ["PAYMENT_KEY"]'}),
]
rules = parse_rules(f"""
{key}==>PAYMENT_KEY_REMOVED
regex:password\\s*=\\s*\\S+==>password = REMOVED
""")
print(scrub(f'PAYMENT_KEY = "{key}"', rules))
print(scrub("password = hunter2", rules))
rewrite(history, rules)
```

Output:

```
PAYMENT_KEY = "PAYMENT_KEY_REMOVED"
password = REMOVED
1f0566e -> 1f0566e  same     Add README
391835f -> d71475a  changed  Add payment config
d1fb774 -> d7c52cd  changed  Read key from env
```

Commits before the leak keep their IDs. The leaking commit gets a new ID, and so does "Read key from env", even though its files were already clean, because its **parent** changed. filter-repo prints the first changed commit(s) for exactly this reason: everything from there onwards is new history.

### 5. Check, Then Force-Push

Before pushing, check that the secret is gone and look at what changed:

```bash
git log --all -S "sk_live_" --oneline           # should print nothing
grep -c '^refs/pull/.*/head$' .git/filter-repo/changed-refs
```

Example output:

```
2
```

That second command counts the pull requests whose history was affected (drop `-c` to list them). If it's much higher than you expected, stop, throw the clone away and think again: after the next step the rewrite can't be undone.

Push every ref. (In its normal mode filter-repo removes the `origin` remote after a rewrite, to prevent accidental pushes; if `git remote -v` shows nothing, add it back with `git remote add origin <url>` first.)

```bash
git push --force --mirror origin
```

Pushes to `refs/pull/*` will be rejected, because GitHub treats them as read-only; that's expected. If a protected branch rejects the push, an admin may need to relax the protection or ruleset briefly (see [Branch Protection, Rulesets and CODEOWNERS](../course.md#m6)), then restore it immediately.

### 6. The Parts You Don't Control

**Pull request refs and cached views.** Old commits stay reachable through `refs/pull/N/head` and GitHub's cached diff views. Contact **GitHub Support** with the repository name, the number of affected pull requests, and the "First Changed Commit(s)" filter-repo printed (plus any note about orphaned Git LFS objects). Support can dereference or delete the affected PRs, run garbage collection on the server, and remove cached views. They help only with genuinely sensitive data, and only when rotating the credential can't solve the problem.

**Forks.** Each fork is someone else's copy. GitHub can't remove data from it for you or give you its owner's contact details; you need to ask fork owners to delete or clean their forks.

**Everyone's clones.** Teammates still have the old commits. If one of them merges an old branch, the secret comes straight back. Ask everyone to:

```bash
git fetch origin
git switch main
git reset --hard origin/main         # discards local main; save any work first
git rebase --onto origin/main <old-base> feature-branch   # for branches built on old history
```

Rebasing (not merging) their branches onto the new history is the safe route; deleting and re-cloning is simpler still.

**Side effects to expect.** Commit hashes change (breaking links and tools that store them), signed commits and tags lose their signatures, closed pull requests may stop showing diffs, and open pull requests may change. Merge or close open PRs first where you can.

### 7. The BFG Repo-Cleaner

You'll see the **BFG Repo-Cleaner** (a Java tool) in older guides. It works on a bare mirror clone and is fast at two jobs:

```bash
git clone --mirror https://github.com/chai-co/chai-bill.git
java -jar bfg.jar --delete-files .env chai-bill.git
java -jar bfg.jar --replace-text passwords.txt chai-bill.git
cd chai-bill.git
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push
```

By default, BFG doesn't change the files in your latest commit (it assumes you've already fixed HEAD). It's still usable, but GitHub's current guide is written for filter-repo, whose `--sensitive-data-removal` mode also handles pull request refs and the Support report, so prefer filter-repo for GitHub repositories.

### 8. Never Again: Prevention

| Layer | What to set up |
|---|---|
| **Your machine** | A `pre-commit` hook with a secret scanner such as gitleaks, detect-secrets or trufflehog (see [Git Hooks and pre-commit](../11-open-source-and-advanced-git/git-hooks-and-pre-commit.md)) |
| **`.gitignore`** | `.env`, `*.pem`, `credentials.json`, cloud CLI config folders ([.gitignore and What Never to Commit](../course.md#m2)) |
| **GitHub** | Secret scanning **push protection**, which blocks pushes containing known secret formats before they land |
| **Code** | Read secrets from environment variables or a secret manager; commit an `.env.example` with placeholder values |
| **CI** | OIDC instead of long-lived cloud keys, so there's less to leak in the first place |
| **People** | A short, blame-free incident runbook (this lesson) so the first move is "rotate", not "hide" |

---

## Try It Yourself

1. **Order of operations.** A teammate pushed an AWS access key to a private repository 20 minutes ago. Put these in order: force-push the rewritten history; deactivate the key in IAM; run `git filter-repo`; check CloudTrail for use of the key; ask teammates to rebase.
2. **Choose the option.** For each, would you use `--invert-paths --path` or `--replace-text`? (a) `deploy/prod.pem` was committed; (b) a password appears in one line of a 400-line `settings.py`; (c) a binary `keystore.jks` file.
3. **Extend the simulation.** Using `parse_rules` and `scrub`, what does a rule line with no `==>` produce for the text `host = db.internal.chai.example`?
4. **Spot the leak.** Why does `git log --all -S "sk_live_"` find leaks that `git grep "sk_live_"` (with no revision arguments) misses?

<details>
<summary>Show answers</summary>

**1.** Deactivate the key in IAM; check CloudTrail; run `git filter-repo`; force-push; ask teammates to rebase (and contact Support if PR refs are affected).

**2.** (a) `--invert-paths --path deploy/prod.pem` (and rotate the certificate); (b) `--replace-text`, to keep the rest of the file; (c) `--invert-paths --path`, because `--replace-text` doesn't touch binary files.

**3.**

```python
print(scrub("host = db.internal.chai.example", parse_rules("db.internal.chai.example")))
```

Output:

```
host = ***REMOVED***
```

**4.** `git grep` without revisions only searches the current working tree, where the secret is already gone. `git log --all -S` searches the diffs of every commit on every ref.

</details>

---

## Real-World Examples

### Example 1: Rotate, Then Tidy

A startup's intern pushed a SendGrid key to a public repository. Secret scanning's partner programme notified SendGrid, which revoked it; the team got an alert within minutes. They issued a new key from the secret manager, then cleaned history the following morning, calmly, with filter-repo, because the old key no longer worked.

### Example 2: The Secret That Came Back

A team rewrote history to remove a database password but didn't tell a contractor, who merged his old feature branch a week later. The password reappeared in `main`. Their runbook now ends with "everyone deletes and re-clones" and a secret-scanning push protection rule that would have blocked the merge.

### Example 3: When Rewriting Isn't Worth It

An internal tool's repository contained a long-rotated test token from 2019. Rewriting would have broken hundreds of links to commits in tickets. The security team confirmed the token was dead, closed the secret-scanning alert as "revoked", and left history alone.

---

## Common Misconceptions

### Misconception 1: "Deleting the file in a new commit removes it"

The old commit still contains it, and anyone can check it out.

### Misconception 2: "A private repository means the secret is safe"

Every collaborator, every CI log, every integration and every laptop clone has it. Rotate anyway.

### Misconception 3: "Force-pushing erases it from GitHub"

Pull request refs, cached views and forks can still hold the old commits. That's what GitHub Support and fork owners are for.

### Misconception 4: "Rewriting history is the main fix"

Rotation is the fix. Rewriting is optional clean-up that's sometimes worth doing.

---

## Interview Relevance

"You've pushed a secret, what do you do?" is a classic DevOps and security interview question. A strong answer has this shape:

- **Revoke and rotate immediately**, then check for misuse.
- **Explain why a new commit isn't enough**: history and hashes.
- **Rewrite with `git filter-repo`** (`--invert-paths --path` or `--replace-text`), verify with `git log --all -S`, force-push.
- **Handle what's outside your control**: PR refs and caches (GitHub Support), forks, teammates' clones (rebase or re-clone).
- **Prevent recurrence**: push protection, pre-commit scanners, `.gitignore`, OIDC.

Common follow-ups: *"Why not `git filter-branch`?"* (slow, error-prone, discouraged by Git's own docs). *"What breaks after a rewrite?"* (hashes, signatures, PR diffs, people's clones).

---

## Key Takeaways

- **A pushed secret is a stolen secret**: revoke and rotate first, then check for abuse.
- **A follow-up commit doesn't remove anything**; only rewriting history does, and it changes every later hash.
- **Use `git filter-repo --sensitive-data-removal`** with `--invert-paths --path` for files or `--replace-text` for strings, in a fresh clone, then `git push --force --mirror`.
- **Contact GitHub Support** for PR refs and cached views, ask fork owners to clean up, and have every collaborator re-clone or rebase.
- **Prevent it**: push protection, pre-commit secret scanners, `.gitignore` and short-lived credentials.

---

**Up next:** [Contributing to Open Source](../11-open-source-and-advanced-git/contributing-to-open-source.md)
