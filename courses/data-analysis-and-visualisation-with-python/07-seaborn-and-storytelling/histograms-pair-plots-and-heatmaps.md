---
title: "Histograms, Pair Plots and Heatmaps"
course: "Data Analysis and Visualisation with Python"
module: "7. Seaborn and Storytelling"
type: Article
level: Beginner
reading_time: 28 min
---

# Histograms, Pair Plots and Heatmaps: The Complete Guide

> 📚 **Before you start**
>
> - [Statistical Plots with Seaborn](statistical-plots-with-seaborn.md), for `hue`, long-form data and Axes-level vs figure-level functions
> - [Descriptive Statistics in pandas](../course.md#m5) (Data Analysis and Visualisation with Python), for `describe`, `corr` and `pivot_table`

## Introduction

You're helping a friend choose a flat to rent in Pune. A broker says "average rent around here is ₹24,000". Is that useful? Not really. If most flats are ₹15,000 and a few luxury ones are ₹80,000, the average describes almost nothing you can actually rent. You need to see the **distribution**: where most values sit, how spread out they are, whether there are two clusters, and how far the long tail stretches.

Then you want to know what *drives* rent. Is it area, distance from the metro, the building's age? With five numeric columns there are ten pairs to check. And once you understand the city, you might want a single grid showing, for example, how train delays vary by hour and weekday.

This lesson covers those three jobs. **Histograms**, density curves and ECDFs show the shape of one variable. **Pair plots** and joint plots show relationships between many variables at once. **Heatmaps** show a whole table of numbers as colour, including correlation matrices. By the end you will choose bin widths deliberately, compare groups without misleading overlaps, read a pair plot in seconds, and build a correctly coloured correlation heatmap.

> 💡 **Key Insight**
>
> A single number (mean, correlation) is a summary that can hide almost anything, as Anscombe's quartet showed. Distribution plots and pair plots are how you check the summary before you trust it. Make them **first** when you meet a new dataset, not last.

---

## Core Explanation

### 1. Setup and a dataset

We'll make 500 made-up rental listings. Rent depends on area, number of bedrooms, and distance from a metro station, with some randomness:

```python
import os
import tempfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")
out_dir = tempfile.mkdtemp()
rng = np.random.default_rng(11)

n = 500
bhk = rng.choice([1, 2, 3], size=n, p=[0.35, 0.45, 0.20])
area = (rng.normal(450, 50, n) + (bhk - 1) * 350).round(-1)
metro_km = rng.gamma(2, 1.2, n).round(1)
age = rng.integers(0, 30, n)
rent = (area * 30 - metro_km * 700 - age * 100 + rng.normal(0, 1500, n)).round(-2)

flats = pd.DataFrame({
    "bhk": pd.Categorical([f"{b} BHK" for b in bhk], categories=["1 BHK", "2 BHK", "3 BHK"]),
    "area_sqft": area, "metro_km": metro_km, "age_years": age, "rent": rent,
})
print(flats.describe().round(0).loc[["mean", "50%", "min", "max"]].to_string())
```

Output:

```
      area_sqft  metro_km  age_years     rent
mean      738.0       2.0       15.0  19103.0
50%       780.0       2.0       15.0  19800.0
min       320.0       0.0        0.0   3800.0
max      1270.0      10.0       29.0  36600.0
```

Mean and median rent are close, and rents run from about ₹4,000 to ₹37,000. These numbers can't tell you whether that range holds one big group of similar flats or several distinct groups. A picture can.

### 2. Histograms and the bin-width decision

A **histogram** splits the range into intervals called **bins** and draws a bar for how many values fall in each. The bin width is a choice, and it changes the story:

```python
fig, axes = plt.subplots(1, 3, figsize=(13, 3.6), sharey=False, layout="constrained")
for ax, bins in zip(axes, [5, 30, 150]):
    sns.histplot(data=flats, x="rent", bins=bins, ax=ax)
    ax.set_title(f"bins={bins}")
    ax.set_xlabel("Monthly rent (₹)")
fig.savefig(os.path.join(out_dir, "hist-bins.png"), bbox_inches="tight")
plt.close(fig)

counts, edges = np.histogram(flats["rent"], bins=5)
print("5 bins, width ₹", round(edges[1] - edges[0]), "->", counts.tolist())
```

Output:

```
5 bins, width ₹ 6560 -> [87, 105, 180, 63, 65]
```

![Three histograms of the same rent data with 5, 30 and 150 bins: too few bins hide the shape, 30 bins show three humps, 150 bins are noisy](/img/data-visualization-with-matplotlib-and-seaborn/hist-bins.png)

- **Too few bins** (5) blur the shape into a lump.
- **Too many** (150) turn it into noise; every bar holds a handful of flats.
- **In between** (30) shows the real structure: three humps, which turn out to be 1, 2 and 3 BHK flats.

Seaborn picks a sensible number by default (`bins="auto"` uses NumPy's rules), but always try a couple of values. You can also set **`binwidth=1000`**, which is often easier to explain ("each bar is ₹1,000 wide"), or **`binrange=(5000, 50000)`** to fix the range.

`np.histogram` returns the counts and the bin **edges**, so you can see exactly what a histogram computes.

#### What the y axis means: `stat`

| `stat=` | Bar height is | Use when |
|---|---|---|
| `"count"` (default) | Number of rows in the bin | One dataset |
| `"percent"` / `"probability"` | Share of rows (bars sum to 100 or 1) | Comparing groups of different sizes |
| `"density"` | Share ÷ bin width (total area = 1) | Overlaying a density curve |

### 3. Comparing groups: `hue` and `multiple`

Add `hue="bhk"` and Seaborn draws one histogram per group. How they are combined is set by `multiple`:

```python
fig, axes = plt.subplots(2, 2, figsize=(11, 6.5), sharex=True, layout="constrained")
for ax, how in zip(axes.flat, ["layer", "stack", "dodge", "fill"]):
    sns.histplot(data=flats, x="rent", hue="bhk", multiple=how, binwidth=1500,
                 element="step" if how == "layer" else "bars", ax=ax,
                 legend=(how == "layer"))
    ax.set_title(f'multiple="{how}"')
    ax.set_xlabel("Monthly rent (₹)")
fig.savefig(os.path.join(out_dir, "hist-multiple.png"), bbox_inches="tight")
plt.close(fig)
print(flats.groupby("bhk", observed=True)["rent"].median().to_dict())
```

Output:

```
{'1 BHK': 10500.0, '2 BHK': 20700.0, '3 BHK': 31400.0}
```

![Four histograms of rent split by 1, 2 and 3 BHK: overlapping steps, stacked bars, side-by-side bars, and a filled 100 percent view](/img/data-visualization-with-matplotlib-and-seaborn/hist-multiple.png)

- **`layer`** overlaps the groups (with `element="step"` drawing outlines so they stay visible). Best for comparing shapes.
- **`stack`** piles them up, so the top edge is the overall histogram. Good for "what is each group's contribution", bad for comparing the upper groups' shapes.
- **`dodge`** puts bars side by side within each bin. Gets busy fast.
- **`fill`** stretches every bin to 100%, showing the *mix* of groups at each rent level.

When groups have very different sizes, add `stat="density", common_norm=False` so each group is normalised separately; otherwise a large group dwarfs a small one.

### 4. Density curves (KDE)

A **kernel density estimate** (KDE) replaces bars with a smooth curve. It places a small bell curve on every data point and adds them up. The width of those bells, the **bandwidth**, plays the same role as bin width:

```python
fig, axes = plt.subplots(1, 2, figsize=(12, 3.8), layout="constrained")
for adjust, style in [(0.3, ":"), (1, "-"), (3, "--")]:
    sns.kdeplot(data=flats, x="rent", bw_adjust=adjust, linestyle=style,
                label=f"bw_adjust={adjust}", ax=axes[0])
axes[0].legend(frameon=False)
axes[0].set_title("Bandwidth controls smoothness")

sns.kdeplot(data=flats, x="rent", hue="bhk", fill=True, alpha=0.3,
            common_norm=False, ax=axes[1])
axes[1].set_title("One curve per group, each with area 1")
for ax in axes:
    ax.set_xlabel("Monthly rent (₹)")
fig.savefig(os.path.join(out_dir, "kde.png"), bbox_inches="tight")
plt.close(fig)
```

![Left: three density curves of rent with small, default and large bandwidths, from wiggly to over-smoothed. Right: filled density curves for 1, 2 and 3 BHK flats](/img/data-visualization-with-matplotlib-and-seaborn/kde.png)

- **`bw_adjust`** multiplies the default bandwidth. Below 1 is wigglier, above 1 smoother. At 3 the three humps melt into one.
- **`common_norm=False`** gives each group's curve an area of 1, so a small group is as visible as a big one.
- **KDEs extend past the data.** A density curve for rent will show a little probability below the smallest rent, and one for age could show negative ages. Use `cut=0` to stop the curve at the data's minimum and maximum, or use a histogram for bounded data.

KDEs look polished and compare groups well. Histograms are more honest about small samples and exact counts. A common combination is `sns.histplot(..., kde=True)`, which draws both.

### 5. The ECDF: no bins, no bandwidth

An **empirical cumulative distribution function** (ECDF) plots, for every value, the share of data at or below it. It has no tuning parameter at all, and it answers "what share of flats rent for under ₹X?" directly:

```python
fig, ax = plt.subplots(figsize=(7.5, 3.8), layout="constrained")
sns.ecdfplot(data=flats, x="rent", hue="bhk", ax=ax)
ax.axvline(20000, color="grey", linestyle="--", linewidth=1)
ax.set(xlabel="Monthly rent (₹)", ylabel="Share of flats at or below",
       title="ECDF: read off 'what share costs less than X'")
fig.savefig(os.path.join(out_dir, "ecdf.png"), bbox_inches="tight")
plt.close(fig)

share = (flats["rent"] <= 20000).groupby(flats["bhk"], observed=True).mean().round(2)
print(share.to_dict())
```

Output:

```
{'1 BHK': 1.0, '2 BHK': 0.33, '3 BHK': 0.0}
```

![ECDF curves of rent for 1, 2 and 3 BHK flats with a dashed line at 20,000 rupees, where almost all 1 BHK flats are below and almost no 3 BHK flats are](/img/data-visualization-with-matplotlib-and-seaborn/ecdf.png)

Where the dashed line crosses each curve is the share of that group renting for ₹20,000 or less. ECDFs are less familiar to general audiences, so use them for analysis and explain them carefully if they go in a report.

`displot` is the figure-level version of all of these: `sns.displot(data=flats, x="rent", col="bhk", kind="hist")` (or `kind="kde"`, `kind="ecdf"`) draws one panel per group. Add `rug=True` to mark each individual value with a tick along the axis.

### 6. Two variables at once: joint plots

`jointplot` draws the relationship between two numbers in the middle and each variable's own distribution along the edges:

```python
g = sns.jointplot(data=flats, x="area_sqft", y="rent", hue="bhk", height=5.5,
                  alpha=0.6, marginal_kws={"common_norm": False})
g.set_axis_labels("Area (sq ft)", "Monthly rent (₹)")
g.savefig(os.path.join(out_dir, "jointplot.png"))
plt.close(g.figure)
print(type(g).__name__, round(flats["area_sqft"].corr(flats["rent"]), 2))
```

Output:

```
JointGrid 0.96
```

![Joint plot of rent against area coloured by BHK, with density curves for area along the top and for rent along the right side](/img/data-visualization-with-matplotlib-and-seaborn/jointplot.png)

`kind=` switches the centre: `"scatter"` (default), `"kde"` for contour lines, `"hist"` for a two-dimensional histogram (a grid of coloured squares, good for thousands of points), `"hex"` for hexagonal bins, and `"reg"` to add a regression line.

### 7. Pair plots: every relationship in one figure

A **pair plot** draws a scatter plot for every pair of numeric columns, with each column's distribution on the diagonal. It is the fastest way to explore a new table:

```python
g = sns.pairplot(data=flats, vars=["rent", "area_sqft", "metro_km", "age_years"],
                 hue="bhk", height=2.0, corner=True,
                 plot_kws={"alpha": 0.5, "s": 12}, diag_kws={"common_norm": False})
g.savefig(os.path.join(out_dir, "pairplot.png"), dpi=72)
plt.close(g.figure)
print(g.axes.shape)
```

Output:

```
(4, 4)
```

![Pair plot of rent, area, metro distance and building age coloured by BHK, showing only the lower triangle: rent rises strongly with area while metro distance and age show no clear pattern](/img/data-visualization-with-matplotlib-and-seaborn/pairplot.png)

How to read it:

- **Each cell** is one pair. The cell in row "area_sqft", column "rent" plots area (up the y axis) against rent (along the x axis).
- **The diagonal** shows each variable alone (density curves per group here).
- **`corner=True`** drops the upper triangle, which only mirrors the lower one.
- **What to look for**: clear upward or downward clouds (relationships), separate clusters (groups), curved patterns, and points far from the rest.

Here the story is quick to read: rent rises strongly with area, and the BHK groups separate cleanly on both. Metro distance and building age show no obvious pattern at this scale; their small effects are swamped by size. Notice also the age density on the diagonal running below zero: the KDE edge effect from section 4.

A pair plot of *n* variables has *n²* cells, so pick the few columns that matter. For full control, `sns.PairGrid` lets you choose what goes in each region: `g = sns.PairGrid(df); g.map_lower(sns.scatterplot); g.map_diag(sns.histplot); g.map_upper(sns.kdeplot)`.

### 8. Heatmaps of a table

A **heatmap** shows a 2-D table as a grid of coloured cells. The input is a **wide** table: rows and columns become the two axes. A classic use is a time grid. Here are made-up average train delays by weekday and hour:

```python
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
hours = list(range(6, 23))
delay_rng = np.random.default_rng(5)
records = []
for d_i, d in enumerate(days):
    for h in hours:
        rush = 9 * np.exp(-((h - 9) ** 2) / 2) + 11 * np.exp(-((h - 18.5) ** 2) / 2)
        weekday = 1.0 if d_i < 5 else 0.35
        records.append({"day": d, "hour": h,
                        "delay": round(2 + rush * weekday + delay_rng.normal(0, 0.8), 1)})
delays = pd.DataFrame(records)

grid = delays.pivot(index="day", columns="hour", values="delay").loc[days]
print(grid.shape)
print(grid.loc[["Mon", "Sun"], [8, 9, 18, 19]].to_string())
```

Output:

```
(7, 17)
hour   8     9     18    19
day                        
Mon   7.3  11.3  10.9  13.0
Sun   4.0   6.7   4.9   4.6
```

```python
fig, ax = plt.subplots(figsize=(12, 3.8), layout="constrained")
sns.heatmap(grid, cmap="rocket_r", annot=True, fmt=".0f", linewidths=0.5,
            cbar_kws={"label": "Average delay (minutes)"}, ax=ax)
ax.set(xlabel="Hour of day", ylabel="", title="Weekday rush hours bring the longest train delays")
fig.savefig(os.path.join(out_dir, "heatmap-delays.png"), bbox_inches="tight")
plt.close(fig)
```

![Heatmap of average train delay with weekdays as rows and hours 6 to 22 as columns, each cell annotated; dark cells cluster at 9 am and 6 to 7 pm on weekdays](/img/data-visualization-with-matplotlib-and-seaborn/heatmap-delays.png)

- **`annot=True, fmt=".0f"`** writes the value in each cell, with `fmt` as a format code. Only annotate when the grid is small enough to read.
- **`cmap="rocket_r"`** is a *sequential* colour map (light to dark). The `_r` suffix reverses it so bigger delays are darker, which matches intuition. `"viridis"`, `"mako"` and `"Blues"` are other good sequential choices.
- **`linewidths`** draws thin gaps between cells.
- **`vmin`, `vmax`** fix the colour scale, essential when comparing two heatmaps.

### 9. Correlation heatmaps, done right

A **correlation matrix** (`df.corr()`) holds the correlation between every pair of columns, from −1 (perfect inverse relationship) through 0 (none) to +1 (perfect relationship). It's the numeric summary of a pair plot. It needs a *diverging* colour map centred on zero, and the redundant upper triangle should be hidden:

```python
corr = flats[["rent", "area_sqft", "metro_km", "age_years"]].corr().round(2)
print(corr.to_string())

mask = np.triu(np.ones_like(corr, dtype=bool))      # True above and on the diagonal
fig, ax = plt.subplots(figsize=(5.5, 4.5), layout="constrained")
sns.heatmap(corr, mask=mask, cmap="vlag", vmin=-1, vmax=1, center=0,
            annot=True, fmt=".2f", square=True, linewidths=0.5, ax=ax)
ax.set_title("Correlation between listing features")
fig.savefig(os.path.join(out_dir, "heatmap-corr.png"), bbox_inches="tight")
plt.close(fig)
```

Output:

```
           rent  area_sqft  metro_km  age_years
rent       1.00       0.96     -0.04      -0.12
area_sqft  0.96       1.00      0.12      -0.00
metro_km  -0.04       0.12      1.00      -0.04
age_years -0.12      -0.00     -0.04       1.00
```

![Lower-triangle correlation heatmap with a blue-white-red scale from minus 1 to 1: rent and area strongly positive, other pairs near zero](/img/data-visualization-with-matplotlib-and-seaborn/heatmap-corr.png)

Three rules make a correlation heatmap honest:

1. **Diverging colour map, centred on zero** (`cmap="vlag"` or `"coolwarm"`, `center=0`). Positive and negative get different hues, and zero is neutral white.
2. **Fixed scale `vmin=-1, vmax=1`.** Without it, the strongest correlation present gets the darkest colour, so a weak 0.3 could look dramatic.
3. **Mask the upper triangle and the diagonal.** The matrix is symmetric and the diagonal is always 1, so they only add noise. `np.triu` builds a mask of the upper triangle including the diagonal.

Correlation measures only *straight-line* relationships. A U-shaped relationship can have a correlation near zero, which is why you look at the pair plot too.

### 10. Clustered heatmaps

`sns.clustermap` reorders rows and columns so that similar ones sit together, and draws a tree (a *dendrogram*) showing the grouping. It needs SciPy:

```python
g = sns.clustermap(grid, cmap="rocket_r", figsize=(9, 5), col_cluster=False,
                   cbar_pos=(0.02, 0.8, 0.03, 0.15))
g.savefig(os.path.join(out_dir, "clustermap.png"), dpi=80)
plt.close(g.figure)
print([grid.index[i] for i in g.dendrogram_row.reordered_ind])
```

Output:

```
['Sat', 'Sun', 'Wed', 'Tue', 'Fri', 'Mon', 'Thu']
```

![Clustered heatmap of train delays where the rows are reordered so that Saturday and Sunday sit together apart from the five weekdays, with a dendrogram on the left](/img/data-visualization-with-matplotlib-and-seaborn/clustermap.png)

The algorithm found, with no labels, that Saturday and Sunday behave alike and differently from weekdays. `col_cluster=False` keeps the hours in time order, because reordering time would make the chart harder to read.

---

## Try It Yourself

1. **Bin width in rupees.** Draw a histogram of rent with `binwidth=2500` and `stat="percent"`. Print the number of bins Seaborn used (`len(ax.patches)`).
2. **Skew.** Print the mean and median of `metro_km`. Draw its histogram. Which side is the tail on, and how do mean and median show it?
3. **Correlation check.** Which two columns in `flats` have the strongest *negative* correlation with rent? Answer from `corr` in code.
4. **Your own heatmap.** Pivot `delays` to show the **average delay per day** (one column) and draw it as a one-column heatmap. Print the worst day.

<details>
<summary>Show answers</summary>

```python
fig, ax = plt.subplots()
sns.histplot(data=flats, x="rent", binwidth=2500, stat="percent", ax=ax)
print("bins:", len(ax.patches))
fig.savefig(os.path.join(out_dir, "ex-binwidth.png"))
plt.close(fig)

print("mean", round(flats["metro_km"].mean(), 2), "median", flats["metro_km"].median())

rent_corr = corr["rent"].drop("rent").sort_values()
print(rent_corr.index[0], rent_corr.iloc[0])

per_day = delays.groupby("day")["delay"].mean().loc[days].round(1).to_frame()
fig, ax = plt.subplots(figsize=(2.5, 4))
sns.heatmap(per_day, annot=True, cmap="rocket_r", ax=ax)
fig.savefig(os.path.join(out_dir, "ex-per-day.png"), bbox_inches="tight")
plt.close(fig)
print("worst day:", per_day["delay"].idxmax())
```

Output:

```
bins: 13
mean 2.38 median 2.0
age_years -0.12
worst day: Thu
```

1. With ₹2,500 bins over the rent range you get the printed count of bars, and the y axis now reads in percent.
2. The tail is on the right (a few flats are far from the metro). The mean is pulled toward the tail, so it is larger than the median: the signature of right skew.
3. `age_years` is the most negative (−0.12) and `metro_km` is close to zero. Both are tiny next to the 0.96 correlation with area. In this data, area explains almost everything, so the small effects of age and distance only show up once you compare flats of similar size.
4. A weekday, since weekend delays are scaled down.

</details>

---

## Real-World Examples

### Example 1: Pricing analysis

An e-commerce analyst plots the distribution of order values with a histogram and finds two humps: small single-item orders and large festive gift orders. The "average order value" KPI was describing neither group. They start reporting the two segments separately.

### Example 2: Feature exploration before modelling

Before training a model to predict house prices, a data scientist runs a pair plot and a correlation heatmap. Two features are correlated at 0.97 (built-up area and carpet area), so one is dropped. A curved relationship with age shows up in the pair plot, which a linear correlation of −0.1 had hidden.

### Example 3: Operations heatmaps

A metro operator shows a weekday-by-hour heatmap of crowding in its control room. Planners spot that the 6 pm peak starts 30 minutes earlier on Fridays, and adjust the train frequency for that slot only.

---

## Common Misconceptions

### Misconception 1: "The histogram shows the true shape of the data"

It shows the shape at **one bin width**. Change the bins and peaks can appear or vanish. Try at least two widths before drawing conclusions.

### Misconception 2: "A KDE is more accurate than a histogram"

A KDE is smoother, not more accurate. It invents probability between and beyond data points and depends on bandwidth just as a histogram depends on bins. For small samples or bounded values, a histogram is often more honest.

### Misconception 3: "Any colour map will do for a heatmap"

Sequential data (delays, counts) needs a one-direction colour map. Data with a meaningful middle (correlations, change versus last year) needs a diverging map centred on that middle. Rainbow maps like `jet` create false boundaries where the hue changes and are unreadable for many colour-blind readers.

### Misconception 4: "Zero correlation means no relationship"

It means no *straight-line* relationship. Curves, clusters and relationships that only hold for part of the data can all have correlation near zero. Always check the scatter plot.

---

## Interview Relevance

These charts come up constantly in data analyst and data scientist interviews, often as "how would you explore this dataset?":

- *"How do you choose the number of bins?"* Start with an automatic rule, then try narrower and wider bins; prefer a bin width that is meaningful in the units (₹1,000, 5 minutes). Mention that bins can create or hide peaks.
- *"Histogram vs KDE vs ECDF?"* Histogram for counts and honesty, KDE for smooth comparison of groups, ECDF for exact percentiles and no tuning parameters.
- *"What would you do first with a new dataset?"* Distribution plots of each column, a pair plot of the key numeric columns, and a correlation heatmap, looking for skew, outliers, clusters and redundant features.
- *"How should a correlation heatmap be coloured?"* Diverging, centred at zero, fixed from −1 to 1, with the upper triangle masked.
- *"Correlation is 0.05. Is there no relationship?"* Not necessarily; check for non-linear patterns.

---

## Key Takeaways

- **Distributions first**: histograms, KDEs and ECDFs reveal skew, multiple peaks and outliers that averages hide.
- **Bin width and bandwidth are choices** that change the picture; try more than one and prefer meaningful units.
- **Compare groups** with `hue` plus the right `multiple` and `common_norm=False` when group sizes differ.
- **Pair plots and joint plots** show many relationships at once; use them before modelling.
- **Heatmaps** need a wide table; use a **sequential** colour map for magnitudes and a **diverging, centred, fixed-range** one for correlations.
- **Correlation only measures straight lines**, so always look at the scatter plots too.

---

**Up next:** [Styling Charts for Communication](styling-charts-for-communication.md)
