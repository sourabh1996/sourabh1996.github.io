"""Renders the chart images that a lesson embeds, straight from the lesson's own code.

Chart lessons save every figure into a folder made with `tempfile.mkdtemp()`, so readers and
tools/check_code.py never write into the repo. This script runs a lesson's ```python blocks the
same way check_code.py does, but makes `tempfile.mkdtemp()` return
site/public/img/<course-slug>/, so the PNGs the lesson shows are exactly what its code draws.

Usage: python3 tools/render_lesson_images.py courses/<course>/<module>/<lesson>.md [...]
"""
import contextlib, io, os, sys, tempfile

os.environ["MPLBACKEND"] = "Agg"
import matplotlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_code import FENCE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def render(path):
    course = os.path.relpath(os.path.abspath(path), os.path.join(ROOT, "courses")).split(os.sep)[0]
    out = os.path.join(ROOT, "site", "public", "img", course)
    os.makedirs(out, exist_ok=True)
    matplotlib.rcdefaults()  # ignore any local matplotlibrc so images match a fresh install
    real_mkdtemp, tempfile.mkdtemp = tempfile.mkdtemp, lambda *a, **k: out
    try:
        ns = {"__name__": "__main__"}
        for m in FENCE.finditer(open(path).read()):
            if m.group(1) == "python" and not m.group(2).lstrip().startswith("# not-run"):
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(compile(m.group(2), path, "exec"), ns)
    finally:
        tempfile.mkdtemp = real_mkdtemp
        import matplotlib.pyplot as plt
        plt.close("all")
    for name in sorted(f for f in os.listdir(out) if f.endswith(".png")):
        size = os.path.getsize(os.path.join(out, name)) // 1024
        if size > 120:
            print(f"  warning: {name} is {size} KB")
    print(f"rendered {os.path.relpath(path, ROOT)} -> {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        render(p)
