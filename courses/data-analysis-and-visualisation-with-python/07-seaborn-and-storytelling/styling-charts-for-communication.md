---
title: "Styling Charts for Communication"
course: "Data Analysis and Visualisation with Python"
module: "7. Seaborn and Storytelling"
type: Article
level: Beginner
reading_time: 26 min
---

# Styling Charts for Communication: The Complete Guide

> 📚 **Before you start**
>
> - [Creating and Customising Plots](../06-matplotlib/creating-and-customising-plots.md), for annotations, tick formatters and `axhline`
> - [Statistical Plots with Seaborn](statistical-plots-with-seaborn.md), for `hue` and how Seaborn picks colours
> - [Histograms, Pair Plots and Heatmaps](histograms-pair-plots-and-heatmaps.md), for sequential and diverging colour maps

## Introduction

Two analysts present the same quarterly numbers to their manager. The first shows a chart titled "Sales by region" with eight rainbow-coloured bars in alphabetical order, a legend in a box, a heavy grid and tick labels rotated 45 degrees. The manager squints and asks, "So... what am I looking at?" The second shows the same eight bars sorted, all grey except one in blue, a title that reads "The East region fell 18% while every other region grew", and the value written at the end of each bar. The manager says "Why did East fall?" and the meeting moves on to the real conversation.

Same data, same chart type. The difference is **design for communication**: deciding what the reader should take away and then making every visual choice serve that. This lesson teaches that as a set of concrete techniques: Seaborn themes and contexts, choosing colour palettes (including for colour-blind readers), decluttering, highlighting, direct labelling, honest scales and reusable style files.

By the end you'll be able to take any default chart and turn it into one a busy person understands in five seconds.

> 💡 **Key Insight**
>
> Decide the **one sentence** the chart should say before you style anything. Then put that sentence in the title, make the data that proves it the most prominent thing on the page, and push everything else (grid, axes, other series) into the background.

---

## Core Explanation

### 1. Exploratory vs explanatory charts

You draw two kinds of chart:

| | Exploratory | Explanatory |
|---|---|---|
| Audience | You | Someone else |
| Goal | Find something | Show what you found |
| Number | Dozens, fast | One or two, careful |
| Styling | Defaults are fine | Every element earns its place |
| Title | "rent vs area" | "Bigger flats cost more, but metro distance barely matters" |

Everything in this lesson is about explanatory charts. Don't spend time polishing exploratory ones.

```python
import os
import tempfile

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

out_dir = tempfile.mkdtemp()
rng = np.random.default_rng(8)
```

### 2. Seaborn themes: style and context

`sns.set_theme()` changes Matplotlib's defaults (it sets `rcParams`) for every chart that follows. It has three main arguments:

- **`style`**: the background and grid: `"darkgrid"` (default), `"whitegrid"`, `"dark"`, `"white"`, `"ticks"`.
- **`context`**: the scale of text and lines for where the chart will be seen: `"paper"`, `"notebook"` (default), `"talk"`, `"poster"`.
- **`palette`**: the default colour cycle.

To compare styles side by side, `sns.axes_style(...)` works as a context manager that applies a style only to Axes created inside it:

```python
values = [23, 17, 35, 29]
labels = ["A", "B", "C", "D"]
styles = ["darkgrid", "whitegrid", "dark", "white", "ticks"]

fig = plt.figure(figsize=(14, 2.8), layout="constrained")
for i, style in enumerate(styles, start=1):
    with sns.axes_style(style):
        ax = fig.add_subplot(1, len(styles), i)
        ax.bar(labels, values, color="#4C72B0")
        ax.set_title(f'"{style}"')
fig.savefig(os.path.join(out_dir, "styles.png"), bbox_inches="tight")
plt.close(fig)
print(sns.axes_style("whitegrid")["axes.facecolor"], sns.axes_style("darkgrid")["axes.facecolor"])
```

Output:

```
white #EAEAF2
```

![The same small bar chart drawn in five Seaborn styles: darkgrid with grey background, whitegrid, dark, white and ticks](/img/data-visualization-with-matplotlib-and-seaborn/styles.png)

For explanatory charts, **`"whitegrid"`** (when readers need to read values off the axis) and **`"white"`** or **`"ticks"`** (when values are labelled directly) are the usual choices. The grey `darkgrid` is pleasant for exploration but makes printed charts look heavy.

The context scales fonts and line widths together:

```python
for context in ["paper", "notebook", "talk", "poster"]:
    rc = sns.plotting_context(context)
    print(f"{context:<9} font.size={rc['font.size']:<5g} lines.linewidth={rc['lines.linewidth']:g}")
```

Output:

```
paper     font.size=9.6   lines.linewidth=1.2
notebook  font.size=12    lines.linewidth=1.5
talk      font.size=18    lines.linewidth=2.25
poster    font.size=24    lines.linewidth=3
```

Use **`"talk"`** for slides: a chart that looks fine on your laptop is unreadable from the back of a meeting room. Add `font_scale=1.2` to fine-tune. Your final call usually looks like this:

```python
sns.set_theme(style="whitegrid", context="notebook", palette="colorblind")
print(mpl.rcParams["axes.facecolor"], mpl.rcParams["axes.grid"])
```

Output:

```
white True
```

`sns.reset_defaults()` undoes everything if you need Matplotlib's original look back.

### 3. Colour has three jobs

Pick a palette by what the colour *means*:

| Job | Data | Palette type | Seaborn examples |
|---|---|---|---|
| **Tell groups apart** | Categories with no order (cities, products) | Qualitative | `"colorblind"`, `"deep"`, `"Set2"`, `"tab10"` |
| **Show amount** | Low to high (counts, rent, delay) | Sequential | `"rocket"`, `"mako"`, `"viridis"`, `"Blues"` |
| **Show direction from a midpoint** | Negative to positive (change, correlation) | Diverging | `"vlag"`, `"icefire"`, `"coolwarm"` |

```python
palettes = {
    "colorblind (qualitative)": sns.color_palette("colorblind", 8),
    "mako (sequential)": sns.color_palette("mako", 8),
    "vlag (diverging)": sns.color_palette("vlag", 8),
}
fig, axes = plt.subplots(len(palettes), 1, figsize=(8, 2.6), layout="constrained")
for ax, (name, colours) in zip(axes, palettes.items()):
    ax.bar(range(len(colours)), [1] * len(colours), color=colours, width=1)
    ax.set_title(name, loc="left", fontsize=10)
    ax.set_axis_off()
fig.savefig(os.path.join(out_dir, "palettes.png"), bbox_inches="tight")
plt.close(fig)

print(sns.color_palette("colorblind", 3).as_hex())
```

Output:

```
['#0173b2', '#de8f05', '#029e73']
```

![Three rows of colour swatches: eight distinct colour-blind-safe hues, a dark-to-light blue-green sequential ramp, and a blue to white to red diverging ramp](/img/data-visualization-with-matplotlib-and-seaborn/palettes.png)

Rules that keep colour honest:

- **Qualitative palettes have no order**, so never use them for low-to-high values. Sequential palettes imply order, so never use them for unordered groups.
- **Diverging palettes need a meaningful midpoint** (zero, last year's value, a target). Set it with `center=` in heatmaps.
- **Keep it to about 5 to 7 categories.** Beyond that, colours become hard to tell apart and to match with a legend. Group small categories into "Other", or use small multiples.
- **Avoid rainbow maps** (`"jet"`, `"hsv"`) for amounts. Their brightness jumps around, so they invent boundaries that aren't in the data.
- **Keep a colour's meaning fixed.** If "Mumbai" is orange in one chart, it's orange in every chart of the report.

#### Designing for colour-blind readers

Roughly 1 in 12 men and 1 in 200 women have some form of colour vision deficiency (the commonly quoted figures for people of European ancestry; rates vary between populations), most often difficulty telling red from green. Three habits cover most of it:

1. Use a **colour-blind-safe palette** such as Seaborn's `"colorblind"`, or sequential maps like `"viridis"`, `"rocket"` and `"mako"`, which also vary in brightness.
2. **Encode twice**: colour *and* marker shape (`style=` in Seaborn), line style, or a direct label.
3. **Never use red vs green alone** to mean bad vs good.

### 4. Declutter: remove what doesn't carry data

Every line, box and label costs the reader a little attention. Here is a typical default chart next to a cleaned version of the same data:

```python
regions = pd.Series({"North": 412, "South": 455, "East": 298, "West": 431,
                     "Central": 367, "North-East": 188, "Islands": 96, "Metro": 520})
last_year = pd.Series({"North": 380, "South": 420, "East": 363, "West": 401,
                       "Central": 350, "North-East": 170, "Islands": 90, "Metro": 470})
growth = ((regions / last_year - 1) * 100).round(1)
print(growth.sort_values().to_string())
```

Output:

```
East         -17.9
Central        4.9
Islands        6.7
West           7.5
South          8.3
North          8.4
North-East    10.6
Metro         10.6
```

```python
fig, (before, after) = plt.subplots(1, 2, figsize=(13, 4.4), layout="constrained")

# Before: defaults plus common bad habits
before.bar(regions.index, regions.values, color=sns.color_palette("hsv", 8), edgecolor="black")
before.set_title("Sales by region")
before.tick_params(axis="x", labelrotation=45)
before.grid(True, which="both", color="grey", linewidth=0.8)
before.legend(before.patches, regions.index, title="Region", loc="upper right", ncols=2, fontsize=7)

# After: sorted, one highlight, direct labels, minimal axes
ordered = regions.sort_values()
colours = ["#C44E52" if name == "East" else "#B8B8B8" for name in ordered.index]
bars = after.barh(ordered.index, ordered.values, color=colours)
after.bar_label(bars, labels=[f"₹{v} L" for v in ordered.values], padding=3, fontsize=9)
after.set_title("East is the only region that shrank (-17.9% vs last year)", loc="left",
                fontsize=12, fontweight="bold")
after.xaxis.set_visible(False)
after.spines[["top", "right", "bottom"]].set_visible(False)
after.tick_params(axis="y", length=0)
after.grid(False)

fig.savefig(os.path.join(out_dir, "declutter.png"), bbox_inches="tight")
plt.close(fig)
```

![Left: a cluttered bar chart with rainbow colours, rotated labels, heavy grid and a redundant legend. Right: the same data as sorted horizontal grey bars with East highlighted in red, values written on each bar and a title stating that East shrank](/img/data-visualization-with-matplotlib-and-seaborn/declutter.png)

What changed, and why:

| Before | After | Why |
|---|---|---|
| Unsorted (whatever order the data had) | Sorted by value | Ranking is visible instantly |
| Eight rainbow colours | Grey plus one red | Colour now *means* something: "look here" |
| Legend repeating the axis labels | No legend | Labels are already on the axis |
| Rotated labels | Horizontal bars | Labels read naturally |
| Heavy grid and x axis | Values on the bars, no x axis | Readers read the number, not a gridline |
| "Sales by region" | The finding as the title | The reader knows what to look for |

A useful habit: after drawing, go through each element and ask "if I delete this, does the reader lose information?" If not, delete it.

### 5. Highlight one thing, mute the rest

When many series share a chart, a spaghetti of coloured lines says nothing. Draw everything in grey and the one series that matters in colour:

```python
months = pd.date_range("2025-04-01", periods=12, freq="MS")
products = ["Masala chai", "Ginger chai", "Green tea", "Filter coffee", "Cold coffee", "Lemon tea"]
base = rng.integers(80, 140, size=len(products))
sales = pd.DataFrame(
    {p: b + np.cumsum(rng.normal(0, 6, 12)) for p, b in zip(products, base)}, index=months
).round()
sales["Cold coffee"] = (np.linspace(60, 175, 12) + rng.normal(0, 5, 12)).round()

fig, ax = plt.subplots(figsize=(9, 4.4), layout="constrained")
for name in sales.columns:
    is_focus = name == "Cold coffee"
    ax.plot(sales.index, sales[name], color="#1F77B4" if is_focus else "#C8C8C8",
            linewidth=2.8 if is_focus else 1.4, zorder=3 if is_focus else 2)
    ax.text(sales.index[-1] + pd.Timedelta(days=8), sales[name].iloc[-1], name,
            va="center", fontsize=9, color="#1F77B4" if is_focus else "#8C8C8C",
            fontweight="bold" if is_focus else "normal")

ax.set_title("Cold coffee nearly tripled in a year and is now the best seller",
             loc="left", fontweight="bold")
ax.set_ylabel("Cups per day")
ax.set_xticks(months[::3], labels=[m.strftime("%b %Y") for m in months[::3]])
ax.spines[["top", "right"]].set_visible(False)
ax.set_xlim(right=sales.index[-1] + pd.Timedelta(days=75))
fig.savefig(os.path.join(out_dir, "highlight.png"), bbox_inches="tight")
plt.close(fig)
print(sales.iloc[-1].sort_values(ascending=False).head(3).to_dict())
```

Output:

```
{'Cold coffee': 175.0, 'Masala chai': 134.0, 'Lemon tea': 123.0}
```

![Six product sales lines over a year, five in light grey and cold coffee in bold blue rising steeply to the top, each line labelled by name at its right end](/img/data-visualization-with-matplotlib-and-seaborn/highlight.png)

Two techniques at once:

- **Highlighting**: grey for context, one strong colour for the story, a thicker line, and a higher `zorder` so it sits on top.
- **Direct labels**: names written at the end of each line replace the legend. The reader's eyes never leave the data to decode colours. `ax.set_xlim(right=...)` leaves room for the labels.

If two labels collide, nudge one up or down by hand; there's no shame in a manual tweak on an explanatory chart.

### 6. Honest scales

Styling can mislead as easily as it can clarify. The most common distortion is a **truncated axis** on a bar chart:

```python
banks = pd.Series({"Bank A": 7.10, "Bank B": 7.25, "Bank C": 7.40})
fig, (bad, good) = plt.subplots(1, 2, figsize=(10, 3.6), layout="constrained")

bad.bar(banks.index, banks.values, color="#C44E52")
bad.set_ylim(7.0, 7.45)
bad.set_title("Misleading: axis starts at 7.0", loc="left")

good.bar(banks.index, banks.values, color="#4C72B0")
good.set_ylim(0, 8)
good.bar_label(good.containers[0], fmt="%.2f%%", padding=3)
good.set_title("Honest: bars start at zero", loc="left")
for ax in (bad, good):
    ax.set_ylabel("Home loan rate (%)")
    ax.spines[["top", "right"]].set_visible(False)
fig.savefig(os.path.join(out_dir, "truncated-axis.png"), bbox_inches="tight")
plt.close(fig)
print(f"Bank C vs Bank A: {banks['Bank C'] / banks['Bank A'] - 1:.1%} higher")
```

Output:

```
Bank C vs Bank A: 4.2% higher
```

![Two bar charts of three bank loan rates: on the left the axis starts at 7.0 so Bank C's bar looks four times taller than Bank A's; on the right the axis starts at zero and the bars look nearly equal, with values labelled](/img/data-visualization-with-matplotlib-and-seaborn/truncated-axis.png)

On the left, Bank C's bar looks four times taller than Bank A's. The real difference is about 4%. The checklist for honest charts:

- **Bars and areas start at zero.** Lines may zoom in, because readers judge their slope and position, not their length; say so in the axis if it matters.
- **Shared scales across panels** you want compared (`sharey=True`).
- **No dual y-axes**; index to a common base or use two panels.
- **No 3D effects** on 2-D data; perspective changes apparent sizes.
- **Consistent intervals**: don't skip years on a time axis without showing the gap.
- **Aspect ratio**: a very tall, thin line chart exaggerates change; a very wide, flat one hides it. Aim for a shape where the main trend is at roughly 45 degrees or less steep.

### 7. Text that does the work

Most readers read the title, glance at the chart, and stop. So:

- **Title = the finding.** "East is the only region that shrank" beats "Sales by region". Left-aligned titles (`loc="left"`) read like a headline.
- **Subtitle or axis label = the details.** Units, time period, what an error bar means.
- **Source line** at the bottom for anything you publish.
- **Annotate the one or two points** the story depends on, not every point.
- **Readable sizes.** Nothing smaller than about 9 points in a report, bigger on slides (that's what `context="talk"` is for).
- **Format numbers for people**: `₹4.2 Cr`, `18%`, `Feb`. See the formatters in [Creating and Customising Plots](../06-matplotlib/creating-and-customising-plots.md).

A small helper keeps titles and subtitles consistent across a report:

```python
def headline(ax, title, subtitle):
    """Bold left-aligned title with a grey subtitle underneath."""
    ax.set_title(subtitle, loc="left", fontsize=10, color="#666666", pad=8)
    ax.text(0, 1.12, title, transform=ax.transAxes, fontsize=13, fontweight="bold")

fig, ax = plt.subplots(figsize=(8, 3.6), layout="constrained")
ax.plot(months, sales["Cold coffee"], color="#1F77B4", linewidth=2.5)
headline(ax, "Cold coffee sales nearly tripled",
         "Cups per day, April 2025 to March 2026, all stalls")
ax.spines[["top", "right"]].set_visible(False)
fig.savefig(os.path.join(out_dir, "headline.png"), bbox_inches="tight")
plt.close(fig)
```

![A single blue line rising over the year under a bold title reading Cold coffee sales nearly tripled and a grey subtitle giving units, period and scope](/img/data-visualization-with-matplotlib-and-seaborn/headline.png)

### 8. Accessibility checklist

- **Colour-blind-safe palette** and a second encoding (shape, label, line style).
- **Contrast**: dark text on light background; avoid light grey text for anything important.
- **Alt text** when the chart goes on the web or in a document: one or two sentences saying what the chart shows *and* its main finding, as in every image on this site.
- **Don't rely on hover or interactivity** for key information in a static report.
- **A table of the numbers** in an appendix helps screen-reader users and anyone who needs exact values.

### 9. Reusable style files

Once you've settled on a look, store it in a **Matplotlib style file** (`.mplstyle`) so every chart in a project matches. It's a plain text file of `rcParams`:

```python
style_text = """
axes.spines.top: False
axes.spines.right: False
axes.titlelocation: left
axes.titleweight: bold
axes.titlesize: 13
axes.grid: True
axes.grid.axis: y
grid.color: E6E6E6
axes.prop_cycle: cycler('color', ['1F77B4', 'C44E52', '55A868', '8172B3', 'CCB974'])
font.size: 10
figure.figsize: 8, 4
figure.dpi: 100
savefig.bbox: tight
"""
style_path = os.path.join(out_dir, "house.mplstyle")
with open(style_path, "w") as f:
    f.write(style_text)

sns.reset_defaults()
with plt.style.context(style_path):
    fig, ax = plt.subplots(layout="constrained")
    for name in ["Masala chai", "Cold coffee", "Green tea"]:
        ax.plot(months, sales[name], linewidth=2, label=name)
    ax.set_title("House style applied from a file")
    ax.legend(frameon=False)
    print(mpl.rcParams["axes.titlelocation"], mpl.rcParams["axes.spines.top"])
    fig.savefig(os.path.join(out_dir, "house-style.png"))
    plt.close(fig)
print(mpl.rcParams["axes.titlelocation"])
```

Output:

```
left False
center
```

![A three-line chart drawn with a custom style file: left-aligned bold title, no top or right spines, light horizontal gridlines only](/img/data-visualization-with-matplotlib-and-seaborn/house-style.png)

Inside `plt.style.context(...)` the style applies; outside, the defaults return. For a whole script use `plt.style.use(style_path)`. Commit the file to your repository so the whole team shares one look. Colours in style files are written without the `#`.

---

## Try It Yourself

1. **Talk-ready.** Set `sns.set_theme(context="talk")` and print `mpl.rcParams["font.size"]`. Then reset with `sns.set_theme()` and print it again.
2. **Pick the palette.** For each, say qualitative, sequential or diverging: (a) temperature anomaly vs the 30-year average, (b) number of orders per pin code, (c) payment method.
3. **Highlight two.** Redraw the product chart highlighting both Cold coffee (blue) and the product with the lowest final value (red). Print the name of the lowest one.
4. **Fix the title.** Write a findings-style title for the bank-rate chart.

<details>
<summary>Show answers</summary>

```python
sns.set_theme(context="talk")
print(mpl.rcParams["font.size"])
sns.set_theme()
print(mpl.rcParams["font.size"])

lowest = sales.iloc[-1].idxmin()
fig, ax = plt.subplots(figsize=(9, 4))
for name in sales.columns:
    colour = {"Cold coffee": "#1F77B4", lowest: "#C44E52"}.get(name, "#C8C8C8")
    ax.plot(sales.index, sales[name], color=colour, linewidth=2.5 if colour != "#C8C8C8" else 1.2)
fig.savefig(os.path.join(out_dir, "ex-highlight-two.png"))
plt.close(fig)
print("lowest:", lowest)
sns.reset_defaults()
```

Output:

```
18.0
12.0
lowest: Green tea
```

1. `"talk"` scales fonts up by about 1.5 times compared with `"notebook"`.
2. (a) Diverging, centred on zero anomaly. (b) Sequential. (c) Qualitative.
3. See the printed name. A dictionary lookup with `.get(name, grey)` is a tidy way to assign highlight colours.
4. For example: "All three banks charge between 7.1% and 7.4%: a gap of 0.3 percentage points, roughly ₹6,000 of interest in the first year of a ₹20 lakh loan." A title should give the reader the conclusion, ideally in terms they care about.

</details>

---

## Real-World Examples

### Example 1: Newsrooms

Data journalism teams at major newspapers publish style guides with fixed fonts, a small palette, left-aligned headline titles, source lines and rules such as "bars start at zero". Readers recognise their charts instantly, and the rules prevent accidental distortion under deadline pressure.

### Example 2: Board decks

A finance team replaces a slide of six coloured lines with one blue line (their business unit) over grey lines (competitors) and a title stating the market-share change. The board discussion shifts from "which line is us?" to the strategy question.

### Example 3: Government dashboards

Public health dashboards often use colour-blind-safe sequential maps for case counts by district, with explicit legends, because their readers include millions of people with colour vision deficiencies and print the charts in black and white.

---

## Common Misconceptions

### Misconception 1: "Good design means more decoration"

Good design usually means *less*: fewer colours, fewer lines, fewer words. The decoration that remains, a highlight colour, an annotation, a strong title, is there because it carries meaning.

### Misconception 2: "Colour is the best way to distinguish groups"

Position and length are read far more accurately than colour. Colour is best for one highlight or a handful of categories, and it should be backed up by labels or shapes.

### Misconception 3: "A neutral title like 'Sales by region' is more objective"

A neutral title isn't more objective; it just makes every reader find the point alone, and different readers will find different points. A findings title is honest as long as the chart supports it.

### Misconception 4: "Default styles are good enough for a presentation"

Defaults are designed to be safe for exploration. In a meeting room, text needs to be bigger (`context="talk"`), the message needs to be in the title, and the grid can usually go.

---

## Interview Relevance

Interviews for analyst roles often include a chart critique ("what would you improve here?") or a take-home presentation:

- *"Critique this chart."* Work through: message in the title, sorted bars, zero baseline, unnecessary colour, legend vs direct labels, clutter, readable text, honest scales, accessibility.
- *"How do you choose colours?"* By job: qualitative for categories, sequential for amounts, diverging around a midpoint; colour-blind-safe; consistent meanings across charts.
- *"How would you show one product among many?"* Grey context lines, one highlighted line, direct labels.
- *"How do you make sure a chart isn't misleading?"* Zero baselines for bars, shared scales, no dual axes or 3D, sensible aspect ratio, clear units and source.
- *"How do you keep a team's charts consistent?"* A shared `.mplstyle` file or a small helper module with the palette and title functions.

---

## Key Takeaways

- **Decide the one-sentence message first**, then make the title say it and the data that proves it stand out.
- **Themes and contexts** (`sns.set_theme(style=..., context=...)`) set the baseline; use `"talk"` for slides.
- **Colour by job**: qualitative, sequential or diverging; colour-blind-safe; never more than a handful of categories.
- **Declutter, highlight, label directly**: grey for context, one colour for the story, names on the data instead of a legend.
- **Stay honest**: zero baselines for bars, shared scales, no dual axes or 3D.
- **Capture your look in a `.mplstyle` file** so every chart in a project matches.

---

**Up next:** [Lab: Build a one-page visual report](lab-build-a-one-page-visual-report.md)
