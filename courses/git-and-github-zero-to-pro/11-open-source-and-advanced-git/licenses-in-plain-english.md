---
title: "Licenses in Plain English"
course: "Git and GitHub: Zero to Pro"
module: "11. Open Source and Advanced Git"
type: Article
level: Intermediate
reading_time: 20 min
---

# Licenses in Plain English: The Complete Guide

> 📚 **Before you start**
>
> - [A Great README, LICENSE and Profile](../course.md#m5)
> - [Contributing to Open Source](contributing-to-open-source.md)

## Introduction

When your aunt shares her famous mango pickle recipe, she might say "use it however you like", or "make it, but don't sell it", or "if you share it, share the full recipe, don't keep your tweaks secret". Same recipe, very different rules.

Software licences are those rules, written carefully enough to stand up in court. Code on GitHub isn't automatically free to use: **without a licence, copyright law means nobody else may copy, modify or distribute it**, even if it's public. A licence is the owner's written permission, with conditions.

This lesson explains the main open source licences in plain language, what "permissive" and "copyleft" really mean, how to pick one for your project, how to check the licences of your dependencies, and where "source-available" licences fit in. (This is an engineer's guide, not legal advice. For anything with real money or risk attached, ask a lawyer.)

> 💡 **Key Insight**
>
> Every open source licence says "you may use, change and share this". They differ in **what you must do in return**: keep a notice (**permissive**), share your changes to the library (**weak copyleft**), or release your whole program under the same licence (**strong copyleft**).

---

## Core Explanation

### 1. No Licence Means "All Rights Reserved"

A public repository without a `LICENSE` file lets people **view** the code (GitHub's terms allow viewing and forking on GitHub), but not legally reuse it in their own projects. If you want people to use your code, add a licence. If you find useful code with no licence, open an issue asking the author to add one.

"Open source" has a specific meaning: a licence approved by the **Open Source Initiative (OSI)**, which guarantees freedoms like using the code for any purpose, including commercially.

### 2. The Three Families

| Family | Your obligations when you distribute | Examples |
|---|---|---|
| **Permissive** | Keep the copyright and licence notice | MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, ISC |
| **Weak copyleft** | Changes to the **licensed files or library** must be released under the same licence; your own code that uses it can stay under any licence | MPL-2.0 (per file), LGPL-2.1/3.0 (per library) |
| **Strong copyleft** | The **whole program** that includes the code must be released under the same licence, with source | GPL-2.0, GPL-3.0 |
| **Network copyleft** | Like GPL, and also applies when users interact with it **over a network** (a SaaS) | AGPL-3.0 |

"Distribute" matters: GPL obligations trigger when you **give** someone the software (an app download, a device with firmware). Running modified GPL code on your own servers isn't distribution, which is exactly the gap AGPL closes.

### 3. The Licences You'll Meet Most

**MIT** (very short): do anything, keep the notice, no warranty. The most popular licence on GitHub.

**BSD-3-Clause**: like MIT, plus "don't use our name to endorse your product".

**Apache-2.0**: permissive, plus:
- an explicit **patent grant** from contributors, which ends if you sue them over patents in the software;
- you must state significant changes and keep any **NOTICE** file.
Popular with companies for the patent clarity.

**MPL-2.0**: copyleft at the **file** level. Modify an MPL file and you must share that file's changes; your other files can be proprietary.

**LGPL**: copyleft at the **library** level. You can link a proprietary app against an LGPL library, but changes to the library must be shared and users must be able to swap in a modified library.

**GPL-3.0**: anything that includes GPL code and is distributed must be GPL with source available. It adds patent and "anti-tivoisation" provisions to GPL-2.0. The Linux kernel is **GPL-2.0-only**, which is why it can't simply move to GPL-3.0.

**AGPL-3.0**: GPL plus the network clause: if users interact with your modified version over a network, they must be able to get its source.

**For non-code content:** Creative Commons licences such as **CC BY 4.0** (credit the author) or **CC0** (public domain dedication) suit documentation, datasets and images. Creative Commons doesn't recommend CC licences for software.

### 4. "-only" versus "-or-later", and SPDX Identifiers

GPL licences come in variants: `GPL-3.0-only` (exactly version 3) or `GPL-3.0-or-later` (version 3 or any later version the FSF publishes). **SPDX identifiers** are the standard short names, used in package metadata and at the top of files:

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Chai Co contributors
```

Python packaging uses them too. In `pyproject.toml`:

~~~toml
[project]
name = "chai-bill"
license = "Apache-2.0"
license-files = ["LICENSE", "NOTICE"]
~~~

### 5. Compatibility: Can These Licences Live Together?

Combining code under different licences in one program works only if you can satisfy **all** of them at once:

- Permissive code can go into almost anything (keep the notices).
- GPL code makes the **whole distributed program** GPL.
- Some pairs **conflict**: Apache-2.0 code can't be combined with **GPL-2.0-only** code (the Free Software Foundation considers Apache-2.0's patent terms extra restrictions GPL-2.0 doesn't allow), but it can be combined with GPL-3.0. `GPL-2.0-only` and `GPL-3.0-only` code can't be combined with each other.

A simplified dependency audit:

```python
KIND = {
    "MIT": "permissive", "BSD-3-Clause": "permissive", "Apache-2.0": "permissive",
    "MPL-2.0": "weak copyleft", "LGPL-3.0-only": "weak copyleft",
    "GPL-2.0-only": "copyleft", "GPL-3.0-only": "copyleft", "AGPL-3.0-only": "copyleft",
}
# Pairs that can't be combined in one distributed program (simplified, well-known cases).
INCOMPATIBLE = {frozenset({"Apache-2.0", "GPL-2.0-only"}), frozenset({"GPL-2.0-only", "GPL-3.0-only"})}

def audit(project_license, dependencies):
    licenses = {project_license, *dependencies.values()}
    for name, lic in dependencies.items():
        clash = [other for other in licenses if frozenset({lic, other}) in INCOMPATIBLE]
        kind = KIND.get(lic)
        if clash:
            verdict = f"CONFLICT with {', '.join(sorted(clash))}"
        elif kind is None:
            verdict = "unknown licence: check manually"
        elif kind == "permissive":
            verdict = "ok: keep its copyright notice" + (" and NOTICE file" if lic == "Apache-2.0" else "")
        elif kind == "weak copyleft":
            verdict = "ok: changes to this library itself must stay open"
        elif lic == project_license:
            verdict = "ok: same licence"
        else:
            verdict = f"whole program must be distributed under {lic}"
        print(f"{name:<11} {lic:<14} {verdict}")

deps = {"requests": "Apache-2.0", "click": "BSD-3-Clause", "certifi": "MPL-2.0"}
audit("MIT", deps)
print()
audit("MIT", {**deps, "readline-x": "GPL-3.0-only"})
print()
audit("GPL-2.0-only", deps)
```

Output:

```
requests    Apache-2.0     ok: keep its copyright notice and NOTICE file
click       BSD-3-Clause   ok: keep its copyright notice
certifi     MPL-2.0        ok: changes to this library itself must stay open

requests    Apache-2.0     ok: keep its copyright notice and NOTICE file
click       BSD-3-Clause   ok: keep its copyright notice
certifi     MPL-2.0        ok: changes to this library itself must stay open
readline-x  GPL-3.0-only   whole program must be distributed under GPL-3.0-only

requests    Apache-2.0     CONFLICT with GPL-2.0-only
click       BSD-3-Clause   ok: keep its copyright notice
certifi     MPL-2.0        ok: changes to this library itself must stay open
```

Adding one GPL dependency changed the obligations of the entire MIT app. Real tools do this at scale: GitHub's **dependency graph** shows licences of dependencies, the **dependency review action** can fail a PR that adds a disallowed licence (its `deny-licenses` / `allow-licenses` inputs), and tools such as `pip-licenses`, ScanCode and FOSSA produce full reports.

### 6. Choosing a Licence for Your Project

| You want... | Choose |
|---|---|
| Maximum adoption, minimum fuss | **MIT** |
| Permissive, with patent protection (common for company-backed projects) | **Apache-2.0** |
| Improvements to your library to stay open, but anyone can use it in any app | **MPL-2.0** or **LGPL** |
| Everything built on your code to stay open | **GPL-3.0** |
| The same, including for SaaS | **AGPL-3.0** |
| Docs, data or images | **CC BY 4.0** or **CC0** |

On GitHub: **Add file → Create new file**, name it `LICENSE`, and click **Choose a licence template**; or pick one when creating the repository. choosealicense.com (run by GitHub) explains each in plain terms. GitHub detects the licence and shows it in the repository sidebar.

**Employer check:** code you write at work, or on work equipment, often belongs to your employer. Read your contract and your company's open source policy before publishing or contributing.

### 7. Source-Available Is Not Open Source

Some companies have moved projects from open source to **source-available** licences that restrict competing hosted services: HashiCorp's move of Terraform to the Business Source Licence (BSL) in 2023 led the community to fork it as **OpenTofu** under the Linux Foundation; Redis moved to dual RSAL/SSPL licensing in 2024, which led to the **Valkey** fork, and then added **AGPL-3.0** as an option with Redis 8 in 2025. The code is visible, but the licences aren't OSI-approved, so check the terms before building a business on them.

### 8. Contributor Inbound Licensing

When you accept contributions, you need to know you can distribute them under your licence. The common pattern is "inbound = outbound": contributions are licensed under the project's licence (Apache-2.0 says so explicitly in section 5), plus a DCO sign-off. Some projects use a CLA instead, which can let the owner relicense later; that's one reason contributors are sometimes wary of CLAs.

---

## Try It Yourself

1. You're building a closed-source Android app. Which of these dependencies are fine, and what must you do for each? MIT, Apache-2.0, LGPL-3.0, GPL-3.0.
2. Run `audit("Apache-2.0", {"kernel-module": "GPL-2.0-only"})`. What does it print, and why?
3. A friend's repository of handy scripts is public but has no licence. Can you copy a script into your company's codebase?
4. Your startup offers a hosted analytics service built on a modified AGPL-3.0 database. What do you owe your users?

<details>
<summary>Show answers</summary>

**1.** MIT: fine, keep the notice (an "open source licences" screen in the app is the usual way). Apache-2.0: fine, keep the licence and any NOTICE. LGPL-3.0: possible if you use it as a separately replaceable library and share changes to it, which is tricky on mobile, so get advice. GPL-3.0: would require releasing the whole app under GPL, so avoid it for a closed-source app.

**2.**

```python
audit("Apache-2.0", {"kernel-module": "GPL-2.0-only"})
```

Output:

```
kernel-module GPL-2.0-only   CONFLICT with Apache-2.0
```

Apache-2.0 and GPL-2.0-only can't be combined in one distributed program. (The name is longer than the column, so the alignment slips; a real report would size columns to fit.)

**3.** No. Without a licence it's all rights reserved. Ask your friend to add one (MIT is a common choice for snippets).

**4.** Users interacting with the service over the network must be offered the source code of your modified version of the database, under AGPL-3.0.

</details>

---

## Real-World Examples

### Example 1: A Licence Check in CI

A fintech company adds `actions/dependency-review-action` to every pull request with an allow-list of permissive licences. When a developer adds a GPL charting library, the check fails and suggests talking to the open source office, before the app ships.

### Example 2: The Missing NOTICE

An enterprise customer's audit found that a vendor's product bundled Apache-2.0 libraries without their NOTICE files. The fix was easy (include them in the distribution), but the release was delayed a week. Many companies now generate a third-party notices file automatically during builds.

### Example 3: Forks After a Licence Change

When Terraform moved to the BSL, companies building products on it had to choose between the new terms and the community's open source fork, OpenTofu. Licence choices made years earlier suddenly mattered for product strategy.

---

## Common Misconceptions

### Misconception 1: "Public on GitHub means free to use"

Without a licence, the default is all rights reserved.

### Misconception 2: "GPL means I can't use it at work or sell it"

You can use GPL software internally and even sell it; the obligation is to provide source under the GPL when you distribute it.

### Misconception 3: "MIT and Apache are the same"

Both are permissive, but Apache-2.0 adds an explicit patent grant and NOTICE requirements, and it's incompatible with GPL-2.0-only.

### Misconception 4: "Source-available is open source"

Licences like BSL and SSPL restrict usage and aren't OSI-approved.

---

## Interview Relevance

Licensing questions appear in senior engineering, open source program office and startup interviews:

- **Permissive versus copyleft**, with examples, and what "distribution" triggers.
- **Why Apache-2.0** for company projects (patent grant).
- **AGPL and SaaS**.
- **Dependency licence compliance** in CI (dependency review, SBOMs, notices files).
- **What happens with no licence.**

A common follow-up: *"Can we use this GPL library in our product?"* A good answer distinguishes internal use, SaaS (fine for GPL, not for modified AGPL without sharing source), and distributed apps, and suggests involving legal.

---

## Key Takeaways

- **No licence = no permission**; add a `LICENSE` file to anything you want others to use.
- **Permissive** (MIT, BSD, Apache-2.0) asks for notices; **weak copyleft** (MPL, LGPL) asks you to share changes to the library; **strong copyleft** (GPL) covers the whole distributed program; **AGPL** extends it to network use.
- **Apache-2.0 adds a patent grant** and is incompatible with GPL-2.0-only; use **SPDX identifiers** everywhere.
- **Check dependency licences automatically** with the dependency graph, dependency review and licence scanners.
- **Source-available licences aren't open source**, and code you write at work may belong to your employer.

---

**Up next:** [Maintaining a Project: Templates, Releases and Semver](maintaining-a-project-templates-releases-and-semver.md)
