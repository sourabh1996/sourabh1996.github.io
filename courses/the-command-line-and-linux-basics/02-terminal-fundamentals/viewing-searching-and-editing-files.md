---
title: "Viewing, Searching and Editing Files"
course: The Command Line and Linux Basics
module: "2. Terminal Fundamentals"
type: Article
level: Beginner
reading_time: 25 min
---

# Viewing, Searching and Editing Files: The Complete Guide

> 📚 **Before you start**
>
> - [What is a Terminal and a Shell?](what-is-a-terminal-and-a-shell.md): running commands, options and arguments.
> - [Files, Folders and Paths](files-folders-and-paths.md): `cd`, `ls`, relative paths and wildcards. This lesson keeps using the `~/projects/cricket-stats` folder from there.

## Introduction

It's 9:10 a.m. and the payments page of a small online shop has been failing since 9:03. Somewhere on the server is a log file with a hundred thousand lines. You could download it and scroll through it in a text editor, hoping to spot the problem. Or you could type one short command and see only the lines that say `ERROR`, with line numbers, in under a second.

That is what this lesson gives you. Developers spend a surprising amount of time *reading* files rather than writing them: log files, configuration files, CSV exports, code they didn't write. The terminal has small, fast tools for each kind of reading: show the whole file, page through a huge file, look at just the start or the end, watch a file grow in real time, count lines, find the lines that match a word, and find files by name, size or age. When it's time to change something, you'll be able to make a quick edit without leaving the terminal, which matters a lot on servers where there's no graphical editor at all.

By the end, you'll know `cat`, `less`, `head`, `tail`, `wc`, `grep`, `find` and `diff`, how to survive in `nano` and `vim`, why files from Windows sometimes break Linux scripts, and how to do the same reading and searching from Python.

> 💡 **Key Insight**
>
> **Never open a whole file when you only need part of it.** Use `head` for the start, `tail` for the end, `less` to browse, and `grep` to jump straight to the lines that matter. These tools read files as a stream, so they're just as fast on a 5 GB log as on a 5-line note.

---

## Core Explanation

### 1. Set Up Something to Read

Let's add a small application log to the practice project. Copy this block into your terminal exactly as it is. The `<<'EOF'` part (called a **here-document**) feeds every line up to `EOF` into the file; you'll learn how it works in the pipes lesson.

```bash
cd ~/projects/cricket-stats
mkdir -p logs
cat > logs/app.log <<'EOF'
2026-10-10 09:00:01 INFO  server started on port 8000
2026-10-10 09:00:05 INFO  GET /matches 200 12ms
2026-10-10 09:01:17 INFO  GET /matches/42 200 8ms
2026-10-10 09:02:33 WARN  slow query: 1530ms on /stats
2026-10-10 09:03:02 ERROR database connection refused
2026-10-10 09:03:03 INFO  retrying database connection
2026-10-10 09:03:05 INFO  database connected
2026-10-10 09:05:40 INFO  POST /upi/pay 201 95ms
2026-10-10 09:06:12 ERROR payment gateway timeout for order 7781
2026-10-10 09:06:13 WARN  falling back to queue for order 7781
2026-10-10 09:07:55 INFO  GET /matches 200 10ms
2026-10-10 09:09:30 ERROR payment gateway timeout for order 7790
EOF
printf 'date,team,opponent,runs,wickets\n2026-09-01,India,Australia,287,6\n2026-09-03,India,England,312,4\n2026-09-05,India,Pakistan,245,9\n2026-09-08,India,South Africa,198,10\n2026-09-10,India,New Zealand,301,5\n' > data/scores.csv
printf '# Cricket stats\n\nSmall project to analyse match scores.\n' > README.md
printf 'import csv\n\nwith open("data/scores.csv") as f:\n    rows = list(csv.DictReader(f))\nprint(len(rows), "matches")\n' > scripts/summary.py
```

`printf` prints text where `\n` means "new line", and `>` saves it into a file. You now have a log, a CSV, a README and a tiny Python script to practise on.

### 2. Text Files and Binary Files

Everything in this lesson works on **text files**: files that contain readable characters arranged in lines, such as `.txt`, `.csv`, `.json`, `.py`, `.log`, `.md`, `.yaml` and most configuration files. Each line ends with an invisible **newline** character.

**Binary files** (images, PDFs, ZIP archives, Excel `.xlsx`, compiled programs, Parquet files) contain bytes that aren't meant to be read as text. Printing one to the terminal fills the screen with garbage and can even scramble your terminal's settings. If that happens, type `reset` and press Enter. When in doubt, check first with `file`:

```bash
file logs/app.log
```

Example output:

```
logs/app.log: ASCII text
```

### 3. `cat`: Print the Whole File

`cat` prints a file's entire contents. It's perfect for short files:

```bash
cat data/scores.csv
```

Example output:

```
date,team,opponent,runs,wickets
2026-09-01,India,Australia,287,6
2026-09-03,India,England,312,4
2026-09-05,India,Pakistan,245,9
2026-09-08,India,South Africa,198,10
2026-09-10,India,New Zealand,301,5
```

`cat -n` adds line numbers. The name comes from con**cat**enate: given several files, it prints them one after another, which is how you join files together (`cat jan.csv feb.csv > both.csv`).

Don't `cat` a large file. The text scrolls past faster than you can read and you only see the end. That's what `less` is for.

### 4. `less`: Browse Any File, Any Size

`less` opens a file in a scrollable viewer. It loads only what's on screen, so it opens a multi-gigabyte log instantly.

```bash
less logs/app.log
```

Inside `less`:

| Key | Action |
|---|---|
| **Space** / **b** | Down / back one page |
| **↓** / **↑** (or **j** / **k**) | One line down / up |
| **g** / **G** | Jump to the start / end of the file |
| **/** `word` then Enter | Search forward for `word` |
| **n** / **N** | Next / previous match |
| **F** | Follow: keep showing new lines as they're added (Ctrl + C to stop following) |
| **q** | Quit |

`less -N` shows line numbers, and `less -S` stops long lines from wrapping (handy for wide CSVs). You've used `less` already without knowing it: `man` pages open in it. (There's an older tool, `more`, that does a subset of this. "less is more", as the joke goes.)

### 5. `head` and `tail`: The Start and the End

`head` shows the first lines of a file (10 by default); `tail` shows the last lines. Use `-n` to choose how many.

```bash
head -n 3 logs/app.log
```

Example output:

```
2026-10-10 09:00:01 INFO  server started on port 8000
2026-10-10 09:00:05 INFO  GET /matches 200 12ms
2026-10-10 09:01:17 INFO  GET /matches/42 200 8ms
```

```bash
tail -n 2 logs/app.log
```

Example output:

```
2026-10-10 09:07:55 INFO  GET /matches 200 10ms
2026-10-10 09:09:30 ERROR payment gateway timeout for order 7790
```

Two tricks you'll use constantly:

- **Peek at a CSV's columns**: `head -n 1 data/scores.csv` prints just the header row.
- **Skip the header**: `tail -n +2 data/scores.csv` means "start from line 2", so you get every line *except* the header.

**`tail -f` follows a file**: it prints the last lines and then waits, printing each new line as soon as it's written. Run your app in one terminal and `tail -f logs/app.log` in another, and you're watching the log live. Press **Ctrl + C** to stop watching. (`tail -F` does the same but keeps going even if the file is replaced, which happens when logs are "rotated" each night.)

### 6. `wc`: Count Lines, Words and Bytes

```bash
wc logs/app.log
```

Example output:

```
 12  89 651 logs/app.log
```

That's 12 lines, 89 words and 651 bytes. Most of the time you just want lines:

```bash
wc -l logs/app.log data/scores.csv
```

Example output:

```
 12 logs/app.log
  6 data/scores.csv
 18 total
```

A CSV with 6 lines has 5 data rows plus a header, a classic off-by-one to watch for.

### 7. `grep`: Find the Lines That Match

`grep` prints every line in a file that contains a pattern. It's the tool from the introduction:

```bash
grep ERROR logs/app.log
```

Example output:

```
2026-10-10 09:03:02 ERROR database connection refused
2026-10-10 09:06:12 ERROR payment gateway timeout for order 7781
2026-10-10 09:09:30 ERROR payment gateway timeout for order 7790
```

The options you'll reach for most:

| Option | Meaning | Example |
|---|---|---|
| `-i` | Ignore upper/lower case | `grep -i error` matches `ERROR`, `Error`, `error` |
| `-n` | Show line numbers | `grep -n WARN logs/app.log` |
| `-c` | Just count matching lines | `grep -c ERROR logs/app.log` → `3` |
| `-v` | Invert: lines that do **not** match | `grep -v INFO` hides the noise |
| `-w` | Whole words only | `grep -w cat` won't match `concatenate` |
| `-r` | Search every file in a folder, recursively | `grep -r "scores" .` |
| `-l` | Only list the names of files that match | `grep -rl "TODO" src/` |
| `-C 2` | Show 2 lines of context around each match (`-A` after, `-B` before) | see below |
| `-E` | Extended patterns, such as "this OR that" | `grep -E "ERROR\|WARN"` |

```bash
grep -n WARN logs/app.log
```

Example output:

```
4:2026-10-10 09:02:33 WARN  slow query: 1530ms on /stats
10:2026-10-10 09:06:13 WARN  falling back to queue for order 7781
```

Context is how you understand *why* something happened:

```bash
grep -C 1 "connection refused" logs/app.log
```

Example output:

```
2026-10-10 09:02:33 WARN  slow query: 1530ms on /stats
2026-10-10 09:03:02 ERROR database connection refused
2026-10-10 09:03:03 INFO  retrying database connection
```

Search a whole project, with file names and line numbers:

```bash
grep -rn "scores" .
```

Example output:

```
./README.md:3:Small project to analyse match scores.
./scripts/summary.py:3:with open("data/scores.csv") as f:
```

Add `--include="*.py"` to search only Python files, or `--exclude-dir=.venv` to skip a folder.

Put the pattern in quotes whenever it contains spaces or special characters: `grep "order 7781" logs/app.log`. Without quotes, the shell would split it into two arguments and `grep` would look for `order` in a file called `7781`.

When nothing matches, `grep` prints nothing and finishes with exit code `1` instead of `0`. Scripts use that to decide what to do next. The pipes lesson goes much deeper into `grep`: patterns (regular expressions), and using it as a filter on other commands' output.

### 8. `find`: Find Files by Name, Type, Size or Age

`grep` searches *inside* files. `find` searches for the files *themselves*. Its shape is `find <where> <tests>`:

```bash
find . -name "*.csv"
```

Example output:

```
./data/scores.csv
```

The tests you'll use most:

| Test | Meaning |
|---|---|
| `-name "*.csv"` | Name matches the pattern (case-sensitive) |
| `-iname "*.csv"` | Same, ignoring case (matches `.CSV` too) |
| `-type f` / `-type d` | Only files / only directories |
| `-size +100M` | Larger than 100 MB (`k`, `M`, `G` units; `-` means smaller) |
| `-mtime -7` | Modified within the last 7 days (`+7`: more than 7 days ago) |
| `-mmin -60` | Modified within the last 60 minutes |
| `-maxdepth 1` | Don't go deeper than one level |

Tests combine with "and" by default:

```bash
find ~ -type f -name "*.log" -size +50M     # big log files anywhere in your home folder
find . -type d -name ".venv"                  # every virtual environment folder here
find data -name "*.csv" -mtime -1             # CSVs changed in the last day
```

> ⚠️ **Always quote the pattern** in `-name "*.csv"`. Without quotes, the shell expands `*.csv` itself *before* `find` runs (remember: the shell expands wildcards). If the current folder happens to contain one CSV, `find` receives that one name and silently searches for the wrong thing.

`find` can also act on what it finds. `-exec` runs a command on each result, with `{}` standing for the file name and `\;` ending the command:

```bash
find data -name "*.csv" -exec wc -l {} \;
```

Example output:

```
6 data/scores.csv
```

There's also `-delete`, which deletes every match. It's the standard way to clean up old files (`find /tmp/reports -name "*.csv" -mtime +30 -delete`), and you'll use it in the lab. Always run the same `find` **without** `-delete` first and read the list.

One gotcha: `-size` rounds sizes **up** to the unit before comparing, so `-size -1k` means "rounds up to less than 1 KB", which only matches empty files. Use `-size -1024c` (bytes) when you need precision.

### 9. `diff`: What Changed Between Two Files?

`diff` compares two text files line by line. Make a modified copy to see it:

```bash
cp data/scores.csv /tmp/scores_v2.csv
sed -i 's/198,10/203,10/' /tmp/scores_v2.csv          # change one score (on macOS: sed -i '' ...; see section 11)
echo "2026-09-12,India,Sri Lanka,276,7" >> /tmp/scores_v2.csv   # add a match at the end
diff data/scores.csv /tmp/scores_v2.csv
```

Example output:

```
5c5
< 2026-09-08,India,South Africa,198,10
---
> 2026-09-08,India,South Africa,203,10
6a7
> 2026-09-12,India,Sri Lanka,276,7
```

`5c5` means "line 5 changed", `<` lines come from the first file and `>` lines from the second, and `6a7` means "after line 6, a line was added". The **unified** format, `diff -u`, is easier to read and is what Git shows you:

```bash
diff -u data/scores.csv /tmp/scores_v2.csv
```

Example output:

```
--- data/scores.csv	2026-10-11 05:29:49.744150979 +0000
+++ /tmp/scores_v2.csv	2026-10-11 05:37:22.788005427 +0000
@@ -2,5 +2,6 @@
 2026-09-01,India,Australia,287,6
 2026-09-03,India,England,312,4
 2026-09-05,India,Pakistan,245,9
-2026-09-08,India,South Africa,198,10
+2026-09-08,India,South Africa,203,10
 2026-09-10,India,New Zealand,301,5
+2026-09-12,India,Sri Lanka,276,7
```

Lines starting with `-` were removed, `+` were added, and a space means unchanged context. If the files are identical, `diff` prints nothing and exits with `0`.

### 10. Editing Files in the Terminal

On your laptop you'll write code in a full editor such as VS Code (run `code .` in a folder to open it there). But on a server, inside a Docker container, or when Git opens an editor for a commit message, you need a terminal editor. Learn the basics of two:

**nano: the friendly one.** Run `nano notes.txt`. Type normally; arrow keys move the cursor. The shortcuts are listed at the bottom of the screen, where `^` means Ctrl:

| Keys | Action |
|---|---|
| **Ctrl + O**, then Enter | Save ("write Out") |
| **Ctrl + X** | Exit (asks to save if there are changes) |
| **Ctrl + W** | Search ("Where is") |
| **Ctrl + K** / **Ctrl + U** | Cut a line / paste it |

**vim: the powerful one.** `vim` (or `vi`) is installed on almost every Linux server, so it's worth knowing how to survive in it. Its big idea is **modes**: in *normal mode* keys are commands; in *insert mode* keys type text. Beginners get stuck because they start typing in normal mode. The survival kit:

| Keys | Action |
|---|---|
| **i** | Enter insert mode; now you can type |
| **Esc** | Back to normal mode |
| **:w** then Enter | Save |
| **:q** then Enter | Quit |
| **:wq** then Enter | Save and quit |
| **:q!** then Enter | Quit **without** saving (your escape hatch) |
| **/word** | Search |
| **dd** / **u** | Delete a line / undo |

If you're ever stuck in vim: press **Esc** a couple of times, type `:q!` and press Enter.

Many tools (Git, `crontab -e`, `sudoedit`) open "your editor". They choose it from the `EDITOR` environment variable. Add `export EDITOR=nano` to your shell settings if you'd rather not meet vim by surprise. (Environment variables are explained in *Processes, Ports and Environment Variables*.)

### 11. Quick Edits Without an Editor

Sometimes you just need to change one thing in a file, or many files. `sed` (stream editor) can replace text:

```bash
sed 's/India/IND/' data/scores.csv | head -n 3
```

Example output:

```
date,team,opponent,runs,wickets
2026-09-01,IND,Australia,287,6
2026-09-03,IND,England,312,4
```

`s/old/new/` replaces the first `old` on each line; add `g` (`s/old/new/g`) to replace every occurrence. Used like this, `sed` only *prints* the changed text and leaves the file alone. To change the file itself, add `-i` (in place):

```bash
sed -i 's/Sri Lanka/SL/' /tmp/scores_v2.csv        # Linux and WSL
sed -i '' 's/Sri Lanka/SL/' /tmp/scores_v2.csv     # macOS needs an empty '' after -i
```

(Section 9 used the same `sed -i` form to change a score.) The extra `''` on macOS is one of the GNU-versus-BSD differences mentioned in the first lesson. To add a line to the end of a file, `echo "new line" >> file.txt` works everywhere (`>>` appends; you'll meet it properly in the pipes lesson).

### 12. Line Endings: Why Windows Files Break Linux Scripts

Linux and macOS end each line with one invisible character, **LF** (line feed, written `\n`). Windows traditionally uses two, **CR LF** (`\r\n`). Most editors hide the difference, but shell scripts and some tools don't: a script saved with Windows line endings fails on Linux with confusing errors like `$'\r': command not found` or `/usr/bin/env: 'bash\r': No such file or directory`.

Create two small files with Windows line endings to see it (`\r\n` writes CR LF):

```bash
printf 'Buy milk\r\nBook train tickets\r\n' > todo.txt
printf 'name,city\r\nAsha,Pune\r\n' > data/windows.csv
```

`file` spots it:

```bash
file todo.txt
```

Example output:

```
todo.txt: ASCII text, with CRLF line terminators
```

and `cat -A` makes the hidden characters visible (`^M` is the CR, `$` marks the end of each line):

```bash
cat -A data/windows.csv
```

Example output:

```
name,city^M$
Asha,Pune^M$
```

Fix it with the `dos2unix` tool (install it with your package manager), or `sed -i 's/\r$//' file`. In VS Code, the status bar shows `CRLF` or `LF`; click it to switch. If you're on Windows, set Git to keep LF in your repositories (the Git course covers this), and keep projects inside WSL.

### 13. The Same Tools in PowerShell

| Task | Linux / macOS / WSL | PowerShell |
|---|---|---|
| Print a file | `cat file` | `Get-Content file` (`cat`, `type`) |
| First / last 10 lines | `head file`, `tail file` | `Get-Content file -TotalCount 10`, `Get-Content file -Tail 10` |
| Follow a log | `tail -f file` | `Get-Content file -Wait -Tail 10` |
| Count lines | `wc -l file` | `(Get-Content file).Count` |
| Find matching lines | `grep -n ERROR file` | `Select-String ERROR file` (case-insensitive by default) |
| Find files by name | `find . -name "*.csv"` | `Get-ChildItem -Recurse -Filter *.csv` |
| Compare files | `diff a b` | `Compare-Object (Get-Content a) (Get-Content b)` |
| Edit | `nano file` | `notepad file` |

### 14. The Same Ideas in Python

Reading and searching files is just as natural in Python. Like `head`, `tail` and `grep`, this code reads the file one line at a time, so it would work on a huge log too. It writes a small log into a temporary folder first so it runs anywhere:

```python
import re
import tempfile
from collections import deque
from itertools import islice
from pathlib import Path

LOG = """2026-10-10 09:00:01 INFO  server started on port 8000
2026-10-10 09:02:33 WARN  slow query: 1530ms on /stats
2026-10-10 09:03:02 ERROR database connection refused
2026-10-10 09:05:40 INFO  POST /upi/pay 201 95ms
2026-10-10 09:06:12 ERROR payment gateway timeout for order 7781
2026-10-10 09:09:30 ERROR payment gateway timeout for order 7790
"""

tmp = tempfile.TemporaryDirectory()
log_path = Path(tmp.name) / "logs" / "app.log"
log_path.parent.mkdir()
log_path.write_text(LOG)

with log_path.open() as f:                     # head -n 2
    print("HEAD:", [line.rstrip() for line in islice(f, 2)])

with log_path.open() as f:                     # tail -n 1 (a deque keeps only the last N lines)
    print("TAIL:", deque(f, maxlen=1)[0].rstrip())

with log_path.open() as f:                     # grep -n ERROR, and wc -l
    total = 0
    for number, line in enumerate(f, start=1):
        total = number
        if "ERROR" in line:
            print(f"{number}:{line.rstrip()}")
print("lines:", total)
```

Output:

```
HEAD: ['2026-10-10 09:00:01 INFO  server started on port 8000', '2026-10-10 09:02:33 WARN  slow query: 1530ms on /stats']
TAIL: 2026-10-10 09:09:30 ERROR payment gateway timeout for order 7790
3:2026-10-10 09:03:02 ERROR database connection refused
5:2026-10-10 09:06:12 ERROR payment gateway timeout for order 7781
6:2026-10-10 09:09:30 ERROR payment gateway timeout for order 7790
lines: 6
```

And `find` plus `grep -o` (print only the matching part) translate to `rglob` and a regular expression:

```python
(Path(tmp.name) / "data").mkdir()
(Path(tmp.name) / "data" / "scores.csv").write_text("date,runs\n")
(Path(tmp.name) / "data" / "NOTES.CSV").write_text("note\n")

root = Path(tmp.name)
print("find -name '*.csv':", [str(p.relative_to(root)) for p in sorted(root.rglob("*.csv"))])
print("find -iname '*.csv':", [str(p.relative_to(root)) for p in sorted(root.rglob("*"))
                               if p.suffix.lower() == ".csv"])

orders = re.findall(r"order (\d+)", log_path.read_text())
print("orders that timed out:", orders)

tmp.cleanup()
```

Output:

```
find -name '*.csv': ['data/scores.csv']
find -iname '*.csv': ['data/NOTES.CSV', 'data/scores.csv']
orders that timed out: ['7781', '7790']
```

For a quick look, the terminal tools are faster to type. For anything you'll rerun, combine with other logic, or test, Python is the better home.

---

## Try It Yourself

Use the `logs/app.log` and `data/scores.csv` files from section 1.

1. **Count the problems.** How many lines in `logs/app.log` are *not* `INFO` lines? Answer with one `grep` command.
2. **Data rows only.** Print `data/scores.csv` without its header, then print just the last two data rows.
3. **Find recent Python.** Write a `find` command that lists `.py` files under `~/projects` modified in the last 7 days, skipping nothing. Why must `"*.py"` be quoted?
4. **Survive vim.** Open `vim /tmp/practice.txt`, type the line `chai at 4pm`, save and quit. Then open it again, delete the line, and quit *without* saving. Check the file with `cat`.

<details>
<summary>Show answers</summary>

**1.** `grep -vc INFO logs/app.log` prints `5` (2 warnings and 3 errors). `-v` inverts the match and `-c` counts.

**2.**

```bash
tail -n +2 data/scores.csv
tail -n 2 data/scores.csv
```

The second command prints the South Africa and New Zealand rows.

**3.** `find ~/projects -type f -name "*.py" -mtime -7`. The quotes stop the shell from expanding `*.py` against the current folder before `find` sees it. Without them, a single `.py` file in your current folder would replace the pattern and `find` would search for that exact name.

**4.** `vim /tmp/practice.txt`, press **i**, type the text, press **Esc**, type `:wq` and Enter. Reopen, press **dd** to delete the line, then `:q!` and Enter. `cat /tmp/practice.txt` still prints `chai at 4pm`, because you quit without saving.

</details>

---

## Real-World Examples

### Example 1: The 9 a.m. Incident

An on-call engineer at a food-delivery company is paged: payments are failing. They SSH to the server, run `tail -n 200 /var/log/app/payments.log | grep -i error` to see recent errors, notice `gateway timeout` repeated, and run `grep -c "gateway timeout" payments.log` to see it's happened 1,400 times in an hour. Two commands, under a minute, and they know which team to call.

### Example 2: Checking a Data Delivery

A data engineer receives a daily CSV from a partner bank. Before loading it, they run `head -n 3` to check the columns haven't changed, `wc -l` to compare the row count with yesterday's, and `file` to catch Windows line endings or a wrong encoding. These ten-second checks stop bad data before it reaches a dashboard.

### Example 3: Finding What Filled the Disk

A cloud VM stops working because its disk is full. `find / -type f -size +1G 2>/dev/null` lists every file over 1 GB (the `2>/dev/null` hides "Permission denied" noise; you'll learn it in the pipes lesson). The culprit is a debug log that grew to 40 GB. `find /var/log/myapp -name "*.log" -mtime +7 -delete` clears old logs, and the server recovers.

---

## Common Misconceptions

### Misconception 1: "`cat` is how you read a file"

`cat` dumps the whole file at once. For anything longer than a screen, use `less` to browse, or `head`, `tail` and `grep` to see only what you need.

### Misconception 2: "`grep` searches for file names"

`grep` searches the **contents** of files. To search for files by **name**, use `find` (or `ls` with a wildcard). `grep -l` combines them a little: it prints the names of files whose contents match.

### Misconception 3: "I'm stuck in vim forever"

Press **Esc**, then type `:q!` and Enter. That always quits without saving. Then set `EDITOR=nano` if you prefer.

### Misconception 4: "A file that looks fine in my editor is fine"

Invisible characters matter: Windows line endings, a byte-order mark at the start of a UTF-8 file, or trailing spaces can all break scripts and data loads. `file` and `cat -A` reveal them.

---

## Interview Relevance

These tools come up in almost every DevOps, SRE, backend and data engineering interview, often as a hands-on task: "here's a server, find out why the app is failing."

- **"How do you view a 10 GB log file?"** Not with an editor. `less` to browse, `tail -n` or `tail -f` for recent and live lines, `grep` to filter. Explain that these stream the file instead of loading it all.
- **"Find all files over 100 MB modified in the last week."** `find / -type f -size +100M -mtime -7`. Mention quoting `-name` patterns and testing before `-delete`.
- **"Search a codebase for every use of a function."** `grep -rn "function_name" .`, with `--include` or `--exclude-dir` to narrow it. Bonus: mention faster modern tools like `ripgrep` (`rg`).
- **"A script works on Windows but fails on Linux with `\r` errors. Why?"** CRLF line endings; fix with `dos2unix` or editor/Git settings.
- **"How do you exit vim?"** Esc, then `:q!` (discard) or `:wq` (save). Said with a smile, it shows you've been there.

---

## Key Takeaways

- **`cat`** for short files, **`less`** for browsing anything large, **`head`/`tail`** for the start and end, **`tail -f`** to watch a log live.
- **`wc -l`** counts lines; remember the header row in CSVs.
- **`grep`** finds matching lines (`-i`, `-n`, `-v`, `-c`, `-r`, `-C`); **`find`** finds files by name, type, size and age. Quote your patterns.
- **`diff -u`** shows what changed between two files, in the same format Git uses.
- In **nano**, Ctrl + O saves and Ctrl + X exits. In **vim**, `i` to type, Esc, then `:wq` to save or `:q!` to bail out.
- **Windows line endings (CRLF)** break Linux scripts; spot them with `file`, fix them with `dos2unix`.

---

**Up next:** [Permissions and Users](permissions-and-users.md)
