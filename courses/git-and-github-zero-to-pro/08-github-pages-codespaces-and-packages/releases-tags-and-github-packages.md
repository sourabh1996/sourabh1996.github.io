---
title: "Releases, Tags and GitHub Packages"
course: "Git and GitHub: Zero to Pro"
module: "8. GitHub Pages, Codespaces and Packages"
type: Article
level: Intermediate
reading_time: 25 min
---

# Releases, Tags and GitHub Packages: The Complete Guide

> 📚 **Before you start**
>
> - [Blobs, Trees, Commits and Tags](../course.md#m3) (How Git Works Inside), for lightweight versus annotated tags
> - [Triggers and Events](../07-github-actions/triggers-and-events.md), for tag and release triggers
> - [Secrets, Variables and Environments](../07-github-actions/secrets-variables-and-environments.md), for `GITHUB_TOKEN` permissions

## Introduction

A mithai shop doesn't sell "whatever's on the counter right now". It sells boxes: sealed, labelled with a date and a batch, with a list of what's inside. If a customer complains about Tuesday's kaju katli, the shop knows exactly which batch it was.

Software needs the same discipline. `main` changes every day; users need fixed, labelled versions they can install, report bugs against and roll back to. Git gives you **tags** to mark a commit as a version. GitHub builds **releases** on top of tags, with notes and downloadable files. And **GitHub Packages** hosts the built artifacts (container images, npm packages, Maven and NuGet packages) right next to the code that produced them.

By the end of this article you'll know how to tag versions properly, publish releases by hand and from a workflow, generate release notes automatically, publish a Docker image to GitHub Container Registry, use the other package registries, and make published versions trustworthy with immutable releases.

> 💡 **Key Insight**
>
> A **tag** names a commit; a **release** describes and packages it; a **package** is the installable thing built from it. Automate all three from one trigger (pushing a version tag), so every version is built the same way, from a known commit, with no "I built it on my laptop" in the story.

---

## Core Explanation

### 1. Tags: Naming a Commit

You met tags in [Blobs, Trees, Commits and Tags](../course.md#m3). For releases, always use **annotated** tags: they store who tagged, when, and a message, and can be signed.

```bash
git switch main && git pull
git tag -a v1.4.0 -m "v1.4.0: UPI QR codes on bills"
git push origin v1.4.0          # tags are NOT pushed by a plain git push
git tag --list "v1.*"
git show v1.4.0 --stat
```

Example output (`git tag --list "v1.*"`):

```
v1.2.0
v1.3.0
v1.3.1
v1.4.0
```

Conventions that tools expect:

- Prefix with `v` and use **semantic versioning**: `v<major>.<minor>.<patch>` (covered fully in [Maintaining a Project](../10-open-source-and-advanced-git/maintaining-a-project-templates-releases-and-semver.md)).
- **Never move or reuse a version tag.** Someone may already have built from it. If `v1.4.0` is broken, release `v1.4.1`.
- Pre-releases use suffixes: `v2.0.0-rc.1`, `v2.0.0-beta.2`.

### 2. Releases: Tags with Notes and Files

A GitHub **release** is attached to a tag and adds:

- A **title** and **release notes** in Markdown.
- **Assets**: downloadable files such as binaries, wheels, zip files and checksums. GitHub also adds the source code as zip and tar.gz automatically.
- Flags: **draft** (not public yet), **pre-release** (shown as not production-ready), and **latest** (the one shown on the repository's front page).

Create one from the web (**Releases → Draft a new release**) or from the terminal:

```bash
gh release create v1.4.0 dist/*.whl dist/*.tar.gz \
  --title "v1.4.0: UPI QR codes" \
  --generate-notes

gh release create v2.0.0-rc.1 --prerelease --generate-notes
gh release list
gh release download v1.4.0 --pattern "*.whl"
```

Example output (`gh release list`):

```
TITLE                TYPE         TAG NAME      PUBLISHED
v2.0.0-rc.1          Pre-release  v2.0.0-rc.1   about 1 minute ago
v1.4.0: UPI QR codes Latest       v1.4.0        about 3 minutes ago
v1.3.1                            v1.3.1        about 12 days ago
```

If the tag doesn't exist yet, `gh release create` creates it from the default branch's latest commit (or from `--target <branch-or-sha>`). Creating the tag yourself first is clearer.

### 3. Automatic Release Notes

`--generate-notes` (or the **Generate release notes** button) lists the pull requests merged since the previous release, with their authors and a list of new contributors. Group them with a `.github/release.yml` file:

```yaml
# .github/release.yml
changelog:
  exclude:
    labels:
      - ignore-for-release
    authors:
      - octocat
  categories:
    - title: Breaking changes
      labels: [breaking]
    - title: New features
      labels: [feature, enhancement]
    - title: Bug fixes
      labels: [bug]
    - title: Other changes
      labels: ["*"]
```

Each pull request lands in the **first** category whose labels it matches; `"*"` catches everything left. Here is that logic in Python, to make the rules concrete:

```python
release_config = {
    "exclude_labels": ["ignore-for-release"],
    "categories": [
        {"title": "Breaking changes", "labels": ["breaking"]},
        {"title": "New features", "labels": ["feature", "enhancement"]},
        {"title": "Bug fixes", "labels": ["bug"]},
        {"title": "Other changes", "labels": ["*"]},
    ],
}

merged_prs = [
    {"number": 41, "title": "Add UPI QR code on the bill", "author": "meera", "labels": ["feature"]},
    {"number": 42, "title": "Fix rounding when splitting among 7", "author": "ravi", "labels": ["bug"]},
    {"number": 43, "title": "Bump pytest from 8.3 to 8.4", "author": "dependabot", "labels": ["dependencies"]},
    {"number": 44, "title": "Rename split() to split_bill()", "author": "meera", "labels": ["breaking"]},
    {"number": 45, "title": "Typo in README", "author": "anil", "labels": ["ignore-for-release"]},
]

def release_notes(prs, config, tag):
    lines = [f"## What's changed in {tag}"]
    remaining = [p for p in prs if not set(p["labels"]) & set(config["exclude_labels"])]
    for category in config["categories"]:
        wanted = set(category["labels"])
        picked = [p for p in remaining if "*" in wanted or set(p["labels"]) & wanted]
        if picked:
            lines.append(f"### {category['title']}")
            lines += [f"* {p['title']} by @{p['author']} in #{p['number']}" for p in picked]
            remaining = [p for p in remaining if p not in picked]
    return "\n".join(lines)

print(release_notes(merged_prs, release_config, "v2.0.0"))
```

Output:

```
## What's changed in v2.0.0
### Breaking changes
* Rename split() to split_bill() by @meera in #44
### New features
* Add UPI QR code on the bill by @meera in #41
### Bug fixes
* Fix rounding when splitting among 7 by @ravi in #42
### Other changes
* Bump pytest from 8.3 to 8.4 by @dependabot in #43
```

The lesson for teams: **good release notes start with good pull request titles and labels.** Nobody writes the changelog at release time; it's collected as you go.

### 4. Releasing from a Workflow

Doing releases by hand invites mistakes: building from the wrong branch, forgetting an asset. Trigger on a version tag and let Actions do it:

```yaml
name: Release

on:
  push:
    tags: ["v*.*.*"]

permissions:
  contents: write      # create the release and upload assets

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.13"
      - name: Build wheel and sdist
        run: |
          python -m pip install build
          python -m build
      - name: Checksums
        run: cd dist && sha256sum * > SHA256SUMS.txt
      - name: Create the GitHub release
        env:
          GH_TOKEN: ${{ github.token }}
          TAG: ${{ github.ref_name }}
        run: |
          flags="--generate-notes --verify-tag"
          if [[ "$TAG" == *-* ]]; then flags="$flags --prerelease"; fi
          gh release create "$TAG" dist/* $flags
```

Notes:

- `--verify-tag` makes `gh` fail rather than create a tag, so the release always matches the tag that triggered the run.
- A hyphen in the tag (`v2.0.0-rc.1`) marks it as a pre-release.
- `contents: write` is needed to create releases. Keep other permissions off.
- The `gh` CLI is preinstalled on GitHub-hosted runners. Marketplace actions such as `softprops/action-gh-release` do the same job if you prefer YAML inputs.

**The release event.** Publishing a release fires the `release` event, so you can split work: one workflow creates the release, another listens to `release: types: [published]` and publishes packages.

### 5. Immutable Releases

A release whose tag or assets can be swapped after publishing is a supply-chain risk: an attacker who gets write access could replace `v1.4.0`'s wheel with a malicious one, and everyone pinned to `v1.4.0` would download it. Turn on **immutable releases** in the repository (or organization) settings. Once a release is published:

- Its **tag can't be moved or deleted**.
- Its **assets can't be added, changed or removed**.
- GitHub records a **release attestation**, so users can verify that what they downloaded is what was published.

Drafts stay editable, so the usual pattern is: create a **draft**, upload all assets, then publish. With immutability on, fix mistakes by publishing a new version.

### 6. GitHub Packages: Registries Next to Your Code

**GitHub Packages** hosts built packages and links them to the repository that published them. It supports:

| Registry | Host | Typical client |
|---|---|---|
| **Container registry** | `ghcr.io` | `docker`, `podman` |
| npm | `npm.pkg.github.com` | `npm` |
| Maven / Gradle | `maven.pkg.github.com` | `mvn`, `gradle` |
| NuGet | `nuget.pkg.github.com` | `dotnet` |
| RubyGems | `rubygems.pkg.github.com` | `gem` |

There is **no Python registry** in GitHub Packages. Python packages are published to PyPI (with trusted publishing, as in the [OIDC lesson](../07-github-actions/oidc-deploying-to-the-cloud-without-stored-keys.md)), or to a private index elsewhere, and attached as release assets.

Public packages are free. Private packages use your account's included storage and data-transfer allowance; downloads from inside GitHub Actions using `GITHUB_TOKEN` don't count toward data transfer.

### 7. Publishing a Container Image to `ghcr.io`

This is the most common use of GitHub Packages. The workflow logs in with `GITHUB_TOKEN`, computes tags from the Git ref, builds and pushes:

```yaml
name: Publish image

on:
  push:
    branches: [main]
    tags: ["v*.*.*"]

permissions:
  contents: read
  packages: write       # push to ghcr.io

env:
  IMAGE: ghcr.io/${{ github.repository }}

jobs:
  image:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - uses: docker/login-action@v4
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - id: meta
        uses: docker/metadata-action@v6
        with:
          images: ${{ env.IMAGE }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=ref,event=branch
            type=sha

      - uses: docker/setup-buildx-action@v4

      - id: push
        uses: docker/build-push-action@v7
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

What you get for tag `v1.4.0`:

Example output:

```
ghcr.io/chai-co/orders-api:1.4.0
ghcr.io/chai-co/orders-api:1.4
ghcr.io/chai-co/orders-api:sha-4c1d2e9
```

And on every push to `main`, `ghcr.io/chai-co/orders-api:main`. Key details:

- **Image names must be lowercase.** `github.repository` keeps the owner's case, so if your username has capitals, lowercase it in a step first.
- The metadata action adds the OCI label `org.opencontainers.image.source` pointing at the repository, which **links the package to the repo** so it appears on the repository page and can inherit its access settings.
- `cache-from`/`cache-to: type=gha` stores Docker layer cache in the Actions cache, so unchanged layers aren't rebuilt.
- A new package is **private** by default. Change visibility under the package's **Package settings** if it should be public.
- The `digest` output of the push step (`steps.push.outputs.digest`) is the image's immutable `sha256:` fingerprint. Deploy by digest when you need certainty, and attest it as shown in [Signed Commits and Artifact Attestations](../09-security-and-supply-chain/signed-commits-and-artifact-attestations.md).

Pulling it:

```bash
docker pull ghcr.io/chai-co/orders-api:1.4.0
# private packages need a login first:
echo "$GITHUB_PAT" | docker login ghcr.io -u YOUR-USERNAME --password-stdin
```

For local logins, use a personal access token with the `read:packages` scope (or `write:packages` to push). Inside Actions, `GITHUB_TOKEN` is enough.

### 8. Publishing an npm Package to GitHub Packages

npm packages on GitHub must be **scoped** to the owner (`@chai-co/ui-kit`). In `package.json`, set `"name": "@chai-co/ui-kit"` and add `"publishConfig": { "registry": "https://npm.pkg.github.com" }`. Then:

```yaml
on:
  release:
    types: [published]

permissions:
  contents: read
  packages: write

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version: 22
          registry-url: https://npm.pkg.github.com
          scope: "@chai-co"
      - run: npm ci
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Consumers add one line to their `.npmrc`: `@chai-co:registry=https://npm.pkg.github.com`, plus a token if the package is private.

### 9. Managing Packages

- **Access:** a package can inherit access from its linked repository, or have its own list of users, teams and repositories. For a private image used by a workflow in **another** repository, give that repository read access in the package settings.
- **Deleting versions:** possible from the package page, but a public version with downloads should rarely be deleted; publish a fix instead.
- **Cleaning up:** CI images tagged per commit pile up fast. Schedule a workflow that deletes old untagged versions via the API, or use a cleanup action.

---

## Try It Yourself

1. **Tag and push.** Write the commands to create an annotated tag `v0.3.0` on the current commit and push only that tag.
2. **Categorise.** Add a PR `{"number": 46, "title": "Add Hindi menu", "author": "priya", "labels": ["enhancement", "i18n"]}` to `merged_prs` and regenerate the notes. Which section is it in?
3. **Pre-release.** Your release workflow ran for `v3.0.0-beta.1`. Will it be marked as a pre-release? Why?
4. **Fix the push.** A workflow fails to push `ghcr.io/Chai-Co/orders-api:main` with an error about an invalid reference. Why, and what's the fix?

<details>
<summary>Show answers</summary>

**1.**

```bash
git tag -a v0.3.0 -m "v0.3.0"
git push origin v0.3.0
```

**2.** Under "New features", because `enhancement` matches that category before the `"*"` catch-all.

```python
merged_prs.append({"number": 46, "title": "Add Hindi menu", "author": "priya", "labels": ["enhancement", "i18n"]})
print(release_notes(merged_prs, release_config, "v2.1.0").split("### Bug fixes")[0])
```

Output:

```
## What's changed in v2.1.0
### Breaking changes
* Rename split() to split_bill() by @meera in #44
### New features
* Add UPI QR code on the bill by @meera in #41
* Add Hindi menu by @priya in #46

```

**3.** Yes. The tag contains a hyphen, so the script adds `--prerelease`.

**4.** Image references must be lowercase. Lowercase the name before using it, for example with a step `echo "IMAGE=${GITHUB_REPOSITORY,,}" >> "$GITHUB_ENV"` and then `ghcr.io/${{ env.IMAGE }}`. (`docker/metadata-action` also lowercases the image names it outputs.)

</details>

---

## Real-World Examples

### Example 1: A CLI Tool's Downloads

A Go command-line tool's release workflow builds binaries for Linux, macOS and Windows in a matrix, uploads them with a `SHA256SUMS.txt` to a draft release, then publishes it. Users download from the Releases page or with `gh release download`, and verify checksums.

### Example 2: Microservices on ghcr.io

A logistics company's services each publish images to `ghcr.io/<org>/<service>` on every merge (tagged `main` and `sha-...`) and on version tags. Kubernetes deploys by digest, and package access is inherited from each repository, so only the owning team can push.

### Example 3: An Internal Design System

A company publishes `@company/ui-kit` to GitHub's npm registry. Every web team installs it with their GitHub credentials, and access follows organization membership, with no separate npm accounts to manage.

---

## Common Misconceptions

### Misconception 1: "`git push` pushes my tags"

It doesn't. Push a tag explicitly (`git push origin v1.4.0`), or use `git push --follow-tags` for annotated tags reachable from the pushed commits.

### Misconception 2: "A release is just a tag"

A tag is a Git ref. A release is a GitHub object on top of it, with notes, assets, flags and (when immutable) protections.

### Misconception 3: "I can publish my Python package to GitHub Packages"

GitHub Packages has no Python registry. Use PyPI (ideally with trusted publishing) or another index, and attach wheels to releases if you like.

### Misconception 4: "Re-tagging a fixed build with the same version is fine"

Anyone who already pulled the old one now has a different artifact under the same name. Bump the version instead, and turn on immutable releases.

---

## Interview Relevance

Release engineering questions come up in DevOps, backend and open source contexts:

- **Tagging:** annotated, semantic versions, never moved.
- **Automation:** tag-triggered workflows that build, checksum and publish with least-privilege permissions; pre-release detection.
- **Release notes:** generated from labelled pull requests via `.github/release.yml`.
- **Containers:** ghcr.io with `GITHUB_TOKEN` and `packages: write`, metadata-driven tags, digests, lowercase names, cache.
- **Integrity:** immutable releases, checksums, attestations.

Common follow-ups:

- *"How do you roll back a bad release?"* Deploy the previous version (by tag or digest) and ship a fixed patch release; don't rewrite the bad one.
- *"Why deploy by digest?"* Tags can move; a digest always identifies exactly one image.

---

## Key Takeaways

- **Annotated, semver tags** (`v1.4.0`) mark versions; push them explicitly and never move them.
- **Releases** add notes, assets and flags; **`--generate-notes` plus `.github/release.yml`** turns labelled PRs into a changelog.
- **Automate releases from a tag push** with `contents: write`, and turn on **immutable releases**.
- **GitHub Packages** hosts containers (ghcr.io), npm, Maven/Gradle, NuGet and RubyGems, but not Python.
- **Publish images with `GITHUB_TOKEN` and `packages: write`**, lowercase names, OCI source labels, layer caching and digests.

---

**Up next:** [Lab: Deploy a static site with Actions](lab-deploy-a-static-site-with-actions.md)
