---
title: "SSH Keys, Tokens and the GitHub CLI"
course: "Git and GitHub: Zero to Pro"
module: "5. Remotes and GitHub Basics"
type: Article
level: Intermediate
reading_time: 22 min
---

# SSH Keys, Tokens and the GitHub CLI: The Complete Guide

> 📚 **Before you start**
>
> - [clone, fetch, pull and push](clone-fetch-pull-and-push.md)
> - [SSH and Remote Servers](../../the-command-line-and-linux-basics/course.md#m3) (The Command Line and Linux Basics), for what an SSH key pair is
> - [Installing and Configuring Git](../02-version-control-from-scratch/installing-and-configuring-git.md), for `git config` levels

## Introduction

The first time most people push to GitHub, they type their GitHub password when asked and get an error. GitHub stopped accepting account passwords for Git operations in 2021. Instead, your computer proves who you are with either a **token** sent over HTTPS or a **key** used over SSH. Setting this up properly once saves you from typing secrets all day and, more importantly, from leaking them.

This article covers both routes from zero. You'll learn what each one is, how to set it up on any operating system, how Git remembers credentials, how to install and use the GitHub CLI (`gh`), which can do the whole setup for you, and how to sign your commits so GitHub shows them as **Verified**. You'll also learn to read the common authentication errors and fix them.

By the end you'll be able to choose between HTTPS and SSH, create a fine-grained personal access token with the minimum permissions, configure a credential helper, generate and protect an Ed25519 SSH key, load it into `ssh-agent`, write an `~/.ssh/config` entry, switch a remote between HTTPS and SSH, log in with `gh auth login`, and sign commits with your SSH key.

> 💡 **Key Insight**
>
> Authentication answers one question: "which GitHub account is this?" Over **HTTPS**, Git sends a **token** (a long random password with limited permissions), usually supplied by a **credential helper** so you never type it. Over **SSH**, your machine proves it holds a **private key** whose public half you uploaded to GitHub; the private key never leaves your machine. Both are secure. Pick one per machine, protect the secret, and let tools (a credential manager, `ssh-agent`, or `gh`) handle it for you.

---

## Core Explanation

### 1. Two Ways In: HTTPS and SSH URLs

Every GitHub repository has two clone URLs, shown under the green **Code** button:

| Protocol | URL | Proves identity with | Port |
|----------|-----|----------------------|------|
| HTTPS | `https://github.com/asha-rao/chai-ledger.git` | Token (via a credential helper) | 443 |
| SSH | `git@github.com:asha-rao/chai-ledger.git` | SSH key pair | 22 (443 as fallback) |

In the SSH URL, `git` is the user name every GitHub SSH connection uses; GitHub identifies **you** by which key you present, not by the user name. Public repositories can be cloned over HTTPS with no authentication at all. You need credentials to push, and to clone or fetch private repositories.

| Choose HTTPS when | Choose SSH when |
|-------------------|-----------------|
| You want the simplest setup, especially on Windows or macOS with a credential manager | You already use SSH keys for servers |
| A corporate firewall blocks port 22 | You want one key for every repository with no token expiry |
| You use the GitHub CLI and want it to handle everything | You also want to sign commits with the same key |

### 2. Tokens: Passwords with Limits

A **personal access token (PAT)** replaces your password over HTTPS. GitHub offers two kinds:

| Kind | Prefix | Permissions | Recommendation |
|------|--------|-------------|----------------|
| **Fine-grained** | `github_pat_` | Chosen per repository and per permission (for example "Contents: read and write" on one repository) | Prefer this |
| **Classic** | `ghp_` | Broad scopes such as `repo`, covering every repository you can access | Only when a tool doesn't support fine-grained tokens |

Create one at **Settings → Developer settings → Personal access tokens**. Give it:

- A **name** that says where it's used ("laptop git", "CI deploy").
- An **expiration**. Short is safer; you'll get an email before it expires.
- **Repository access**: only the repositories it needs.
- **Permissions**: for pushing code, "Contents: Read and write" (metadata read access is added automatically).

GitHub shows the token **once**. When Git asks for a password over HTTPS, paste the token, not your account password. Never put a token in a URL like `https://asha-rao:TOKEN@github.com/...`: it ends up in `.git/config`, shell history and logs.

### 3. Credential Helpers: How Git Remembers

Typing a 90-character token for every push isn't realistic. Git hands authentication to a **credential helper**, set with `credential.helper`:

| Helper | Where it keeps secrets | Platform |
|--------|-----------------------|----------|
| `manager` (Git Credential Manager) | The OS secure store; can also run a browser login | Windows (bundled with Git for Windows), macOS, Linux |
| `osxkeychain` | macOS Keychain | macOS |
| `libsecret` | GNOME Keyring / KWallet | Linux desktops (must be built or installed separately) |
| `cache` | Memory, for 15 minutes by default (`--timeout=<seconds>`) | macOS, Linux |
| `store` | **Plain text** in `~/.git-credentials` | Anywhere; avoid on shared machines |

To see exactly how helpers behave, you can drive one by hand with `git credential`, the command Git itself uses. Here's the `store` helper on a practice machine, with a fake token:

```bash
git config --global credential.helper store
git config --show-origin --get-all credential.helper
printf "protocol=https\nhost=github.com\nusername=asha-rao\npassword=ghp_EXAMPLEnotARealTokenXXXXXXXXXXXXXXXX\n\n" | git credential approve
cat ~/.git-credentials
```

Example output:

```
file:/home/asha/.gitconfig	store

https://asha-rao:ghp_EXAMPLEnotARealTokenXXXXXXXXXXXXXXXX@github.com
```

`approve` is what Git runs after a successful login: it tells the helper to save the credential. The `store` helper wrote it in **plain text**, readable by anything running as you. That's why the secure-store helpers are better. When Git needs a credential, it runs `fill`:

```bash
printf "protocol=https\nhost=github.com\n\n" | git credential fill
```

Example output:

```
protocol=https
host=github.com
username=asha-rao
password=ghp_EXAMPLEnotARealTokenXXXXXXXXXXXXXXXX
```

And when the server rejects a credential (for example an expired token), Git runs `reject` so the helper forgets it and you're asked again next time:

```bash
printf "protocol=https\nhost=github.com\n\n" | git credential reject
wc -c ~/.git-credentials
```

Example output:

```
0 /home/asha/.git-credentials
```

The file is now empty (zero bytes). Knowing `reject` is handy: if Git keeps using an old, revoked token, erasing it this way (or deleting it from your OS keychain) makes Git prompt again.

Practical setup per platform:

- **Windows:** Git for Windows installs Git Credential Manager. The first push opens a browser window to sign in to GitHub. Nothing else to do.
- **macOS:** `git config --global credential.helper osxkeychain` (Homebrew and Apple's Git usually set this already), or install Git Credential Manager.
- **Linux:** install Git Credential Manager, or let the GitHub CLI act as your helper (section 7).

### 4. SSH Keys: Generate One

An SSH key is a **pair**: a private key that stays on your machine and a public key you give to GitHub. When you connect, GitHub sends a challenge only the private key can answer. Generate an **Ed25519** key, the modern default:

```bash
ssh -V
ssh-keygen -t ed25519 -C "asha@example.com" -f ~/.ssh/id_ed25519
```

Example output:

```
OpenSSH_9.6p1 Ubuntu-3ubuntu13.19, OpenSSL 3.0.13 30 Jan 2024

Generating public/private ed25519 key pair.
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/asha/.ssh/id_ed25519
Your public key has been saved in /home/asha/.ssh/id_ed25519.pub
The key fingerprint is:
SHA256:irjFjm4CBzvx2+/Gfns46VDc/d96y9Be5/h5xsXpbec asha@example.com
The key's randomart image is:
+--[ED25519 256]--+
|                 |
|                 |
|                 |
|o      . . .     |
| =      S . .  ..|
|+ oo . o     ...o|
|.o.o+.o  o   .oo=|
|. o=. o.= .   +=&|
| ++ .=+oo+    o%E|
+----[SHA256]-----+
```

The flags:

- **`-t ed25519`**: the key type. Short keys, fast, strong. Use `-t rsa -b 4096` only for ancient servers that don't support Ed25519.
- **`-C`**: a comment stored with the public key, conventionally your email, so you can recognise it later.
- **`-f`**: the file path. Without it, `ssh-keygen` asks, defaulting to `~/.ssh/id_ed25519`.

**Use a passphrase.** It encrypts the private key file, so a stolen laptop backup doesn't hand over your GitHub account. `ssh-agent` (section 5) means you type it once per session, not per push. You can add or change it later without making a new key:

```bash
ssh-keygen -p -f ~/.ssh/id_ed25519
```

Example output:

```
Enter old passphrase:
Key has comment 'asha@example.com'
Enter new passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved with the new passphrase.
```

Two files now exist:

```bash
ls -l ~/.ssh
cat ~/.ssh/id_ed25519.pub
ssh-keygen -lf ~/.ssh/id_ed25519.pub
```

Example output:

```
total 8
-rw------- 1 asha asha 464 Oct 11 11:34 id_ed25519
-rw-r--r-- 1 asha asha  98 Oct 11 11:34 id_ed25519.pub

ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIO/8OBmkxAN2w/mWZNSzYuoqtEfo8osgyUd17vVbDos/ asha@example.com

256 SHA256:irjFjm4CBzvx2+/Gfns46VDc/d96y9Be5/h5xsXpbec asha@example.com (ED25519)
```

- **`id_ed25519`** is the **private** key, readable only by you (`-rw-------`). Never copy it anywhere, paste it into a chat, or commit it. SSH refuses to use a private key whose permissions are too open.
- **`id_ed25519.pub`** is the **public** key, safe to share. This one line is what you give GitHub.
- **`ssh-keygen -lf`** prints the **fingerprint**, a short hash of the public key. GitHub shows the same fingerprint next to each key in your settings, so you can match them.

### 5. ssh-agent: Type the Passphrase Once

`ssh-agent` is a small background program that holds decrypted keys in memory. You unlock the key once; every `git push` after that uses the agent.

```bash
eval "$(ssh-agent -s)"
ssh-add -l
ssh-add ~/.ssh/id_ed25519
ssh-add -l
```

Example output:

```
Agent pid 17848

The agent has no identities.

Enter passphrase for /home/asha/.ssh/id_ed25519:
Identity added: /home/asha/.ssh/id_ed25519 (asha@example.com)

256 SHA256:irjFjm4CBzvx2+/Gfns46VDc/d96y9Be5/h5xsXpbec asha@example.com (ED25519)
```

`ssh-agent -s` prints shell commands that set `SSH_AUTH_SOCK` (how programs find the agent); `eval` runs them in your current shell. Platform notes:

- **macOS:** an agent is always running. Add `--apple-use-keychain` to `ssh-add` to store the passphrase in the Keychain.
- **Windows:** in an administrator PowerShell, enable the built-in OpenSSH agent service once: `Get-Service ssh-agent | Set-Service -StartupType Automatic` then `Start-Service ssh-agent`. Git for Windows' Git Bash also ships its own `ssh-agent`.
- **Linux desktops:** GNOME and KDE usually run an agent at login.

### 6. Give GitHub the Public Key, Then Test

Copy the contents of `id_ed25519.pub` and add it at **Settings → SSH and GPG keys → New SSH key**, with a title like "Asha's laptop" and type **Authentication Key**. (Or let `gh` do it, section 7.)

Test the connection with `ssh -T git@github.com`. The first time, SSH asks you to confirm GitHub's **host key**, which protects you from connecting to an impostor server. GitHub publishes its fingerprints in its documentation ("GitHub's SSH key fingerprints"); the Ed25519 one is `SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU`. Compare before typing `yes`. SSH then saves the host key in `~/.ssh/known_hosts`. If the key works, GitHub replies with a greeting naming your account, along the lines of "Hi asha-rao! You've successfully authenticated, but GitHub does not provide shell access." That last part is expected: GitHub only accepts Git commands over SSH, not a shell.

Now point an existing clone at the SSH URL:

```bash
git remote -v
git remote set-url origin git@github.com:asha-rao/chai-ledger.git
git remote -v
```

Example output:

```
origin	https://github.com/asha-rao/chai-ledger.git (fetch)
origin	https://github.com/asha-rao/chai-ledger.git (push)

origin	git@github.com:asha-rao/chai-ledger.git (fetch)
origin	git@github.com:asha-rao/chai-ledger.git (push)
```

Nothing else changes: same remote name, same branches and bookmarks, different transport.

### 7. ~/.ssh/config: Defaults, Port 443 and Multiple Accounts

`~/.ssh/config` sets per-host options so you don't need flags. A good GitHub entry:

```
Host github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
  AddKeysToAgent yes
```

`AddKeysToAgent yes` loads the key into the agent the first time you use it. Check what SSH will actually do with `ssh -G`, which prints the final settings without connecting:

```bash
ssh -G github.com | grep -E '^(user|hostname|port|identityfile|addkeystoagent) '
```

Example output:

```
user git
hostname github.com
port 22
identityfile ~/.ssh/id_ed25519
addkeystoagent true
```

**Blocked port 22?** Some office and campus networks block it. GitHub accepts SSH on port 443 at the host `ssh.github.com`:

```
Host github.com
  HostName ssh.github.com
  Port 443
  User git
```

**Two GitHub accounts on one laptop** (say, personal and work)? GitHub identifies you by key, so each account needs its own key, and SSH needs to know which key to offer. Create a host alias:

```
Host github-work
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_work
  IdentitiesOnly yes
```

Then clone work repositories with `git@github-work:company/payments.git`. `IdentitiesOnly yes` stops SSH from offering your personal key first.

### 8. The GitHub CLI: gh

The **GitHub CLI** (`gh`) brings GitHub features (repositories, pull requests, issues, Actions runs) to the terminal, and it can set up authentication for Git too. Install it with your package manager: `winget install --id GitHub.cli` on Windows, `brew install gh` on macOS, or GitHub's apt/dnf repository on Linux (instructions at cli.github.com).

```bash
gh --version
```

Example output:

```
gh version 2.89.0 (2026-03-26)
https://github.com/cli/cli/releases/tag/v2.89.0
```

Log in:

```bash
gh auth login
```

It asks a few questions (GitHub.com or an enterprise server; HTTPS or SSH for Git; log in with a browser or paste a token). With the browser option it shows a one-time code, opens github.com/login/device, and you approve it there. Useful flags, all from `gh auth login --help`:

| Flag | Effect |
|------|--------|
| `-w`, `--web` | Go straight to the browser login |
| `-p`, `--git-protocol ssh` or `https` | Choose the protocol for Git operations |
| `--with-token` | Read a token from standard input (for scripts: `gh auth login --with-token < token.txt`) |
| `-h`, `--hostname` | Log in to a GitHub Enterprise Server instead of github.com |
| `-s`, `--scopes` | Request extra permissions |
| `--skip-ssh-key` | Don't offer to generate or upload an SSH key |

If you choose **HTTPS**, `gh` offers to configure itself as Git's credential helper, which is the same as running `gh auth setup-git`. From then on, `git push` over HTTPS uses `gh`'s stored login, kept in your OS secure store. If you choose **SSH**, `gh` offers to generate a key and upload it for you. Either way, one command finishes the whole setup.

Other day-to-day authentication commands:

| Command | What it does |
|---------|--------------|
| `gh auth status` | Shows which accounts are logged in, the protocol and the token's scopes |
| `gh auth switch` | Switches the active account when you've logged in to more than one |
| `gh auth refresh -s <scope>` | Adds permissions to the existing login |
| `gh auth token` | Prints the current token (handy for scripts; treat the output as a secret) |
| `gh auth logout` | Removes the stored login |
| `gh ssh-key add ~/.ssh/id_ed25519.pub --title "Asha's laptop"` | Uploads an SSH public key |

And a taste of what `gh` does beyond authentication:

```bash
gh repo create chai-ledger --private --source . --push
gh repo clone asha-rao/chai-ledger
gh repo view --web
gh browse menu.txt
```

The first command creates a new private repository on GitHub from the current local repository, adds it as `origin` and pushes. `gh repo clone` accepts the short `owner/name` form and uses your preferred protocol. `gh repo view --web` and `gh browse` open the repository, or a specific file, in your browser. You'll use `gh pr` and `gh issue` heavily in [module 6](../course.md#m6).

### 9. Signing Commits with Your SSH Key

Anyone can set `user.email` to anything, so the author line of a commit proves nothing. A **signature** does: it's made with your private key and checked against your public key. On GitHub, signed commits from keys registered to your account show a **Verified** badge. Since Git 2.34 you can sign with the SSH key you already have instead of setting up GPG:

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
git commit -m "Add the menu"
```

Example output:

```
[main (root-commit) edbec81] Add the menu
 1 file changed, 1 insertion(+)
 create mode 100644 menu.txt
```

`commit.gpgsign true` signs every commit (and `tag.gpgSign true` does the same for annotated tags). For one-off signing, use `git commit -S`. To **verify** signatures locally, Git needs a list of trusted keys, the **allowed signers** file. Without it you'll see an error:

```bash
git log --show-signature -1
```

Example output:

```
error: gpg.ssh.allowedSignersFile needs to be configured and exist for ssh signature verification
commit edbec811a16a4772addafd28e117b7e9bf4cffc2
No signature
Author: Asha Rao <asha@example.com>
Date:   Mon Oct 5 09:15:00 2026 +0530

    Add the menu
```

The commit *is* signed; Git just can't check it yet. Each line of the allowed signers file is an email followed by a public key:

```bash
echo "asha@example.com $(cat ~/.ssh/id_ed25519.pub)" > ~/.ssh/allowed_signers
git config --global gpg.ssh.allowedSignersFile ~/.ssh/allowed_signers
git log --show-signature -1
git log --format="%h %G? %GS %s"
```

Example output:

```
commit edbec811a16a4772addafd28e117b7e9bf4cffc2
Good "git" signature for asha@example.com with ED25519 key SHA256:irjFjm4CBzvx2+/Gfns46VDc/d96y9Be5/h5xsXpbec
Author: Asha Rao <asha@example.com>
Date:   Mon Oct 5 09:15:00 2026 +0530

    Add the menu

edbec81 G asha@example.com Add the menu
```

`%G?` prints `G` for a good signature (`N` means none, `B` bad), and `%GS` prints the signer. `git verify-commit HEAD` checks a single commit and exits non-zero if the signature is bad, which is useful in scripts.

For GitHub to show **Verified**, upload the same public key again as a **Signing Key** (the same settings page, or `gh ssh-key add ~/.ssh/id_ed25519.pub --type signing`), and make sure your commit email is one verified on your account. Repository rules can require signed commits on protected branches ([Branch Protection, Rulesets and CODEOWNERS](../06-collaborating-on-github/branch-protection-rulesets-and-codeowners.md)), and [module 10](../course.md#m10) goes deeper into signing and supply-chain trust.

### 10. Reading Authentication Errors

| Error | Likely cause | Fix |
|-------|--------------|-----|
| `remote: Support for password authentication was removed...` then `Authentication failed` | You typed your account password over HTTPS | Use a token, Git Credential Manager or `gh auth setup-git` |
| `Authentication failed` after it used to work | Token expired or was revoked; the helper keeps sending it | Erase it (`git credential reject` or your keychain), then push again and enter a new one |
| `git@github.com: Permission denied (publickey).` | No key offered, or GitHub doesn't know the key | `ssh-add -l` to check the agent; confirm the key is on GitHub; `ssh -vT git@github.com` shows which keys were tried |
| `ERROR: Repository not found.` / `remote: Repository not found.` | Wrong URL, or you're authenticated as an account without access (GitHub hides private repositories from it) | Check `git remote -v`; check which account you are (`ssh -T`, `gh auth status`) |
| `ssh: connect to host github.com port 22: Connection timed out` | Port 22 blocked | Use `ssh.github.com` on port 443 (section 7), or HTTPS |
| `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!` | The host key differs from `known_hosts` (either a real key rotation or an attack) | Compare against GitHub's published fingerprints; if they match, remove the old entry with `ssh-keygen -R github.com` and connect again |

### 11. Keeping Credentials Safe

- **Least privilege:** fine-grained tokens, limited to the repositories and permissions needed, with expiry dates.
- **One key per device:** if a laptop is lost, delete just that key on GitHub.
- **Leaked a token or key?** Revoke it on GitHub **first** (Settings → Developer settings, or Settings → SSH and GPG keys), then clean up. Deleting it from a commit is not enough; it's already in history and possibly in clones ([.gitignore and What Never to Commit](../02-version-control-from-scratch/gitignore-and-what-never-to-commit.md)).
- **Turn on two-factor authentication.** GitHub requires it for accounts that contribute code on github.com.
- **Push protection:** GitHub's secret scanning can block a push that contains a recognisable token; you'll meet it in [module 10](../course.md#m10).

---

## Try It Yourself

1. **Generate and inspect.** Create an Ed25519 key with a passphrase in a test path (`-f ~/.ssh/test_key`). Print its fingerprint. Which file would you upload to GitHub?
2. **Agent.** Start an agent, list its identities, add the test key and list again. What changed?
3. **Credential helper by hand.** On a test machine or a throwaway user, configure `credential.helper store`, `approve` a fake credential, `fill` it, then `reject` it. What does `~/.git-credentials` contain after each step?
4. **Switch protocols.** In any clone, use `git remote set-url` to switch `origin` from HTTPS to SSH and back, checking `git remote -v` each time.
5. **Sign and verify.** Configure SSH signing in a scratch repository, make a commit, set up an allowed signers file, and run `git log --format="%h %G? %s"`. What letter appears for a commit made before you enabled signing?

<details>
<summary>Show answers</summary>

1. `ssh-keygen -t ed25519 -C "you@example.com" -f ~/.ssh/test_key` creates `test_key` (private) and `test_key.pub` (public); `ssh-keygen -lf ~/.ssh/test_key.pub` prints the fingerprint. Upload only the `.pub` file's contents.
2. Before: "The agent has no identities." After `ssh-add ~/.ssh/test_key` and the passphrase: one line with the key's fingerprint and comment.
3. After `approve`: one line, `https://user:token@github.com`. `fill` prints the stored username and password. After `reject`: the file is empty. Remove the helper afterwards with `git config --global --unset credential.helper`.
4. `git remote set-url origin git@github.com:owner/repo.git`, then `git remote set-url origin https://github.com/owner/repo.git`. Only the URLs change.
5. `N` (no signature) for the earlier commit, `G` for the signed one.

</details>

---

## Real-World Examples

### Example 1: A New Laptop in Ten Minutes

A developer joining a team installs Git and `gh`, runs `gh auth login -w -p https`, approves the device code in the browser, and accepts the offer to configure Git. Every clone and push over HTTPS now works, with the login stored in the OS keychain. No token is ever copied by hand.

### Example 2: Separate Work and Personal Identities

A freelancer uses `Host github-client` in `~/.ssh/config` with a separate key for a client's organisation, plus a local `user.email` in each client repository. Commits and pushes never cross accounts, and the client can revoke access by removing one key.

### Example 3: Verified Commits for a Release Team

An open source project requires signed commits on `main`. Maintainers sign with SSH keys registered as signing keys, so every merged commit shows **Verified**, and a commit claiming to be from a maintainer but made by someone else would show **Unverified**.

---

## Common Misconceptions

### Misconception 1: "I'll just use my GitHub password"

GitHub hasn't accepted account passwords for Git operations since 2021. Use a token (preferably through a credential manager or `gh`) or an SSH key.

### Misconception 2: "The public key is secret"

The `.pub` file is meant to be shared; it's what you upload. The **private** key (no extension) is the secret.

### Misconception 3: "SSH is more secure than HTTPS"

Both encrypt traffic and authenticate strongly. The real differences are convenience, firewalls and how the secret is stored and scoped.

### Misconception 4: "My commit email proves I wrote the commit"

Anyone can set any email. Only a signature checked against a registered key proves authorship.

### Misconception 5: "A passphrase means typing it on every push"

With `ssh-agent` (or the macOS Keychain) you type it once per login session.

---

## Interview Relevance

Authentication questions test practical readiness and security awareness:

- **"HTTPS or SSH, and why?"** Explain tokens plus credential helpers versus key pairs, and the trade-offs (firewalls, setup, expiry, signing).
- **"What's a personal access token, and how would you scope one for a CI job?"** Fine-grained, single repository, minimum permissions, short expiry, stored as a secret, never in a URL or file.
- **"You get `Permission denied (publickey)`. Debug it."** `ssh-add -l`, check the key on GitHub, `ssh -vT git@github.com`, check `~/.ssh/config`.
- **"A token was pushed to a public repository. What now?"** Revoke immediately, then rotate, then remove from history and check audit logs.
- **"How do you prove a commit came from you?"** Commit signing (GPG or SSH) and GitHub's Verified badge.

---

## Key Takeaways

- GitHub needs a **token over HTTPS** or a **key over SSH**; account passwords don't work for Git.
- Let a **credential helper** (Git Credential Manager, Keychain or `gh`) store tokens securely; avoid plain-text `store` on shared machines.
- Generate **Ed25519** keys with a **passphrase**, load them with **`ssh-agent`**, and configure hosts in **`~/.ssh/config`** (port 443, multiple accounts).
- **`gh auth login`** sets up authentication end to end; `gh auth status` shows who you are.
- **Sign commits** with your SSH key (`gpg.format ssh`) and register it as a signing key for the Verified badge.
- **Least privilege and fast revocation**: scoped, expiring tokens, one key per device, revoke first if anything leaks.

---

**Up next:** [Forks, Upstreams and Remotes](forks-upstreams-and-remotes.md)
