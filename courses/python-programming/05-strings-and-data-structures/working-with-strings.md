---
title: "Working with Strings"
course: Python Programming
module: "5. Strings and Data Structures"
type: Article
level: Beginner
reading_time: 45 min
---

# Working with Strings: The Complete Guide

> 📚 **Before you start**
>
> - [Numbers, Booleans and Strings](../02-getting-started-with-python/numbers-booleans-and-strings.md), for creating strings, escapes, indexing and f-string basics
> - [Containers and Mutability](../03-core-language-concepts/containers-and-mutability.md), for what "immutable" means
> - [for and while Loops](../04-control-flow/for-and-while-loops.md), for looping over characters

## Introduction

Most of the data in the world is text. Names and addresses on a delivery form. The description line on a bank statement: `UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl`. A PAN number, an IFSC code, a WhatsApp message, a product review, a log file from a server, and every prompt you'll ever send to an AI model.

That text is rarely clean. Names come in as `"  rAHUL sharma "`, phone numbers as `"+91 98765-43210"`, amounts as `"₹1,299.00"`. Before you can use it, you need to **clean** it, **search** it, **split** it into pieces and **reassemble** it into something tidy. Python's `str` type comes with around 47 built-in methods for exactly this, plus slicing and f-strings.

By the end of this lesson you'll be able to slice any part of a string, use the string methods that matter (grouped so they're easy to remember), split and join text, format output precisely, understand what Unicode means for Hindi and emoji, and write small but real text-cleaning programs.

> 💡 **Key Insight**
>
> Strings are **immutable**: no method ever changes a string in place. Every method **returns a new string**, which you must store (`name = name.strip()`). Once that's second nature, you can **chain** methods left to right, `raw.strip().lower().replace("-", "")`, each step working on the result of the one before.

---

## Core Explanation

### 1. A string is a sequence of characters

A string is an ordered, immutable sequence of **characters**. Everything you know about sequences applies: `len()`, indexing, slicing, `in`, looping.

```python
city = "Bengaluru"
print(len(city))
print(city[0], city[-1])
print("galu" in city)
for ch in city[:4]:
    print(ch, end=" ")
print()
```

Output:

```
9
B u
True
B e n g
```

### 2. Slicing in full

A slice `s[start:stop:step]` takes characters from `start` up to (not including) `stop`, jumping `step` each time. Any part can be left out:

- missing `start` means "from the beginning",
- missing `stop` means "to the end",
- missing `step` means 1.

```
  B   e   n   g   a   l   u   r   u
  0   1   2   3   4   5   6   7   8
 -9  -8  -7  -6  -5  -4  -3  -2  -1
```

```python
city = "Bengaluru"
print(city[0:4])      # first four
print(city[:4])       # same
print(city[4:])       # from index 4 to the end
print(city[-3:])      # last three
print(city[:-3])      # all but the last three
print(city[::2])      # every second character
print(city[::-1])     # reversed
print(city[1:7:2])
```

Output:

```
Beng
Beng
aluru
uru
Bengal
Bnauu
urulagneB
egl
```

Unlike indexing, slicing **never** raises an error for out-of-range positions. It just gives you what exists:

```python
print(city[5:100])
print(repr(city[20:30]))
```

Output:

```
luru
''
```

A practical example: masking a card number so only the last four digits show.

```python
card = "4111222233334444"
masked = "*" * (len(card) - 4) + card[-4:]
print(masked)
```

Output:

```
************4444
```

### 3. Immutability in practice

You can read characters but never assign to them:

```python
# not-run: shows an error on purpose
name = "rahul"
name[0] = "R"
```

Running it shows:

```
Traceback (most recent call last):
  File "/home/you/python-practice/example.py", line 3, in <module>
    name[0] = "R"
    ~~~~^^^
TypeError: 'str' object does not support item assignment
```

Build a new string instead, and rebind the name if you want:

```python
name = "rahul"
name = "R" + name[1:]
print(name)
```

Output:

```
Rahul
```

### 4. Changing case

| Method | Result for `"rAHUL sharma"` |
|---|---|
| `.upper()` | `'RAHUL SHARMA'` |
| `.lower()` | `'rahul sharma'` |
| `.title()` | `'Rahul Sharma'` |
| `.capitalize()` | `'Rahul sharma'` (only the first letter of the whole string) |
| `.swapcase()` | `'Rahul SHARMA'` |
| `.casefold()` | like `.lower()` but more thorough for some languages |

```python
raw = "rAHUL sharma"
print(raw.upper(), "|", raw.lower(), "|", raw.title(), "|", raw.capitalize())
print("Straße".lower(), "Straße".casefold())
```

Output:

```
RAHUL SHARMA | rahul sharma | Rahul Sharma | Rahul sharma
straße strasse
```

Use `.casefold()` when comparing text case-insensitively across languages; for English, `.lower()` is fine. Note that `.title()` capitalises after **any** non-letter, so `"o'brien".title()` gives `"O'Brien"` but `"don't".title()` gives `"Don'T"`.

### 5. Trimming whitespace and other characters

**Whitespace** means spaces, tabs (`\t`) and newlines (`\n`). Text from forms and files is full of stray whitespace.

```python
raw = "   Priya Nair \n"
print(repr(raw.strip()))      # both ends
print(repr(raw.lstrip()))     # left end only
print(repr(raw.rstrip()))     # right end only

price = "₹₹1,299.00--"
print(price.strip("₹-"))      # strip any of these characters from both ends
```

Output:

```
'Priya Nair'
'Priya Nair \n'
'   Priya Nair'
1,299.00
```

The argument to `strip` is a **set of characters** to remove, not a word. To remove an exact piece from the start or end, use `removeprefix` / `removesuffix`:

```python
print("Dr. Mehta".removeprefix("Dr. "))
print("report_final.pdf".removesuffix(".pdf"))
print("www.example.in".strip("w."))          # strips characters: careful!
print("www.example.in".removeprefix("www."))
```

Output:

```
Mehta
report_final
example.in
example.in
```

They agree here, but `"wow.in".strip("w.")` would give `"ow.in"`, eating the `w` that belongs to the word. Prefer `removeprefix` when you mean an exact prefix.

### 6. Searching

```python
narration = "UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl"

print(narration.startswith("UPI"))
print(narration.endswith(("@ybl", "@okaxis")))   # a tuple means "any of these"
print(narration.find("SWIGGY"))                  # index of first match
print(narration.find("ZOMATO"))                  # -1 means not found
print(narration.count("/"))
print(narration.lower().count("swiggy"))
print(narration.rfind("/"))                      # last match
```

Output:

```
True
True
20
-1
5
2
31
```

`.index()` is like `.find()` but raises an error when not found, which is better when absence means something has gone wrong:

```python
# not-run: shows an error on purpose
narration = "UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl"
position = narration.index("ZOMATO")
```

Running it shows:

```
Traceback (most recent call last):
  File "/home/you/python-practice/example.py", line 3, in <module>
    position = narration.index("ZOMATO")
ValueError: substring not found
```

For a simple yes/no, `in` is clearest: `"SWIGGY" in narration`.

### 7. Replacing

`.replace(old, new)` replaces **every** occurrence; an optional third argument limits how many:

```python
phone = "+91 98765-43210"
digits = phone.replace("+91", "").replace(" ", "").replace("-", "")
print(digits)

print("a-b-c-d".replace("-", "/", 2))
```

Output:

```
9876543210
a/b/c-d
```

### 8. Splitting and joining

`.split()` breaks a string into a **list** of pieces. With no argument it splits on any run of whitespace and ignores whitespace at the ends, which is usually what you want for words:

```python
sentence = "  the   quick brown\tfox \n"
print(sentence.split())
```

Output:

```
['the', 'quick', 'brown', 'fox']
```

With an argument, it splits on exactly that separator, keeping empty pieces:

```python
narration = "UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl"
parts = narration.split("/")
print(parts)
print("Merchant:", parts[3].title())

print("a,,b".split(","))                       # empty piece kept
print("2026-10-11".split("-", maxsplit=1))     # split only once
print("ap-south-1.log".rsplit(".", 1))         # split once from the right
```

Output:

```
['UPI', 'DR', '412345678901', 'SWIGGY', 'YESB', 'swiggy@ybl']
Merchant: Swiggy
['a', '', 'b']
['2026', '10-11']
['ap-south-1', 'log']
```

`.splitlines()` splits multi-line text into lines, and `.partition(sep)` splits once into exactly three parts (before, separator, after):

```python
text = "line one\nline two\nline three"
print(text.splitlines())

email = "priya.nair@example.co.in"
user, at, domain = email.partition("@")
print(user, "|", domain)
```

Output:

```
['line one', 'line two', 'line three']
priya.nair | example.co.in
```

**Joining** is the reverse of splitting. The syntax surprises everyone at first: you call `.join()` on the **separator**, and pass the list:

```python
words = ["chai", "samosa", "jalebi"]
print(", ".join(words))
print(" -> ".join(["NDLS", "AGC", "GWL", "BPL"]))
print("".join(["a", "b", "c"]))
```

Output:

```
chai, samosa, jalebi
NDLS -> AGC -> GWL -> BPL
abc
```

`join` needs every item to be a string. Joining numbers fails:

```python
# not-run: shows an error on purpose
print(", ".join([10, 20, 30]))
```

Running it shows:

```
Traceback (most recent call last):
  File "/home/you/python-practice/example.py", line 2, in <module>
    print(", ".join([10, 20, 30]))
          ~~~~~~~~~^^^^^^^^^^^^^^
TypeError: sequence item 0: expected str instance, int found
```

Convert them first. A small loop works (comprehensions in a later lesson make it a one-liner):

```python
amounts = [10, 20, 30]
as_text = []
for a in amounts:
    as_text.append(str(a))
print(", ".join(as_text))
```

Output:

```
10, 20, 30
```

**Why join instead of `+` in a loop?** Because strings are immutable, `result = result + piece` builds a brand-new string every time, copying everything so far. For thousands of pieces that gets slow. Collecting pieces in a list and joining once at the end is the standard, efficient approach.

### 9. Testing what a string contains

These methods return `True` or `False`, and all return `False` for an empty string:

| Method | True when every character is... | `"2026"` | `"abc"` | `"ab12"` | `" "` |
|---|---|---|---|---|---|
| `.isdigit()` | a digit | True | False | False | False |
| `.isalpha()` | a letter | False | True | False | False |
| `.isalnum()` | a letter or digit | True | True | True | False |
| `.isspace()` | whitespace | False | False | False | True |
| `.isupper()` / `.islower()` | (cased letters) upper / lower | False | False / True | False / True | False |

```python
pan = "ABCDE1234F"
print(len(pan) == 10)
print(pan[:5].isalpha() and pan[:5].isupper())
print(pan[5:9].isdigit())
print(pan[9].isalpha())
```

Output:

```
True
True
True
True
```

That's a reasonable first check of an Indian PAN format: five capital letters, four digits, one letter. (For complex patterns, Python's `re` module for **regular expressions** is the professional tool, covered in [Advanced Python Programming](../course.md).)

A subtle point: `.isdigit()` is true for some Unicode characters that `int()` can't convert, like superscript `²`. For "can I safely call `int()`?" checks on everyday input, `.isdecimal()` is the strictest:

```python
print("²".isdigit(), "²".isdecimal())
print("१२३".isdecimal(), int("१२३"))    # Devanagari digits are real decimal digits
```

Output:

```
True False
True 123
```

### 10. Aligning and padding

```python
print("[" + "Total".center(15) + "]")
print("[" + "Total".ljust(15, ".") + "]")
print("[" + "499".rjust(8) + "]")
print("42".zfill(6), "-42".zfill(6))
```

Output:

```
[     Total     ]
[Total..........]
[     499]
000042 -00042
```

f-strings can do the same alignment more compactly, as the next section shows.

### 11. Formatting in depth

You met f-strings in [Numbers, Booleans and Strings](../02-getting-started-with-python/numbers-booleans-and-strings.md). The part after the colon is the **format spec**, and it follows a pattern: `[fill][align][sign][,][width][.precision][type]`.

| Part | Examples | Meaning |
|---|---|---|
| fill + align | `<` `>` `^`, e.g. `*^10` | left, right, centre; fill with `*` |
| sign | `+` | always show the sign |
| `,` or `_` | `,` | thousands separator |
| width | `10` | minimum total width |
| `.precision` | `.2` | digits after the point (`f`) or significant digits (`g`) |
| type | `f` `d` `%` `e` `g` `x` `b` | fixed-point, integer, percent, scientific, general, hex, binary |

```python
item, qty, price = "Masala Dosa", 3, 89.5

print(f"{'Item':<15}{'Qty':>5}{'Amount':>10}")
print(f"{item:<15}{qty:>5}{qty * price:>10.2f}")
print(f"{'':-^30}")
print(f"{'TOTAL':*^30}")
print(f"{1234567.891:,.1f} | {0.256:.1%} | {12345678:e} | {255:x} | {5:b}")
```

Output:

```
Item             Qty    Amount
Masala Dosa        3    268.50
------------------------------
************TOTAL*************
1,234,567.9 | 25.6% | 1.234568e+07 | ff | 101
```

The width and precision can themselves come from variables, using nested braces:

```python
width = 12
for value in [3.14159, 2.71828]:
    print(f"[{value:>{width}.3f}]")
```

Output:

```
[       3.142]
[       2.718]
```

#### Older formatting styles

You'll meet two older styles in existing code. They do the same job:

```python
name, amount = "Priya", 1245.5
print("Hello {}, you owe ₹{:.2f}".format(name, amount))       # str.format
print("Hello %s, you owe ₹%.2f" % (name, amount))             # printf-style
print(f"Hello {name}, you owe ₹{amount:.2f}")                 # f-string: prefer this
```

Output:

```
Hello Priya, you owe ₹1245.50
Hello Priya, you owe ₹1245.50
Hello Priya, you owe ₹1245.50
```

`str.format` is still useful when the template is stored separately from the values, for example a message template loaded from a file.

### 12. Unicode: Hindi, Tamil and emoji

Python strings are **Unicode**: every character from every writing system has a number called its **code point**. `ord()` gives the number and `chr()` turns a number back into a character:

```python
print(ord("A"), ord("₹"), ord("अ"))
print(chr(8377), chr(2309))
```

Output:

```
65 8377 2309
₹ अ
```

What counts as one "character" in Python is one code point, which isn't always one visible letter. Many Indian scripts combine a consonant with vowel signs and a *virama* (्), each of which is its own code point:

```python
greeting = "नमस्ते"
print(len(greeting))
print(list(greeting))
```

Output:

```
6
['न', 'म', 'स', '्', 'त', 'े']
```

You see four visible syllables, but Python counts six code points. So reversing or slicing Hindi text by position can split a syllable in half. For most tasks (searching, replacing, splitting on spaces) this doesn't matter; for character counting in Indian languages, be aware of it.

To store text in a file or send it over a network, it's **encoded** into **bytes**. The universal standard is **UTF-8**, where English letters take 1 byte and other characters take 2 to 4:

```python
print("chai".encode("utf-8"))
print(len("chai".encode("utf-8")), len("चाय".encode("utf-8")))
data = "₹500".encode("utf-8")
print(data)
print(data.decode("utf-8"))
```

Output:

```
b'chai'
4 9
b'\xe2\x82\xb9500'
₹500
```

A `b'...'` value is a `bytes` object. `.decode()` turns bytes back into a string. You'll use this when reading files in [Advanced Python Programming](../course.md#m8).

### 13. Comparing and sorting strings

Strings compare by code point, so uppercase letters sort before lowercase ones. For human-friendly sorting, sort by a lowercased version using `key=`:

```python
names = ["meera", "Arjun", "zoya", "Bhavna"]
print(sorted(names))
print(sorted(names, key=str.lower))
print(sorted(names, key=len))
```

Output:

```
['Arjun', 'Bhavna', 'meera', 'zoya']
['Arjun', 'Bhavna', 'meera', 'zoya']
['zoya', 'meera', 'Arjun', 'Bhavna']
```

Here the first two agree by luck; add `"aditi"` and the plain sort would put it after `"Bhavna"`. `key=` takes a function that's applied to each item before comparing. You'll learn more in [Lambda, map and Functional Style](../06-functions-and-iterators/lambda-map-and-functional-style.md).

### 14. Putting it together: cleaning a messy record

```python
raw = "  rAHUL   sharma | +91 98765-43210 |  PUNE , maharashtra "

name_part, phone_part, place_part = raw.split("|")

name = " ".join(name_part.split()).title()          # collapse inner spaces too
phone = phone_part.strip().removeprefix("+91").replace(" ", "").replace("-", "")
city, state = place_part.split(",")
city, state = city.strip().title(), state.strip().title()

print(f"Name : {name}")
print(f"Phone: {phone[:5]} {phone[5:]}")
print(f"Place: {city}, {state}")
print(f"Valid phone: {len(phone) == 10 and phone.isdigit() and phone[0] in '6789'}")
```

Output:

```
Name : Rahul Sharma
Phone: 98765 43210
Place: Pune, Maharashtra
Valid phone: True
```

`" ".join(text.split())` is a handy idiom: split on any whitespace, then rejoin with single spaces, which collapses runs of spaces.

### 15. Common errors with strings

**Calling a list method on a string:**

```python
# not-run: shows an error on purpose
name = "Priya"
name.append(" Nair")
```

Running it shows:

```
Traceback (most recent call last):
  File "/home/you/python-practice/example.py", line 3, in <module>
    name.append(" Nair")
    ^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'append'
```

An `AttributeError` means "this type of object has no method (or attribute) with that name". Strings are joined with `+` or f-strings, not appended to.

**Forgetting to keep the result:** `name.strip()` on its own line does nothing visible, because the new string is thrown away. Write `name = name.strip()`.

**Forgetting the brackets on a method:**

```python
# not-run: the printed memory address changes on every run
name = "priya"
print(name.upper)
print(name.upper())
```

Running it shows:

```
<built-in method upper of str object at 0x7f6b81e6fc30>
PRIYA
```

Without `()` you get the method itself, not its result. The hexadecimal number after `at` is a memory address, and it will be different on your computer.

---

## Try It Yourself

1. Given `email = "  Kavya.Iyer@Example.COM "`, produce a cleaned lowercase email and print just the part before `@`.
2. Count the vowels in `"Incredible India"` (case-insensitively) with a loop.
3. Check whether a word is a **palindrome** (reads the same backwards), ignoring case: test `"Malayalam"` and `"Kerala"`.
4. Turn `"2026-10-11"` into `"11/10/2026"` using `split` and `join`.
5. Format this receipt line so the item name takes 20 characters (left-aligned) and the price takes 10 characters with 2 decimals (right-aligned): item `"Paneer Tikka"`, price `249`.

<details>
<summary>Show answers</summary>

```python
email = "  Kavya.Iyer@Example.COM "
clean = email.strip().lower()
print(clean, "|", clean.split("@")[0])

vowels = 0
for ch in "Incredible India".lower():
    if ch in "aeiou":
        vowels += 1
print("Vowels:", vowels)

for word in ["Malayalam", "Kerala"]:
    w = word.lower()
    print(word, w == w[::-1])

print("/".join(reversed("2026-10-11".split("-"))))

print(f"[{'Paneer Tikka':<20}{249:>10.2f}]")
```

Output:

```
kavya.iyer@example.com | kavya.iyer
Vowels: 7
Malayalam True
Kerala False
11/10/2026
[Paneer Tikka            249.00]
```

</details>

---

## Real-World Examples

### Example 1: Categorising bank transactions

A budgeting app reads narrations like `UPI/DR/.../SWIGGY/...` and `NEFT/HDFC/RENT OCT`. It uppercases each narration, checks `if "SWIGGY" in n or "ZOMATO" in n:` for food, `"IRCTC"` for travel, `"RENT"` for housing, and so on. Simple string methods correctly categorise most transactions with no machine learning at all.

### Example 2: Preparing text for AI models

Before sending documents to an LLM or a search index, pipelines clean them: strip whitespace, collapse repeated spaces, remove page headers with `removeprefix`, split into paragraphs with `split("\n\n")`, and join chunks back with separators. Prompt templates are just f-strings or `str.format` templates with placeholders.

### Example 3: Log analysis

A server log line like `2026-10-11 09:14:03 ERROR payment-service Timeout after 30s` is parsed with `line.split(maxsplit=4)` into date, time, level, service and message. Counting lines where `level == "ERROR"` per service is the first step of most incident investigations. You'll build exactly this kind of tool in the [Log file analyser lab](../course.md#m8).

---

## Common Misconceptions

### Misconception 1: "`s.upper()` changes `s`"

Strings are immutable. It returns a new string; `s` is unchanged unless you write `s = s.upper()`.

### Misconception 2: "`strip("abc")` removes the word abc"

It removes any of the characters `a`, `b`, `c` from both ends, in any order and quantity. Use `removeprefix`/`removesuffix` for exact text.

### Misconception 3: "`split(" ")` and `split()` are the same"

`split()` splits on any run of whitespace and drops empty pieces. `split(" ")` splits on each single space and keeps empty pieces: `"a  b".split(" ")` is `['a', '', 'b']`.

### Misconception 4: "`len()` counts visible letters"

It counts Unicode code points. For scripts with combining marks (Devanagari, Tamil and many others) and for some emoji, that's more than the number of visible symbols.

### Misconception 5: "Joining with `+` in a loop is fine"

For a few pieces, yes. For thousands, it's slow because each `+` copies the whole string. Collect pieces in a list and `"".join(pieces)` once.

---

## Interview Relevance

String manipulation is the most common topic in coding rounds. Expect:

- **Classic problems:** reverse a string (`s[::-1]`), palindrome check, anagram check (`sorted(a) == sorted(b)`), count characters or words, first non-repeating character, capitalise each word, compress `"aaabb"` to `"a3b2"`.
- **Immutability questions:** why `s[0] = "x"` fails, and why `join` beats `+=` in a loop (quadratic copying).
- **Method knowledge:** `find` vs `index`, `split()` vs `split(" ")`, `strip` semantics, `partition`.
- **Slicing fluency:** negative indexes, steps, out-of-range behaviour.
- **Unicode awareness:** code points vs bytes vs visible characters, and UTF-8 encoding/decoding.

---

## Key Takeaways

- Strings are **immutable sequences of Unicode characters**: index, slice (`[start:stop:step]`), loop, and use `in`, but never assign to a position.
- Every method **returns a new string**. Group them in your head: **case** (`lower`, `title`), **trim** (`strip`, `removeprefix`), **search** (`find`, `startswith`, `count`), **replace**, **split/join**, **test** (`isdigit`, `isalpha`), **align** (`center`, `zfill`).
- **`split()` and `"sep".join(list)`** are a pair; joining needs strings.
- **f-string format specs** handle alignment, width, decimals, separators and percentages: `f"{x:>10,.2f}"`.
- **Unicode** means `len` counts code points; **UTF-8** turns text into bytes and back.

---

**Up next:** [Lists and Tuples](lists-and-tuples.md)
