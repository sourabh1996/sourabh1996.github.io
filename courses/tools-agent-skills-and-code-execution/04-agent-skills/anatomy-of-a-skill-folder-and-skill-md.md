---
title: "Anatomy of a Skill Folder and SKILL.md"
course: "Tools, Agent Skills and Code Execution"
module: "4. Agent Skills"
type: Article
level: Intermediate
reading_time: 34 min
---

# Anatomy of a Skill Folder and SKILL.md: The Complete Guide

> 📚 **Before you start**
>
> - [What is an Agent Skill?](what-is-an-agent-skill.md), for what a skill is and the three levels of loading.
> - [Naming, Descriptions and Parameters](../02-writing-tools-for-agents/naming-descriptions-and-parameters.md): a skill's description does the same job as a tool's, and the same rules apply.

## Introduction

A recipe card from your grandmother has a shape you recognise instantly: the dish's name at the top, a line on when to make it ("for Sankranti"), the ingredients, the steps, and maybe a note stapled to the back. Anyone in the family can pick up any card and use it, because they all follow the same shape.

`SKILL.md` gives agent know-how that kind of shape. In this lesson we'll build a complete, production-style skill for MandiMart's finance team, **`gst-invoice`**, which prepares GST tax invoices with the right CGST, SGST or IGST split. Along the way you'll learn every part of the format:

- the folder layout: `SKILL.md`, `scripts/`, `references/`, `assets/`;
- the frontmatter fields defined by the open specification, with their exact rules;
- optional fields that individual products add, like Claude Code's `allowed-tools` and `disable-model-invocation`;
- how to write the instructions body and point to bundled files;
- where each agent looks for skills on disk;
- and a Python validator that checks a skill against the spec, like the official `skills-ref validate` command.

> 💡 **Key Insight**
>
> The format is deliberately tiny: **a folder whose name matches the `name` field, a `SKILL.md` with a `name` and a `description`, and Markdown instructions**. Everything else is optional. That small core is what lets the same skill work across Claude Code, Codex, Gemini CLI, Copilot and the Claude API.

---

## Core Explanation

### 1. The folder

```
gst-invoice/
├── SKILL.md                     # required: frontmatter + instructions
├── scripts/
│   └── gst_calc.py              # code the agent runs (it reads the output, not the source)
├── references/
│   └── gst-rates.md             # detail the agent reads only if needed
└── assets/
    └── invoice-template.md      # a template the agent fills in
```

| Part | Required? | What it's for | Loaded when |
|---|---|---|---|
| `SKILL.md` | Yes | Metadata and instructions | Frontmatter always; body when the skill is activated |
| `scripts/` | No | Executable code: deterministic calculations, validations, file conversions | Run when a step says so |
| `references/` | No | Longer documentation: rate tables, policies, API notes | Read when a step needs it |
| `assets/` | No | Templates, sample files, images, schemas | Used when producing output |

The specification recommends keeping file references **one level deep** from `SKILL.md` (`references/gst-rates.md`, not a chain of files that link to more files), so the agent can find everything from the instructions directly.

### 2. The SKILL.md

Here's the complete file:

```markdown
---
name: gst-invoice
description: Prepares GST tax invoices for MandiMart orders, working out CGST and SGST for sales within a state or IGST across states, using current item rates. Use when someone asks for a GST invoice, tax invoice, B2B bill, or the GST breakup of an order.
license: Proprietary. Internal use at MandiMart only.
compatibility: Needs Python 3.10+ to run scripts/gst_calc.py. No network access required.
metadata:
  owner: finance-ops
  version: "1.3"
---

# GST invoice

## Before you start
- You need: the order ID, the buyer's name, address and GSTIN (for B2B), and the buyer's state.
- MandiMart's Pune entity is registered in Maharashtra (state code 27). Bengaluru stores bill
  from Karnataka (state code 29).

## Steps
1. Get the order's items (name, category, quantity, unit price before tax).
2. Map each item to a category in `references/gst-rates.md`. If an item doesn't fit any
   category, stop and ask finance; never guess a rate.
3. Save the items as JSON and run:
   `python scripts/gst_calc.py --items items.json --seller-state 27 --buyer-state <code>`
   Same state codes mean CGST + SGST; different codes mean IGST. The script decides this.
4. Fill in `assets/invoice-template.md` with the script's output. Do not recalculate any numbers.
5. Show the invoice to the user for review. Never send it to the customer yourself.

## Rules
- Amounts are in rupees with two decimals. Round each line, not just the total.
- A B2B invoice must show the buyer's GSTIN. Check it has 15 characters and starts with the
  buyer's state code.
- If the script prints an error, show it to the user and stop.
```

Let's go through it part by part.

### 3. The frontmatter fields

The frontmatter is YAML between two `---` lines at the very top of the file. The open specification defines six fields:

| Field | Required | Rules |
|---|---|---|
| `name` | Yes | 1 to 64 characters; lowercase letters, digits and hyphens only; can't start or end with a hyphen or contain `--`; **must match the folder name** |
| `description` | Yes | 1 to 1,024 characters; says **what the skill does and when to use it** |
| `license` | No | A licence name or a pointer to a bundled licence file |
| `compatibility` | No | Up to 500 characters on environment needs: products, system packages, network access |
| `metadata` | No | A map of string keys to string values for anything else (owner, version) |
| `allowed-tools` | No, experimental | Space-separated tools the skill may use without asking, e.g. `Bash(python:*) Read` |

The **description is the most important line in the whole skill**. It's the only part the agent sees before deciding to use the skill, so it has to say both what the skill does and the situations (in the user's words) where it applies. Ours names the outcome ("GST tax invoices... CGST and SGST... IGST") and the triggers ("GST invoice, tax invoice, B2B bill, GST breakup"). A later lesson is devoted to testing and tuning descriptions.

Notice `version: "1.3"` is quoted: `metadata` values must be strings, and unquoted `1.3` would be a number in YAML.

### 4. Fields that products add

Products extend the frontmatter with their own optional fields. Other products ignore fields they don't recognise, so adding them doesn't break portability. Some common ones:

| Field | Supported by | Effect |
|---|---|---|
| `disable-model-invocation: true` | Claude Code, VS Code | The agent never loads the skill by itself; only the user can, by typing `/gst-invoice` |
| `user-invocable: false` | Claude Code, VS Code | Hidden from the `/` menu; only the agent loads it, as background knowledge |
| `argument-hint` | Claude Code, VS Code | Hint shown when the user types the slash command, e.g. `[order-id]` |
| `allowed-tools` | Claude Code (and the spec, experimental) | Tools usable without a permission prompt while the skill is active |
| `context: fork` | Claude Code, VS Code | Runs the skill in a separate subagent with its own context |
| `model`, `effort` | Claude Code | Model and reasoning effort to use while the skill runs |
| `paths` | Claude Code | Only offer the skill when working with matching files |

Codex keeps its extras out of `SKILL.md` altogether, in an optional `agents/openai.yaml` file (for example `allow_implicit_invocation: false` to make a skill explicit-only). For a skill that moves money or sends messages, making it user-invoked only (`disable-model-invocation: true` in Claude Code, `allow_implicit_invocation: false` in Codex) is a sensible default.

Claude Code also lets the body use **substitutions**: `$ARGUMENTS` for whatever the user typed after `/gst-invoice`, and `${CLAUDE_SKILL_DIR}` for the skill's own folder. They're handy, but they're Claude Code features: other agents will see the literal text.

### 5. The body: instructions that work

The body is plain Markdown with no required structure, but a few habits make skills reliable:

- **Say when it applies and what's needed first** ("Before you start"), so the agent gathers inputs before acting.
- **Numbered steps** for procedures, with the exact command to run. Agents follow concrete commands far more reliably than descriptions of what a command should do.
- **Push exact work into scripts.** Tax arithmetic, date maths and file formats belong in `gst_calc.py`, and the instructions say "do not recalculate". The model handles judgement (which category is this item?); code handles calculation.
- **Say what not to do** and when to stop: "never guess a rate", "never send it to the customer yourself".
- **Point to files by relative path** (`references/gst-rates.md`) and say *when* to read them.
- **Keep it short.** The specification recommends keeping `SKILL.md` under 500 lines and the instructions under about 5,000 tokens. Move detail into `references/`.

### 6. Build the whole skill on disk

Let's create the folder for real. First the reference file and the template:

```python
import json, os, subprocess, sys, tempfile, textwrap

ROOT = tempfile.mkdtemp()
SKILL_DIR = os.path.join(ROOT, "gst-invoice")
for sub in ["scripts", "references", "assets"]:
    os.makedirs(os.path.join(SKILL_DIR, sub))

def write(rel_path, text):
    with open(os.path.join(SKILL_DIR, rel_path), "w") as f:
        f.write(textwrap.dedent(text).lstrip())

write("references/gst-rates.md", """
    # GST rates for MandiMart categories

    Rates from 22 September 2025 (GST 2.0). Check with finance before adding a category.

    | Category | Examples | GST % |
    |---|---|---|
    | fresh_vegetables | onion, tomato, potato | 0 |
    | uht_milk | Amul Taaza UHT 1L | 0 |
    | paneer | paneer 200g | 0 |
    | roti_paratha | frozen paratha | 0 |
    | butter | Amul Butter 100g | 5 |
    | ghee | cow ghee 1L | 5 |
    | cheese | cheese slices | 5 |
    | biscuits | Parle-G 800g | 5 |
    | namkeen | bhujia 400g | 5 |
    | soap / shampoo / toothpaste | bath soap, shampoo 340ml | 5 |
    | aerated_drinks | cola 750ml | 40 |
    """)

write("assets/invoice-template.md", """
    # TAX INVOICE
    **MandiMart Retail Pvt Ltd** · GSTIN {seller_gstin} · {seller_address}
    Invoice no: {invoice_no}   Date: {date}   Order: {order_id}
    Bill to: {buyer_name}, {buyer_address} · GSTIN {buyer_gstin}
    Supply: {supply}

    {lines_table}

    Taxable value: Rs {taxable} | CGST: Rs {cgst} | SGST: Rs {sgst} | IGST: Rs {igst}
    **Total: Rs {grand_total}**
    """)
print(sorted(os.listdir(SKILL_DIR)))
```

Output:

```
['assets', 'references', 'scripts']
```

Next the script. It follows the habits for agent-facing scripts that the specification's guide recommends: arguments instead of interactive prompts, a `--help`, JSON on standard output, clear errors on standard error, and a non-zero exit code on failure. It uses `Decimal` so rupee amounts round exactly.

```python
GST_CALC = r'''#!/usr/bin/env python3
"""Calculate GST for a MandiMart invoice. Reads items as JSON, prints the invoice totals as JSON.

Usage: python gst_calc.py --items items.json --seller-state 27 --buyer-state 29
"""
import argparse, json, sys
from decimal import Decimal, ROUND_HALF_UP

RATES = {  # category -> GST %, rates effective 22 Sep 2025 (see references/gst-rates.md)
    "fresh_vegetables": 0, "uht_milk": 0, "paneer": 0, "roti_paratha": 0,
    "butter": 5, "ghee": 5, "cheese": 5, "biscuits": 5, "namkeen": 5,
    "soap": 5, "shampoo": 5, "toothpaste": 5,
    "aerated_drinks": 40,
}
PAISE = Decimal("0.01")

def money(x):
    return Decimal(x).quantize(PAISE, rounding=ROUND_HALF_UP)

def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--items", required=True, help="JSON file: list of {name, category, qty, unit_price}")
    p.add_argument("--seller-state", required=True, help="2-digit GST state code of the seller, e.g. 27")
    p.add_argument("--buyer-state", required=True, help="2-digit GST state code of the buyer, e.g. 29")
    a = p.parse_args()

    items = json.load(open(a.items))
    intra = a.seller_state == a.buyer_state
    lines = []
    totals = {"taxable": Decimal(0), "cgst": Decimal(0), "sgst": Decimal(0), "igst": Decimal(0)}
    for it in items:
        if it["category"] not in RATES:
            print(f"error: unknown category '{it['category']}'. Known: {', '.join(sorted(RATES))}. "
                  "Check references/gst-rates.md or ask finance.", file=sys.stderr)
            sys.exit(2)
        rate = Decimal(RATES[it["category"]])
        taxable = money(Decimal(str(it["unit_price"])) * it["qty"])
        tax = money(taxable * rate / 100)
        line = {"name": it["name"], "qty": it["qty"], "rate_pct": int(rate), "taxable": str(taxable)}
        if intra:
            half = money(tax / 2)
            line.update(cgst=str(half), sgst=str(half))
            totals["cgst"] += half
            totals["sgst"] += half
        else:
            line.update(igst=str(tax))
            totals["igst"] += tax
        totals["taxable"] += taxable
        lines.append(line)
    print(json.dumps({"supply": "intra-state" if intra else "inter-state", "lines": lines,
                      "totals": {k: str(v) for k, v in totals.items()},
                      "grand_total": str(sum(totals.values()))}, indent=1))

if __name__ == "__main__":
    main()
'''
with open(os.path.join(SKILL_DIR, "scripts", "gst_calc.py"), "w") as f:
    f.write(GST_CALC)

help_text = subprocess.run([sys.executable, os.path.join(SKILL_DIR, "scripts", "gst_calc.py"), "--help"],
                           capture_output=True, text=True).stdout
print(help_text)
```

Output:

```
usage: gst_calc.py [-h] --items ITEMS --seller-state SELLER_STATE
                   --buyer-state BUYER_STATE

Calculate GST for a MandiMart invoice. Reads items as JSON, prints the invoice
totals as JSON.

options:
  -h, --help            show this help message and exit
  --items ITEMS         JSON file: list of {name, category, qty, unit_price}
  --seller-state SELLER_STATE
                        2-digit GST state code of the seller, e.g. 27
  --buyer-state BUYER_STATE
                        2-digit GST state code of the buyer, e.g. 29
```

That `--help` output is what an agent sees if it's unsure how to call the script. Now the `SKILL.md` itself, exactly as shown in section 2:

```python
SKILL_MD = """---
name: gst-invoice
description: Prepares GST tax invoices for MandiMart orders, working out CGST and SGST for sales within a state or IGST across states, using current item rates. Use when someone asks for a GST invoice, tax invoice, B2B bill, or the GST breakup of an order.
license: Proprietary. Internal use at MandiMart only.
compatibility: Needs Python 3.10+ to run scripts/gst_calc.py. No network access required.
metadata:
  owner: finance-ops
  version: "1.3"
---

# GST invoice

## Before you start
- You need: the order ID, the buyer's name, address and GSTIN (for B2B), and the buyer's state.
- MandiMart's Pune entity is registered in Maharashtra (state code 27). Bengaluru stores bill
  from Karnataka (state code 29).

## Steps
1. Get the order's items (name, category, quantity, unit price before tax).
2. Map each item to a category in `references/gst-rates.md`. If an item doesn't fit any
   category, stop and ask finance; never guess a rate.
3. Save the items as JSON and run:
   `python scripts/gst_calc.py --items items.json --seller-state 27 --buyer-state <code>`
   Same state codes mean CGST + SGST; different codes mean IGST. The script decides this.
4. Fill in `assets/invoice-template.md` with the script's output. Do not recalculate any numbers.
5. Show the invoice to the user for review. Never send it to the customer yourself.

## Rules
- Amounts are in rupees with two decimals. Round each line, not just the total.
- A B2B invoice must show the buyer's GSTIN. Check it has 15 characters and starts with the
  buyer's state code.
- If the script prints an error, show it to the user and stop.
"""
with open(os.path.join(SKILL_DIR, "SKILL.md"), "w") as f:
    f.write(SKILL_MD)

for dirpath, dirs, files in os.walk(SKILL_DIR):
    dirs.sort()
    depth = dirpath[len(ROOT):].count(os.sep) - 1
    print("    " * depth + os.path.basename(dirpath) + "/")
    for name in sorted(files):
        print("    " * (depth + 1) + name)
```

Output:

```
gst-invoice/
    SKILL.md
    assets/
        invoice-template.md
    references/
        gst-rates.md
    scripts/
        gst_calc.py
```

### 7. Run it the way an agent would

When an agent follows step 3 for a B2B order from the Kothrud store to a café in Bengaluru, it writes the items file and runs the script:

```python
items = [
    {"name": "Amul Butter 500g", "category": "butter", "qty": 10, "unit_price": 271.43},
    {"name": "Paneer 1kg", "category": "paneer", "qty": 4, "unit_price": 420},
    {"name": "Cola 750ml", "category": "aerated_drinks", "qty": 24, "unit_price": 28.57},
]
items_path = os.path.join(ROOT, "items.json")
with open(items_path, "w") as f:
    json.dump(items, f)

def run_gst(seller, buyer, path=items_path):
    return subprocess.run([sys.executable, os.path.join(SKILL_DIR, "scripts", "gst_calc.py"),
                           "--items", path, "--seller-state", seller, "--buyer-state", buyer],
                          capture_output=True, text=True)

inter = json.loads(run_gst("27", "29").stdout)       # Maharashtra -> Karnataka
intra = json.loads(run_gst("27", "27").stdout)       # within Maharashtra
print(inter["supply"], inter["totals"], "grand", inter["grand_total"])
print(intra["supply"], intra["totals"], "grand", intra["grand_total"])
```

Output:

```
inter-state {'taxable': '5079.98', 'cgst': '0', 'sgst': '0', 'igst': '409.99'} grand 5489.97
intra-state {'taxable': '5079.98', 'cgst': '205.00', 'sgst': '205.00', 'igst': '0'} grand 5489.98
```

Same items, same tax, different split: across states the whole tax is IGST; within Maharashtra it's split equally into CGST and SGST. Look closely and the totals differ by one paisa: the cola line's IGST is Rs 274.27, but within the state each half (Rs 137.135) is rounded on its own to Rs 137.14, as the rules require, so CGST plus SGST comes to Rs 274.28. That's exactly the kind of detail a model doing mental arithmetic would get inconsistent, and a script gets the same way every time. The model never did arithmetic; it only chose categories and state codes.

And when a category is unknown, the script fails clearly and tells the agent what to do next, following the instruction "If the script prints an error, show it to the user and stop":

```python
bad_path = os.path.join(ROOT, "bad.json")
with open(bad_path, "w") as f:
    json.dump([{"name": "Dark chocolate 100g", "category": "chocolate", "qty": 2, "unit_price": 150}], f)
r = run_gst("27", "27", bad_path)
print("exit code:", r.returncode)
print(r.stderr.strip())
```

Output:

```
exit code: 2
error: unknown category 'chocolate'. Known: aerated_drinks, biscuits, butter, cheese, fresh_vegetables, ghee, namkeen, paneer, roti_paratha, shampoo, soap, toothpaste, uht_milk. Check references/gst-rates.md or ask finance.
```

### 8. A validator for the specification

The reference library offers `skills-ref validate ./gst-invoice`. Let's write our own small version, which also shows exactly what the spec requires. It parses the frontmatter (simple `key: value` lines plus one nested map for `metadata`) and checks each rule:

```python
import re

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KNOWN = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

def parse_frontmatter(text):
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with '---' frontmatter")
    front, _, body = text[4:].partition("\n---\n")
    meta, current = {}, None
    for line in front.splitlines():
        if not line.strip():
            continue
        if line.startswith((" ", "\t")) and current:          # nested map entry, e.g. under metadata:
            k, _, v = line.strip().partition(":")
            meta[current][k.strip()] = v.strip().strip('"')
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if v == "":
            meta[k], current = {}, k
        else:
            meta[k], current = v.strip('"'), None
    return meta, body

def validate_skill(skill_dir):
    problems = []
    path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(path):
        return ["missing SKILL.md"]
    text = open(path).read()
    meta, body = parse_frontmatter(text)
    name, desc = meta.get("name", ""), meta.get("description", "")
    if not name:
        problems.append("name is required")
    elif len(name) > 64 or not NAME_RE.match(name):
        problems.append(f"name '{name}' must be 1-64 chars of a-z, 0-9 and single hyphens")
    if name and name != os.path.basename(os.path.normpath(skill_dir)):
        problems.append(f"name '{name}' must match the folder name '{os.path.basename(skill_dir)}'")
    if not desc:
        problems.append("description is required")
    elif len(desc) > 1024:
        problems.append(f"description is {len(desc)} chars; the limit is 1024")
    if len(meta.get("compatibility", "")) > 500:
        problems.append("compatibility must be at most 500 chars")
    if "metadata" in meta and not isinstance(meta["metadata"], dict):
        problems.append("metadata must be a map of strings")
    for key in sorted(set(meta) - KNOWN):
        problems.append(f"warning: '{key}' is not in the open spec (fine for a specific product)")
    if len(text.splitlines()) > 500:
        problems.append("warning: SKILL.md is over 500 lines; move detail into references/")
    for ref in re.findall(r"`((?:scripts|references|assets)/[^`\s]+)`", body):
        if not os.path.exists(os.path.join(skill_dir, ref)):
            problems.append(f"body mentions {ref}, which doesn't exist")
    return problems

print(validate_skill(SKILL_DIR) or "gst-invoice: valid")
```

Output:

```
gst-invoice: valid
```

Now break it in the ways people actually do:

```python
import shutil

def try_variant(label, folder, frontmatter_edit, body_edit=None):
    """Copy the skill into ROOT/label/folder, edit its SKILL.md, and validate the copy."""
    d = os.path.join(ROOT, label, folder)
    shutil.copytree(SKILL_DIR, d)
    text = SKILL_MD.replace(*frontmatter_edit)
    if body_edit:
        text = text.replace(*body_edit)
    with open(os.path.join(d, "SKILL.md"), "w") as f:
        f.write(text)
    return validate_skill(d)

print(try_variant("a", "GST_Invoice", ("name: gst-invoice", "name: GST_Invoice")))
print(try_variant("b", "gst-invoices", ("name: gst-invoice", "name: gst-invoice")))
print(try_variant("c", "gst-invoice", ("name: gst-invoice", "name: gst-invoice\nauthor: kavya"),
                  ("references/gst-rates.md", "references/rates.md")))
```

Output:

```
["name 'GST_Invoice' must be 1-64 chars of a-z, 0-9 and single hyphens"]
["name 'gst-invoice' must match the folder name 'gst-invoices'"]
["warning: 'author' is not in the open spec (fine for a specific product)", "body mentions references/rates.md, which doesn't exist"]
```

Three classic mistakes: capitals and underscores in the name, a folder renamed without updating `name`, and a body that points to a file that doesn't exist (plus a non-standard field, which is only a warning). Run a validator like this in CI for every skill in your repository.

### 9. Where agents look for skills

The folder format is shared; the place you put it differs by product. As of October 2026:

| Agent | Project skills (in the repo) | Personal skills (your machine) |
|---|---|---|
| **Claude Code** | `.claude/skills/<name>/` (also nested folders in a monorepo) | `~/.claude/skills/<name>/`; plus plugins and enterprise-managed skills |
| **OpenAI Codex** | `.agents/skills/` in the current folder and every parent up to the repo root | `~/.agents/skills/`; admin skills in `/etc/codex/skills` |
| **Gemini CLI** | `.gemini/skills/` or `.agents/skills/` | `~/.gemini/skills/` or `~/.agents/skills/` |
| **VS Code / GitHub Copilot** | `.github/skills/`, `.claude/skills/` or `.agents/skills/` | `~/.copilot/skills/`, `~/.claude/skills/` or `~/.agents/skills/` |
| **Claude API** | Uploaded through the Skills API and attached to requests | (workspace-wide once uploaded) |

`.agents/skills/` has become the closest thing to a shared location; Codex, Gemini CLI and VS Code all read it. Claude Code reads `.claude/skills/`, so teams that use several agents commonly keep skills in `.agents/skills/` and add a symbolic link from `.claude/skills/<name>` to it (the lab at the end of this module does exactly this). When the same skill name exists at several levels, products apply a precedence order: for example, Claude Code prefers enterprise over personal over project skills, while Gemini CLI prefers workspace skills.

---

## Try It Yourself

1. **Add a category.** Add `chocolate` to the rates table (as an assumption for this exercise, use 5%) in both `references/gst-rates.md` and the script's `RATES`, then rerun the bad order. What does it print now? Why must both files change together?
2. **Check a GSTIN.** The instructions ask the agent to check a GSTIN's length and state code. Write a small function `gstin_ok(gstin, state_code)` that returns True for `"29ABCDE1234F1Z5"` with `"29"` and False for `"27ABCDE1234F1Z5"` with `"29"`. Where in the skill would you put it, and why?
3. **Validate a description that's too long.** Use `try_variant` to give the skill a 1,100-character description. What does the validator say?

<details>
<summary>Show answers</summary>

**1.**

```python
script_path = os.path.join(SKILL_DIR, "scripts", "gst_calc.py")
src = open(script_path).read().replace('"aerated_drinks": 40,', '"aerated_drinks": 40, "chocolate": 5,')
open(script_path, "w").write(src)
ref_path = os.path.join(SKILL_DIR, "references", "gst-rates.md")
open(ref_path, "a").write("| chocolate | dark chocolate 100g | 5 |\n")
print(json.loads(run_gst("27", "27", bad_path).stdout)["totals"])
```

Output:

```
{'taxable': '300.00', 'cgst': '7.50', 'sgst': '7.50', 'igst': '0'}
```

The reference is what the agent reads to choose a category; the script is what calculates. If they disagree, the agent could pick a category the script rejects, or worse, a rate table and a calculation that silently differ. A good improvement is to have the script load its rates from one data file that the reference also documents.

**2.**

```python
def gstin_ok(gstin, state_code):
    return len(gstin) == 15 and gstin[:2] == state_code and gstin.isalnum() and gstin.isupper()

print(gstin_ok("29ABCDE1234F1Z5", "29"), gstin_ok("27ABCDE1234F1Z5", "29"))
```

Output:

```
True False
```

Put it in `scripts/` (for example `scripts/check_gstin.py`) and have step 3 run it. Format checks are exact rules, which code gets right every time and a model only usually.

**3.**

```python
long_desc = "Prepares GST tax invoices. " * 41
print(len(long_desc.strip()))
print(try_variant("d", "gst-invoice", (SKILL_MD.split("\n")[2], "description: " + long_desc.strip())))
```

Output:

```
1106
['description is 1106 chars; the limit is 1024']
```

Over 1,024 characters is invalid under the spec. Long descriptions also cost tokens in every conversation; Claude Code, for example, truncates a skill's description text in its listing beyond 1,536 characters.

</details>

---

## Real-World Examples

- **Anthropic's `pdf`, `docx`, `xlsx` and `pptx` skills** follow exactly this shape: a `SKILL.md` that routes to the right procedure, Python scripts that do the file work, and reference files for advanced cases.
- **Codex repositories** check skills into `.agents/skills/` so every developer and CI agent gets the same procedures, with `agents/openai.yaml` marking risky skills as explicit-only.
- **Finance and compliance teams** package calculation-heavy procedures (tax, payroll, reconciliation) as skills with scripts, so the model handles judgement while code handles numbers.
- **The `skills-ref` reference library** is used in CI pipelines to validate skills before they're published to a team repository or plugin marketplace.

---

## Common Misconceptions

### "The folder name doesn't matter"

The spec requires `name` to match the folder name, and several products use the folder name for slash commands and lookups. Rename both together.

### "Put everything in SKILL.md so the agent can't miss it"

The body is loaded in full on activation. Long tables and rarely-needed detail belong in `references/`, read only when a step needs them.

### "Scripts are just examples for the model to read"

Scripts are meant to be *run*. The agent reads their output (and `--help` if needed), not their source, which saves tokens and gives exact results.

### "Product-specific fields break other agents"

Unknown frontmatter fields are ignored by other products. Just don't rely on them for safety in agents that don't support them.

---

## Interview Relevance

*"Walk me through the structure of an Agent Skill."* A folder named like the skill, containing `SKILL.md` with YAML frontmatter (`name`: lowercase, hyphens, 1 to 64 characters, matching the folder; `description`: up to 1,024 characters, what and when; optional `license`, `compatibility`, `metadata`, experimental `allowed-tools`) and a Markdown body of instructions, plus optional `scripts/` (run), `references/` (read on demand) and `assets/` (templates). Mention keeping `SKILL.md` under 500 lines, references one level deep, product extensions like `disable-model-invocation` or Codex's `agents/openai.yaml`, discovery paths (`.claude/skills`, `.agents/skills`), and validating with `skills-ref`.

Follow-up: *"How do you split work between instructions and scripts?"* Judgement and process in instructions; exact, repeatable work (calculations, validation, file formats) in scripts with clear arguments, JSON output and helpful errors.

---

## Key Takeaways

- **A skill is a folder named after it**, with `SKILL.md` and optional `scripts/`, `references/` and `assets/`.
- **Only `name` and `description` are required**; the description must say what the skill does and when to use it.
- **Instructions handle judgement; scripts handle exact work**, with arguments, JSON output and clear errors.
- **Products add optional fields and different discovery folders**, but the core format is shared; `.agents/skills/` is the most widely read location.
- **Validate skills automatically**: name rules, folder match, length limits and that every referenced file exists.

---

**Up next:** [Progressive Disclosure: Discovery, Activation, Execution](progressive-disclosure-discovery-activation-execution.md)
