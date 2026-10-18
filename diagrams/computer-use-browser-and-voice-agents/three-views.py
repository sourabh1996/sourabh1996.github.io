# One web page, three ways an agent can perceive it, and what each costs and misses.
SPEC = {
    "title": "Three ways an agent can see a web page",
    "accent": "blue",
    "width": 1100, "height": 640,
    "nodes": {
        "page": {"x": 40, "y": 230, "w": 200, "h": 150, "icon": "🌐", "label": "The live page", "sub": "Sharma Kirana Store\nin Chromium", "color": "gray"},
        "dom": {"x": 330, "y": 95, "w": 330, "h": 140, "icon": "🧾", "label": "Raw HTML / DOM",
                 "sub": "every tag, class, script\nlargest: often 10k to 100k+ tokens\nfull detail, mostly noise", "color": "coral"},
        "ax": {"x": 330, "y": 255, "w": 330, "h": 140, "icon": "🌳", "label": "Accessibility tree",
                "sub": "role + name of what matters\nsmall: hundreds to a few k tokens\nmisses visual layout", "color": "green"},
        "shot": {"x": 330, "y": 415, "w": 330, "h": 140, "icon": "📸", "label": "Screenshot",
                  "sub": "exactly what a person sees\nfixed cost: ~1.3k tokens at 1280x800\nneeds coordinates to act", "color": "purple"},
        "dom_act": {"x": 740, "y": 110, "w": 320, "h": 110, "label": "Act by CSS selector", "sub": "#cart > button.add\nbreaks when markup changes", "color": "coral"},
        "ax_act": {"x": 740, "y": 270, "w": 320, "h": 110, "label": "Act by reference or role", "sub": "click e6 · button \"Add\"\nmost reliable for forms", "color": "green"},
        "shot_act": {"x": 740, "y": 430, "w": 320, "h": 110, "label": "Act by pixel coordinate", "sub": "click (246, 199)\nworks on anything you can see", "color": "purple"},
    },
    "edges": [
        {"from": "page", "to": "dom", "to_side": "left"},
        {"from": "page", "to": "ax", "to_side": "left"},
        {"from": "page", "to": "shot", "to_side": "left"},
        {"from": "dom", "to": "dom_act"},
        {"from": "ax", "to": "ax_act"},
        {"from": "shot", "to": "shot_act"},
    ],
    "notes": [
        {"x": 550, "y": 600, "text": "Most browser agents read the accessibility tree first and take a screenshot only when they need to see layout.", "size": 15, "weight": 700, "color": "#2f5fb3"},
    ],
}
