---
title: "SSH and Remote Servers"
course: The Command Line and Linux Basics
module: "3. Working Like a Developer"
type: Article
level: Beginner
reading_time: 35 min
---

# SSH and Remote Servers: The Complete Guide

> 📚 **Before you start**
>
> - [Permissions and Users](../02-terminal-fundamentals/permissions-and-users.md): `chmod 600`/`700`, users and `sudo`. SSH is strict about permissions.
> - [Processes, Ports and Environment Variables](processes-ports-and-environment-variables.md): ports, background processes and `nohup`.
> - [Shell Scripts and cron](shell-scripts-and-cron.md): useful for running jobs on a server once you're connected.

## Introduction

Somewhere in a data centre in Mumbai or Hyderabad, there's a computer with no screen, no keyboard and no mouse. It runs your company's API, or a nightly data pipeline, or a GPU training job for a model. You need to check its logs, deploy new code and restart a service. You can't walk up to it. You may not even know which building it's in.

You'll use **SSH**, the Secure Shell. One command on your laptop opens a terminal on that machine, encrypted end to end, as if you were sitting in front of it. Everything you've learned in this course (files, permissions, processes, pipes, scripts, cron) works there exactly the same way, because a typical cloud server is just a Linux machine you reach over the network.

This lesson takes you from your first connection to working comfortably on remote machines. You'll create an SSH key pair and understand why keys beat passwords, install your key on a server, write a config file so `ssh prod` is all you type, copy files with `scp` and `rsync`, keep jobs running after you disconnect with `tmux`, reach a remote web app through a tunnel, and secure a fresh server. You'll also learn to read the common SSH errors, which look scary but usually have one-line fixes.

> 💡 **Key Insight**
>
> SSH key authentication uses a **pair** of keys. The **public key** is like a padlock: you can hand out copies freely and fit them on any server. The **private key** is the only key that opens those padlocks: it never leaves your machine and must be readable only by you. Get those two facts right and most of SSH falls into place.

---

## Core Explanation

### 1. What SSH Is

**SSH** is a **protocol** (an agreed set of rules) for logging into and running commands on another computer securely over a network. There are two sides:

- The **SSH client**, the `ssh` command on your laptop. It's built into Linux, macOS, WSL and Windows 10 and 11.
- The **SSH server**, a background service (`sshd`, the SSH daemon) on the remote machine, listening on **port 22** by default.

Everything that passes between them, including your password, your commands and their output, is **encrypted**. Before SSH (in the 1990s), people used `telnet`, which sent everything, passwords included, as plain readable text.

```mermaid
flowchart LR
  subgraph Laptop["Your laptop"]
    C["ssh client<br/>+ private key"]
  end
  subgraph Server["Remote server (203.0.113.10)"]
    D["sshd on port 22<br/>+ your public key"]
    SH["bash, running as you"]
  end
  C <-->|"encrypted connection"| D
  D --> SH
```

Where do servers come from? Most often a **cloud provider**: AWS EC2, Google Cloud Compute Engine, Azure, DigitalOcean and others rent you a **virtual machine (VM)** by the hour. When you create one, the provider gives you its **IP address** and a user name (for example `ubuntu` on Ubuntu images on AWS) and asks for your public key. A Raspberry Pi on your desk, a lab machine at college, or a GPU box at work are reached the same way.

The examples use the address `203.0.113.10`, a range reserved for documentation. Replace it with your server's real address.

### 2. Your First Connection

The basic form is `ssh user@host`:

```bash
ssh ubuntu@203.0.113.10
```

The very first time you connect to a server, SSH can't be sure it's really the machine you meant, so it shows the server's **fingerprint** and asks:

Example output:

```
The authenticity of host '203.0.113.10 (203.0.113.10)' can't be established.
ED25519 key fingerprint is SHA256:3vC2bYk9mJq7rT0xWnL4pHs8aZd1fGe6uKoRi5NcVyE.
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '203.0.113.10' (ED25519) to the list of known hosts.
Welcome to Ubuntu 24.04 LTS (GNU/Linux x86_64)
...
ubuntu@ip-172-31-5-20:~$
```

Type `yes` and press Enter. SSH saves the fingerprint in `~/.ssh/known_hosts` and checks it on every future visit. If the fingerprint ever changes, SSH refuses to connect, because someone might be impersonating the server (more in section 11). Cautious teams compare the fingerprint with the one shown in the cloud console before typing `yes`.

Notice the prompt changed: you're now typing on the **server**. `hostname`, `whoami`, `ls` and `df -h` all describe the remote machine. To leave, type `exit` or press **Ctrl + D**, and you're back on your laptop.

Useful variations:

```bash
ssh -p 2222 ubuntu@203.0.113.10          # server listens on a non-standard port
ssh -i ~/.ssh/aws-key.pem ubuntu@203.0.113.10   # use a specific private key file
ssh ubuntu@203.0.113.10 'df -h / && uptime'     # run commands and come straight back
```

The last form runs commands remotely and prints the output locally, without opening an interactive session. Quote the remote command so your local shell doesn't interpret `&&`, pipes or variables before sending it.

### 3. Passwords vs Keys

SSH can authenticate you with a password, but keys are better in every way:

| | Password | SSH key |
|---|---|---|
| **Can be guessed?** | Yes; bots try millions of common passwords against every public server, all day | Practically impossible |
| **Sent to the server?** | Yes (encrypted, but the server sees it) | No; you prove you hold the private key without revealing it |
| **Reused elsewhere?** | Often, sadly | Each server only has your public key |
| **Convenient?** | Type it every time | No typing once loaded into an agent |
| **Used by GitHub, cloud VMs, CI?** | Rarely accepted | Standard |

How does a key "prove" something without being sent? When you connect, the server uses your **public key** to set a challenge that only the matching **private key** can answer. Your client answers it locally and sends back the proof. The private key itself never travels.

### 4. Creating a Key Pair

Generate a modern **Ed25519** key (fast, small and secure; the recommended type today). The `-C` comment is just a label to recognise the key later:

```bash
ssh-keygen -t ed25519 -C "sourabh@laptop"
```

Example output:

```
Generating public/private ed25519 key pair.
Enter file in which to save the key (/home/sourabh/.ssh/id_ed25519):
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/sourabh/.ssh/id_ed25519
Your public key has been saved in /home/sourabh/.ssh/id_ed25519.pub
The key fingerprint is:
SHA256:pQ4mX0r7Kc2ZsVb9LhT1uWy5NaE3dGf8JoRi6kMnBxY sourabh@laptop
The key's randomart image is:
+--[ED25519 256]--+
...
+----[SHA256]-----+
```

(The exact wording of the prompts varies slightly between OpenSSH versions.) Press Enter to accept the default location. When asked for a **passphrase**, set one: it encrypts the private key on disk, so a stolen laptop or a leaked backup doesn't hand over your servers. You won't have to type it constantly; the agent remembers it (next section).

Two files now exist:

```bash
ls -l ~/.ssh
```

Example output:

```
-rw------- 1 sourabh sourabh 464 Oct 11 06:02 id_ed25519
-rw-r--r-- 1 sourabh sourabh  96 Oct 11 06:02 id_ed25519.pub
```

| File | What it is | Share it? |
|---|---|---|
| `id_ed25519` | **Private key** (`600`: only you can read it) | **Never.** Not in chat, not in Git, not in email. |
| `id_ed25519.pub` | **Public key** (one line of text) | Yes, freely: servers, GitHub, cloud consoles |

```bash
cat ~/.ssh/id_ed25519.pub
```

Example output:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK8vJ2mQ7pX4rT9wL1sN6bY3cZ0dE5fG8hU2iV7jK4mA sourabh@laptop
```

You'll see older guides use `ssh-keygen -t rsa -b 4096`. RSA keys still work, and some old systems need them, but Ed25519 is the better default.

### 5. The SSH Agent: Type the Passphrase Once

The **ssh-agent** is a small background program that holds your decrypted private keys in memory, so you type the passphrase once per session instead of on every connection:

```bash
eval "$(ssh-agent -s)"            # start an agent for this shell (many desktops already run one)
ssh-add ~/.ssh/id_ed25519         # unlock the key once
ssh-add -l                        # list keys the agent holds
```

Example output:

```
Agent pid 5120
Enter passphrase for /home/sourabh/.ssh/id_ed25519:
Identity added: /home/sourabh/.ssh/id_ed25519 (sourabh@laptop)
256 SHA256:pQ4mX0r7Kc2ZsVb9LhT1uWy5NaE3dGf8JoRi6kMnBxY sourabh@laptop (ED25519)
```

On macOS, `ssh-add --apple-use-keychain ~/.ssh/id_ed25519` stores the passphrase in your Keychain so you never type it again after login. On Windows, the "OpenSSH Authentication Agent" service plays the same role.

### 6. Putting Your Public Key on a Server

A server lets you in with a key if your **public key** is listed in `~/.ssh/authorized_keys` in the home folder of the user you log in as. Ways to get it there:

- **When creating a cloud VM**: paste your public key into the console, or choose a key pair. The provider writes `authorized_keys` for you.
- **With `ssh-copy-id`** (if you can already log in with a password):

```bash
ssh-copy-id ubuntu@203.0.113.10
```

- **By hand**, from an existing session on the server:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo "ssh-ed25519 AAAAC3Nza...jK4mA sourabh@laptop" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Use `>>` (append), never `>`, or you'll wipe out other keys already there, possibly your teammates' or your own only way in.

Now `ssh ubuntu@203.0.113.10` logs in without a password. The same public key works for GitHub too, which you'll set up in [Git and GitHub: Zero to Pro](../../git-and-github-zero-to-pro/course.md#m5).

### 7. The SSH Config File: Short Names for Servers

Typing `ssh -i ~/.ssh/aws-key.pem -p 2222 ubuntu@203.0.113.10` gets old quickly. Create `~/.ssh/config` (permissions `600`) and give each server a short name:

```
Host prod
    HostName 203.0.113.10
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519

Host gpu
    HostName 203.0.113.25
    User sourabh
    Port 2222

Host *
    ServerAliveInterval 60
```

Now:

```bash
ssh prod
ssh gpu 'nvidia-smi'
```

The aliases work in every SSH-based tool: `scp`, `rsync`, `git`, and editors like VS Code's Remote SSH extension, which lists the hosts from this file. `ServerAliveInterval 60` sends a small "still here" message every minute, which stops idle connections from being dropped by routers and firewalls.

### 8. Copying Files: `scp`, `rsync` and `sftp`

**`scp`** (secure copy) works like `cp`, with `host:path` for the remote side:

```bash
scp data/scores.csv prod:/home/ubuntu/            # laptop → server
scp prod:/var/log/app/app.log ./logs/              # server → laptop
scp -r reports prod:/home/ubuntu/reports           # a whole folder (-r)
```

**`rsync`** is smarter: it copies only what changed, can resume, and shows exactly what it's doing. It's the standard tool for deploying folders and syncing data:

```bash
rsync -avz --exclude .venv ~/projects/cricket-stats/ prod:/home/ubuntu/cricket-stats/
```

Example output:

```
sending incremental file list
created directory /home/ubuntu/cricket-stats
./
README.md
data/
data/scores.csv
logs/
logs/app.log
scripts/
scripts/summary.py

sent 1,105 bytes  received 145 bytes  833.33 bytes/sec
total size is 1,013  speedup is 0.81
```

Run the same command again and it sends almost nothing, because nothing changed. The options: `-a` (archive: recurse and keep permissions and times), `-v` (verbose), `-z` (compress in transit). Two rsync rules worth memorising:

- **The trailing slash on the source matters.** `cricket-stats/` copies the folder's *contents*; `cricket-stats` (no slash) copies the folder itself, creating `cricket-stats/cricket-stats` on the other side if you're not careful.
- **Preview with `--dry-run`** (or `-n`) before anything risky, especially with `--delete`, which removes files on the destination that no longer exist on the source.

**`sftp`** gives an interactive file-transfer session (`ls`, `cd`, `get`, `put`), and graphical apps like FileZilla or Cyberduck use the same protocol if you prefer clicking.

### 9. Keeping Work Running: `tmux`

Start a two-hour data job over SSH, close your laptop, and the job dies: when the connection drops, the shell and its children receive the "hang up" signal. You met `nohup` in the processes lesson. The more comfortable tool is **tmux**, a **terminal multiplexer**: it runs your shell sessions on the server itself, so they survive disconnection, and you can reattach later from anywhere.

```bash
ssh prod
tmux new -s pipeline          # start a named session
python3 train.py              # start the long job inside it
```

Now press **Ctrl + B**, release, then press **D** to **detach**. You're back at the normal prompt; the job keeps running inside tmux. Log out, go home, reconnect:

```bash
ssh prod
tmux ls                       # list sessions
tmux attach -t pipeline       # reattach and see the job, exactly as you left it
```

Example output:

```
pipeline: 1 windows (created Sun Oct 11 06:20:14 2026)
```

| tmux keys (after Ctrl + B) | Action |
|---|---|
| `d` | Detach |
| `c` | New window |
| `n` / `p` | Next / previous window |
| `%` / `"` | Split the pane side by side / top and bottom |
| arrow keys | Move between panes |

`screen` is an older tool that does the same job. For programs that should run **permanently** (a web API, a worker), use a service manager like systemd or Docker instead, so they restart after crashes and reboots; the [FastAPI course](../../apis-and-apps-fastapi-streamlit-and-docker/course.md#m9) covers deploying them.

### 10. Tunnels: Reaching a Remote Web App Safely

You start Jupyter or Streamlit on the server, on port 8501, listening only on the server's `localhost` (as it should, for safety). Your laptop's browser can't reach it. An **SSH tunnel** (local port forwarding) fixes that without opening any firewall ports:

```bash
ssh -N -L 8501:localhost:8501 prod
```

Read `-L 8501:localhost:8501` as: "connections to port **8501 on my laptop** should travel through the SSH connection and come out at **localhost:8501 on the server**". `-N` means "don't open a shell, just hold the tunnel". Leave it running, open `http://localhost:8501` in your laptop's browser, and you're using the remote app, encrypted, with nothing exposed to the internet. Press **Ctrl + C** to close the tunnel.

```mermaid
flowchart LR
  B["Browser on laptop<br/>localhost:8501"] --> T["ssh -L tunnel"]
  T -->|"encrypted, port 22"| S["Server"]
  S --> A["Streamlit on server<br/>localhost:8501"]
```

### 11. Securing a New Server

A server with a public IP address is scanned and attacked by bots within minutes of booting. A few steps make it a much harder target. Run them on the server:

```bash
sudo apt update && sudo apt upgrade -y        # install security updates
sudo adduser deploy                           # a normal user for daily work
sudo usermod -aG sudo deploy                  # allowed to use sudo
```

Copy your public key into the new user's `~/.ssh/authorized_keys` (section 6) and **check that you can log in as that user with your key** in a **second terminal**, before changing anything else.

Then turn off password logins and direct root logins in the SSH server's settings, `/etc/ssh/sshd_config` (some systems also read extra files in `/etc/ssh/sshd_config.d/`):

```
PasswordAuthentication no
PermitRootLogin no
```

Check the file for mistakes and reload the service (on Ubuntu the service is called `ssh`; on Fedora and RHEL it's `sshd`):

```bash
sudo sshd -t && sudo systemctl reload ssh
```

Finally, turn on a firewall that allows only SSH (and later, your web ports). On Ubuntu, **ufw** ("uncomplicated firewall") makes this simple:

```bash
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

Example output:

```
Status: active

To                         Action      From
--                         ------      ----
OpenSSH                    ALLOW       Anywhere
OpenSSH (v6)               ALLOW       Anywhere (v6)
```

> ⚠️ **Never lock yourself out.** Keep your existing SSH session open while you change SSH or firewall settings, and test from a new terminal. If the new login fails, you can still fix things from the old one. Always `allow OpenSSH` *before* `ufw enable`. Cloud providers also have their own firewalls ("security groups" on AWS) that must allow port 22.

### 12. Reading SSH Errors

| Error | What it means | Fix |
|---|---|---|
| `Permission denied (publickey)` | The server didn't accept any key you offered | Right user name? Right key (`-i` or `IdentityFile`)? Is your public key in that user's `authorized_keys`? |
| `WARNING: UNPROTECTED PRIVATE KEY FILE!` | Your private key is readable by others, so SSH refuses to use it | `chmod 600 ~/.ssh/id_ed25519` and `chmod 700 ~/.ssh` |
| `Connection refused` | The machine is reachable, but nothing listens on that port | Is `sshd` running? Right port? |
| `Connection timed out` | Packets aren't getting through at all | Wrong IP, machine off, or a firewall/security group blocking port 22 |
| `REMOTE HOST IDENTIFICATION HAS CHANGED!` | The server's fingerprint differs from `known_hosts` | Expected if the server was rebuilt: `ssh-keygen -R 203.0.113.10` removes the old entry. If not expected, stop and investigate. |
| `Host key verification failed` | Same cause, in a non-interactive context | As above |

The permissions error looks like this:

Example output:

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0644 for '/home/sourabh/.ssh/id_ed25519' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
Load key "/home/sourabh/.ssh/id_ed25519": bad permissions
ubuntu@203.0.113.10: Permission denied (publickey).
```

For anything else, add `-v` (verbose; up to `-vvv`) to see each step of the connection, including which keys were tried. The line where it stops tells you where the problem is.

### 13. SSH on Windows

Windows 10 and 11 include the same OpenSSH client, so `ssh`, `scp`, `ssh-keygen` and `ssh-add` all work in PowerShell and Command Prompt. Your keys live in `C:\Users\<you>\.ssh\`. A few differences:

- **WSL has its own `~/.ssh`**, separate from Windows'. Keys created in one aren't automatically visible in the other. Pick one place (inside WSL is simplest for this course) or copy the keys over and fix permissions with `chmod`.
- Don't keep keys on `/mnt/c` and use them from WSL: Linux permissions don't stick there by default, so SSH rejects them as too open.
- **PuTTY** is an older graphical SSH client that uses its own `.ppk` key format; you don't need it any more.
- VS Code's **Remote - SSH** extension works on every system and reads your `~/.ssh/config`.

### 14. SSH Helpers in Python

Automation scripts often prepare SSH work: check that keys have safe permissions, read the config file, and build commands. Here's a pre-flight check that inspects an `.ssh` folder (a fake one in a temporary directory, so nothing real is touched) and reports the same problems SSH would complain about:

```python
import os
import stat
import tempfile
from pathlib import Path

def ssh_permission_problems(ssh_dir):
    problems = []
    if stat.S_IMODE(ssh_dir.stat().st_mode) & 0o077:
        problems.append(f"{ssh_dir.name}/ should be 700")
    for path in sorted(ssh_dir.iterdir()):
        mode = stat.S_IMODE(path.stat().st_mode)
        private = path.name in ("config", "authorized_keys") or not path.name.endswith(".pub")
        if private and mode & 0o077:
            problems.append(f"{path.name} is {oct(mode)[2:]}, should be 600")
    return problems

tmp = tempfile.TemporaryDirectory()
ssh_dir = Path(tmp.name) / ".ssh"
ssh_dir.mkdir()
(ssh_dir / "id_ed25519").write_text("-----BEGIN OPENSSH PRIVATE KEY-----\n(fake)\n")
(ssh_dir / "id_ed25519.pub").write_text("ssh-ed25519 AAAAfake sourabh@laptop\n")
(ssh_dir / "config").write_text("Host prod\n    HostName 203.0.113.10\n    User ubuntu\n")

os.chmod(ssh_dir, 0o755)                         # too open
os.chmod(ssh_dir / "id_ed25519", 0o644)          # too open: SSH would refuse this key
os.chmod(ssh_dir / "id_ed25519.pub", 0o644)      # fine: public keys may be readable
os.chmod(ssh_dir / "config", 0o664)              # too open

print("before:", ssh_permission_problems(ssh_dir))

os.chmod(ssh_dir, 0o700)
for name in ("id_ed25519", "config"):
    os.chmod(ssh_dir / name, 0o600)
print("after:", ssh_permission_problems(ssh_dir))
```

Output:

```
before: ['.ssh/ should be 700', 'config is 664, should be 600', 'id_ed25519 is 644, should be 600']
after: []
```

And a tiny reader for the config file format from section 7, which turns host aliases into settings, plus a safely built remote command:

```python
import shlex

def read_ssh_config(text):
    hosts, current = {}, None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split(maxsplit=1)
        if key.lower() == "host":
            current = hosts.setdefault(value, {})
        elif current is not None:
            current[key] = value
    return hosts

config = read_ssh_config((ssh_dir / "config").read_text())
print(config)

remote = "tail -n 50 /var/log/app/app.log | grep ERROR"
command = ["ssh", "prod", remote]            # the remote part travels as ONE argument
print(shlex.join(command))
tmp.cleanup()
```

Output:

```
{'prod': {'HostName': '203.0.113.10', 'User': 'ubuntu'}}
ssh prod 'tail -n 50 /var/log/app/app.log | grep ERROR'
```

`shlex.join` shows the command as you'd type it, with the quoting that keeps the pipe on the **remote** side. Actually running it needs a real server, so it isn't executed here:

```python
# not-run: needs a reachable SSH server called "prod" in ~/.ssh/config
import subprocess

result = subprocess.run(["ssh", "prod", "uptime"], capture_output=True, text=True, timeout=30)
print(result.returncode, result.stdout.strip())
```

Example output:

```
0 06:41:07 up 12 days,  3:02,  1 user,  load average: 0.08, 0.05, 0.01
```

For heavier automation, Python libraries such as Paramiko and Fabric speak SSH directly, and tools like Ansible manage fleets of servers over SSH.

---

## Try It Yourself

1. **Make a key.** Create an Ed25519 key with a passphrase (if you already have one, skip this). Check its permissions with `ls -l ~/.ssh`, and print the public key.
2. **Rehearse safely on your own machine.** If your Linux or WSL system has an SSH server (`sudo apt install openssh-server`, then `sudo systemctl start ssh`), add your public key to your own `~/.ssh/authorized_keys` and run `ssh localhost 'whoami && hostname'`. (On macOS, enable System Settings → General → Sharing → Remote Login.)
3. **Config alias.** Add a `Host me` entry to `~/.ssh/config` that points at `localhost` with your user name, and connect with `ssh me`. Then copy a file to yourself with `scp data/scores.csv me:/tmp/`.
4. **Diagnose.** A teammate gets `Permission denied (publickey)` connecting as `root` to a new Ubuntu VM on AWS, using the right key. What's the most likely cause? Another gets `Connection timed out`. What would you check first?

<details>
<summary>Show answers</summary>

**1.** `ssh-keygen -t ed25519 -C "you@laptop"`, set a passphrase. `ls -l ~/.ssh` should show `-rw-------` for `id_ed25519` and `-rw-r--r--` for `id_ed25519.pub`. `cat ~/.ssh/id_ed25519.pub` prints one line starting with `ssh-ed25519`.

**2.**

```bash
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
ssh localhost 'whoami && hostname'
```

After accepting the fingerprint, it prints your user name and your machine's name, then returns to your prompt.

**3.**

```
Host me
    HostName localhost
    User sourabh
```

`ssh me` connects; `scp data/scores.csv me:/tmp/` copies, and `ls /tmp/scores.csv` confirms it.

**4.** Ubuntu images on AWS log in as `ubuntu`, not `root` (root login is disabled), so the server rejects the attempt even with the right key: use `ssh ubuntu@...`. For a timeout, check the IP address and whether the security group or firewall allows inbound port 22 from your IP, then whether the instance is running.

</details>

---

## Real-World Examples

### Example 1: Deploying a Small App

A two-person startup runs its FastAPI app on one cloud VM. Their deploy is a script: `rsync -avz --exclude .venv ./ prod:/srv/app/` to copy the code, then `ssh prod 'cd /srv/app && uv sync && sudo systemctl restart app'` to install dependencies and restart. Two SSH commands, under a minute, and fully repeatable. When they grow, CI runs the same steps for them.

### Example 2: Training on a Rented GPU

An ML engineer rents a GPU machine by the hour. They `ssh gpu`, start `tmux new -s train`, launch training, detach and go home. From home, `ssh -N -L 6006:localhost:6006 gpu` tunnels the TensorBoard dashboard to their laptop's browser, and `scp gpu:~/runs/best.pt .` fetches the trained model in the morning.

### Example 3: The Leaked Private Key

A developer commits a folder that includes `id_rsa` to a public GitHub repository. Within hours, automated scanners find it, and the company's servers that trusted that key are at risk. The fix: remove the key from every `authorized_keys`, generate a new pair, and treat the old key as compromised forever. This is why private keys never go into project folders, and why the Git course spends time on [secrets](../../coding-agents-and-harness-engineering/course.md#m4).

---

## Common Misconceptions

### Misconception 1: "I send my private key to the server"

Only the **public** key goes to servers. The private key stays on your machine and proves your identity without ever being transmitted.

### Misconception 2: "A passphrase on my key is pointless if I have a laptop password"

The passphrase protects the key file itself: in backups, on a stolen disk, or if malware copies it. With an agent or Keychain, you type it rarely, so it costs almost nothing.

### Misconception 3: "Closing my laptop pauses my remote job"

When the SSH connection drops, the remote shell is hung up and normally kills its jobs. Use `tmux` (or `nohup`, or a proper service) for anything that must outlive the connection.

### Misconception 4: "Changing the SSH port makes a server secure"

It reduces log noise from bots, but real security comes from key-only authentication, no root login, updates, and a firewall.

---

## Interview Relevance

SSH questions appear in DevOps, SRE, backend, data and ML engineering interviews, often alongside cloud deployment questions.

- **"How does SSH key authentication work?"** Public key on the server in `authorized_keys`, private key stays local; the server issues a challenge only the private key can answer. Mention passphrases and the agent.
- **"How do you copy files to a server?"** `scp` for one-off copies, `rsync -avz` for efficient, resumable syncs; mention the trailing-slash rule and `--dry-run`.
- **"A process must keep running after you log out. How?"** `tmux`/`screen` for interactive work, `nohup` for quick cases, systemd or containers for services.
- **"How would you access a database or web UI on a private server?"** An SSH tunnel with `-L local:host:remote`, without opening the port publicly.
- **"How do you harden a new Linux server?"** Updates, non-root sudo user, key-only SSH, `PermitRootLogin no`, firewall, and keeping a session open while testing changes.
- **"What does 'REMOTE HOST IDENTIFICATION HAS CHANGED' mean?"** The host key differs from `known_hosts`: either the server was rebuilt or there's a possible man-in-the-middle; verify before removing the old entry.

---

## Key Takeaways

- **SSH** gives you an encrypted terminal on a remote machine: `ssh user@host`, port 22, `exit` to leave.
- Use **key pairs**: `ssh-keygen -t ed25519`, keep the **private key at `600`** and never share it, put the **public key** in the server's `~/.ssh/authorized_keys`.
- A **`~/.ssh/config`** file turns long commands into `ssh prod`, and works with `scp`, `rsync`, Git and VS Code.
- Copy with **`scp`** or **`rsync -avz`** (mind the trailing slash, preview with `--dry-run`); keep jobs alive with **`tmux`**; reach private web apps with **`ssh -L`** tunnels.
- Harden servers: **updates, a sudo user, no passwords, no root login, a firewall**, and never lock yourself out.
- Read errors calmly: **`Permission denied (publickey)`**, **"unprotected private key"**, **refused**, **timed out** and **host key changed** each have a clear cause; `ssh -v` shows the details.

---

**Up next:** [Lab: Automate a daily data download](lab-automate-a-daily-data-download.md)
