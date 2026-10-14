"""Moves written lessons after the catalog is restructured, and rewrites links between them.

When build_catalog.py merges, splits or reorders courses and modules, lesson files written under the old layout
must move to the new one. This script compares an old catalog.json with the current build_catalog.py, then:

- moves every written lesson to courses/<new-course>/<NN-new-module>/<lesson>.md (matched by lesson title),
- keeps one "How This Course Works" per new course (from the old course that contributes its first module) and
  deletes the others,
- rewrites every relative .md link in every lesson, including course.md#mN module anchors.

Run from the repository root of a branch written against the old layout, after merging main:
    python3 tools/migrate_lessons.py tools/restructure/catalog-2026-10-11.json origin/main
The second argument limits the work to files the branch added or changed, so lessons already in the new layout
are left alone.
Then run python3 build_catalog.py . as usual. Running it twice is harmless.
"""
import json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = "How This Course Works"
# Old modules whose lessons were all dropped as duplicates: (old course slug, old module number) -> new home.
DROPPED_MODULES = {
    ("enterprise-llm-systems", 6): ("agent-security-and-safety", 2),  # Guardrails and Security
}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def layout(catalog):
    """lesson title -> (course slug, module dir), course slug -> [module dirs], plus start-here per course."""
    where, mods = {}, {}
    for c in catalog:
        mods[c["slug"]] = []
        for i, m in enumerate(c["modules"], 1):
            d = f"{i:02d}-{slug(m['title'])}"
            mods[c["slug"]].append(d)
            for l in m["lessons"]:
                if l["title"] != START:
                    where[l["title"]] = (c["slug"], d)
    return where, mods


def changed_since(base):
    out = subprocess.run(["git", "-C", ROOT, "diff", "--name-only", base, "--", "courses"], check=True,
                         capture_output=True, text=True).stdout.split()
    out += subprocess.run(["git", "-C", ROOT, "ls-files", "--others", "--exclude-standard", "courses"], check=True,
                          capture_output=True, text=True).stdout.split()
    return set(out)


def main(old_path, base=None):
    only = changed_since(base) if base else None
    old = json.load(open(old_path))
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, os.path.join(ROOT, "build_catalog.py"), tmp], check=True, stdout=subprocess.DEVNULL)
        new = json.load(open(os.path.join(tmp, "catalog.json")))
    new_where, new_mods = layout(new)
    old_slugs = {c["slug"] for c in old}

    # Where each old module went: the new module that holds its first lesson.
    anchor, course_home, first_pos = {}, {}, {}
    for c in old:
        for i, m in enumerate(c["modules"], 1):
            for l in m["lessons"]:
                if l["title"] in new_where:
                    ns, nd = new_where[l["title"]]
                    anchor[(c["slug"], i)] = (ns, int(nd[:2]))
                    if c["slug"] not in course_home:
                        course_home[c["slug"]] = ns
                        first_pos[c["slug"]] = int(nd[:2])
                    break
    anchor.update({k: v for k, v in DROPPED_MODULES.items() if k not in anchor})
    for c in old:  # a course whose lessons were all dropped falls back to itself
        course_home.setdefault(c["slug"], c["slug"])
    # The old course that contributes the earliest module keeps its "How This Course Works".
    primary = {}
    for s_ in sorted(course_home, key=lambda x: first_pos.get(x, 99)):
        primary.setdefault(course_home[s_], s_)

    # Old file path -> new file path (None means delete).
    moves = {}
    title_of = {(c["slug"], slug(l["title"])): l["title"] for c in old for m in c["modules"] for l in m["lessons"]}
    for c in old:
        base = os.path.join(ROOT, "courses", c["slug"])
        if not os.path.isdir(base):
            continue
        for dp, _, files in os.walk(base):
            for f in files:
                if not f.endswith(".md") or f == "course.md":
                    continue
                src = os.path.relpath(os.path.join(dp, f), ROOT)
                title = title_of.get((c["slug"], f[:-3]))
                if title == START:
                    ns = course_home[c["slug"]]
                    dst = f"courses/{ns}/{new_mods[ns][0]}/{f}" if primary.get(ns) == c["slug"] else None
                elif title in new_where:
                    ns, nd = new_where[title]
                    dst = f"courses/{ns}/{nd}/{f}"
                else:
                    dst = None
                    if title is None:
                        continue  # not a lesson of the old catalog (already migrated)
                moves[src] = dst

    def new_target(target_abs, frag):
        rel = os.path.relpath(target_abs, ROOT)
        if rel in moves:
            return moves[rel], frag
        parts = rel.split(os.sep)
        if len(parts) == 3 and parts[0] == "courses" and parts[2] == "course.md" and parts[1] in old_slugs:
            s = parts[1]
            m = re.fullmatch(r"#m(\d+)", frag or "")
            if m and (s, int(m.group(1))) in anchor:
                ns, j = anchor[(s, int(m.group(1)))]
                return f"courses/{ns}/course.md", f"#m{j}"
            return f"courses/{course_home[s]}/course.md", frag
        return rel, frag

    link = re.compile(r"\]\(([^)#\s:]+\.md)(#[^)\s]*)?\)")
    all_files = []
    for dp, _, files in os.walk(os.path.join(ROOT, "courses")):
        all_files += [os.path.relpath(os.path.join(dp, f), ROOT) for f in files if f.endswith(".md") and f != "course.md"]
    for src in all_files:
        if only is not None and src not in only:
            continue  # already in the new layout
        dst = moves.get(src, src)
        if dst is None:
            continue
        text = open(os.path.join(ROOT, src)).read()

        def fix(mt):
            target, frag = mt.group(1), mt.group(2) or ""
            t_abs = os.path.normpath(os.path.join(ROOT, os.path.dirname(src), target))
            nt, nf = new_target(t_abs, frag)
            if nt is None:  # linked lesson was dropped: point at its course page instead
                nt = f"courses/{course_home.get(os.path.relpath(t_abs, ROOT).split(os.sep)[1], '')}/course.md"
            return f"]({os.path.relpath(os.path.join(ROOT, nt), os.path.dirname(os.path.join(ROOT, dst)))}{nf})"

        new_text = link.sub(fix, text)
        if dst != src:
            os.makedirs(os.path.dirname(os.path.join(ROOT, dst)), exist_ok=True)
            open(os.path.join(ROOT, dst), "w").write(new_text)
            os.remove(os.path.join(ROOT, src))
            print("moved  ", src, "->", dst)
        elif new_text != text:
            open(os.path.join(ROOT, src), "w").write(new_text)
    for src, dst in moves.items():
        if dst is None and os.path.exists(os.path.join(ROOT, src)):
            os.remove(os.path.join(ROOT, src))
            print("deleted", src, "(lesson no longer in the catalog)")
    # Remove emptied folders and generated pages of courses that no longer exist.
    new_slugs = {c["slug"] for c in new}
    for s in old_slugs - new_slugs:
        p = os.path.join(ROOT, "courses", s)
        if os.path.isdir(p):
            for dp, dirs, files in os.walk(p, topdown=False):
                for f in files:
                    if f == "course.md":
                        os.remove(os.path.join(dp, f))
                if not os.listdir(dp):
                    os.rmdir(dp)
    for dp, dirs, files in os.walk(os.path.join(ROOT, "courses"), topdown=False):
        if not os.listdir(dp):
            os.rmdir(dp)
    fix_front_matter(new, None if only is None else {moves.get(f) or f for f in only})


def fix_front_matter(new, only=None):
    """Set each lesson's course: and module: lines to where the lesson now lives."""
    info = {}
    for c in new:
        for i, m in enumerate(c["modules"], 1):
            info[(c["slug"], f"{i:02d}-{slug(m['title'])}")] = (c["title"], f"{i}. {m['title']}")
    for (cs, md), (ct, mt) in info.items():
        d = os.path.join(ROOT, "courses", cs, md)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            p = os.path.join(d, f)
            if only is not None and os.path.relpath(p, ROOT) not in only:
                continue
            text = open(p).read()
            if not text.startswith("---\n"):
                continue
            head, rest = text[4:].split("\n---\n", 1)
            head = re.sub(r"(?m)^course: .*$", lambda _: "course: " + json.dumps(ct, ensure_ascii=False), head)
            head = re.sub(r"(?m)^module: .*$", lambda _: "module: " + json.dumps(mt, ensure_ascii=False), head)
            new_text = "---\n" + head + "\n---\n" + rest
            if new_text != text:
                open(p, "w").write(new_text)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
