"""Runs the Python examples in written lessons and checks their printed output.

For each lesson, ```python blocks run in order in one shared namespace, like a reader
pasting them into one file. When a python block is followed by an "Output:" line and a
plain ``` block, the printed output must match it exactly.

A block whose first line starts with "# not-run" is skipped (use it for code that needs an
API key, network access or a package the course installs later).

Usage: python3 tools/check_code.py [lesson.md ...]   (default: every written lesson)
"""
import contextlib, glob, io, os, re, sys, traceback

FENCE = re.compile(r"^```(\w*)[^\n]*\n(.*?)^```\s*$", re.S | re.M)


def check(path):
    text = open(path).read()
    blocks = [(m.group(1), m.group(2), m.start(), m.end()) for m in FENCE.finditer(text)]
    ns = {"__name__": "__main__"}
    problems, ran = [], 0
    for i, (lang, code, _, end) in enumerate(blocks):
        if lang != "python" or code.lstrip().startswith("# not-run"):
            continue
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                exec(compile(code, f"{path}:block{i}", "exec"), ns)
        except Exception:
            problems.append(f"block {i} raised:\n{traceback.format_exc(limit=2)}")
            continue
        ran += 1
        if i + 1 < len(blocks):
            nlang, ncode, nstart, _ = blocks[i + 1]
            between = text[end:nstart].strip()
            if nlang == "" and between.lower().rstrip(":") == "output":
                if out.getvalue().rstrip() != ncode.rstrip():
                    problems.append(f"block {i} output differs.\n--- expected\n{ncode.rstrip()}\n--- got\n{out.getvalue().rstrip()}")
    return ran, problems


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = sys.argv[1:] or [f for f in glob.glob(os.path.join(root, "courses/*/*/*.md"))]
    failed = 0
    for f in sorted(files):
        ran, problems = check(f)
        status = "ok" if not problems else "FAIL"
        print(f"{status:4} {ran:2} block(s)  {os.path.relpath(f, root)}")
        for p in problems:
            print("     " + p.replace("\n", "\n     "))
        failed += bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
