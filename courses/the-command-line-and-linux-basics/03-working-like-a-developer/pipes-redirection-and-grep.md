---
title: "Pipes, Redirection and grep"
course: The Command Line and Linux Basics
module: "3. Working Like a Developer"
type: Article
level: Beginner
reading_time: 30 min
---

# Pipes, Redirection and grep: The Complete Guide

> 📚 **Before you start**
>
> - [Viewing, Searching and Editing Files](../02-terminal-fundamentals/viewing-searching-and-editing-files.md): `head`, `tail`, `wc`, the basics of `grep`, and the `logs/app.log` file used throughout this lesson.
> - [Files, Folders and Paths](../02-terminal-fundamentals/files-folders-and-paths.md): relative paths and wildcards.

## Introduction

Picture the kitchen of a busy dhaba. One person only chops onions. Another only grinds masala. Another only works the tandoor. None of them could make a full meal alone, but pass the work from one station to the next and out comes dal makhani for forty people. Each station is simple; the line is powerful.

The command line works the same way. `grep` only finds lines. `sort` only sorts. `uniq` only collapses repeats. `wc` only counts. On their own they're modest. Connected with a **pipe**, the `|` character, they become an assembly line: *"take the log, keep the errors, cut out the message, group identical ones, count them, show the biggest first"*, written in one line and run in a fraction of a second.

This lesson teaches you how that assembly line works. You'll learn the three streams every program has, how to send output into files and throw away noise, how pipes connect programs, the handful of text tools that make pipelines useful, how to write search patterns (regular expressions) for `grep`, and how to chain commands so the next one runs only if the last one worked. You'll finish by doing the same things from Python, which is exactly how many automation scripts and AI agents run shell commands.

> 💡 **Key Insight**
>
> Every program reads from **standard input** and writes to **standard output** and **standard error**. **Redirection** (`>`, `>>`, `<`, `2>`) connects those streams to files. **Pipes** (`|`) connect one program's output straight into the next program's input. Learn that and you can combine any tools, including ones that were never designed to work together.

---

## Core Explanation

### 1. The Unix Idea: Small Tools, Joined by Text

Unix systems were designed around a simple philosophy: write programs that **do one thing well**, that **work together**, and that **use plain text** as their common language. Because every tool reads and writes lines of text, the output of any tool can be the input of any other. That's why a tool written in 1974 (`sort`) works perfectly on the output of one written last month.

You'll use the `logs/app.log` file from the previous lesson. If you don't have it, scroll back to section 1 of [Viewing, Searching and Editing Files](../02-terminal-fundamentals/viewing-searching-and-editing-files.md) and run the setup block. Then:

```bash
cd ~/projects/cricket-stats
```

### 2. The Three Standard Streams

Every program starts with three channels already open, each with a number called a **file descriptor**:

| Stream | Number | Default destination | Used for |
|---|---|---|---|
| **standard input** (stdin) | 0 | Your keyboard | Data the program reads |
| **standard output** (stdout) | 1 | Your terminal screen | Normal results |
| **standard error** (stderr) | 2 | Your terminal screen | Error and progress messages |

```mermaid
flowchart LR
  K([Keyboard]) -->|"stdin (0)"| P["Program"]
  P -->|"stdout (1)"| S([Screen])
  P -->|"stderr (2)"| S
```

stdout and stderr both appear on the screen, so they look the same. They're separate on purpose: you can save results to a file while still seeing errors, or throw away errors while keeping results. Watch them in one command, which lists a real folder and a missing one:

```bash
ls data missing-folder
```

Example output:

```
ls: cannot access 'missing-folder': No such file or directory
data:
scores.csv
```

The first line came through **stderr**; the rest through **stdout**. The next sections pull them apart.

### 3. Sending Output to a File: `>` and `>>`

`>` sends stdout into a file instead of the screen. The file is created if it doesn't exist and **emptied first if it does**:

```bash
grep ERROR logs/app.log > errors.txt
cat errors.txt
```

Example output:

```
2026-10-10 09:03:02 ERROR database connection refused
2026-10-10 09:06:12 ERROR payment gateway timeout for order 7781
2026-10-10 09:09:30 ERROR payment gateway timeout for order 7790
```

`>>` **appends** to the end instead of replacing:

```bash
echo "extra line" >> errors.txt
wc -l errors.txt
```

Example output:

```
4 errors.txt
```

> ⚠️ `>` empties the file **before** the command even runs. That means `sort data.csv > data.csv` destroys your data: the shell empties `data.csv`, then `sort` reads an empty file. Always write to a new file and rename it afterwards (`sort data.csv > sorted.csv && mv sorted.csv data.csv`). Running `set -o noclobber` makes bash refuse to overwrite existing files with `>`; use `>|` when you really mean it.

### 4. Redirecting Errors: `2>`, `2>&1` and `/dev/null`

Put the stream number in front of `>` to redirect that stream. `2>` redirects stderr:

```bash
ls data missing-folder 2> err.txt
```

Example output:

```
data:
scores.csv
```

The error went into `err.txt`; the screen shows only the normal output.

**`/dev/null`** is a special file that discards everything written to it, a black hole. Use it to hide noise:

```bash
ls data missing-folder 2>/dev/null
```

Example output:

```
data:
scores.csv
```

`find / -name "*.conf" 2>/dev/null` is a classic: it searches everywhere but hides the hundreds of "Permission denied" messages from folders you can't read.

To send **both** streams to the same file, redirect stdout and then say "send stream 2 wherever stream 1 is going" with `2>&1`:

```bash
ls data missing-folder > all.txt 2>&1
cat all.txt
```

Example output:

```
ls: cannot access 'missing-folder': No such file or directory
data:
scores.csv
```

**Order matters.** Redirections are processed left to right. `> all.txt 2>&1` first points stdout at the file, then points stderr at "wherever stdout is now", the file. Written the other way round, `2>&1 > all.txt` points stderr at the *screen* (where stdout was at that moment) and only then moves stdout to the file, so errors still appear on screen. bash also has a shorthand, `&> all.txt`, for "both streams to this file".

| You write | stdout goes to | stderr goes to |
|---|---|---|
| `cmd > out.txt` | out.txt | screen |
| `cmd 2> err.txt` | screen | err.txt |
| `cmd > out.txt 2> err.txt` | out.txt | err.txt |
| `cmd > all.txt 2>&1` | all.txt | all.txt |
| `cmd &> all.txt` (bash, zsh) | all.txt | all.txt |
| `cmd > /dev/null 2>&1` | nowhere | nowhere |

### 5. Feeding Input: `<`, Here-Documents and Here-Strings

`<` makes a file a program's stdin:

```bash
wc -l < data/scores.csv
```

Example output:

```
6
```

Compare with `wc -l data/scores.csv`, which prints `6 data/scores.csv`. With `<`, `wc` never learns the file's name; it just reads a stream, so it prints only the number. That's handy in scripts.

A **here-document** feeds several lines typed right in the command, up to a marker word you choose (often `EOF`). You used one to create the log file:

```bash
cat > greeting.txt <<'EOF'
Namaste!
Your order has shipped.
EOF
```

Quoting the marker (`'EOF'`) keeps the text exactly as typed. Without the quotes, the shell would replace things like `$HOME` inside the text with their values first.

A **here-string** (`<<<`, bash and zsh) feeds a single string:

```bash
tr 'a-z' 'A-Z' <<< "upi payment received"
```

Example output:

```
UPI PAYMENT RECEIVED
```

### 6. Pipes: Connecting Programs

The pipe, `|`, connects the stdout of the command on its left to the stdin of the command on its right. No temporary file is needed; data flows straight through.

```bash
grep ERROR logs/app.log | wc -l
```

Example output:

```
3
```

`grep` finds the three error lines and, instead of printing them, hands them to `wc -l`, which counts them. You can chain as many stages as you like:

```mermaid
flowchart LR
  A["awk: print column 3<br/>(the log level)"] -->|"|"| B["sort<br/>(group equal lines)"]
  B -->|"|"| C["uniq -c<br/>(count each group)"]
  C -->|"|"| D["sort -rn<br/>(biggest first)"]
  D --> S([Screen])
```

```bash
awk '{print $3}' logs/app.log | sort | uniq -c | sort -rn
```

Example output:

```
      7 INFO
      3 ERROR
      2 WARN
```

Read pipelines left to right, like a sentence: "print each line's third column, sort them, count repeats, sort by count, highest first". To build one, start with the first command alone, look at its output, add one stage, look again. Never write a six-stage pipeline in one go.

All the programs in a pipeline start at the same time and run together, passing data as it's produced. That's why `tail -f app.log | grep ERROR` shows new errors live, and why pipelines handle files far bigger than your memory.

Only **stdout** goes through a pipe. Error messages still go to the screen, which is usually what you want. To push stderr through as well, use `2>&1 |` (or `|&` in bash).

### 7. The Pipeline Toolbox

These small tools do most of the work in real pipelines.

**`sort`** sorts lines alphabetically. Options: `-n` numeric, `-r` reverse, `-u` unique, `-t,` to set the separator and `-k4` to sort by the fourth field.

```bash
printf '10\n9\n100\n' | sort
printf '10\n9\n100\n' | sort -n
```

Example output:

```
10
100
9
9
10
100
```

Without `-n`, numbers sort like words ("1" before "9"), a very common surprise.

**`uniq`** collapses **adjacent** duplicate lines; `-c` counts them. Because it only compares neighbours, you almost always `sort` first:

```bash
printf 'apple\napple\nbanana\napple\n' | uniq -c
```

Example output:

```
      2 apple
      1 banana
      1 apple
```

**`cut`** extracts columns. `-d,` sets the delimiter, `-f3,4` picks fields:

```bash
cut -d, -f3,4 data/scores.csv
```

Example output:

```
opponent,runs
Australia,287
England,312
Pakistan,245
South Africa,198
New Zealand,301
```

`cut` is simple-minded: it doesn't understand quoted CSV fields that contain commas. For real-world CSVs, use Python or a proper tool.

**Top three scores**, combining several tools:

```bash
tail -n +2 data/scores.csv | sort -t, -k4 -n -r | head -n 3
```

Example output:

```
2026-09-03,India,England,312,4
2026-09-10,India,New Zealand,301,5
2026-09-01,India,Australia,287,6
```

**`tr`** translates or deletes characters: `tr 'a-z' 'A-Z'` uppercases, `tr -d '\r'` removes Windows carriage returns, `tr ':' '\n'` puts each item of a colon-separated list on its own line.

**`awk`** is a small language for column-based text. `$1`, `$2`... are the fields of each line (split on spaces by default, or on what you give with `-F`), `NR` is the line number, and `END { }` runs after the last line. A total in one line:

```bash
awk -F, 'NR > 1 { total += $4 } END { print "Total runs:", total }' data/scores.csv
```

Example output:

```
Total runs: 1343
```

Or keep rows that meet a condition, like a tiny SQL `WHERE`:

```bash
awk '$3 == "ERROR" { print $2 }' logs/app.log
```

Example output:

```
09:03:02
09:06:12
09:09:30
```

**`sed`** edits text as it flows past (`s/old/new/`), as you saw in the previous lesson.

**`tee`** is a T-junction: it writes its input to a file **and** passes it on, so you can save an intermediate result and keep going:

```bash
grep WARN logs/app.log | tee warnings.txt | wc -l
```

Example output:

```
2
```

The two warning lines are now in `warnings.txt`, and the count was printed. `tee` is also how you write to a protected file through `sudo`: `echo "127.0.0.1 myapp.local" | sudo tee -a /etc/hosts` (plain `sudo echo ... >> /etc/hosts` fails, because the `>>` is done by *your* shell, not by the root process).

**`xargs`** turns lines of input into **arguments** for a command. Some commands (`rm`, `wc`, `cp`) take file names as arguments rather than reading stdin, and `xargs` bridges the gap:

```bash
find . -maxdepth 1 -name "*.txt" | sort | xargs wc -l
```

Example output:

```
  3 ./all.txt
  1 ./err.txt
  4 ./errors.txt
  2 ./greeting.txt
  2 ./warnings.txt
 12 total
```

`find` lists the text files you've created in this lesson (`-maxdepth 1` stays in the current folder), `sort` puts them in a stable order, and `xargs` runs `wc -l` with all of them as arguments.

File names with spaces break plain `xargs`; the safe form is `find . -name "*.txt" -print0 | xargs -0 wc -l`, which separates names with an invisible null character.

### 8. grep and Regular Expressions

Searching for a fixed word is only the start. `grep` understands **regular expressions** (regex): patterns that describe text. The same ideas appear in Python's `re` module, in editors, in SQL and in almost every programming language, so they're worth learning once.

| Pattern | Matches | Example |
|---|---|---|
| `.` | Any single character | `h.t` matches `hat`, `hot`, `h9t` |
| `*` | The previous item, zero or more times | `go*d` matches `gd`, `god`, `good` |
| `^` | The start of a line | `^ERROR` only if the line starts with ERROR |
| `$` | The end of a line | `ms$` only if the line ends with `ms` |
| `[abc]`, `[0-9]` | One character from a set or range | `[0-9][0-9]` two digits |
| `[^0-9]` | One character **not** in the set | |
| `\` | Make the next character literal | `\.` matches an actual dot |

With `grep -E` (**extended** regex) you also get:

| Pattern | Matches |
|---|---|
| `+` | The previous item, one or more times |
| `?` | The previous item, optional |
| `{4}`, `{2,5}` | Exactly 4 times, or between 2 and 5 |
| `a\|b` | `a` or `b` |
| `( )` | Group items together |

**Always wrap patterns in single quotes.** Characters like `*`, `$`, `|` and `?` mean something to the shell too; single quotes stop the shell from touching them, so `grep` receives the pattern exactly. Some examples on the log:

```bash
grep -E '[0-9]{4}ms' logs/app.log          # any timing of four digits or more
```

Example output:

```
2026-10-10 09:02:33 WARN  slow query: 1530ms on /stats
```

```bash
grep 'ms$' logs/app.log | wc -l             # lines ending in a timing
```

Example output:

```
4
```

```bash
grep -E 'ERROR|WARN' logs/app.log          # either level
```

Example output:

```
2026-10-10 09:02:33 WARN  slow query: 1530ms on /stats
2026-10-10 09:03:02 ERROR database connection refused
2026-10-10 09:06:12 ERROR payment gateway timeout for order 7781
2026-10-10 09:06:13 WARN  falling back to queue for order 7781
2026-10-10 09:09:30 ERROR payment gateway timeout for order 7790
```

`-o` prints **only the matching part** of each line, which turns `grep` into an extraction tool:

```bash
grep -oE '(GET|POST) /[a-z/0-9]+' logs/app.log | sort | uniq -c | sort -rn
```

Example output:

```
      2 GET /matches
      1 POST /upi/pay
      1 GET /matches/42
```

That's an endpoint usage report in one line. Lines with equal counts can appear in a different order on your machine, because `sort` breaks ties using your language settings.

GNU `grep` on Linux also has `-P` for Perl-style patterns (with shortcuts like `\d` for a digit); macOS's `grep` doesn't, so stick to `-E` in anything that must run on both.

### 9. Running Commands in Sequence: `;`, `&&` and `||`

Every command finishes with an **exit code** (also called exit status): `0` means success, and anything else means some kind of failure. The shell stores the last one in `$?`:

```bash
grep -q ERROR logs/app.log
echo $?
grep -q CRITICAL logs/app.log
echo $?
```

Example output:

```
0
1
```

(`-q` means quiet: print nothing, just set the exit code.) Three operators use exit codes to chain commands:

| Operator | Meaning | Example |
|---|---|---|
| `a ; b` | Run `a`, then `b`, no matter what | `cd /tmp ; ls` |
| `a && b` | Run `b` **only if** `a` succeeded | `mkdir -p out && cp data/*.csv out/` |
| `a \|\| b` | Run `b` **only if** `a` failed | `grep -q ERROR app.log \|\| echo "all clear"` |

```bash
ls missing && echo "never printed"
ls missing || echo "fallback ran"
```

Example output:

```
ls: cannot access 'missing': No such file or directory
ls: cannot access 'missing': No such file or directory
fallback ran
```

`&&` is the one you'll use most. `cd project && rm -r build` is much safer than `cd project; rm -r build`: if the `cd` fails, the `&&` version stops instead of deleting `build` from whatever folder you happen to be in.

In a pipeline, `$?` is normally the exit code of the **last** command only, so `false | true` "succeeds". In scripts you'll turn on `set -o pipefail` to make a failure anywhere in the pipeline count, as you'll see in the scripting lesson.

### 10. Command Substitution: `$( )`

`$(command)` runs a command and drops its output into the middle of another command:

```bash
echo "Today is $(date +%A) and there are $(ls | wc -l) items here"
```

Example output:

```
Today is Sunday and there are 9 items here
```

(The nine items are the project's folders and files plus the `.txt` files you've created in this lesson.)

You'll use this constantly in scripts: `today=$(date +%F)` stores today's date (like `2026-10-11`) in a variable, and `cp report.csv "report-$(date +%F).csv"` makes a dated copy. (You may see the older backtick form, `` `date` ``; `$( )` does the same and nests cleanly.)

### 11. A Real Investigation, Step by Step

Question: *which kinds of errors happened, and how often?* Build it one stage at a time.

```bash
grep ERROR logs/app.log                                     # step 1: the error lines
grep ERROR logs/app.log | cut -d' ' -f4-                     # step 2: drop date, time, level
grep ERROR logs/app.log | cut -d' ' -f4- | sed 's/ for order [0-9]*//'   # step 3: remove the order number
```

Step 3 makes errors that differ only by order number identical, so they can be grouped. Now count:

```bash
grep ERROR logs/app.log | cut -d' ' -f4- | sed 's/ for order [0-9]*//' | sort | uniq -c | sort -rn
```

Example output:

```
      2 payment gateway timeout
      1 database connection refused
```

That one line is a summary report you could paste into an incident channel. Save it with `> error-summary.txt`, or add `| tee error-summary.txt` to see it and save it.

### 12. Pipes in PowerShell

PowerShell has pipes and redirection too, but its pipes pass **objects** (with properties like `Name` and `Length`), not lines of text. The shapes look familiar:

| Task | bash / zsh | PowerShell |
|---|---|---|
| Save output | `cmd > out.txt` | `cmd > out.txt` (or `Out-File`) |
| Append | `cmd >> out.txt` | `cmd >> out.txt` |
| Hide errors | `cmd 2>/dev/null` | `cmd 2>$null` |
| Both streams | `cmd > all.txt 2>&1` | `cmd > all.txt 2>&1` (or `*> all.txt`) |
| Find lines | `grep ERROR app.log` | `Select-String ERROR app.log` |
| Count lines | `... \| wc -l` | `... \| Measure-Object -Line` |
| Sort | `... \| sort` | `... \| Sort-Object` |
| Count by group | `sort \| uniq -c` | `Group-Object` |
| Run if previous succeeded | `a && b` | `a && b` (PowerShell 7 and later) |

### 13. Pipes and Redirection from Python

Python's `subprocess` module gives your programs the same powers. You can feed a program's stdin, capture stdout and stderr **separately**, and check the exit code:

```python
import subprocess

LOG = """2026-10-10 09:00:01 INFO  server started on port 8000
2026-10-10 09:03:02 ERROR database connection refused
2026-10-10 09:06:12 ERROR payment gateway timeout for order 7781
2026-10-10 09:06:13 WARN  falling back to queue for order 7781
2026-10-10 09:09:30 ERROR payment gateway timeout for order 7790
"""

# Like: grep -c ERROR <<< "$LOG"   (input= feeds stdin)
result = subprocess.run(["grep", "-c", "ERROR"], input=LOG, capture_output=True, text=True)
print("error lines:", result.stdout.strip(), "| exit code:", result.returncode)

# No match: grep prints nothing and exits with 1
result = subprocess.run(["grep", "CRITICAL"], input=LOG, capture_output=True, text=True)
print("CRITICAL found?", result.returncode == 0)

# stdout and stderr arrive separately, just like > and 2>
result = subprocess.run(["ls", "/definitely-missing-folder"], capture_output=True, text=True)
print("stdout:", repr(result.stdout))
print("stderr:", result.stderr.strip())
print("exit code:", result.returncode)
```

Output:

```
error lines: 3 | exit code: 0
CRITICAL found? False
stdout: ''
stderr: ls: cannot access '/definitely-missing-folder': No such file or directory
exit code: 2
```

To build a real pipe between two programs, connect one process's stdout to the next one's stdin with `subprocess.Popen`, which is exactly what the shell does for `|`:

```python
# Like: grep ERROR | wc -l
grep = subprocess.Popen(["grep", "ERROR"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
wc = subprocess.Popen(["wc", "-l"], stdin=grep.stdout, stdout=subprocess.PIPE, text=True)
grep.stdin.write(LOG)
grep.stdin.close()
grep.stdout.close()            # let wc own the pipe now
print("piped count:", wc.communicate()[0].strip())
grep.wait()
```

Output:

```
piped count: 3
```

For text processing you control, it's usually clearer to do the whole pipeline in Python. Here's the "error kinds" report from section 11, with `re` playing `grep`/`sed` and `Counter` playing `sort | uniq -c | sort -rn`:

```python
import re
from collections import Counter

kinds = Counter()
for line in LOG.splitlines():
    if " ERROR " in line:
        message = line.split(maxsplit=3)[3]                    # cut -d' ' -f4-
        message = re.sub(r" for order \d+", "", message)       # sed 's/ for order [0-9]*//'
        kinds[message] += 1

for message, count in kinds.most_common():
    print(f"{count:>7} {message}")
```

Output:

```
      2 payment gateway timeout
      1 database connection refused
```

You'll often see `subprocess.run("grep ERROR app.log | wc -l", shell=True)`. `shell=True` hands the whole string to a shell, so pipes and wildcards work, but it's dangerous with any text that comes from users or files: a value like `x; rm -rf ~` becomes a second command. Prefer lists of arguments, and if you must build a shell string, quote each piece with `shlex.quote()`.

---

## Try It Yourself

Use `logs/app.log` and `data/scores.csv`.

1. **Save and hide.** Run `find / -name "hosts"`, saving the results to `found.txt` and throwing away all the "Permission denied" errors. Then print how many results there were.
2. **Lowest score.** Print the opponent and runs of the lowest-scoring match (one line), using `tail`, `sort`, `head` and `cut`.
3. **Requests per minute.** From the log, count how many lines there are for each minute (`09:00`, `09:01`, ...). Hint: `cut -c` cuts by character position; the time starts at character 12.
4. **Safe chaining.** Write one line that creates a `backup` folder and, only if that worked, copies `data/scores.csv` into it, then prints "backed up" only if the copy worked.

<details>
<summary>Show answers</summary>

**1.**

```bash
find / -name "hosts" 2>/dev/null > found.txt
wc -l < found.txt
```

The count depends on your system; `/etc/hosts` is always one of them.

**2.**

```bash
tail -n +2 data/scores.csv | sort -t, -k4 -n | head -n 1 | cut -d, -f3,4
```

Example output:

```
South Africa,198
```

**3.**

```bash
cut -c 12-16 logs/app.log | sort | uniq -c
```

Example output:

```
      2 09:00
      1 09:01
      1 09:02
      3 09:03
      1 09:05
      2 09:06
      1 09:07
      1 09:09
```

**4.**

```bash
mkdir -p backup && cp data/scores.csv backup/ && echo "backed up"
```

</details>

---

## Real-World Examples

### Example 1: The Daily Error Digest

An operations team at an e-commerce company runs a one-line pipeline each morning: `grep -h ERROR /var/log/shop/*.log | cut -d' ' -f4- | sort | uniq -c | sort -rn | head -n 20 > digest.txt`, and emails `digest.txt` to the team. Twenty lines tell them which problems were most frequent overnight. No dashboards were needed to start; just pipes.

### Example 2: Quick Data Checks Before Loading

A data engineer receives a CSV of 2 million UPI transactions. Before loading it, `cut -d, -f5 txns.csv | sort | uniq -c` shows the count per status (`SUCCESS`, `FAILED`, `PENDING`) and immediately reveals a new, unexpected status value, `REVERSED`, that the loading code doesn't handle.

### Example 3: Agents Reading Command Output

Coding agents run commands like `pytest 2>&1 | tail -n 40`: run the tests, merge errors into the output so nothing is lost, and keep only the last 40 lines to save context. Understanding `2>&1` and pipes lets you read and trust what the agent actually saw.

---

## Common Misconceptions

### Misconception 1: "`>` adds to a file"

`>` **replaces** the file's contents (and empties it before the command runs). `>>` appends. Mixing them up is one of the most common ways to lose data.

### Misconception 2: "Errors go through the pipe too"

Only stdout goes through `|`. Error messages still appear on screen. Use `2>&1 |` if you want them in the pipeline.

### Misconception 3: "`uniq` removes all duplicates"

It removes only **adjacent** duplicates. Sort first (`sort | uniq`), or use `sort -u`.

### Misconception 4: "`sort` understands numbers"

By default it sorts text, so `100` comes before `9`. Add `-n` for numbers, and `-t` and `-k` to sort a specific column.

---

## Interview Relevance

Pipeline questions are popular in DevOps, SRE, data engineering and backend interviews, often as a live task on a log file.

- **"Find the ten most common IP addresses in an access log."** `awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -n 10`. Explain each stage and why `sort` must come before `uniq`.
- **"What's the difference between `>` and `>>`? What does `2>&1` do?"** Overwrite vs append; redirect stderr to wherever stdout currently points. Strong answers explain why the order of redirections matters.
- **"What's `/dev/null`?"** A device that discards everything written to it; used to silence output.
- **"`&&` vs `;`?"** `&&` runs the next command only on success (exit code 0). Mention exit codes and `$?`.
- **"How would you run a pipeline from Python safely?"** `subprocess.run` with a list of arguments, `capture_output=True`, checking `returncode`; avoid `shell=True` with untrusted input, or use `shlex.quote`.

---

## Key Takeaways

- Every program has **stdin (0), stdout (1) and stderr (2)**. They're separate so you can handle results and errors differently.
- **`>` overwrites, `>>` appends, `<` reads, `2>` redirects errors, `2>&1` merges them, `/dev/null` discards.**
- **`|` connects stdout to the next stdin.** Build pipelines one stage at a time, checking the output as you go.
- The toolbox: **`sort` (`-n`, `-r`, `-k`), `uniq -c`, `cut`, `tr`, `awk`, `sed`, `tee`, `xargs`**, and **`grep -E` / `-o`** with single-quoted regular expressions.
- **Exit code 0 means success.** `&&` continues on success, `||` on failure; prefer `&&` before anything destructive.
- From Python, use **`subprocess.run([...], capture_output=True, text=True)`** and avoid `shell=True` with untrusted text.

---

**Up next:** [Processes, Ports and Environment Variables](processes-ports-and-environment-variables.md)
