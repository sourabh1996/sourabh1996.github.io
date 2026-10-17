---
title: "PageIndex and Chunk-Free Segmentation"
course: "Retrieval-Augmented Generation (RAG)"
module: "8. Vectorless RAG"
type: Article
level: Advanced
reading_time: 30 min
---

# PageIndex and Chunk-Free Segmentation: The Complete Guide

> 📚 **Before you start**
>
> - [Limits of Vector RAG](limits-of-vector-rag.md), for the failures this approach is designed to fix, and the annual report we keep using.
> - [Chunking Strategies](../06-implementing-rag/chunking-strategies.md), for fixed-size, structure-aware and semantic chunking, which this lesson moves beyond.

## Introduction

Think about how a good reference librarian at a university in Pune helps you find something in a thick government report. They don't photocopy every page, cut the copies into strips of 200 words and shuffle them into a box. They open the contents, notice how the report is organised, and point you to a chapter. The **structure** the authors built is the index.

**PageIndex** is an open-source project from VectifyAI (MIT licence) that applies this idea to RAG. Its own tagline sums it up: *reasoning-based RAG, no vector database, no chunking*. It does two things:

1. **Indexing**: turn a long PDF (or Markdown file) into a **tree** of the document's own sections, each with a title, a summary and the pages it covers. This is the "table of contents, made machine-usable".
2. **Retrieval**: give an LLM the tree and the question, and let it **reason** about which sections to open, read them, and decide whether it has enough, much like the analyst from the last lesson.

This lesson covers the first half: how a document becomes a set of natural sections without fixed-size chunks (**chunk-free segmentation**), how the structure is found and checked, and how to run PageIndex itself. The next two lessons look at the tree in detail and at the search loop.

> 💡 **Key Insight**
>
> Chunk-free segmentation means **the document decides the boundaries**, not a token counter. Sections, sub-sections and notes become the units of retrieval, so every unit has a meaningful title, a clear page range and a place in the hierarchy. Size limits only come into play to split a section that's too big for the model to read at once.

---

## Core Explanation

### 1. The big picture

![Vectorless RAG in two bands. Index band: a long PDF goes through finding its structure from the contents page or headings with page starts verified, into natural sections without fixed chunks, into a document tree whose nodes carry node id, title, summary, start and end page and child nodes. Search band: a question goes to an LLM that reads the tree's titles and summaries and picks node ids, then fetches the full text of those nodes' pages, then judges whether that is enough; if not it loops back to follow a reference or pick another node; if so it answers with exact page numbers.](/img/diagrams/retrieval-augmented-generation-rag/rag-vectorless-tree-search.svg)

*Indexing (top) runs once per document and costs LLM calls for structure and summaries. Search (bottom) runs per question and is a loop: read, pick, fetch, judge.*

Compare that with vector RAG: there, indexing produces thousands of anonymous vectors and search is one similarity lookup. Here, indexing produces one small, readable tree and search is a short conversation between the LLM and that tree.

We'll keep using the same 16-page annual report:

```python
import json, re, zlib
import numpy as np

# The text layer of a 16-page annual report, one string per page. Headings sit on their own lines.
REPORT = {
    1: "Bharat Grid Power Limited\nAnnual Report 2025-26\nContents: Chairman's message 2, Business review 3, Risk management 6, Financial statements 8, Notes to the accounts 11, Corporate governance 15.",
    2: "1 Chairman's message\nDear shareholders, 2025-26 was our most profitable year yet. Net profit grew 16.5% and our net profit margin improved for the third year in a row. I thank our employees for this result.",
    3: "2 Business review\n2.1 Generation\nOur plants generated 41,300 million units of electricity. Coal plants ran at a plant load factor of 71%.",
    4: "2.2 Transmission\nWe added 1,150 circuit km of transmission lines. Line availability stayed above 99.6%.",
    5: "2.3 Renewable projects\nWe commissioned 640 MW of solar capacity in Rajasthan and Gujarat. A 300 MW wind project in Tamil Nadu is due in 2027.",
    6: "3 Risk management\n3.1 Financial risks\nInterest rate risk is managed by keeping 60% of borrowings at fixed rates. The company is contesting several tax disputes with the authorities, and the amounts involved are disclosed in Note 31.",
    7: "3.2 Operational risks\nCoal supply disruptions during the monsoon and heat waves that push up peak demand are the main operational risks.",
    8: "4 Financial statements\n4.1 Statement of profit and loss\nRevenue from operations Rs 18,420 crore. Total expenses Rs 16,710 crore. Profit after tax Rs 1,284 crore (previous year Rs 1,102 crore).",
    9: "4.2 Balance sheet\nTotal assets Rs 52,600 crore. Total equity Rs 19,900 crore. Borrowings are detailed in Note 12.",
    10: "4.3 Cash flow statement\nCash from operating activities Rs 3,870 crore. Capital expenditure Rs 4,950 crore, mostly on solar projects.",
    11: "5 Notes to the accounts\nNote 12 Borrowings\nLong-term loans Rs 21,300 crore and short-term loans Rs 2,900 crore. Rs 3,450 crore of the long-term loans is repayable within one year.",
    12: "Note 18 Revenue from operations\nSale of power Rs 16,980 crore, transmission charges Rs 1,210 crore and other operating income Rs 230 crore.",
    13: "Note 27 Employee benefits\nGratuity and provident fund contributions were Rs 312 crore. The company had 9,400 employees at the year end.",
    14: "Note 31 Contingent liabilities\nClaims not acknowledged as debts: income tax demands Rs 412 crore, GST demands Rs 96 crore and land compensation cases Rs 58 crore.",
    15: "6 Corporate governance\n6.1 Board of directors\nThe board has 11 directors, 6 of them independent. It met 8 times during the year.",
    16: "6.2 Independent auditor's report\nIn our opinion the financial statements give a true and fair view. Auditors: Mehta Iyer and Co, Chartered Accountants.",
}
print(len(REPORT), "pages,", sum(len(t.split()) for t in REPORT.values()), "words")
```

Output:

```
16 pages, 407 words
```

### 2. Where does the structure come from?

A document's structure can come from three places, roughly in order of reliability:

- **A contents page** with titles and page numbers. Annual reports, filings, books and manuals almost always have one.
- **Headings in the text**: numbered (`4.2 Balance sheet`), styled (bold, larger font) or Markdown (`## Balance sheet`).
- **An LLM reading the pages** and proposing where sections start, when there is neither.

PageIndex works through these in the same spirit. It first checks the opening pages for a contents page (the `--toc-check-pages` option, 20 pages by default). When it finds one, it uses it; when it doesn't, it asks the LLM to generate the structure from the page text. Either way, it then checks that each section really starts where the structure claims.

Let's do the contents-page route by hand. Page 1 of our report has a one-line contents list:

```python
toc_text = REPORT[1].split("Contents: ")[1].rstrip(".")
toc = [(m.group(1).strip(), int(m.group(2))) for m in re.finditer(r"([^,]+?) (\d+)(?:,|$)", toc_text)]
print(toc)
```

Output:

```
[("Chairman's message", 2), ('Business review', 3), ('Risk management', 6), ('Financial statements', 8), ('Notes to the accounts', 11), ('Corporate governance', 15)]
```

A real contents page is messier (dotted leaders, two columns, roman numerals), which is exactly why PageIndex uses an LLM to read it rather than a regular expression.

### 3. Verify, and fix page offsets

The numbers on a contents page are **printed** page numbers. A PDF's pages are **physical** pages, counted from the cover. They often differ: two cover pages and a blank page push everything by three. A contents entry saying "Financial statements 8" might be physical page 11.

So every entry must be **verified**: does the title actually appear **as a heading** on the page we think it starts on? (Merely appearing isn't enough: the contents page itself mentions every title.) Here's a check, plus an offset search for when it fails. To see it work, we build a version of the report with two extra pages at the front, as a real PDF often has:

```python
def starts_on(title, text):        # the title must be a heading line, not just mentioned somewhere
    return any(line.lower().endswith(title.lower()) for line in text.splitlines())

def verified(toc, pages, offset=0):
    return [title for title, page in toc if starts_on(title, pages.get(page + offset, ""))]

def find_offset(toc, pages, max_shift=5):
    best = max(range(-max_shift, max_shift + 1), key=lambda s: len(verified(toc, pages, s)))
    return best, len(verified(toc, pages, best))

print("our report: offset", find_offset(toc, REPORT))

with_cover = {1: "Bharat Grid Power Limited", 2: "This page is intentionally left blank."}
with_cover.update({page + 2: text for page, text in REPORT.items()})
print("as printed:", len(verified(toc, with_cover)), "of", len(toc), "entries verified")
print("PDF with two front pages: offset", find_offset(toc, with_cover))
```

Output:

```
our report: offset (0, 6)
as printed: 0 of 6 entries verified
PDF with two front pages: offset (2, 6)
```

With the printed numbers, every entry fails verification; with an offset of 2, all six pass. Real pipelines (PageIndex included) do this per entry rather than with one global shift, because offsets can change mid-document (an inserted fold-out map, a separately numbered annexure), and they let the LLM fix entries that still don't match.

### 4. Segment by headings, not by size

The contents page gives the top level. Headings inside the pages give the finer levels. In our report's text layer, headings sit on their own lines and start with a section number or "Note N":

```python
HEADING = re.compile(r"^(?:(\d+(?:\.\d+)*)|Note (\d+)) ([A-Z][^.\n]*)$")

def segment(pages):
    sections = []
    for page, text in pages.items():
        for line in text.splitlines():
            if HEADING.match(line):
                sections.append({"heading": line, "page": page, "text": ""})
            elif sections:
                sections[-1]["text"] += line + " "
    return sections

sections = segment(REPORT)
print(len(sections), "sections")
for s in sections[5:9]:
    print(f"p. {s['page']:>2}  {s['heading']:<34} {len(s['text'].split())} words")
```

Output:

```
20 sections
p.  6  3 Risk management                  0 words
p.  6  3.1 Financial risks                32 words
p.  7  3.2 Operational risks              19 words
p.  8  4 Financial statements             0 words
```

Twenty sections, each a natural unit with its own title and page. Some are empty (a parent heading like "3 Risk management" followed straight away by its first sub-section), which is fine: in a tree, the parent's content is its children.

Compare a fixed-size splitter that runs over the whole document. Let's count how often a 40-word chunk straddles two or more sections:

```python
labels, current = [], "front matter"
for page, text in REPORT.items():
    for line in text.splitlines():
        if HEADING.match(line):
            current = line
        labels += [current] * len(line.split())

starts = range(0, len(labels), 40)
mixed = [i for i in starts if len(set(labels[i:i + 40])) > 1]
print(f"{len(starts)} fixed chunks, {len(mixed)} of them span more than one section")
print("e.g. chunk at word", mixed[3], "covers:", sorted(set(labels[mixed[3]:mixed[3] + 40])))
```

Output:

```
11 fixed chunks, 10 of them span more than one section
e.g. chunk at word 120 covers: ['2.3 Renewable projects', '3 Risk management', '3.1 Financial risks']
```

Almost every fixed chunk mixes sections. Our sections are tiny, which exaggerates it, but in real documents the boundary chunks are exactly where answers get split from their headings.

### 5. When a section is too big

Natural sections vary wildly: a two-line note and a 40-page management discussion. A node is useful only if the model can read it when it's chosen. So PageIndex has two limits, `--max-pages-per-node` (default 10) and `--max-tokens-per-node` (default 20,000). A node larger than these is subdivided, preferably along its own sub-headings, so the split still follows structure.

```python
def split_if_large(title, start, end, max_pages=10):
    if end - start + 1 <= max_pages:
        return [(title, start, end)]
    parts = []
    for i, s in enumerate(range(start, end + 1, max_pages)):
        parts.append((f"{title} (part {i + 1})", s, min(s + max_pages - 1, end)))
    return parts

print(split_if_large("Notes to the accounts", 11, 14))
print(split_if_large("Management discussion and analysis", 20, 44))
```

Output:

```
[('Notes to the accounts', 11, 14)]
[('Management discussion and analysis (part 1)', 20, 29), ('Management discussion and analysis (part 2)', 30, 39), ('Management discussion and analysis (part 3)', 40, 44)]
```

This fallback splits by page count when a long section has no sub-headings. It's the only place size matters, and even then the parts keep the section's title.

### 6. Running PageIndex

PageIndex installs with pip and runs on a PDF or a Markdown file. It calls an LLM for structure detection, verification and summaries, so it needs an API key for the provider you configure.

```python
# not-run: shell commands, need the pageindex repository or package and an LLM API key
# pip install -U pageindex
# python3 run_pageindex.py --pdf_path bharat-grid-annual-report-2025-26.pdf \
#     --toc-check-pages 20 --max-pages-per-node 10 --max-tokens-per-node 20000 \
#     --if-add-node-id yes --if-add-node-summary yes --if-add-doc-description yes
# python3 run_pageindex.py --md_path handbook.md       # Markdown: the tree comes from # headings
```

Example output (an excerpt of the JSON tree it writes):

```
{
  "title": "Financial statements",
  "node_id": "0008",
  "start_index": 8,
  "end_index": 10,
  "summary": "Audited statement of profit and loss, balance sheet and cash flow statement for 2025-26.",
  "nodes": [
    {"title": "Statement of profit and loss", "node_id": "0009", "start_index": 8, "end_index": 8, "summary": "..."}
  ]
}
```

`start_index` and `end_index` are the node's first and last pages. The project also offers a hosted version with an API and an MCP server for agents, and its README tracks a fast-moving SDK, so check the current docs before you build on a specific function name. The vendor reports 98.7% accuracy on the FinanceBench benchmark of questions about company filings with a system built on this approach; that's the vendor's own number, but it shows why the idea took off for financial documents.

### 7. What indexing costs

Indexing a vector store costs embedding calls, which are cheap. Indexing a PageIndex tree costs **LLM calls**: reading the contents page, verifying section starts, generating structure when there's no contents page, and writing a summary for every node. For a 300-page report that's typically dozens of calls, done once. It pays off when the same long document is questioned many times (a loan file, a contract under negotiation, a product manual) and is wasteful for a constantly changing stream of short documents.

---

## Try It Yourself

1. **A wrong entry.** Change the contents entry for "Risk management" to page 7 and run `verified(toc, REPORT)`. Which entry fails, and how should a pipeline repair it?
2. **Markdown structure.** Write a function that turns a Markdown string into `(level, title)` pairs from its `#` headings, and test it on a three-heading document.
3. **Split sizes.** With `max_pages=10`, how many nodes does a 95-page section with no sub-headings become? What's the last node's page range if it starts on page 101?

<details>
<summary>Show answers</summary>

**1.**

```python
bad_toc = [(t, 7 if t == "Risk management" else p) for t, p in toc]
ok = verified(bad_toc, REPORT)
print([t for t, _ in bad_toc if t not in ok])
```

Output:

```
['Risk management']
```

Only "Risk management" fails. A pipeline should search nearby pages for the title (page 6 matches) and correct that single entry, instead of shifting everything.

**2.**

```python
def markdown_headings(md):
    return [(len(m.group(1)), m.group(2).strip()) for m in re.finditer(r"^(#{1,6}) (.+)$", md, re.M)]

print(markdown_headings("# Leave policy\nIntro.\n## Annual leave\n24 days.\n## Sick leave\n10 days."))
```

Output:

```
[(1, 'Leave policy'), (2, 'Annual leave'), (2, 'Sick leave')]
```

The number of `#` characters is the level, which gives the tree directly. This is why Markdown input to PageIndex needs no contents-page detection.

**3.**

```python
parts = split_if_large("Schedules", 101, 195)
print(len(parts), parts[-1])
```

Output:

```
10 ('Schedules (part 10)', 191, 195)
```

</details>

---

## Real-World Examples

- **Financial filings**: annual reports and regulatory filings have reliable contents pages and numbered notes, which makes them the classic fit.
- **Legal documents**: contracts and judgments are organised in numbered clauses and paragraphs that make natural nodes.
- **Product and service manuals**: chapters, sections and numbered procedures map directly to a tree, and technicians think in those terms.
- **Internal documentation in Markdown**: headings give the structure for free, so a tree index costs only the summary calls.

---

## Common Misconceptions

### "Chunk-free means the whole document goes into the prompt"

No. The model sees a compact tree of titles and summaries, then reads only the sections it chooses.

### "PageIndex needs perfect headings"

It works best with a contents page or clear headings, and can ask the LLM to propose structure when they're missing, but badly structured documents (a scanned letter, a chat export) give weak trees.

### "The page numbers on the contents page are the PDF pages"

They're printed numbers and often offset from the physical pages. Always verify.

### "Section-based units are always small enough"

Sections vary from a line to dozens of pages; large ones must be subdivided, ideally along sub-headings.

---

## Interview Relevance

*"How does PageIndex index a document without chunking?"* It recovers the document's own hierarchy (from the contents page, headings or an LLM pass), verifies where each section starts, subdivides only sections that exceed page or token limits, and stores a tree of nodes with titles, summaries and page ranges.

*"What can go wrong when building a structure index from a PDF?"* Printed vs physical page offsets, contents entries that don't match headings, documents with no structure, sections too large to read, and indexing cost in LLM calls.

---

## Key Takeaways

- **PageIndex** indexes a document as a tree of its own sections and retrieves by LLM reasoning, with no vectors or fixed chunks.
- **Structure comes from** the contents page, headings, or an LLM pass, in that order of reliability.
- **Verify every section start** and correct printed-to-physical page offsets.
- **Segment by headings**; split by size only when a section is too big to read.
- **Indexing costs LLM calls** up front, which pays off for long documents queried many times.

---

**Up next:** [The Document Tree Model](the-document-tree-model.md)
