---
title: "Git LFS for Large Files"
course: "Git and GitHub: Zero to Pro"
module: "11. Open Source and Advanced Git"
type: Article
level: Intermediate
reading_time: 20 min
---

# Git LFS for Large Files: The Complete Guide

> 📚 **Before you start**
>
> - [Blobs, Trees, Commits and Tags](../course.md#m3) and [Hashes and Content Addressing](../course.md#m3)
> - [.gitignore and What Never to Commit](../course.md#m2)

## Introduction

Your society's WhatsApp group works perfectly for messages. Then someone forwards a 400 MB wedding video, everyone's phone storage fills up, and people who only wanted the AGM notice are stuck downloading it. Sensible groups share big videos as a **link** instead: the chat keeps a tiny pointer, and only people who want the video fetch it.

Git has the same problem. Every clone downloads **every version of every file** ever committed. Text diffs compress beautifully, but a 200 MB Photoshop file edited 30 times is 6 GB of history that everyone must download forever, even after you delete it.

**Git Large File Storage (LFS)** is the "share a link" fix. Big files are replaced in Git by small **pointer files**; the real content lives on an LFS server (GitHub provides one) and is downloaded only for the commits you check out. This lesson shows how LFS works, how to set it up, how to move existing files into it, how it behaves in CI, what it costs on GitHub, and when to use something else.

> 💡 **Key Insight**
>
> Git LFS keeps **Git's history small** by committing a ~130-byte **pointer** (a SHA-256 hash and a size) instead of the file. A Git **filter** swaps pointer and file automatically on commit and checkout, so day-to-day commands look the same.

---

## Core Explanation

### 1. Why Big Files Hurt Git

- **Clones grow forever.** Deleting a file doesn't remove it from history (see [Removing a Leaked Secret from History](../10-security-and-supply-chain/removing-a-leaked-secret-from-history.md) for what that takes).
- **Binary files don't diff or delta-compress well**, so each version is stored nearly whole.
- **GitHub limits** regular Git files: you get a warning for files over **50 MiB**, and pushes containing a file over **100 MiB** are **blocked**.

Good LFS candidates: design files (`.psd`, `.fig` exports, `.blend`), audio and video, game assets, large binary test fixtures, and moderate ML models. Bad candidates: source code, small images, anything you need to diff line by line.

### 2. How It Works: Pointers and Filters

When you track a pattern, Git LFS adds a line to **`.gitattributes`**:

~~~text
*.psd filter=lfs diff=lfs merge=lfs -text
~~~

- `filter=lfs`: on `git add`, the **clean** filter uploads nothing yet but stores the file in a local LFS cache and gives Git a pointer; on checkout, the **smudge** filter replaces the pointer with the real file.
- `diff=lfs` and `merge=lfs`: tell Git not to try text diffs and merges on it.
- `-text`: no line-ending conversion.

The pointer Git actually stores looks like this:

```python
import hashlib, fnmatch

def make_pointer(data):
    oid = hashlib.sha256(data).hexdigest()
    return f"version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {len(data)}\n"

def parse_pointer(text):
    fields = dict(line.split(" ", 1) for line in text.strip().splitlines())
    return fields["oid"].removeprefix("sha256:"), int(fields["size"])

model = b"\x00\x01" * 3_000_000          # stand-in for a 6 MB model file
pointer = make_pointer(model)
print(pointer, end="")
print(len(pointer), "bytes stored in Git instead of", len(model))
oid, size = parse_pointer(pointer)
print(oid == hashlib.sha256(model).hexdigest(), size)
```

Output:

```
version https://git-lfs.github.com/spec/v1
oid sha256:1eca24eabd88df71cdb0c546e464f48f2a96e062f3572bee45ed86d6512ef149
size 6000000
132 bytes stored in Git instead of 6000000
True 6000000
```

On `git push`, a **pre-push hook** installed by Git LFS uploads the real content (keyed by its SHA-256 `oid`) to the LFS server before Git pushes the commits. On clone or checkout, the smudge filter downloads the content for the pointers in that commit only.

### 3. Setting It Up

Install the `git-lfs` package (Git for Windows includes it; `brew install git-lfs` on macOS; `sudo apt install git-lfs` on Debian/Ubuntu), then once per machine:

```bash
git lfs install
```

Example output:

```
Git LFS initialized.
```

That sets up the filters and hooks in your global Git config. Then, in the repository:

```bash
git lfs track "*.psd"
git lfs track "models/**"
git add .gitattributes
git add design/menu-banner.psd models/rates-v3.onnx
git commit -m "build: store design files and models in LFS"
git push
```

Quote the patterns so your shell doesn't expand them. **Commit `.gitattributes` first or together with the files**: files added before their pattern is tracked go into regular Git.

Checking what's in LFS:

```bash
git lfs ls-files
```

Example output:

```
5e1f2c8a4b * design/menu-banner.psd
9a3d77c01e * models/rates-v3.onnx
```

(`*` means the full content is present locally; `-` means only the pointer is.)

### 4. Which Files Belong Where

A small planner that applies `.gitattributes` patterns and GitHub's size limits:

```python
gitattributes = """
*.psd filter=lfs diff=lfs merge=lfs -text
models/** filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
"""
patterns = [line.split()[0] for line in gitattributes.strip().splitlines() if "filter=lfs" in line]

MB = 1024 * 1024
def plan(files):
    for path, size in files.items():
        lfs = any(fnmatch.fnmatch(path, p) or fnmatch.fnmatch(path.rsplit("/", 1)[-1], p) for p in patterns)
        if lfs:
            note = "LFS"
        elif size > 100 * MB:
            note = "BLOCKED by GitHub (over 100 MiB): track with LFS"
        elif size > 50 * MB:
            note = "warning on push (over 50 MiB): consider LFS"
        else:
            note = "git"
        print(f"{path:<26} {size / MB:>7.1f} MiB  {note}")

plan({
    "design/menu-banner.psd": 240 * MB,
    "models/rates-v3.onnx": 812 * MB,
    "data/orders-2026.csv": 130 * MB,
    "assets/logo.png": 0.2 * MB,
    "videos/demo.mov": 75 * MB,
})
```

Output:

```
design/menu-banner.psd       240.0 MiB  LFS
models/rates-v3.onnx         812.0 MiB  LFS
data/orders-2026.csv         130.0 MiB  BLOCKED by GitHub (over 100 MiB): track with LFS
assets/logo.png                0.2 MiB  git
videos/demo.mov               75.0 MiB  warning on push (over 50 MiB): consider LFS
```

`demo.mov` slipped through because only `*.mp4` is tracked. (A 130 MB CSV of orders probably shouldn't be in the repository at all; see section 8.)

### 5. Moving Existing Files into LFS

If big files are already committed, tracking them now only affects **future** commits. `git lfs migrate` rewrites history so past commits use pointers too:

```bash
git lfs migrate info --everything                 # which file types take the most space
git lfs migrate import --include="*.psd,*.mov" --everything
git push --force-with-lease --all
```

`--everything` rewrites all local branches and tags. Like any history rewrite, it changes commit hashes, so coordinate with your team: everyone re-clones or resets (the same process as in the secret-removal lesson). Old blobs stay in GitHub's storage until the old history is no longer referenced and garbage collected; to reclaim space on GitHub fully you may need to contact Support.

The reverse, `git lfs migrate export --include="*.psd" --everything`, moves files back into regular Git.

### 6. Daily Workflow, Locking and Partial Downloads

Most of the time you just use Git. Useful extras:

| Need | Command |
|---|---|
| Clone without downloading LFS content yet | `GIT_LFS_SKIP_SMUDGE=1 git clone <url>` |
| Download content for the current checkout | `git lfs pull` |
| Download only some files | `git lfs pull --include="models/rates-v3.onnx"` |
| Fetch content for all refs (e.g. before going offline) | `git lfs fetch --all` |
| Free local disk space from old versions | `git lfs prune` |
| Check setup and endpoints | `git lfs env` |

**File locking** prevents two designers from editing the same unmergeable file:

~~~text
*.psd filter=lfs diff=lfs merge=lfs -text lockable
~~~

```bash
git lfs lock design/menu-banner.psd
git lfs locks
git lfs unlock design/menu-banner.psd
```

Example output:

```
Locked design/menu-banner.psd
design/menu-banner.psd	priya	ID:1842
Unlocked design/menu-banner.psd
```

With `lockable`, Git LFS keeps those files **read-only** in your working tree until you lock them, which reminds people to lock before editing.

### 7. LFS in GitHub Actions and Its Cost

`actions/checkout` doesn't download LFS content by default:

```yaml
- uses: actions/checkout@v7
  with:
    lfs: true
```

Every CI download counts against your LFS **bandwidth**. Only enable `lfs: true` in jobs that need the files, or cache them (keyed on the list of LFS object IDs, e.g. from `git lfs ls-files --long`).

On GitHub (as of October 2026):

| | Free, Pro, Free for organisations | Team, Enterprise Cloud |
|---|---|---|
| Included storage | 10 GiB | 250 GiB |
| Included bandwidth per month | 10 GiB | 250 GiB |
| Maximum single file size | 2 GB (Free and Pro) | 4 GB (Team), 5 GB (Enterprise Cloud) |

Usage beyond the included amount is billed per GiB if you have a payment method and budget set; otherwise LFS is limited for the rest of the month (pushes or downloads stop working). Downloads of source archives that include LFS objects also count. LFS doesn't work with **GitHub Pages** sites or **template repositories**.

### 8. When LFS Isn't the Answer

| Situation | Better option |
|---|---|
| Build outputs (wheels, binaries, installers) | **GitHub Releases** assets or a package registry |
| Datasets and ML experiments that change often | **DVC** (data version control, storing data in S3, GCS etc.), or a dataset hub such as Hugging Face |
| Huge media libraries | Object storage (S3, GCS, Azure Blob) with paths or URLs in Git |
| Generated files | Don't commit them; generate in CI |
| Secrets, private keys | Never in Git, LFS included |

---

## Try It Yourself

1. Write the `.gitattributes` lines to send all `.wav` files and everything under `fixtures/large/` to LFS, with `.wav` files lockable.
2. A teammate committed `video.mp4` and then ran `git lfs track "*.mp4"`. Is the video in LFS? How do you fix the existing commit?
3. Use `make_pointer` on `b"chai" * 1000`. What size does the pointer report?
4. Your CI's LFS bandwidth runs out in the second week of each month. Name two fixes.

<details>
<summary>Show answers</summary>

**1.**

~~~text
*.wav filter=lfs diff=lfs merge=lfs -text lockable
fixtures/large/** filter=lfs diff=lfs merge=lfs -text
~~~

**2.** No: tracking only affects files added afterwards. Run `git lfs migrate import --include="*.mp4"` (add `--everything` for all branches) and force-push, coordinating with the team. If the commit isn't pushed yet, `git rm --cached video.mp4`, `git add video.mp4` and amend also works.

**3.**

```python
print(parse_pointer(make_pointer(b"chai" * 1000))[1])
```

Output:

```
4000
```

**4.** Only set `lfs: true` in jobs that need the files, and cache LFS objects between runs (keyed on the object IDs). Also consider moving large test fixtures to smaller synthetic ones, or buying more bandwidth.

</details>

---

## Real-World Examples

### Example 1: A Game Studio

A small Pune game studio keeps code, `.blend` models and audio in one repository with LFS and locking on art files. Artists lock a model before editing; programmers clone with `GIT_LFS_SKIP_SMUDGE=1` and pull only the assets for the level they're working on.

### Example 2: The 100 MiB Wall

A data science intern committed a 140 MB CSV, and the push was rejected. Rather than LFS, the team moved the dataset to object storage, committed a small script that downloads it, and added the `data/` folder to `.gitignore`.

### Example 3: The Surprise Bill

An open source project's CI checked out with `lfs: true` on a 20-job matrix, downloading 600 MB per job on every push. Its bandwidth ran out in days. Restricting LFS to the two jobs that needed it, plus caching, fixed it.

---

## Common Misconceptions

### Misconception 1: "Tracking a file type moves my existing files into LFS"

Only new additions. Existing history needs `git lfs migrate import`.

### Misconception 2: "LFS makes Git diff binary files"

It makes Git **stop** trying. You see "Binary files differ" or pointer changes, not content diffs.

### Misconception 3: "Deleting an LFS file frees storage"

Older commits still reference it, so the object stays on the server.

### Misconception 4: "Everyone needs LFS installed to clone"

Without it they get pointer files instead of content, which breaks builds silently. Document it in your README and CONTRIBUTING.md.

---

## Interview Relevance

Git LFS questions appear in DevOps, game development and ML engineering interviews:

- **Why big binaries hurt Git:** every clone carries full history; poor compression; GitHub's 50/100 MiB limits.
- **How LFS works:** pointer files, clean/smudge filters, pre-push upload, SHA-256 object IDs.
- **Migrating:** `git lfs migrate import` rewrites history.
- **CI considerations:** `lfs: true`, bandwidth, caching.
- **Alternatives:** releases, package registries, DVC, object storage.

A common follow-up: *"Should we store our ML models in LFS?"* For a few versioned models, yes; for many frequently retrained models and datasets, a model registry or DVC with object storage scales better.

---

## Key Takeaways

- **Git keeps every version forever**, so big binaries bloat every clone; GitHub warns over 50 MiB and blocks over 100 MiB.
- **Git LFS commits a small pointer** (SHA-256 `oid` and `size`) and stores content on an LFS server, swapping them with clean/smudge filters.
- **`git lfs install`, `git lfs track "pattern"`, commit `.gitattributes`**; use `git lfs migrate import` for files already in history.
- **Use `lockable` and `git lfs lock`** for unmergeable files; in CI, enable `lfs: true` only where needed.
- **Watch quotas** (10 GiB on free plans, billed by the GiB beyond) and prefer releases, registries, DVC or object storage when they fit better.

---

**Up next:** [Git Hooks and pre-commit](git-hooks-and-pre-commit.md)
