---
title: "Lab: Set up Python and run your first script"
course: Python Fundamentals
module: "2. Getting Started with Python"
type: Lab
level: Beginner
reading_time: 45 min
---

# Lab: Set Up Python and Run Your First Script

> 📚 **Before you start**
>
> - [What is Python and Why Use It?](what-is-python-and-why-use-it.md), for what the interpreter does
> - [Numbers, Booleans and Strings](numbers-booleans-and-strings.md), for the code in steps 6 to 8 (you can do steps 1 to 5 before reading it)
>
> You'll type a handful of commands into a **terminal**. This lab explains each one. For a full introduction, see [The Command Line and Linux Basics](../../the-command-line-and-linux-basics/course.md#m2).

## What You'll Build

By the end of this lab your computer will be a working Python workstation, and you'll have written, run and fixed a real program: a **trip expense splitter** that works out who owes what after a weekend in Goa.

```mermaid
flowchart LR
  A["Step 1: Open a terminal"] --> B["Step 2: Install Python 3.13+"]
  B --> C["Step 3: Check the install"]
  C --> D["Step 4: Try the interactive prompt"]
  D --> E["Step 5: Install VS Code"]
  E --> F["Step 6: Write hello.py"]
  F --> G["Step 7: Build the expense splitter"]
  G --> H["Step 8: Break it and fix it"]
  H --> I["Step 9: Virtual environments"]
```

> 💡 **Key Insight**
>
> There are two ways to talk to Python. The **interactive prompt** (`>>>`) runs one line at a time and shows the result immediately: perfect for experiments. A **script** is a `.py` file that runs top to bottom: perfect for anything you want to keep, re-run or share. Professionals use both all day.

---

## Step 1: Open a Terminal

A **terminal** is a window where you type commands as text instead of clicking. The program inside it that reads your commands is called a **shell**.

| Your computer | How to open a terminal |
|---|---|
| **Windows 10/11** | Press the Start key, type `Terminal` (or `PowerShell`), press Enter |
| **macOS** | Press Cmd + Space, type `Terminal`, press Enter |
| **Linux (Ubuntu and similar)** | Press Ctrl + Alt + T |

You'll see a **prompt**, a short line ending in `>`, `$` or `%`, waiting for you to type. In this lab, lines starting with `$` are commands you type (don't type the `$` itself), and the lines after them are what you should see.

First, check whether Python is already installed:

```bash
$ python3 --version
```

On Windows, try these instead:

```powershell
> python --version
> py --version
```

Example output:

```
Python 3.13.7
```

If you see **Python 3.13 or higher**, skip to Step 3. If you see an older version (like 3.10), a "command not found" message, or Windows opens the Microsoft Store, continue with Step 2.

---

## Step 2: Install Python

### Windows: the Python install manager

The recommended way to install Python on Windows today is the **Python install manager**, a small official tool from the Python team that installs and updates Python versions for you.

1. Get it from **one** of these places (they install the same thing):
   - the **Microsoft Store**: search for "Python Install Manager" and click Install, or
   - **python.org/downloads**: download the Windows install manager and double-click it.
2. Open a **new** terminal window and install Python:

```powershell
> py install 3.13
> py list
```

`py list` shows the versions installed, with 3.13 among them.

3. If you're asked whether to add a folder to your **PATH**, say yes. PATH is the list of folders the terminal searches for commands; adding Python's folder lets you type `python` from anywhere.

After this, `python` runs your default Python and `py` lets you pick a version, for example `py -V:3.13`. Older guides tell you to download a `.exe` installer and tick "Add python.exe to PATH". That installer still exists for current versions, but it is deprecated and won't be produced from Python 3.16 onwards, so prefer the install manager.

### macOS

1. Go to **python.org/downloads** and download the latest macOS installer (a `.pkg` file).
2. Double-click it and follow the steps.
3. Open a **new** Terminal window. On macOS the command is `python3` (plain `python` may not exist).

If you already use **Homebrew** (a popular package manager for macOS), `brew install python@3.13` works too.

### Linux

Most Linux distributions already include Python 3. On Ubuntu or Debian, make sure you also have the virtual-environment and pip pieces:

```bash
$ sudo apt update
$ sudo apt install python3 python3-venv python3-pip
```

`sudo` runs a command as administrator and will ask for your password. If your distribution's Python is older than 3.13, the simplest way to get a newer one without touching the system Python is the `uv` tool (`uv python install 3.13`), covered in [Package Managers and Virtual Environments](../../the-command-line-and-linux-basics/course.md#m3).

---

## Step 3: Check the Install

Open a **new** terminal (old windows don't see newly installed programs) and run:

```bash
$ python3 --version
$ python3 -c "print('Python is working')"
```

Example output:

```
Python 3.13.7
Python is working
```

`-c` means "run this little piece of code". If both lines appear, Python works.

> **Which command do I use?** On Windows use `python` (or `py`). On macOS and Linux use `python3`. The rest of this course writes `python3`; Windows users can simply type `python` wherever they see it.

---

## Step 4: Try the Interactive Prompt (the REPL)

Type `python3` on its own and press Enter. You'll see a welcome line and the `>>>` prompt. This is the **REPL**: it **R**eads a line, **E**valuates it, **P**rints the result, and **L**oops back for more.

Type each line after `>>>` and press Enter:

```pycon
>>> 2 + 3
5
>>> 1_00_000 * 12
1200000
>>> "chai" * 3
'chaichaichai'
>>> city = "Pune"
>>> city
'Pune'
>>> len(city)
4
```

Things to notice:

- In the REPL you don't need `print()`; it shows the value of whatever you type. (In a script you **do** need `print()`.)
- Strings are shown with quotes (`'Pune'`) so you can tell `'4'` the text from `4` the number.
- Assignments like `city = "Pune"` show nothing; they just create the name.

Since Python 3.13 the REPL has colours, lets you edit multi-line code with the arrow keys, and remembers previous lines (press the Up arrow). Type `help()` for the built-in help system; type `exit` (or press Ctrl + D on macOS/Linux, Ctrl + Z then Enter on Windows) to leave.

You can try any example from this course in the REPL. When you see a code block with `>>>` like the one above, that's what it means.

---

## Step 5: Install a Code Editor

You can write Python in Notepad, but a **code editor** colours your code, spots mistakes as you type, indents for you and runs your file with one click. We'll use **Visual Studio Code** (VS Code), which is free and runs on all three systems.

1. Download it from **code.visualstudio.com** and install it.
2. Open VS Code, click the **Extensions** icon in the left bar (four small squares), search for **Python**, and install the extension published by **Microsoft**.
3. Make a folder for your practice files, for example `python-practice` in your Documents folder.
4. In VS Code choose **File → Open Folder...** and open `python-practice`.

If you prefer another editor (PyCharm, Zed, Sublime Text, or even the `IDLE` editor that comes with Python on Windows and macOS), that's fine. Everything in this course works the same.

---

## Step 6: Write and Run hello.py

In VS Code, create a new file in your folder called `hello.py`. The `.py` ending tells your computer and your editor that this is Python. Type the code below and save the file (Ctrl + S, or Cmd + S on macOS). Then run it, either with the ▷ **Run** button at the top right of VS Code, or in a terminal opened in the same folder (VS Code: **Terminal → New Terminal**) by typing:

```bash
$ python3 hello.py
```

Here is the file:

```python
# hello.py: my first Python script
print("Namaste! This is my first Python program.")
print("2 + 2 =", 2 + 2)
print("Python can count to a crore:", 1_00_00_000)
```

Output:

```
Namaste! This is my first Python program.
2 + 2 = 4
Python can count to a crore: 10000000
```

Congratulations: you've written and run a program. What happened behind the scenes: the `python3` command started the interpreter, which compiled `hello.py` to bytecode and ran it line by line from top to bottom, exactly as described in [What is Python and Why Use It?](what-is-python-and-why-use-it.md)

If you see `can't open file 'hello.py': [Errno 2] No such file or directory`, your terminal is in a different folder from your file. Use `cd` to move into your folder first (for example `cd Documents/python-practice`), or use VS Code's built-in terminal, which opens in the right folder.

---

## Step 7: Build the Trip Expense Splitter

Four friends went to Goa. Different people paid for different things. Let's work out each person's fair share and who owes what. Create `split.py`:

```python
# split.py: split a trip's expenses fairly (run with: python3 split.py)

# Who paid how much (in rupees)
aarav_paid = 12000    # hotel
diya_paid = 4500      # scooters and fuel
kabir_paid = 6300     # food
meera_paid = 1200     # beach shack snacks

people = 4
total = aarav_paid + diya_paid + kabir_paid + meera_paid
share = total / people

print("=== Goa trip expenses ===")
print(f"Total spent:     ₹{total:,}")
print(f"Each person's share: ₹{share:,.2f}")
print()

# Positive balance: the group owes you. Negative: you owe the group.
print(f"Aarav balance: ₹{aarav_paid - share:+,.2f}")
print(f"Diya balance:  ₹{diya_paid - share:+,.2f}")
print(f"Kabir balance: ₹{kabir_paid - share:+,.2f}")
print(f"Meera balance: ₹{meera_paid - share:+,.2f}")
```

Output:

```
=== Goa trip expenses ===
Total spent:     ₹24,000
Each person's share: ₹6,000.00

Aarav balance: ₹+6,000.00
Diya balance:  ₹-1,500.00
Kabir balance: ₹+300.00
Meera balance: ₹-4,800.00
```

The empty `print()` in the middle prints a blank line, which separates the two sections.

New pieces in this script:

- `{total:,}` adds thousands separators to a whole number.
- `{share:,.2f}` adds separators and shows exactly 2 decimal places.
- `{aarav_paid - share:+,.2f}` puts an expression inside the braces, and the `+` in the format spec forces a sign (`+` or `-`) so you can see at a glance who is owed money.

The balances always add up to zero: Aarav and Kabir are owed ₹6,300 in total, and Diya and Meera owe exactly that much between them. A quick self-check like this is a good habit for any money calculation.

### Make it interactive

Once it works with fixed numbers, you can ask the user for the amounts instead. Replace the four `_paid` lines with:

```python
# not-run: waits for keyboard input
aarav_paid = float(input("How much did Aarav pay? "))
diya_paid = float(input("How much did Diya pay? "))
kabir_paid = float(input("How much did Kabir pay? "))
meera_paid = float(input("How much did Meera pay? "))
```

Example session:

```
How much did Aarav pay? 12000
How much did Diya pay? 4500
How much did Kabir pay? 6300
How much did Meera pay? 1200
=== Goa trip expenses ===
Total spent:     ₹24,000.0
...
```

Remember from the previous lesson: `input()` always returns a string, so we wrap it in `float()` to get a number. Notice the total now prints as `24,000.0` because it's a float; you could format it with `:,.2f` instead.

---

## Step 8: Break It and Fix It

Errors are normal. Let's meet three on purpose so they're familiar when they happen by accident. Make each change, run the script, read the error, then undo the change.

**Break 1: a missing bracket.** Delete the last `)` from `print("=== Goa trip expenses ===")`.

```python
# not-run: shows an error on purpose
aarav_paid = 12000
print("=== Goa trip expenses ==="
print(aarav_paid)
```

Running it shows:

```
  File "/home/you/python-practice/example.py", line 3
    print("=== Goa trip expenses ==="
         ^
SyntaxError: '(' was never closed
```

Python points at the bracket that was opened and never closed. Nothing ran, because a `SyntaxError` is found before running.

**Break 2: a misspelt name.** Change `share = total / people` to `share = totl / people`.

```python
# not-run: shows an error on purpose
total = 24000
people = 4
share = totl / people
```

Running it shows:

```
Traceback (most recent call last):
  File "/home/you/python-practice/example.py", line 4, in <module>
    share = totl / people
            ^^^^
NameError: name 'totl' is not defined. Did you mean: 'total'?
```

Python even suggests the right spelling.

**Break 3: text instead of a number.** Change `diya_paid = 4500` to `diya_paid = "4500"` (with quotes).

```python
# not-run: shows an error on purpose
aarav_paid = 12000
diya_paid = "4500"
total = aarav_paid + diya_paid
```

Running it shows:

```
Traceback (most recent call last):
  File "/home/you/python-practice/example.py", line 4, in <module>
    total = aarav_paid + diya_paid
            ~~~~~~~~~~~^~~~~~~~~~~
TypeError: unsupported operand type(s) for +: 'int' and 'str'
```

"Unsupported operand types for +: int and str" means you tried to add a number and a string. The fix is to remove the quotes (or convert with `int()`).

The three-step routine for **any** error:

1. Read the **last line**: what kind of error, and the message.
2. Read the **line number** and the code shown with `^` markers: where it happened.
3. Look at that line (and sometimes the line just before it, for syntax errors) and fix it.

---

## Step 9: Virtual Environments (Optional for Now, Essential Later)

So far you've used only what comes with Python. Later courses install extra packages such as pandas. Installing packages into your main Python for every project eventually causes conflicts (project A needs version 1, project B needs version 2). The fix is a **virtual environment**: a private folder of packages for one project.

Create and activate one inside your practice folder:

```bash
$ python3 -m venv .venv
$ source .venv/bin/activate          # macOS and Linux
```

```powershell
> python -m venv .venv
> .venv\Scripts\Activate               # Windows
```

Your prompt now starts with `(.venv)`. Inside it, `python` and `pip` refer to this project's private copies. Try installing a package and checking it:

```bash
(.venv) $ pip install requests
(.venv) $ python -c "import requests; print(requests.__version__)"
(.venv) $ deactivate
```

pip prints a few lines ending in `Successfully installed ... requests-...`, and the second command prints the installed version number, such as `2.32.5`.

`deactivate` leaves the environment. VS Code notices a `.venv` folder and offers to use it automatically. You won't need any packages for the rest of this course; everything uses the standard library. The details (pip, requirements files, `uv`) are in [Package Managers and Virtual Environments](../../the-command-line-and-linux-basics/course.md#m3).

---

## Try It Yourself

1. **Add a fifth friend.** Add `rohan_paid = 3000` to `split.py`, update `people` and `total`, and print Rohan's balance. Do the balances still add to zero?
2. **REPL calculator.** In the REPL, work out how many seconds there are in a year (365 days). Then use `_` (an underscore), which in the REPL means "the last result", to divide that by 60.
3. **Run code without a file.** Use `python3 -c` to print the result of `17 // 5` and `17 % 5` on one line.
4. **Format check.** Change `{share:,.2f}` to `{share:,.0f}` and to `{share:.3f}`. What changes?

<details>
<summary>Show answers</summary>

**1.**

```python
aarav_paid = 12000
diya_paid = 4500
kabir_paid = 6300
meera_paid = 1200
rohan_paid = 3000

people = 5
total = aarav_paid + diya_paid + kabir_paid + meera_paid + rohan_paid
share = total / people
print(f"Share: ₹{share:,.2f}")
print(f"Rohan balance: ₹{rohan_paid - share:+,.2f}")
balances = [aarav_paid - share, diya_paid - share, kabir_paid - share,
            meera_paid - share, rohan_paid - share]
print("Sum of balances:", round(sum(balances), 2))
```

Output:

```
Share: ₹5,400.00
Rohan balance: ₹-2,400.00
Sum of balances: 0.0
```

**2.** `365 * 24 * 60 * 60` gives `31536000`; then `_ / 60` gives `525600.0` (minutes in a year).

**3.** `python3 -c "print(17 // 5, 17 % 5)"` prints `3 2`.

**4.** `:,.0f` shows `6,000` with no decimals; `:.3f` shows `6000.000` with three decimals and no separator.

</details>

---

## What You've Learned

- **Installing Python**: the install manager on Windows, the python.org installer on macOS, the package manager on Linux, and how to check the version.
- **The REPL** (`>>>`) for quick experiments, and how it differs from a script (no `print()` needed).
- **Writing and running scripts** with `python3 file.py` or VS Code's Run button.
- **Formatting money** with f-strings: `:,`, `:.2f` and `:+`.
- **Reading errors**: `SyntaxError` (nothing runs), `NameError` (unknown name), `TypeError` (wrong types together), using the last line and the line number.
- **Virtual environments** keep each project's packages separate.

---

**Up next:** [Containers and Mutability](../03-core-language-concepts/containers-and-mutability.md)
