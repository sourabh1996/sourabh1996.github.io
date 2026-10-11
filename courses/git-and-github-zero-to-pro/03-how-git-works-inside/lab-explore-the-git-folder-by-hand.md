---
title: "Lab: Explore the .git folder by hand"
course: "Git and GitHub: Zero to Pro"
module: "3. How Git Works Inside"
type: Lab
level: Intermediate
reading_time: 45 min
---

# Lab: Explore the .git Folder by Hand

> 📚 **Before you start**
>
> - [Blobs, Trees, Commits and Tags](blobs-trees-commits-and-tags.md)
> - [Hashes and Content Addressing](hashes-and-content-addressing.md)
> - [Refs, HEAD and Detached HEAD](refs-head-and-detached-head.md)
> - [The Reflog and Garbage Collection](the-reflog-and-garbage-collection.md)

## What You'll Build

You'll make Git commits **without using `git add` or `git commit`**. Using only plumbing commands, you'll write a file's content into the object database, put it in the index, turn the index into a tree, wrap the tree in a commit, and point a branch at it. Along the way you'll read a raw object file with Python and watch every file in `.git` change.

When you're done, `git log` will show two commits you built by hand, followed by one made the normal way, and you'll know exactly what `git add` and `git commit` do for you.

```mermaid
flowchart LR
  F["menu.txt<br/>content"] -->|"git hash-object -w"| B["blob<br/>.git/objects"]
  B -->|"git update-index"| I["index<br/>.git/index"]
  I -->|"git write-tree"| T["tree"]
  T -->|"git commit-tree"| C["commit"]
  C -->|"git update-ref"| R["refs/heads/main"]
  R -.->|"HEAD: ref: refs/heads/main"| H(["HEAD"])
```

> 💡 **Key Insight**
>
> `git add` = **hash-object + update-index**. `git commit` = **write-tree + commit-tree + update-ref**. Porcelain commands are friendly wrappers around a handful of plumbing steps that each do one small, inspectable thing.

You need Git, and Python 3 for one optional step.

---

## Step 1: An Empty Repository, Inside and Out

```bash
git init by-hand
cd by-hand
find .git -type f | sort
```

Example output:

```
Initialized empty Git repository in /home/asha/projects/by-hand/.git/
.git/HEAD
.git/config
.git/description
.git/hooks/applypatch-msg.sample
.git/hooks/commit-msg.sample
.git/hooks/fsmonitor-watchman.sample
.git/hooks/post-update.sample
.git/hooks/pre-applypatch.sample
.git/hooks/pre-commit.sample
.git/hooks/pre-merge-commit.sample
.git/hooks/pre-push.sample
.git/hooks/pre-rebase.sample
.git/hooks/pre-receive.sample
.git/hooks/prepare-commit-msg.sample
.git/hooks/push-to-checkout.sample
.git/hooks/sendemail-validate.sample
.git/hooks/update.sample
.git/info/exclude
```

What each piece is for:

| Path | Purpose |
|---|---|
| `HEAD` | Which branch you're on |
| `config` | This repository's local configuration |
| `description` | Only used by the old GitWeb browser; safe to ignore |
| `hooks/` | Sample scripts Git can run at certain moments ([module 11](../course.md#m11)); the `.sample` suffix keeps them inactive |
| `info/exclude` | Personal ignore rules for this clone |
| `objects/` | The object database (empty so far, apart from `info/` and `pack/` folders) |
| `refs/heads/`, `refs/tags/` | Branches and tags (empty so far) |

```bash
cat .git/HEAD
cat .git/config
```

Example output:

```
ref: refs/heads/main
[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
```

`HEAD` already points at `refs/heads/main`, but that ref doesn't exist yet. That's what "No commits yet" means: an **unborn branch**.

---

## Step 2: Write a Blob Directly

`git hash-object -w` hashes content **and writes** it into the database:

```bash
echo 'Masala chai: 20' | git hash-object -w --stdin
find .git/objects -type f
```

Example output:

```
5372231a7456b8b9d3fd5d7a77204df01a9102e5
.git/objects/53/72231a7456b8b9d3fd5d7a77204df01a9102e5
```

The object file is named after its hash: folder `53`, file `72231a...`. Ask Git about it using a short prefix:

```bash
git cat-file -t 5372231
git cat-file -p 5372231
```

Example output:

```
blob
Masala chai: 20
```

Now open the raw file yourself. It's zlib-compressed, so decompress it with Python:

```bash
python3 -c "import zlib; print(zlib.decompress(open('.git/objects/53/72231a7456b8b9d3fd5d7a77204df01a9102e5','rb').read()))"
```

Example output:

```
b'blob 16\x00Masala chai: 20\n'
```

There's the header from the hashing lesson: type, space, size, zero byte, content. Yet `git status` knows nothing about it:

```bash
git status
```

Example output:

```
On branch main

No commits yet

nothing to commit (create/copy files and use "git add" to track)
```

The blob is in the database, but no file in the working tree, no index entry and no commit refers to it. It's a dangling blob.

---

## Step 3: Put It in the Index

The index (staging area) maps paths to blob hashes. `git update-index` edits it directly. `--cacheinfo` takes mode, hash and path:

```bash
git update-index --add --cacheinfo 100644,5372231a7456b8b9d3fd5d7a77204df01a9102e5,menu.txt
git ls-files --stage
```

Example output:

```
100644 5372231a7456b8b9d3fd5d7a77204df01a9102e5 0	menu.txt
```

The `0` is the **stage number**. It's always 0 normally; during a merge conflict, the index holds stages 1, 2 and 3 for the base, ours and theirs versions of a file (you'll see this in module 4). Now look at `git status`:

```bash
git status
```

Example output:

```
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
	new file:   menu.txt

Changes not staged for commit:
  (use "git add/rm <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	deleted:    menu.txt

```

This output makes perfect sense once you think in three areas. The **index** has `menu.txt`, and the last commit doesn't (nothing exists yet), so it's a staged new file. The **working tree** doesn't have `menu.txt` at all, so compared with the index, it looks deleted. You've staged a file that has never existed on disk.

---

## Step 4: Turn the Index into a Tree

```bash
git write-tree
```

Example output:

```
827f1c7d3d3bc55ae10c5ab4e8992b1524657366
```

```bash
git cat-file -p 827f1c7d3d3bc55ae10c5ab4e8992b1524657366
```

Example output:

```
100644 blob 5372231a7456b8b9d3fd5d7a77204df01a9102e5	menu.txt
```

`write-tree` snapshots the current index as tree objects (one per folder) and prints the root tree's hash. This is the first half of what `git commit` does.

---

## Step 5: Wrap the Tree in a Commit

`git commit-tree` creates a commit object from a tree, a message, optional parents (`-p`), and your configured name, email and the current time:

```bash
echo 'Add the menu, by hand' | git commit-tree 827f1c7d3d3bc55ae10c5ab4e8992b1524657366
```

Example output:

```
88fb70c3c630638cf27bdd38d62bd9eb6ae93ee2
```

(Your hash will differ: it includes your name and the current time.)

```bash
git cat-file -p 88fb70c
git log --oneline
```

Example output:

```
tree 827f1c7d3d3bc55ae10c5ab4e8992b1524657366
author Asha Rao <asha@example.com> 1791177300 +0530
committer Asha Rao <asha@example.com> 1791177300 +0530

Add the menu, by hand
fatal: your current branch 'main' does not have any commits yet
```

The commit exists, but `git log` can't find it, because **no ref points to it**. `HEAD` says `refs/heads/main`, and that ref still doesn't exist.

---

## Step 6: Point the Branch at It

`git update-ref` safely writes a ref (and records the change in the reflog):

```bash
git update-ref refs/heads/main 88fb70c3c630638cf27bdd38d62bd9eb6ae93ee2
cat .git/refs/heads/main
git log --oneline
```

Example output:

```
88fb70c3c630638cf27bdd38d62bd9eb6ae93ee2
88fb70c Add the menu, by hand
```

You've made a commit with no porcelain at all. Check the status:

```bash
git status
```

Example output:

```
On branch main
Changes not staged for commit:
  (use "git add/rm <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	deleted:    menu.txt

no changes added to commit (use "git add" and/or "git commit -a")
```

The commit and index agree now, but the working tree still has no `menu.txt`. Restore it from the index, which writes the blob's content out to disk:

```bash
git restore menu.txt
cat menu.txt
git status
```

Example output:

```
Masala chai: 20
On branch main
nothing to commit, working tree clean
```

All three areas agree. That's exactly the state `git commit` would have left you in.

---

## Step 7: A Second Commit, with a Parent

This time start from a real file, as `git add` would:

```bash
printf 'Masala chai: 20\nGinger chai: 25\n' > menu.txt
git hash-object -w menu.txt
git update-index menu.txt
git write-tree
```

Example output:

```
f3998fe782971cacfe265d9e28f3c519f8233e62
83e7e6566a0531754449e18dd66cb1027190aa32
```

(`update-index` without `--add` updates an already-tracked path from the file on disk; it prints nothing.) Create the commit with `-p` naming the first commit as its parent, and move the branch:

```bash
echo 'Add ginger chai, by hand' | git commit-tree 83e7e6566a0531754449e18dd66cb1027190aa32 -p 88fb70c3c630638cf27bdd38d62bd9eb6ae93ee2
```

Example output:

```
5dc0501d67e763231d921df40587546fd4f8220d
```

```bash
git update-ref refs/heads/main 5dc0501d67e763231d921df40587546fd4f8220d
git log --oneline
git cat-file -p HEAD
```

Example output:

```
5dc0501 Add ginger chai, by hand
88fb70c Add the menu, by hand
tree 83e7e6566a0531754449e18dd66cb1027190aa32
parent 88fb70c3c630638cf27bdd38d62bd9eb6ae93ee2
author Asha Rao <asha@example.com> 1791181500 +0530
committer Asha Rao <asha@example.com> 1791181500 +0530

Add ginger chai, by hand
```

A two-commit history, linked by the `parent` line, built entirely by hand. Here's the complete object database:

```bash
git cat-file --batch-check --batch-all-objects
```

Example output:

```
5372231a7456b8b9d3fd5d7a77204df01a9102e5 blob 16
5dc0501d67e763231d921df40587546fd4f8220d commit 227
827f1c7d3d3bc55ae10c5ab4e8992b1524657366 tree 36
83e7e6566a0531754449e18dd66cb1027190aa32 tree 36
88fb70c3c630638cf27bdd38d62bd9eb6ae93ee2 commit 176
f3998fe782971cacfe265d9e28f3c519f8233e62 blob 32
```

Two blobs, two trees, two commits. Notice `f3998fe...`: the same blob hash `menu.txt` had in earlier lessons with exactly this content, on a different machine and in a different repository. That's content addressing.

---

## Step 8: Compare with the Porcelain

Now make a commit the normal way and see that it lands in the same structure:

```bash
echo "Elaichi chai: 25" >> menu.txt
git commit -am "Add elaichi chai, the normal way"
git log --oneline
```

Example output:

```
[main 7139279] Add elaichi chai, the normal way
 1 file changed, 1 insertion(+)
7139279 Add elaichi chai, the normal way
5dc0501 Add ginger chai, by hand
88fb70c Add the menu, by hand
```

Git can't tell the difference between commits made by hand and by `git commit`. Look at the reflog file, though:

```bash
cat .git/logs/HEAD
```

Example output:

```
0000000000000000000000000000000000000000 88fb70c3c630638cf27bdd38d62bd9eb6ae93ee2 Asha Rao <asha@example.com> 1791178200 +0530
88fb70c3c630638cf27bdd38d62bd9eb6ae93ee2 5dc0501d67e763231d921df40587546fd4f8220d Asha Rao <asha@example.com> 1791182100 +0530
5dc0501d67e763231d921df40587546fd4f8220d 71392796b5a0b679d3797e24744241b15717713d Asha Rao <asha@example.com> 1791183600 +0530	commit: Add elaichi chai, the normal way
```

The two `update-ref` entries have no description. Porcelain commands pass one (`commit: ...`); with plumbing you add it yourself with `git update-ref -m "reason" ...`. Porcelain also wrote `.git/COMMIT_EDITMSG` (the last message) and ran any active hooks, which plumbing doesn't do.

---

## Step 9: An Annotated Tag by Hand (Optional)

Tags are objects too. `git mktag` builds one from text in the exact format you saw in `git cat-file -p v1.0`, checking it for mistakes first (use your own commit hash):

```bash
git mktag <<EOF
object 5dc0501d67e763231d921df40587546fd4f8220d
type commit
tag v0.1
tagger Asha Rao <asha@example.com> 1791175000 +0530

Two items on the menu
EOF
```

Example output:

```
0a3db34078e45404861da6df8dd90020ba034865
```

That's the tag object. To make it usable as `v0.1`, point a ref at it: `git update-ref refs/tags/v0.1 0a3db34`. Then `git show v0.1` displays it like any tag made with `git tag -a`.

---

## Try It Yourself

1. **A folder by hand.** Add a file at `src/prices.py` using only `hash-object -w` and `update-index --add --cacheinfo`, then `write-tree`. How many tree objects does `write-tree` create?
2. **A merge commit by hand.** `git commit-tree` accepts `-p` more than once. Create a commit with two parents (any two existing commits) and view it with `git log --oneline --graph`.
3. **Plumbing for status.** Use `git ls-files --stage`, `git hash-object <file>` and `git rev-parse HEAD:<file>` to decide by hand whether a file is modified, staged, or both.
4. **Break it, then check it.** Make a **copy** of your practice repository, then in the copy append a byte to any file under `.git/objects/` (you may need to `chmod u+w` it first) and run `git fsck`. What happens?

<details>
<summary>Show answers</summary>

1. Two new trees: one for `src/` and a new root tree that contains `menu.txt` and the `src` tree entry (`git cat-file -p` on the root shows a `040000 tree ... src` line).
2. `echo "Merge by hand" | git commit-tree <tree> -p <commitA> -p <commitB>`, then `git update-ref refs/heads/main <new>`. `cat-file -p` shows two `parent` lines, and the graph shows two lines joining.
3. Compare three hashes: the index entry (`ls-files --stage`), the working file (`hash-object`) and the committed version (`rev-parse HEAD:<file>`). Index differs from HEAD means staged; working file differs from index means modified; both can be true.
4. `git fsck` reports a corrupt or broken object, for example that it can't be inflated or its hash doesn't match. Content addressing makes damage detectable. Delete the copy afterwards.

</details>

---

## What You've Learned

- The layout of **`.git`**: `HEAD`, `config`, `objects/`, `refs/`, `index`, `logs/`, `hooks/`.
- **`git add`** is `hash-object -w` + `update-index`.
- **`git commit`** is `write-tree` + `commit-tree` (with `-p` for parents) + `update-ref`.
- Objects are **zlib-compressed** files named by hash, readable with a line of Python.
- A branch is born when its **ref file** is first written; until then it's **unborn**.
- Porcelain adds conveniences: reflog messages, `COMMIT_EDITMSG`, hooks and safety checks.

---

**Up next:** [Branches Are Just Pointers](../04-branching-and-merging/branches-are-just-pointers.md)
