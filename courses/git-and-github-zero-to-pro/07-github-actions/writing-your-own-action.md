---
title: "Writing Your Own Action"
course: "Git and GitHub: Zero to Pro"
module: "7. GitHub Actions"
type: Article
level: Advanced
reading_time: 30 min
---

# Writing Your Own Action: The Complete Guide

> 📚 **Before you start**
>
> - [Reusable Workflows and Composite Actions](reusable-workflows-and-composite-actions.md), which covers the composite kind
> - [Workflows, Jobs, Steps and Runners](workflows-jobs-steps-and-runners.md), for `GITHUB_OUTPUT` and workflow commands
> - [Functions and Iterators](../../python-programming/course.md#m6) (Python Programming)

## Introduction

Every big Indian kitchen has one gadget nobody else sells: the grandmother's custom dosa spreader, the uncle's improvised coconut scraper. Off-the-shelf tools cover 95% of the cooking; the last 5% needs something you build yourself.

The GitHub Marketplace has thousands of actions, and composite actions cover most glue work. But sometimes you need real logic: parse a test report and post a neat summary, label pull requests by size, call your company's internal API with retries. That's when you write your own action.

By the end of this article you will know the three kinds of action and when to pick each, write a complete `action.yml`, build a JavaScript action and a Docker action in Python, read inputs and write outputs exactly the way the runner expects, test your action, and publish and version it on the Marketplace.

> 💡 **Key Insight**
>
> An action is a **contract** (`action.yml`: inputs, outputs, how to run) plus **code** that reads inputs from environment variables and writes outputs to a file. Once you see that inputs arrive as `INPUT_<NAME>` variables and outputs leave through `$GITHUB_OUTPUT`, every action in any language becomes easy to read and write.

---

## Core Explanation

### 1. The Three Kinds of Action

| Kind | `runs.using` | Runs on | Start-up | Best for |
|---|---|---|---|---|
| **JavaScript** | `node24` | Linux, Windows, macOS runners, directly | Fastest | Most actions, especially ones calling the GitHub API |
| **Docker container** | `docker` | Linux runners only | Slower (build or pull image) | Any language, fixed tool versions |
| **Composite** | `composite` | Wherever the caller runs | Fast | Gluing existing steps and actions |

Composite actions were covered in the previous lesson. This one focuses on JavaScript and Docker actions, which run your own code.

### 2. The Contract: `action.yml`

Every action has a metadata file named `action.yml` (or `action.yaml`) at the root of its folder. We'll build a **PR size labeller**: given the number of changed lines, it picks a label such as `size/S` or `size/XL`.

```yaml
name: PR Size Labeller
description: Label a pull request XS to XL by the number of changed lines
author: chai-co

inputs:
  changed-lines:
    description: Number of added plus deleted lines
    required: true
  thresholds:
    description: Comma-separated LABEL=MAX pairs
    required: false
    default: "XS=10,S=50,M=250,L=1000"
  github-token:
    description: Token used to add the label
    required: false
    default: ${{ github.token }}

outputs:
  label:
    description: The label that was chosen

runs:
  using: node24
  main: dist/index.js

branding:
  icon: tag
  color: green
```

| Key | Purpose |
|---|---|
| `name`, `description`, `author` | Shown on the Marketplace. `name` must be unique there |
| `inputs.<id>` | `description`, `required`, `default`; optionally `deprecationMessage` |
| `outputs.<id>` | `description` (composite actions also need `value`) |
| `runs` | How to execute: depends on the kind |
| `branding` | Marketplace icon (a Feather icon name) and colour |

A `default` can be an expression like `${{ github.token }}`, which is how many actions use the job's token without the caller passing it.

`runs` for each kind:

```yaml
# JavaScript
runs:
  using: node24
  main: dist/index.js       # entry point
  pre: dist/setup.js        # optional, runs before the job's steps
  post: dist/cleanup.js     # optional, runs at the end of the job
  post-if: always()

# Docker, built from a Dockerfile in the action's folder
runs:
  using: docker
  image: Dockerfile
  args:
    - ${{ inputs.changed-lines }}

# Docker, using a prebuilt public image (faster start)
runs:
  using: docker
  image: docker://ghcr.io/chai-co/pr-size-labeller:1.2.0
```

### 3. How Inputs and Outputs Really Travel

When a step uses your action with `with:`, the runner sets one environment variable per input: `INPUT_` plus the input name in upper case, with spaces turned into underscores. Hyphens stay, so `changed-lines` arrives as `INPUT_CHANGED-LINES`. Defaults from `action.yml` are filled in when the caller doesn't pass a value.

Outputs go the other way: your code appends `name=value` lines to the file whose path is in `GITHUB_OUTPUT`. The toolkit libraries just wrap this. Here are the two helpers in plain Python, together with the labeller's logic:

```python
import os

def get_input(name, required=False, default=""):
    """Read an action input the way the runner passes it: INPUT_<NAME> in upper case."""
    key = "INPUT_" + name.replace(" ", "_").upper()
    value = os.environ.get(key, "").strip()
    if required and not value:
        raise ValueError(f"Input required and not supplied: {name}")
    return value or default

def set_output(name, value):
    """Append name=value to the file the runner reads outputs from."""
    with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
        fh.write(f"{name}={value}\n")

def size_label(changed_lines, thresholds):
    """Pick a size label: the first threshold the change fits under."""
    for label, limit in thresholds:
        if changed_lines <= limit:
            return label
    return "size/XL"

def parse_thresholds(text):
    """'XS=10,S=50,M=250' -> [('size/XS', 10), ('size/S', 50), ('size/M', 250)]"""
    pairs = [item.split("=") for item in text.split(",") if item.strip()]
    return sorted(((f"size/{k.strip()}", int(v)) for k, v in pairs), key=lambda p: p[1])

def main():
    changed = int(get_input("changed-lines", required=True))
    thresholds = parse_thresholds(get_input("thresholds", default="XS=10,S=50,M=250,L=1000"))
    label = size_label(changed, thresholds)
    print(f"{changed} changed lines -> {label}")
    set_output("label", label)
```

To test it locally, pretend to be the runner: set the input variables and point `GITHUB_OUTPUT` at a temporary file.

```python
import tempfile
os.environ["GITHUB_OUTPUT"] = os.path.join(tempfile.mkdtemp(), "output.txt")
for lines in [4, 120, 5000]:
    os.environ["INPUT_CHANGED-LINES"] = str(lines)
    main()
print(open(os.environ["GITHUB_OUTPUT"]).read().strip())

del os.environ["INPUT_CHANGED-LINES"]
try:
    main()
except ValueError as err:
    print("Error:", err)
```

Output:

```
4 changed lines -> size/XS
120 changed lines -> size/M
5000 changed lines -> size/XL
label=size/XS
label=size/M
label=size/XL
Error: Input required and not supplied: changed-lines
```

This is exactly how you unit-test an action: the runner is just environment variables and files. (Shells like bash can't read variable names that contain a hyphen, which is why actions written in bash often use underscores in input names.)

For values with newlines, the output file uses a heredoc-style delimiter:

```bash
{
  echo "summary<<EOF"
  cat report.md
  echo "EOF"
} >> "$GITHUB_OUTPUT"
```

### 4. A JavaScript Action

JavaScript actions run directly on the runner's bundled Node.js, so they start instantly on every OS. GitHub's toolkit packages do the plumbing:

- `@actions/core`: `getInput`, `setOutput`, `setFailed`, `info`, `warning`, `setSecret`, `summary`.
- `@actions/github`: `context` (the event payload, repo, sha) and `getOctokit(token)` for the GitHub API.

```javascript
// src/index.js
import * as core from "@actions/core";
import * as github from "@actions/github";

const DEFAULTS = "XS=10,S=50,M=250,L=1000";

function parseThresholds(text) {
  return text
    .split(",")
    .filter((item) => item.trim())
    .map((item) => {
      const [name, max] = item.split("=");
      return [`size/${name.trim()}`, Number(max)];
    })
    .sort((a, b) => a[1] - b[1]);
}

function sizeLabel(changed, thresholds) {
  for (const [label, limit] of thresholds) {
    if (changed <= limit) return label;
  }
  return "size/XL";
}

async function run() {
  try {
    const changed = Number(core.getInput("changed-lines", { required: true }));
    const thresholds = parseThresholds(core.getInput("thresholds") || DEFAULTS);
    const label = sizeLabel(changed, thresholds);
    core.info(`${changed} changed lines -> ${label}`);
    core.setOutput("label", label);

    const pr = github.context.payload.pull_request;
    if (!pr) {
      core.warning("Not a pull_request event, skipping the label.");
      return;
    }
    const octokit = github.getOctokit(core.getInput("github-token"));
    await octokit.rest.issues.addLabels({
      ...github.context.repo,
      issue_number: pr.number,
      labels: [label],
    });
    await core.summary.addHeading("PR size").addRaw(`This change is **${label}**.`).write();
  } catch (error) {
    core.setFailed(error.message);
  }
}

run();
```

The runner doesn't run `npm install` for you, so a JavaScript action must ship its dependencies. The usual approach is to **bundle** everything into one file in `dist/` with a tool such as `@vercel/ncc` or Rollup, and **commit `dist/`**:

```bash
npm init -y
npm install @actions/core @actions/github
npm install --save-dev @vercel/ncc
npx ncc build src/index.js -o dist --license licenses.txt
git add action.yml dist/ src/ package.json package-lock.json
git commit -m "Build PR size labeller"
```

GitHub's `actions/javascript-action` and `actions/typescript-action` template repositories give you this layout, tests, linting and a CI check that fails if `dist/` is out of date.

`core.setFailed` sets a non-zero exit code, which fails the step. Always wrap your logic in `try/catch` so errors become clean failures instead of stack traces.

### 5. A Docker Container Action in Python

If your team lives in Python, or needs specific system tools, a Docker action lets you use any language. Folder layout:

```
pr-size-labeller/
├── action.yml
├── Dockerfile
└── entrypoint.py
```

```dockerfile
FROM python:3.13-slim
COPY entrypoint.py /entrypoint.py
ENTRYPOINT ["python", "/entrypoint.py"]
```

`entrypoint.py` is the Python above with `main()` called at the bottom, plus a small API call to add the label (using `urllib.request` or `httpx` with `GITHUB_TOKEN`). In `action.yml`:

```yaml
runs:
  using: docker
  image: Dockerfile
  env:
    GITHUB_TOKEN: ${{ inputs.github-token }}
```

How the container is run:

- The runner builds the image at the start of the job (or pulls it, if `image` is `docker://...`). Prebuilt images start much faster.
- The workspace is mounted at `/github/workspace`, and `GITHUB_OUTPUT`, `GITHUB_ENV` and friends point at files the runner reads afterwards, so the same helpers work.
- All `INPUT_*` variables and the default `GITHUB_*` variables are passed in.
- Docker actions only run on **Linux** runners.

### 6. Using Your Action

From the same repository (for example while developing):

```yaml
on: pull_request

permissions:
  contents: read
  pull-requests: write

jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      # Expressions have no arithmetic, so add the numbers in the shell first.
      - id: count
        run: echo "lines=$((ADDED + DELETED))" >> "$GITHUB_OUTPUT"
        env:
          ADDED: ${{ github.event.pull_request.additions }}
          DELETED: ${{ github.event.pull_request.deletions }}
      - id: size
        uses: ./                 # the action.yml at the repository root
        with:
          changed-lines: ${{ steps.count.outputs.lines }}
      - run: echo "Labelled ${{ steps.size.outputs.label }}"
```

From another repository, after you publish:

```yaml
- uses: chai-co/pr-size-labeller@v1
  with:
    changed-lines: ${{ steps.count.outputs.lines }}
    thresholds: "XS=20,S=100,M=400,L=1500"
```

Example output:

```
Run chai-co/pr-size-labeller@v1
128 changed lines -> size/M
```

### 7. Testing an Action

Test at three levels:

1. **Unit tests** for the logic (`sizeLabel`, `parseThresholds`) with Jest, Vitest or pytest, mocking inputs as environment variables like we did above.
2. **A CI workflow in the action's own repository** that runs `uses: ./` on sample inputs and checks the outputs:

```yaml
jobs:
  self-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - id: run
        uses: ./
        with:
          changed-lines: "120"
      - name: Check output
        run: test "${{ steps.run.outputs.label }}" = "size/M"
```

3. **A check that `dist/` matches the source** for JavaScript actions: rebuild in CI and fail if `git diff --exit-code dist/` shows changes.

### 8. Publishing and Versioning

To list an action on the **GitHub Marketplace**:

- The repository must be **public** and hold a **single** action, with its `action.yml` at the **root**. Keep the repository focused on the action's code and the files it needs.
- The `name` in `action.yml` must be **unique** on the Marketplace, and can't match another GitHub user or organization's name unless that owner is the publisher.
- The owner must accept the **GitHub Marketplace Developer Agreement**, and you need **two-factor authentication** turned on.
- Draft a **release**, tick **Publish this Action to the GitHub Marketplace**, choose categories, and publish.

Versioning conventions that users rely on:

```bash
git tag -a v1.2.0 -m "v1.2.0: configurable thresholds"
git push origin v1.2.0
# move the major tag so users on @v1 get the update
git tag -fa v1 -m "Update v1 to v1.2.0"
git push origin v1 --force
```

- **Full version tags** (`v1.2.0`) never move.
- **Major tags** (`v1`) move to the latest compatible release.
- **Breaking changes** (renamed inputs, changed defaults) get a new major.
- Turn on **immutable releases** in the repository settings so a published release's tag and assets can't be changed afterwards. Users pinning to a commit SHA are protected either way; immutable releases protect people pinning to full version tags too.

Security responsibilities of an action author: request the least token permission your action needs and document it, never log inputs that may be secrets (call `core.setSecret` on derived sensitive values), keep dependencies updated, and treat event payload fields like titles and branch names as untrusted input.

---

## Try It Yourself

1. **Input names.** What environment variable holds an input named `api base url`? And `retry-count`?
2. **Extend the labeller.** Change `size_label` so that changes over 2,000 lines return `size/XXL` instead of `size/XL`. Test it with 2,500 and 1,200 lines.
3. **Pick the kind.** Which kind of action would you write for: (a) calling the GitHub API to post a formatted test summary, (b) running a CLI that only exists as a Linux binary with system libraries, (c) "checkout, set up Python, install our package"?
4. **Fail cleanly.** In the Python version, what should `main()` do so that a missing input fails the step with a clear message instead of a traceback?

<details>
<summary>Show answers</summary>

**1.** `INPUT_API_BASE_URL` and `INPUT_RETRY-COUNT`.

**2.**

```python
def size_label(changed_lines, thresholds):
    for label, limit in thresholds:
        if changed_lines <= limit:
            return label
    return "size/XXL" if changed_lines > 2000 else "size/XL"

default = parse_thresholds("XS=10,S=50,M=250,L=1000")
print(size_label(2500, default))
print(size_label(1200, default))
```

Output:

```
size/XXL
size/XL
```

**3.** (a) JavaScript, fast and has Octokit built in; (b) Docker, you control the image; (c) composite.

**4.** Catch the error, print a workflow error command and exit non-zero:

```python
import sys

def run_safely():
    try:
        main()
    except ValueError as err:
        print(f"::error::{err}")
        return 1
    return 0

os.environ.pop("INPUT_CHANGED-LINES", None)
print("exit code:", run_safely())
```

Output:

```
::error::Input required and not supplied: changed-lines
exit code: 1
```

In the real entrypoint you'd end with `sys.exit(run_safely())`.

</details>

---

## Real-World Examples

### Example 1: The Actions You Already Use

`actions/checkout`, `actions/setup-python` and `actions/cache` are all JavaScript actions with an `action.yml`, a `dist/index.js` and `post` steps (that's how `actions/cache` saves at the end of the job). Reading their `action.yml` is a great way to learn.

### Example 2: An Internal Deployment Notifier

A food delivery company wrote a small JavaScript action that posts deploy events to their internal incident tool with retries and a formatted Slack message. It's used in 60 repositories as `food-co/deploy-notify@v2`, and an API change in the incident tool was a single release.

### Example 3: A Python Data-Quality Gate

A data team's Docker action runs their in-house data-contract checker (Python with heavy dependencies) against changed SQL models and writes a Markdown table to the job summary. Using a prebuilt image on ghcr.io keeps start-up to a few seconds.

---

## Common Misconceptions

### Misconception 1: "The runner installs my action's npm dependencies"

It doesn't. Bundle them into `dist/` and commit it, or the action fails with "Cannot find module".

### Misconception 2: "Docker actions work everywhere"

Only on Linux runners. Use JavaScript or composite for cross-platform actions.

### Misconception 3: "Outputs are whatever I print"

Printing only writes to the log. Outputs must be written to `$GITHUB_OUTPUT` (or via `core.setOutput`).

### Misconception 4: "Moving a major tag is bad practice"

Moving **major** tags like `v1` is the expected convention. What you must never move is a full version tag like `v1.2.0`.

---

## Interview Relevance

Writing a custom action shows up in platform and DevOps interviews as "how would you share this automation?" or in take-home tasks:

- **Kinds and trade-offs:** JavaScript (fast, cross-platform), Docker (any language, Linux only), composite (glue).
- **The contract:** `action.yml` inputs, outputs, `runs`, branding.
- **Mechanics:** `INPUT_<NAME>` variables, `$GITHUB_OUTPUT`, `setFailed` and exit codes, bundling `dist/`.
- **Release discipline:** semver tags, moving major tags, immutable releases, documenting required permissions.

Common follow-ups:

- *"How do you test an action?"* Unit tests with mocked env vars, a self-test workflow using `uses: ./`, and a `dist/` freshness check.
- *"How does `actions/cache` save at the end of the job?"* A `post:` script in its `action.yml`.

---

## Key Takeaways

- **Three kinds:** JavaScript (`node24`), Docker (`docker`) and composite; pick by speed, language and platform.
- **`action.yml` is the contract**: inputs, outputs, `runs`, branding.
- **Inputs arrive as `INPUT_<NAME>` environment variables; outputs go to `$GITHUB_OUTPUT`.** That makes actions easy to unit-test.
- **JavaScript actions must ship bundled code in `dist/`**; Docker actions only run on Linux.
- **Publish with semver tags, move major tags, enable immutable releases**, and document the permissions your action needs.

---

**Up next:** [Lab: CI that tests and lints a Python project](lab-ci-that-tests-and-lints-a-python-project.md)
