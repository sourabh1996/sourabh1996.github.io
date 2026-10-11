---
title: "Reading and Writing Files"
course: Advanced Python Programming
module: "3. File Handling"
type: Article
level: Intermediate
reading_time: 40 min
---

# Reading and Writing Files: The Complete Guide

> 📚 **Before you start**
>
> - [Working with Strings](../../python-fundamentals/course.md#m5) and [Dictionaries and Dictionary Views](../../python-fundamentals/course.md#m5) (Python Fundamentals)
> - [Iterators and Generators](../../python-fundamentals/course.md#m6) (Python Fundamentals), because a file is an iterator of lines
> - [Dunder Methods](../02-object-oriented-programming/dunder-methods.md), for how `with` works (`__enter__`/`__exit__`)

## Introduction

Every useful program eventually touches files. The accounts team sends a CSV export of last month's UPI transactions. An LLM app keeps its prompts in text files and its settings in a TOML file. A fine-tuning dataset is a JSON Lines file with a million examples. A web scraper saves pages to disk. The log of a crashed server is a 2 GB text file you need to search.

Reading a file looks easy: `open("data.txt").read()`. But real files bring real problems. The file written on Windows has different line endings. The export from Excel starts with three invisible bytes. A customer's name contains "ñ" or "शर्मा" and your program crashes with `UnicodeDecodeError`. A comma inside an address breaks your hand-written CSV parser. Your script forgets to close a file and the data never reaches the disk.

By the end of this lesson you will be able to open files in the right mode, read them efficiently, write them safely, handle text encodings correctly, work with paths using `pathlib`, and read and write CSV and JSON (including JSON Lines) with the standard library. Every example writes into a temporary directory, so you can run them all without leaving anything behind.

> 💡 **Key Insight**
>
> A file on disk holds **bytes**. Text is an *interpretation* of those bytes, and the **encoding** is the rule for that interpretation. Always open text files with an explicit `encoding="utf-8"` and inside a `with` block. Those two habits prevent most file bugs you will ever meet.

---

## Core Explanation

### 1. Setting Up a Safe Playground

All examples in this lesson work inside a temporary directory created by the `tempfile` module. The operating system picks a unique location (in `/tmp` on Linux, a user temp folder on Windows), so nothing clashes with your real files:

```python
import tempfile
from pathlib import Path

tmp = tempfile.TemporaryDirectory()     # a new, empty directory
base = Path(tmp.name)                   # a Path object pointing at it
print(base.is_dir(), list(base.iterdir()))
```

Output:

```
True []
```

At the end of the lesson we call `tmp.cleanup()` to delete it. In normal code you'd write `with tempfile.TemporaryDirectory() as d:` and Python would delete it when the block ends. We keep it open here so later examples can use the files earlier ones created.

### 2. Opening, Writing and Reading a Text File

```python
notes = base / "chai_orders.txt"        # Path's / operator joins path parts

with open(notes, "w", encoding="utf-8") as f:
    f.write("masala chai,2\n")
    f.write("ginger chai,1\n")
    f.write("filter coffee,3\n")

with open(notes, encoding="utf-8") as f:   # mode defaults to "r" (read text)
    content = f.read()

print(repr(content))
print(content, end="")
```

Output:

```
'masala chai,2\nginger chai,1\nfilter coffee,3\n'
masala chai,2
ginger chai,1
filter coffee,3
```

Key points:

- **`open(path, mode, encoding=...)`** returns a **file object**: a Python object connected to the file on disk, with methods such as `read` and `write`.
- **`write()` does not add a newline.** You add `\n` yourself. It returns the number of characters written.
- **`with ... as f:`** guarantees the file is **closed** when the block ends, even if an exception happens inside it. Closing matters: written data sits in a memory buffer until it is flushed to disk, and an operating system only lets a process keep a limited number of files open. (Behind the scenes `with` calls the file's `__enter__` and `__exit__` methods, as you saw in [Dunder Methods](../02-object-oriented-programming/dunder-methods.md).)

```python
print(f.closed)                         # the with block closed it for us
try:
    f.read()
except ValueError as err:
    print("ValueError:", err)
```

Output:

```
True
ValueError: I/O operation on closed file.
```

### 3. File Modes

The second argument to `open` is the **mode**: what you want to do, and whether you work with text or bytes.

| Mode | Meaning | If the file exists | If it doesn't |
|---|---|---|---|
| `"r"` | Read (default) | Read from the start | `FileNotFoundError` |
| `"w"` | Write | **Erased** first (truncated to zero length) | Created |
| `"a"` | Append | Writes go to the end | Created |
| `"x"` | Exclusive create | `FileExistsError` | Created |
| `"r+"` | Read and write | Read/write from the start, no truncation | `FileNotFoundError` |
| `"w+"` | Write and read | Erased first | Created |
| `"a+"` | Append and read | Writes always go to the end | Created |

Add **`b`** for binary (`"rb"`, `"wb"`, `"ab"`): you read and write `bytes` objects and no encoding is applied. Without `b` (or with `t`, which is the default) you are in **text mode**: you read and write `str`, and Python encodes and decodes for you.

```python
with open(notes, "a", encoding="utf-8") as f:          # append keeps what's there
    f.write("cutting chai,4\n")

try:
    with open(notes, "x", encoding="utf-8") as f:       # refuse to overwrite
        f.write("oops")
except FileExistsError as err:
    print("FileExistsError:", err.strerror)

with open(notes, "rb") as f:                            # binary: raw bytes
    raw = f.read()
print(type(raw).__name__, len(raw), raw[:14])
```

Output:

```
FileExistsError: File exists
bytes 59 b'masala chai,2\n'
```

**`"w"` destroys the existing content the moment the file is opened**, before you write a single character. Many people have lost data by opening the wrong file with `"w"`. When a file must not be overwritten, use `"x"`. And when you must replace an important file, write to a temporary file and swap it in (the **atomic write** pattern in [Buffered I/O and Other File Methods](buffered-i-o-and-other-file-methods.md)).

### 4. Reading: All at Once, Line by Line, or in Pieces

```python
with open(notes, encoding="utf-8") as f:
    first = f.readline()            # one line, including its '\n'
    rest = f.readlines()            # a list of the remaining lines

print(repr(first))
print(rest)

with open(notes, encoding="utf-8") as f:
    for line in f:                  # the file object is an iterator of lines
        item, cups = line.rstrip("\n").split(",")
        print(f"{item:<14}{int(cups):>3} cups")
```

Output:

```
'masala chai,2\n'
['ginger chai,1\n', 'filter coffee,3\n', 'cutting chai,4\n']
masala chai     2 cups
ginger chai     1 cups
filter coffee   3 cups
cutting chai    4 cups
```

| Method | Returns | Memory use | Use for |
|---|---|---|---|
| `f.read()` | the whole file as one `str` | whole file | small files |
| `f.read(n)` | up to `n` characters (`""` at the end) | `n` | processing in chunks |
| `f.readline()` | the next line (`""` at the end) | one line | reading a header, then looping |
| `f.readlines()` | list of all lines | whole file | small files when you need a list |
| `for line in f:` | one line per iteration | one line | **any size; the default choice** |

Looping over the file object reads it lazily, one line at a time, exactly like a generator. That's how you process a 10 GB log file with a few megabytes of memory. Each line keeps its trailing `"\n"` (except possibly the last), so use `line.rstrip("\n")` or `line.strip()` before splitting.

### 5. Writing: `write`, `writelines` and `print(file=...)`

```python
report = base / "report.txt"
lines = ["Daily chai report\n", "=================\n"]

with open(report, "w", encoding="utf-8") as f:
    f.writelines(lines)                            # writes each string; adds NO newlines
    print("Total cups:", 10, file=f)               # print adds spaces and a newline for you
    print("Top seller", "cutting chai", sep=": ", file=f)
    count = f.write("End of report\n")

print(count)
print(report.read_text(encoding="utf-8"), end="")
```

Output:

```
14
Daily chai report
=================
Total cups: 10
Top seller: cutting chai
End of report
```

`print(..., file=f)` is the most convenient way to write formatted lines, since it handles separators and newlines.

### 6. Text Encodings: Why `encoding="utf-8"` Matters

Computers store bytes (numbers from 0 to 255). An **encoding** maps characters to bytes and back. **Encoding** turns a `str` into `bytes`; **decoding** turns `bytes` into a `str`.

- **ASCII** covers only English letters, digits and basic symbols, one byte each.
- **UTF-8** covers every character in Unicode (Hindi, Tamil, emoji, everything) using 1 to 4 bytes per character, and is identical to ASCII for English text. It is the standard for the web, JSON, Linux and macOS, and for almost all modern data.
- Older encodings such as **cp1252** (Windows Western European) or **latin-1** cover only a few hundred characters.

```python
for word in ["chai", "café", "नमस्ते", "₹500", "🏏"]:
    data = word.encode("utf-8")
    print(f"{word!r:<10} {len(word)} chars -> {len(data):>2} bytes: {data}")

print(b"caf\xc3\xa9".decode("utf-8"))
```

Output:

```
'chai'     4 chars ->  4 bytes: b'chai'
'café'     4 chars ->  5 bytes: b'caf\xc3\xa9'
'नमस्ते'   6 chars -> 18 bytes: b'\xe0\xa4\xa8\xe0\xa4\xae\xe0\xa4\xb8\xe0\xa5\x8d\xe0\xa4\xa4\xe0\xa5\x87'
'₹500'     4 chars ->  6 bytes: b'\xe2\x82\xb9500'
'🏏'        1 chars ->  4 bytes: b'\xf0\x9f\x8f\x8f'
café
```

(Devanagari "नमस्ते" is 6 Unicode code points: letters plus combining vowel signs and a virama.)

If you read bytes with the **wrong** encoding, you get either an error or garbled text (often called **mojibake**):

```python
legacy = base / "customers_cp1252.txt"
legacy.write_bytes("José Muñoz, Café Goa\n".encode("cp1252"))   # a file from an old Windows system

try:
    legacy.read_text(encoding="utf-8")
except UnicodeDecodeError as err:
    print("UnicodeDecodeError:", err.reason, "at byte", err.start)

print(legacy.read_text(encoding="cp1252"), end="")               # the right encoding
print(legacy.read_text(encoding="utf-8", errors="replace"), end="")  # keep going, mark bad bytes
print("café".encode("utf-8").decode("cp1252"))                   # mojibake
```

Output:

```
UnicodeDecodeError: invalid continuation byte at byte 3
José Muñoz, Café Goa
Jos� Mu�oz, Caf� Goa
cafÃ©
```

The `errors` parameter controls what happens with bytes that don't fit:

| `errors=` | Behaviour |
|---|---|
| `"strict"` (default) | Raise `UnicodeDecodeError` / `UnicodeEncodeError` |
| `"replace"` | Put `�` (reading) or `?` (writing) in place of bad data |
| `"ignore"` | Silently drop bad data (dangerous: you lose information without knowing) |
| `"backslashreplace"` | Write an escape like `\xe9`, useful in logs |

**The default encoding trap.** If you call `open()` without `encoding=`, Python uses a default that, up to Python 3.14, depends on the operating system's locale: usually UTF-8 on Linux and macOS, but often cp1252 on Windows. So code that works on your Mac can fail on a colleague's Windows laptop. Python 3.15 makes UTF-8 the default everywhere ("UTF-8 mode", PEP 686), and you can turn it on in earlier versions with `python -X utf8` or the environment variable `PYTHONUTF8=1`. The simplest rule still holds on every version: **always pass `encoding="utf-8"`** for text files (unless you know the file uses something else).

**The BOM.** Excel and some Windows tools save "UTF-8" files with a 3-byte **byte order mark** (`EF BB BF`) at the start. Read normally, it shows up as an invisible `﻿` character glued to your first column name. The `utf-8-sig` encoding strips it when reading (and writes it when writing, which Excel needs to open UTF-8 CSVs with non-English text correctly):

```python
excel_csv = base / "from_excel.csv"
excel_csv.write_bytes(b"\xef\xbb\xbfname,city\nAsha,Pune\n")

print(repr(excel_csv.read_text(encoding="utf-8")[:10]))
print(repr(excel_csv.read_text(encoding="utf-8-sig")[:10]))
```

Output:

```
'\ufeffname,city'
'name,city\n'
```

### 7. Line Endings and the `newline` Parameter

Windows ends lines with `\r\n`, Linux and macOS with `\n`. In text mode Python handles this for you with **universal newlines**: when reading, `\r\n` and `\r` are both turned into `\n`; when writing, `\n` is turned into the platform's line ending (`\r\n` on Windows).

```python
windows_file = base / "windows.txt"
windows_file.write_bytes(b"line one\r\nline two\r\n")

with open(windows_file, encoding="utf-8") as f:
    print(f.readlines())                       # translated to \n
with open(windows_file, encoding="utf-8", newline="") as f:
    print(f.readlines())                       # newline="" keeps the original endings
```

Output:

```
['line one\n', 'line two\n']
['line one\r\n', 'line two\r\n']
```

`newline=""` turns translation off. The `csv` module requires it, because a CSV field may legitimately contain a line break inside quotes and the module wants to handle line endings itself.

### 8. `pathlib`: Paths as Objects

Hand-building paths with string concatenation (`folder + "/" + name`) breaks across operating systems and is easy to get wrong. The `pathlib` module (standard library) represents a path as a `Path` object with useful attributes and methods:

```python
data_dir = base / "data" / "2026" / "october"
data_dir.mkdir(parents=True, exist_ok=True)       # create missing parents; fine if it exists

sales = data_dir / "sales_report.final.csv"
sales.write_text("city,amount\nPune,1200\n", encoding="utf-8")

print(sales.name)           # last part
print(sales.stem)           # name without the final suffix
print(sales.suffix)         # final suffix
print(sales.suffixes)       # all suffixes
print(sales.parent.name)    # the containing folder's name
print(sales.relative_to(base))
print(sales.relative_to(base).parts)
print(sales.with_suffix(".json").name)
print(sales.exists(), sales.is_file(), sales.is_dir(), data_dir.is_dir())
print(sales.stat().st_size, "bytes")
```

Output:

```
sales_report.final.csv
sales_report.final
.csv
['.final', '.csv']
october
data/2026/october/sales_report.final.csv
('data', '2026', 'october', 'sales_report.final.csv')
sales_report.final.json
True True False True
22 bytes
```

(On Windows the printed relative path would use backslashes; the `Path` object takes care of that for you.)

Listing and finding files:

```python
for name in ["sales_jan.csv", "sales_feb.csv", "notes.txt"]:
    (data_dir / name).write_text("x\n", encoding="utf-8")

print(sorted(p.name for p in data_dir.iterdir()))           # direct children
print(sorted(p.name for p in data_dir.glob("sales_*.csv"))) # pattern in this folder
print(sorted(str(p.relative_to(base)) for p in base.rglob("*.txt")))  # recursive search

(data_dir / "notes.txt").rename(data_dir / "notes_old.txt")
(data_dir / "sales_feb.csv").unlink()                        # delete a file
(data_dir / "missing.csv").unlink(missing_ok=True)           # no error if absent
print(sorted(p.name for p in data_dir.iterdir()))
```

Output:

```
['notes.txt', 'sales_feb.csv', 'sales_jan.csv', 'sales_report.final.csv']
['sales_feb.csv', 'sales_jan.csv', 'sales_report.final.csv']
['chai_orders.txt', 'customers_cp1252.txt', 'data/2026/october/notes.txt', 'report.txt', 'windows.txt']
['notes_old.txt', 'sales_jan.csv', 'sales_report.final.csv']
```

In glob patterns, `*` matches any run of characters (including dots, so `sales_*.csv` also matched `sales_report.final.csv`), `?` matches one character, `[abc]` one of a set, and `**` in `glob()` means "any number of subfolders". `rglob(pattern)` is shorthand for `glob("**/" + pattern)`.

`iterdir()`, `glob()` and `rglob()` return results in whatever order the file system gives them, which differs between machines, so **always sort** when order matters.

A quick reference, with the older `os`/`os.path` equivalents you will still see in existing code:

| Task | `pathlib` | Older style |
|---|---|---|
| Join | `base / "data" / "f.csv"` | `os.path.join(base, "data", "f.csv")` |
| Current / home folder | `Path.cwd()`, `Path.home()` | `os.getcwd()`, `os.path.expanduser("~")` |
| Absolute path | `p.resolve()` | `os.path.abspath(p)` |
| Exists? | `p.exists()` | `os.path.exists(p)` |
| Make folders | `p.mkdir(parents=True, exist_ok=True)` | `os.makedirs(p, exist_ok=True)` |
| Read/write whole file | `p.read_text(encoding=...)`, `p.write_text(...)`, `read_bytes`, `write_bytes` | `open(...)` |
| List | `p.iterdir()`, `p.glob("*.csv")`, `p.rglob(...)` | `os.listdir`, `glob.glob` |
| Delete file / empty folder | `p.unlink()`, `p.rmdir()` | `os.remove`, `os.rmdir` |
| Delete a folder tree, copy, move | `shutil.rmtree(p)`, `shutil.copy2(a, b)`, `shutil.move(a, b)` | same |

`open()` accepts `Path` objects directly, and so does nearly every library (pandas, `csv`, `json` via `open`). Use `pathlib` for all new code.

### 9. CSV Files with the `csv` Module

**CSV** (comma-separated values) is the most common data exchange format. It looks simple enough to parse with `line.split(",")`, until a field contains a comma, a quote or a line break:

```python
import csv

orders = base / "orders.csv"
rows = [
    ["order_id", "customer", "address", "amount"],
    [101, "Asha", "Flat 4, Shanti Nagar, Pune", 450.0],
    [102, 'Ravi "RK" Kumar', "MG Road, Bengaluru", 1299.5],
    [103, "Meera", "Line one\nLine two", 89.0],
]
with open(orders, "w", encoding="utf-8", newline="") as f:
    csv.writer(f).writerows(rows)

print(orders.read_text(encoding="utf-8"))
```

Output:

```
order_id,customer,address,amount
101,Asha,"Flat 4, Shanti Nagar, Pune",450.0
102,"Ravi ""RK"" Kumar","MG Road, Bengaluru",1299.5
103,Meera,"Line one
Line two",89.0
```

The writer quoted fields containing commas or line breaks and doubled the quotes inside `Ravi "RK" Kumar`. That is the standard CSV escaping rule, and `split(",")` would get all of it wrong. Reading it back:

```python
with open(orders, encoding="utf-8", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)                 # the first row
    for row in reader:
        print(row)
print(header)
```

Output:

```
['101', 'Asha', 'Flat 4, Shanti Nagar, Pune', '450.0']
['102', 'Ravi "RK" Kumar', 'MG Road, Bengaluru', '1299.5']
['103', 'Meera', 'Line one\nLine two', '89.0']
['order_id', 'customer', 'address', 'amount']
```

Notice every value comes back as a **string**. CSV has no types; converting `"450.0"` to a number is your job.

`DictReader` and `DictWriter` work with dictionaries keyed by the header, which is clearer and survives column reordering:

```python
with open(orders, encoding="utf-8", newline="") as f:
    total = 0.0
    for row in csv.DictReader(f):
        total += float(row["amount"])
        print(f"{row['order_id']}: {row['customer']:<16} ₹{float(row['amount']):>8.2f}")
print(f"Total: ₹{total:.2f}")

summary = base / "summary.csv"
with open(summary, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["city", "orders", "revenue"])
    writer.writeheader()
    writer.writerow({"city": "Pune", "orders": 1, "revenue": 450.0})
    writer.writerows([{"city": "Bengaluru", "orders": 1, "revenue": 1299.5}])
print(summary.read_text(encoding="utf-8"), end="")
```

Output:

```
101: Asha             ₹  450.00
102: Ravi "RK" Kumar  ₹ 1299.50
103: Meera            ₹   89.00
Total: ₹1838.50
city,orders,revenue
Pune,1,450.0
Bengaluru,1,1299.5
```

Other options: `delimiter="\t"` for tab-separated files, `delimiter=";"` for many European exports, `quoting=csv.QUOTE_ALL` or `QUOTE_NONNUMERIC` to control quoting, and `csv.Sniffer` to guess the format of an unknown file. For heavy data work, pandas' `read_csv` (covered in the NumPy and pandas course) adds type inference and much more, but the `csv` module is perfect for scripts and has no dependencies.

### 10. JSON Files with the `json` Module

**JSON** (JavaScript Object Notation) is the format of web APIs, LLM tool calls and most configuration. Python's `json` module converts between JSON text and Python objects:

| JSON | Python |
|---|---|
| object `{...}` | `dict` (keys are always strings) |
| array `[...]` | `list` (tuples are written as arrays too) |
| string | `str` |
| number | `int` or `float` |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

The four functions: `json.dumps(obj)` → string, `json.loads(text)` → object, `json.dump(obj, file)` → write to a file, `json.load(file)` → read from a file. (The `s` stands for "string".)

```python
import json

profile = {
    "name": "अनन्या",                  # Hindi text
    "city": "Pune",
    "upi_ids": ["ananya@okbank", "ananya@upi"],
    "premium": True,
    "referrer": None,
    "balance": 1520.75,
}

compact = json.dumps(profile)
print(compact)
print(json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True))
```

Output:

```
{"name": "\u0905\u0928\u0928\u094d\u092f\u093e", "city": "Pune", "upi_ids": ["ananya@okbank", "ananya@upi"], "premium": true, "referrer": null, "balance": 1520.75}
{
  "balance": 1520.75,
  "city": "Pune",
  "name": "अनन्या",
  "premium": true,
  "referrer": null,
  "upi_ids": [
    "ananya@okbank",
    "ananya@upi"
  ]
}
```

By default `json` escapes every non-ASCII character as `\uXXXX`. That's valid JSON, but unreadable; `ensure_ascii=False` keeps the real characters (so write the file as UTF-8). `indent` pretty-prints and `sort_keys` gives stable output, which makes files easy to compare in version control.

Writing and reading files:

```python
profile_file = base / "profile.json"
with open(profile_file, "w", encoding="utf-8") as f:
    json.dump(profile, f, ensure_ascii=False, indent=2)

with open(profile_file, encoding="utf-8") as f:
    loaded = json.load(f)

print(loaded == profile, loaded["name"], type(loaded["balance"]).__name__)

try:
    json.loads('{"name": "Asha", }')                # trailing comma: invalid JSON
except json.JSONDecodeError as err:
    print("JSONDecodeError:", err)
```

Output:

```
True अनन्या float
JSONDecodeError: Illegal trailing comma before end of object: line 1 column 16 (char 15)
```

`JSONDecodeError` tells you the line and column of the problem, which is useful when an LLM returns almost-valid JSON.

#### Types JSON doesn't know: `default=` and custom decoding

`datetime`, `Decimal`, sets and your own classes aren't JSON types, so `json.dumps` raises `TypeError`. Pass a `default` function that converts them:

```python
from dataclasses import dataclass, asdict
from datetime import date

@dataclass
class Payment:
    payee: str
    amount: float
    paid_on: date

def to_jsonable(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, set):
        return sorted(obj)
    raise TypeError(f"can't serialise {type(obj).__name__}")

p = Payment("Sharma Chai", 40.0, date(2026, 10, 11))
try:
    json.dumps(p)
except TypeError as err:
    print("TypeError:", err)

text = json.dumps({"payment": asdict(p), "tags": {"food", "upi"}}, default=to_jsonable)
print(text)

data = json.loads(text)
restored = Payment(**{**data["payment"], "paid_on": date.fromisoformat(data["payment"]["paid_on"])})
print(restored == p)
```

Output:

```
TypeError: Object of type Payment is not JSON serializable
{"payment": {"payee": "Sharma Chai", "amount": 40.0, "paid_on": "2026-10-11"}, "tags": ["food", "upi"]}
True
```

Turning JSON back into your own types is manual with the standard library (as above). Pydantic, covered in the FastAPI course, automates it with validation.

#### JSON Lines: one record per line

For large datasets and logs, a single giant JSON array is awkward: you must read the whole thing before using any of it. **JSON Lines** (`.jsonl`) stores one JSON object per line, so you can append records and stream through them line by line. It is the standard format for LLM fine-tuning data, evaluation sets and batch API requests:

```python
dataset = base / "train.jsonl"
examples = [
    {"prompt": "Capital of Maharashtra?", "answer": "Mumbai"},
    {"prompt": "Who wrote 'Wings of Fire'?", "answer": "A. P. J. Abdul Kalam"},
]
with open(dataset, "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

with open(dataset, "a", encoding="utf-8") as f:                 # appending is trivial
    f.write(json.dumps({"prompt": "2 + 2?", "answer": "4"}) + "\n")

with open(dataset, encoding="utf-8") as f:
    for line_no, line in enumerate(f, start=1):
        record = json.loads(line)
        print(line_no, record["answer"])
```

Output:

```
1 Mumbai
2 A. P. J. Abdul Kalam
3 4
```

### 11. Other Formats in the Standard Library

- **TOML** (`tomllib`, read-only, Python 3.11+): the format of `pyproject.toml` and many app configs. Open the file in **binary** mode: `tomllib.load(open(path, "rb"))`. You'll see `pyproject.toml` in [Importing and Managing Modules](../04-modules-and-exceptions/importing-and-managing-modules.md).
- **INI files** (`configparser`): older `[section]` / `key = value` configs.
- **`pickle`**: saves almost any Python object to bytes. Convenient for caching your *own* data, but **never unpickle data from an untrusted source**: loading a pickle can run arbitrary code. Use JSON for anything that crosses a trust boundary.
- **SQLite** (`sqlite3`): a full SQL database in a single file, covered in the databases course.

```python
import tomllib

config_file = base / "app.toml"
config_file.write_text('model = "claude-opus-5-5"\n[retry]\nattempts = 3\nbackoff = 2.0\n', encoding="utf-8")
with open(config_file, "rb") as f:
    config = tomllib.load(f)
print(config)

tmp.cleanup()                       # delete the playground and everything in it
print(base.exists())
```

Output:

```
{'model': 'claude-opus-5-5', 'retry': {'attempts': 3, 'backoff': 2.0}}
False
```

---

## Try It Yourself

Each exercise uses its own temporary directory.

1. Write the lines `"Mumbai"`, `"Delhi"`, `"Chennai"` to `cities.txt` (one per line), then append `"Kolkata"`, then read the file and print the number of lines and the longest city name.
2. Write a CSV of three students (`name,marks`) with `csv.DictWriter`, read it back with `csv.DictReader`, and print the average marks rounded to 1 decimal.
3. Save `{"team": "भारत", "runs": [287, 301]}` to a JSON file *readably* (real Hindi characters, indented), then print the raw file contents.
4. Write a function `count_by_suffix(folder)` that returns a dict like `{".csv": 2, ".txt": 1}` for all files in a folder and its subfolders, sorted by suffix.

<details>
<summary>Show answers</summary>

**1.**

```python
with tempfile.TemporaryDirectory() as d:
    path = Path(d) / "cities.txt"
    with open(path, "w", encoding="utf-8") as f:
        for city in ["Mumbai", "Delhi", "Chennai"]:
            print(city, file=f)
    with open(path, "a", encoding="utf-8") as f:
        print("Kolkata", file=f)
    with open(path, encoding="utf-8") as f:
        cities = [line.strip() for line in f]
    print(len(cities), max(cities, key=len))
```

Output:

```
4 Chennai
```

**2.**

```python
with tempfile.TemporaryDirectory() as d:
    path = Path(d) / "marks.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "marks"])
        w.writeheader()
        w.writerows([{"name": "Asha", "marks": 91}, {"name": "Ravi", "marks": 78},
                     {"name": "Meera", "marks": 85}])
    with open(path, encoding="utf-8", newline="") as f:
        marks = [int(row["marks"]) for row in csv.DictReader(f)]
    print(round(sum(marks) / len(marks), 1))
```

Output:

```
84.7
```

**3.**

```python
with tempfile.TemporaryDirectory() as d:
    path = Path(d) / "score.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"team": "भारत", "runs": [287, 301]}, f, ensure_ascii=False, indent=2)
    print(path.read_text(encoding="utf-8"))
```

Output:

```
{
  "team": "भारत",
  "runs": [
    287,
    301
  ]
}
```

**4.**

```python
from collections import Counter

def count_by_suffix(folder):
    counts = Counter(p.suffix for p in Path(folder).rglob("*") if p.is_file())
    return dict(sorted(counts.items()))

with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    (root / "sub").mkdir()
    for name in ["a.csv", "b.txt", "sub/c.csv"]:
        (root / name).write_text("", encoding="utf-8")
    print(count_by_suffix(root))
```

Output:

```
{'.csv': 2, '.txt': 1}
```

</details>

---

## Real-World Examples

### Example 1: Bank statement imports

Indian banks let you download statements as CSV or Excel. A personal-finance app reads them with `csv.DictReader`, using `encoding="utf-8-sig"` to strip Excel's BOM, converts the amount strings to numbers, and categorises each UPI transaction. Most bugs in such importers are encoding and quoting bugs, exactly the ones covered here.

### Example 2: LLM datasets and batch jobs

Fine-tuning data, evaluation sets and batch API requests for model providers are JSON Lines files: one example or request per line. Your code streams through them line by line with `for line in f: json.loads(line)` so even multi-gigabyte files fit in memory.

### Example 3: Configuration

`pyproject.toml` configures Python projects, many apps keep settings in TOML or JSON, and secrets often come from `.env` files. Reading them correctly (binary mode for `tomllib`, UTF-8 for JSON) is everyday work.

---

## Common Misconceptions

### Misconception 1: "Python closes files automatically, so `with` is optional"

CPython usually closes a file when the object is garbage-collected, but not at a guaranteed moment, and other Python implementations behave differently. Until it is closed, written data may sit in a buffer and never reach the disk if the program crashes. `with` closes it at a known point, always.

### Misconception 2: "Text is just text; encoding doesn't matter"

Every text file is bytes plus an encoding. Leaving `encoding` out means "use this machine's default", which varies between computers (until Python 3.15 made UTF-8 the default). Pass it explicitly.

### Misconception 3: "CSV is just `split(',')`"

Quoted fields, embedded commas, escaped quotes and line breaks inside fields all break naive splitting. Use the `csv` module, and open the file with `newline=""`.

### Misconception 4: "`json.load` gives me back my original objects"

It gives you dicts, lists, strings, numbers, booleans and `None`. Dates come back as strings, tuples as lists, and integer dict keys as strings. Convert back yourself, or use a validation library.

---

## Interview Relevance

File handling comes up in coding rounds ("parse this log/CSV") and in Python knowledge questions. A strong answer covers:

- **Why `with`** (guaranteed close, even on exceptions) and what a context manager is.
- **Modes**, especially that `"w"` truncates immediately and `"x"` refuses to overwrite.
- **Memory-efficient reading** by iterating over the file object instead of `read()`.
- **Encodings**: bytes vs str, UTF-8, `UnicodeDecodeError`, `errors=`, the BOM.
- **`csv` and `json`** usage, including `newline=""`, `DictReader`, `ensure_ascii=False`, `default=` and JSON Lines.

Common follow-ups:

- *"How would you read a 50 GB file?"* Iterate line by line (or in fixed-size chunks for binary data); never `read()` it whole.
- *"How do you serialise a `datetime` to JSON?"* `default=` with `isoformat()`, and `fromisoformat()` when loading.
- *"`os.path` or `pathlib`?"* `pathlib` for new code: objects, `/` joining, cross-platform.

---

## Key Takeaways

- **Open files in a `with` block with an explicit `encoding="utf-8"`**; choose the mode deliberately (`"w"` erases, `"a"` appends, `"x"` refuses to overwrite, `"b"` for bytes).
- **Iterate over the file object** to read any size of file one line at a time.
- **Encoding errors come from reading bytes with the wrong rule**: know `errors=`, `utf-8-sig` for Excel files, and UTF-8 mode.
- **Use `pathlib.Path`** for building, inspecting, listing and creating paths.
- **Use `csv` (with `newline=""`) and `json`** instead of hand-written parsing; JSON Lines is the format of choice for large record sets.

---

**Up next:** [Buffered I/O and Other File Methods](buffered-i-o-and-other-file-methods.md)
