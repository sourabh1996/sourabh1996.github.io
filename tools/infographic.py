"""Draws picture-style explainer diagrams (SVG) from small Python specs.

Each spec lives in diagrams/<course-slug>/<name>.py and defines SPEC, a dict:

    SPEC = {
        "title": "LLM, RAG, Agent and Agentic AI",
        "width": 1000, "height": 640,
        "bands": [   # optional horizontal panels with a coloured label tile on the left
            {"y": 70, "h": 130, "label": "LLM", "color": "blue"},
        ],
        "groups": [  # optional dashed boxes around related nodes
            {"x": 300, "y": 400, "w": 400, "h": 160, "label": "Agentic system", "color": "purple"},
        ],
        "nodes": {   # id -> box; x/y is the top-left corner
            "prompt": {"x": 160, "y": 95, "w": 150, "h": 80, "icon": "💬", "label": "Prompt",
                        "sub": "plus context", "color": "blue", "style": "plain"},
        },
        "edges": [   # from, to, optional label; side picks the connection point (auto by default)
            {"from": "prompt", "to": "llm", "label": "tokens in"},
            {"from": "observe", "to": "decide", "label": "repeat", "via": [(880, 230), (520, 230)]},
        ],
        "notes": [{"x": 500, "y": 620, "text": "Grounded, but not guaranteed correct"}],
    }

Run:  python3 tools/infographic.py            (renders every spec)
      python3 tools/infographic.py diagrams/agentic-ai-fundamentals/llm-rag-agent-agentic.py
Output goes to site/public/img/diagrams/<course-slug>/<name>.svg; lessons embed it with
![Alt text](/img/diagrams/<course-slug>/<name>.svg).
"""
import glob, html, os, runpy, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# fill, stroke, strong (label tiles and headings)
PALETTE = {
    "blue":   ("#e8f0fe", "#7aa2f7", "#2f5fb3"),
    "green":  ("#e6f4ea", "#7cc49a", "#2e7d4f"),
    "amber":  ("#fdf1dc", "#e0b25c", "#9a6412"),
    "purple": ("#efe9fb", "#a68be0", "#5b3fa0"),
    "teal":   ("#e2f5f3", "#6cc3b8", "#1f766d"),
    "coral":  ("#fde8e4", "#ec9a8a", "#b2442f"),
    "gray":   ("#f1f3f5", "#b8bec6", "#4b5563"),
    "pink":   ("#fbe9f2", "#e597bd", "#a3336b"),
}
FONT = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
INK, INK2, LINE = "#1f2328", "#57606a", "#8c959f"


def esc(s):
    return html.escape(str(s), quote=True)


def text_lines(x, y, lines, size, weight=400, color=INK, anchor="middle", gap=1.25):
    out = []
    for i, line in enumerate(lines):
        out.append(f'<text x="{x}" y="{y + i * size * gap:.1f}" font-size="{size}" font-weight="{weight}" '
                   f'fill="{color}" text-anchor="{anchor}">{esc(line)}</text>')
    return "".join(out)


def anchor_point(n, side):
    x, y, w, h = n["x"], n["y"], n["w"], n["h"]
    return {"left": (x, y + h / 2), "right": (x + w, y + h / 2),
            "top": (x + w / 2, y), "bottom": (x + w / 2, y + h)}[side]


def auto_sides(a, b):
    ax, ay = a["x"] + a["w"] / 2, a["y"] + a["h"] / 2
    bx, by = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
    dx, dy = bx - ax, by - ay
    if abs(dx) * 0.6 >= abs(dy):
        return ("right", "left") if dx > 0 else ("left", "right")
    return ("bottom", "top") if dy > 0 else ("top", "bottom")


def render(spec):
    W, H = spec.get("width", 1000), spec.get("height", 600)
    nodes = spec.get("nodes", {})
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'font-family="{FONT}" role="img" aria-label="{esc(spec.get("title", "diagram"))}">',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
           f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker></defs>',
           f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="#ffffff" stroke="#d0d7de" stroke-width="2"/>']
    top = 20
    if spec.get("title"):
        out.append(f'<rect x="28" y="22" width="8" height="34" rx="4" fill="{PALETTE[spec.get("accent", "teal")][2]}"/>')
        out.append(text_lines(48, 48, [spec["title"]], 26, 800, INK, "start"))
        top = 70
    for b in spec.get("bands", []):
        fill, stroke, strong = PALETTE[b.get("color", "gray")]
        x, w = b.get("x", 20), b.get("w", W - 40)
        out.append(f'<rect x="{x}" y="{b["y"]}" width="{w}" height="{b["h"]}" rx="14" fill="#fbfcfd" stroke="#d0d7de" stroke-width="1.5"/>')
        tile = b.get("tile", 110)
        out.append(f'<rect x="{x + 10}" y="{b["y"] + 10}" width="{tile}" height="{b["h"] - 20}" rx="10" fill="{strong}"/>')
        lines = b["label"].split("\n")
        cy = b["y"] + b["h"] / 2 - (len(lines) - 1) * 12 + 8
        out.append(text_lines(x + 10 + tile / 2, cy, lines, 22, 700, "#ffffff"))
    for g in spec.get("groups", []):
        fill, stroke, strong = PALETTE[g.get("color", "gray")]
        out.append(f'<rect x="{g["x"]}" y="{g["y"]}" width="{g["w"]}" height="{g["h"]}" rx="14" fill="none" '
                   f'stroke="{stroke}" stroke-width="2" stroke-dasharray="7 6"/>')
        if g.get("label"):
            lw = 14 + 8.6 * len(g["label"])
            out.append(f'<rect x="{g["x"] + g["w"] / 2 - lw / 2}" y="{g["y"] - 15}" width="{lw}" height="30" rx="15" fill="{strong}"/>')
            out.append(text_lines(g["x"] + g["w"] / 2, g["y"] + 5, [g["label"]], 14, 700, "#ffffff"))
    # edges under nodes
    for e in spec.get("edges", []):
        a, b = nodes[e["from"]], nodes[e["to"]]
        sa, sb = auto_sides(a, b)
        p1 = anchor_point(a, e.get("from_side", sa))
        p2 = anchor_point(b, e.get("to_side", sb))
        pts = [p1, *e.get("via", []), p2]
        d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        dash = "" if e.get("solid") else ' stroke-dasharray="6 5"'
        both = ' marker-start="url(#arrow)"' if e.get("both") else ""
        out.append(f'<path d="{d}" fill="none" stroke="{LINE}" stroke-width="2"{dash} marker-end="url(#arrow)"{both}/>')
        if e.get("label"):
            if "label_at" in e:
                lx, ly = e["label_at"]
            else:
                i = (len(pts) - 1) // 2
                (x1, y1), (x2, y2) = pts[i], pts[i + 1]
                lx, ly = (x1 + x2) / 2, (y1 + y2) / 2 - 9
            lines = e["label"].split("\n")
            wbox = 8 + 7 * max(len(l) for l in lines)
            out.append(f'<rect x="{lx - wbox / 2:.1f}" y="{ly - 14:.1f}" width="{wbox:.1f}" height="{18 * len(lines)}" rx="4" fill="#ffffff" opacity="0.92"/>')
            out.append(text_lines(lx, ly, lines, 13, 500, INK2, gap=1.35))
    for nid, n in nodes.items():
        fill, stroke, strong = PALETTE[n.get("color", "gray")]
        x, y, w, h = n["x"], n["y"], n["w"], n["h"]
        style = n.get("style", "card")
        if style != "plain":
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        lines = n.get("label", "").split("\n")
        sub = n.get("sub", "").split("\n") if n.get("sub") else []
        icon = n.get("icon")
        block = (34 if icon else 0) + 20 * len(lines) + 16 * len(sub)
        cy = y + (h - block) / 2
        if icon:
            out.append(f'<text x="{x + w / 2}" y="{cy + 28}" font-size="28" text-anchor="middle">{esc(icon)}</text>')
            cy += 36
        out.append(text_lines(x + w / 2, cy + 15, lines, n.get("size", 16), 700, strong if style == "plain" else INK))
        if sub:
            out.append(text_lines(x + w / 2, cy + 15 + 20 * len(lines), sub, 12.5, 400, INK2))
    for t in spec.get("notes", []):
        out.append(text_lines(t["x"], t["y"], t["text"].split("\n"), t.get("size", 13), t.get("weight", 500),
                              t.get("color", INK2), t.get("anchor", "middle")))
    out.append("</svg>")
    return "\n".join(out)


def main():
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "diagrams", "*", "*.py")))
    for p in paths:
        spec = runpy.run_path(p)["SPEC"]
        course = os.path.basename(os.path.dirname(os.path.abspath(p)))
        name = os.path.splitext(os.path.basename(p))[0]
        dest = os.path.join(ROOT, "site", "public", "img", "diagrams", course, name + ".svg")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w") as f:
            f.write(render(spec))
        print("wrote", os.path.relpath(dest, ROOT))


if __name__ == "__main__":
    main()
