---
title: "Creating and Customising Plots"
course: "Data Analysis and Visualisation with Python"
module: "6. Matplotlib"
type: Article
level: Beginner
reading_time: 28 min
---

# Creating and Customising Plots: The Complete Guide

> 📚 **Before you start**
>
> - [How Matplotlib Thinks: Figures and Axes](how-matplotlib-thinks-figures-and-axes.md), for `fig, ax = plt.subplots()` and the explicit style
> - [Dates, Times and Timedeltas](../course.md#m4) (Data Analysis and Visualisation with Python), for `pd.date_range` and date columns
> - [Selecting, Sorting and Indexing Data](../course.md#m3), for `sort_values` and `groupby`

## Introduction

A kirana shop owner asks you a simple question: "Are UPI payments growing, and which days are busiest?" You have a DataFrame with 90 days of numbers. You could hand them `df.describe()`. Or you could hand them one line chart with a clear upward trend, the weekends marked, and the record day labelled with its value. Only one of those gets a "Wah, that makes sense" in five seconds.

The previous lesson gave you the structure: Figures, Axes, Artists. This lesson fills it in. You will learn the six chart types that answer most business questions, and then every customisation that turns a default chart into a readable one: colours, markers, labels, legends, tick formatting (including rupees), annotations, reference lines and shaded regions.

By the end you will be able to pick the right chart for a question, draw it from a pandas DataFrame, and polish it until a non-technical reader understands it without you in the room.

> 💡 **Key Insight**
>
> Pick the chart from the **question**, not from the data. "How did it change?" is a line. "How do these compare?" is a bar. "Are these two related?" is a scatter. Every customisation after that has one job: make the answer to that question easier to see.

---

## Core Explanation

### 1. Choose the chart from the question

| The question | Chart | Matplotlib method |
|---|---|---|
| How did a number change over time? | Line | `ax.plot` |
| How do categories compare? | Bar (horizontal when labels are long) | `ax.bar`, `ax.barh` |
| Are two numbers related? | Scatter | `ax.scatter` |
| What is the range or uncertainty? | Shaded band or error bars | `ax.fill_between`, `ax.errorbar` |
| How is a total split into parts? | Stacked bar (pie only for 2 or 3 parts) | `ax.bar(..., bottom=)`, `ax.pie` |
| How are values spread out? | Histogram, box plot | `ax.hist` ([Histograms, Pair Plots and Heatmaps](../07-seaborn-and-storytelling/histograms-pair-plots-and-heatmaps.md) goes deep) |

Set up the imports and an output folder once:

```python
import os
import tempfile

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

out_dir = tempfile.mkdtemp()
rng = np.random.default_rng(42)
```

### 2. Line charts: change over time

Here are 90 days of made-up UPI payments at a shop. Weekends are busier, and there is a slow upward trend:

```python
dates = pd.date_range("2026-01-01", periods=90, freq="D")
weekend_boost = np.where(dates.dayofweek >= 5, 60, 0)
trend = np.linspace(0, 80, 90)
upi = pd.DataFrame({
    "date": dates,
    "payments": (220 + trend + weekend_boost + rng.normal(0, 18, 90)).round().astype(int),
})
upi["avg_7d"] = upi["payments"].rolling(7).mean()
print(upi.head(3).to_string(index=False))
print("rows:", len(upi))
```

Output:

```
      date  payments  avg_7d
2026-01-01       225     NaN
2026-01-02       202     NaN
2026-01-03       295     NaN
rows: 90
```

Plot the raw daily values faintly and the 7-day rolling average boldly, so the trend stands out from the day-to-day noise:

```python
fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
ax.plot(upi["date"], upi["payments"], color="#9DB4D3", linewidth=1, label="Daily payments")
ax.plot(upi["date"], upi["avg_7d"], color="#1F4E8C", linewidth=2.5, label="7-day average")

ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
ax.set_ylabel("UPI payments per day")
ax.set_title("UPI payments are climbing steadily")
ax.legend(loc="upper left", frameon=False)
fig.savefig(os.path.join(out_dir, "line-dates.png"), bbox_inches="tight")
plt.close(fig)
```

![Line chart of daily UPI payments from January to March 2026, with a jagged light line for daily values and a smooth dark line for the 7-day average rising steadily](/img/data-visualization-with-matplotlib-and-seaborn/line-dates.png)

What each piece does:

- **`color`, `linewidth`, `label`** are the three styling arguments you will use most. A hex code like `"#1F4E8C"` gives exact control; names like `"steelblue"` and the default cycle shortcuts `"C0"`, `"C1"` also work.
- **Matplotlib understands pandas dates.** Passing a datetime column puts real dates on the x axis.
- **Locators and formatters** control ticks. A *locator* decides *where* ticks go (`MonthLocator` puts one at the start of each month), a *formatter* decides *what text* they show. `ConciseDateFormatter` writes the shortest unambiguous labels, so you get "Feb" instead of "2026-02-01".
- **`frameon=False`** removes the box around the legend, which is almost always cleaner.

Other line styling options: `linestyle` (`"-"`, `"--"`, `":"`, `"-."`), `marker` (`"o"`, `"s"`, `"^"`, `"x"`), `markersize`, and `alpha` (0 is invisible, 1 is solid). There is also a shorthand format string: `ax.plot(x, y, "o--")` means circle markers joined by a dashed line.

### 3. Scatter plots: is there a relationship?

A scatter plot puts one number on each axis, one dot per row. Two more columns can go into **size** (`s=`) and **colour** (`c=`). Here are made-up innings from a T20 season:

```python
innings = pd.DataFrame({
    "balls": rng.integers(5, 65, 60),
})
innings["strike_rate"] = rng.normal(135, 25, 60).clip(70, 220).round()
innings["runs"] = (innings["balls"] * innings["strike_rate"] / 100).round().astype(int)
innings["sixes"] = (innings["runs"] / 18 + rng.normal(0, 0.8, 60)).clip(0).round().astype(int)
print(innings.describe().loc[["mean", "max"]].round(1).to_string())
```

Output:

```
      balls  strike_rate   runs  sixes
mean   33.7        133.8   46.1    2.6
max    63.0        208.0  106.0    7.0
```

```python
fig, ax = plt.subplots(figsize=(7, 4.5), layout="constrained")
points = ax.scatter(innings["balls"], innings["runs"],
                    c=innings["strike_rate"], cmap="viridis",
                    s=20 + innings["sixes"] * 25, alpha=0.8, edgecolors="white")
fig.colorbar(points, ax=ax, label="Strike rate")
ax.set_xlabel("Balls faced")
ax.set_ylabel("Runs scored")
ax.set_title("Longer innings score more; colour shows how fast")
fig.savefig(os.path.join(out_dir, "scatter.png"), bbox_inches="tight")
plt.close(fig)
```

![Scatter plot of runs against balls faced, coloured by strike rate from purple to yellow, with bigger dots for innings with more sixes](/img/data-visualization-with-matplotlib-and-seaborn/scatter.png)

- **`c=` with a `cmap`** maps a number to a colour. `viridis` runs from dark purple to yellow, is readable in greyscale and works for colour-blind readers, which is why it is Matplotlib's default colour map.
- **`fig.colorbar(points, ax=ax)`** adds the key that explains the colours. Without it, colour carries no information.
- **`s=`** is the marker *area* in points squared. Keep size differences modest; readers judge area poorly.
- **`alpha` and `edgecolors="white"`** keep overlapping dots visible. With thousands of points, lower alpha further.

### 4. Bar charts: comparing categories

Rule one of bar charts: **the bars must start at zero**, because readers compare lengths. Matplotlib does this by default. Rule two: **sort them** unless the categories have a natural order (like days or months).

```python
city_sales = pd.Series(
    {"Pune": 412, "Jaipur": 288, "Kochi": 335, "Indore": 251, "Lucknow": 367, "Nagpur": 199},
    name="sales_lakh",
).sort_values()

fig, ax = plt.subplots(figsize=(7, 4), layout="constrained")
bars = ax.barh(city_sales.index, city_sales.values, color="#4C72B0")
ax.bar_label(bars, labels=[f"₹{v} L" for v in city_sales.values], padding=4)
ax.set_xlabel("Sales this quarter (₹ lakh)")
ax.set_title("Pune leads quarterly sales")
ax.spines[["top", "right"]].set_visible(False)
ax.set_xlim(0, 470)
fig.savefig(os.path.join(out_dir, "bar-sorted.png"), bbox_inches="tight")
plt.close(fig)
print(city_sales.index.tolist())
```

Output:

```
['Nagpur', 'Indore', 'Jaipur', 'Kochi', 'Lucknow', 'Pune']
```

![Horizontal bar chart of quarterly sales for six cities sorted from Nagpur at the bottom to Pune at the top, each bar labelled with its value in rupees lakh](/img/data-visualization-with-matplotlib-and-seaborn/bar-sorted.png)

- **`barh`** makes horizontal bars. City names read naturally on the left instead of being squashed or rotated under vertical bars.
- **Sorting ascending with `barh`** puts the biggest bar on top, because `barh` draws the first category at the bottom.
- **`ax.bar_label`** writes values on the bars. With labels on the bars, readers don't need to trace gridlines.
- **`ax.spines[["top", "right"]].set_visible(False)`** removes two border lines that carry no information.

#### Grouped and stacked bars

To compare two series per category, either place bars side by side (**grouped**) or on top of each other (**stacked**). Matplotlib has no "grouped" switch; you shift each series by half a bar width:

```python
quarters = ["Q1", "Q2", "Q3", "Q4"]
online = np.array([120, 150, 170, 210])
store = np.array([180, 175, 160, 150])
x = np.arange(len(quarters))
width = 0.38

fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4), sharey=True, layout="constrained")

left.bar(x - width / 2, online, width, label="Online", color="#4C72B0")
left.bar(x + width / 2, store, width, label="In store", color="#DD8452")
left.set_xticks(x, labels=quarters)
left.set_title("Grouped: compare channels within a quarter")
left.set_ylabel("Orders (thousands)")
left.legend(frameon=False)

right.bar(quarters, store, label="In store", color="#DD8452")
right.bar(quarters, online, bottom=store, label="Online", color="#4C72B0")
right.set_title("Stacked: see the total and the split")
right.legend(frameon=False, loc="upper left")

fig.savefig(os.path.join(out_dir, "bars-grouped-stacked.png"), bbox_inches="tight")
plt.close(fig)
print("totals:", (online + store).tolist())
```

Output:

```
totals: [300, 325, 330, 360]
```

![Two bar charts side by side: on the left grouped bars comparing online and in-store orders per quarter, on the right the same data stacked to show totals](/img/data-visualization-with-matplotlib-and-seaborn/bars-grouped-stacked.png)

`ax.set_xticks(positions, labels=...)` places a tick at each group's centre and names it. In the stacked version, `bottom=store` starts each online bar where the in-store bar ended.

Which to choose? Grouped bars make it easy to compare the two channels with each other. Stacked bars make the **total** easy to read but only the bottom segment is easy to compare across quarters, because the upper segments have no common baseline.

### 5. Ranges and uncertainty: shaded bands and error bars

When a single number hides a range, show the range. `fill_between` shades the area between two lines:

```python
hours = np.arange(6, 23)
avg_wait = 6 + 5 * np.exp(-((hours - 9) ** 2) / 3) + 6 * np.exp(-((hours - 18.5) ** 2) / 2)
low, high = avg_wait * 0.6, avg_wait * 1.5

fig, ax = plt.subplots(figsize=(8, 3.8), layout="constrained")
ax.fill_between(hours, low, high, color="#4C72B0", alpha=0.2, label="Typical range")
ax.plot(hours, avg_wait, color="#1F4E8C", linewidth=2, label="Average wait")
ax.set_xticks(hours[::2], labels=[f"{h}:00" for h in hours[::2]])
ax.set_ylim(0, None)
ax.set_ylabel("Minutes")
ax.set_title("Metro platform wait by hour of day")
ax.legend(frameon=False, loc="upper left")
fig.savefig(os.path.join(out_dir, "fill-between.png"), bbox_inches="tight")
plt.close(fig)
print(f"worst hour: {hours[avg_wait.argmax()]}:00, {avg_wait.max():.1f} min")
```

Output:

```
worst hour: 18:00, 11.3 min
```

![Line chart of average metro platform waiting time across the day with a shaded band showing the typical range, peaking in the morning and more sharply in the evening](/img/data-visualization-with-matplotlib-and-seaborn/fill-between.png)

`ax.set_ylim(0, None)` fixes the bottom at zero and lets Matplotlib choose the top. For a handful of separate measurements with uncertainty, use error bars instead: `ax.errorbar(x, y, yerr=errors, fmt="o", capsize=4)`, where `fmt="o"` draws only markers (no joining line) and `capsize` adds the little horizontal caps.

### 6. Ticks, limits, scales and formatters

Most "the chart looks wrong" problems are tick problems. The tools:

| Task | Code |
|---|---|
| Set the visible range | `ax.set_xlim(0, 100)`, `ax.set_ylim(bottom=0)` |
| Choose tick positions and labels | `ax.set_xticks([0, 50, 100], labels=["low", "mid", "high"])` |
| Rotate crowded labels | `ax.tick_params(axis="x", labelrotation=45)` |
| At most N "nice" ticks | `ax.yaxis.set_major_locator(mticker.MaxNLocator(5))` |
| Percent | `ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))` |
| Thousands separators | `ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))` |
| Any custom text | `mticker.FuncFormatter(lambda value, pos: ...)` |
| Log scale | `ax.set_yscale("log")` |

Formatters are just functions from a number to a string, so you can test them without drawing anything. Indian readers expect lakh and crore, so write a formatter for that:

```python
def rupees(value, pos=None):
    """Format a rupee amount the Indian way: crore, lakh or plain."""
    if value >= 1e7:
        return f"₹{value / 1e7:.2f}".rstrip("0").rstrip(".") + " Cr"
    if value >= 1e5:
        return f"₹{value / 1e5:.1f}".rstrip("0").rstrip(".") + " L"
    return f"₹{value:,.0f}"

for amount in [75_000, 4_50_000, 2_30_00_000]:
    print(amount, "->", rupees(amount))

print(mticker.StrMethodFormatter("{x:,.0f}")(1234567))
```

Output:

```
75000 -> ₹75,000
450000 -> ₹4.5 L
23000000 -> ₹2.3 Cr
1,234,567
```

The `pos` argument is the tick's position number; Matplotlib passes it, and most formatters ignore it. Use it with `ax.yaxis.set_major_formatter(mticker.FuncFormatter(rupees))`. You'll see it on a chart in the next section.

A **log scale** is the right choice when values span several orders of magnitude (₹500 to ₹50 lakh) or when you care about growth *rates*: on a log axis, equal percentage growth looks like a straight line.

### 7. Annotations, reference lines and highlighted regions

Annotations are where a chart starts telling a story. Mark the target, shade the festival week, and label the record:

```python
months = pd.date_range("2025-04-01", periods=12, freq="MS")
revenue = np.array([42, 45, 44, 48, 51, 55, 83, 61, 58, 60, 64, 70]) * 1e5

fig, ax = plt.subplots(figsize=(9, 4.2), layout="constrained")
ax.plot(months, revenue, marker="o", color="#1F4E8C", linewidth=2)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(rupees))
ax.set_ylim(0, 95e5)

ax.axhline(60e5, color="grey", linestyle="--", linewidth=1)
ax.text(months[0], 61.5e5, "Monthly target ₹60 L", color="grey")

ax.axvspan(pd.Timestamp("2025-09-20"), pd.Timestamp("2025-11-10"), color="#F2C14E", alpha=0.25)
ax.text(pd.Timestamp("2025-09-24"), 8e5, "Festive season", color="#8A6D00")

peak = revenue.argmax()
ax.annotate(f"Diwali month: {rupees(revenue[peak])}",
            xy=(months[peak], revenue[peak]), xytext=(months[peak] + pd.Timedelta(days=45), 88e5),
            arrowprops={"arrowstyle": "->", "color": "black"})

ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
ax.set_title("Revenue crossed the target in the festive season and stayed close after")
ax.spines[["top", "right"]].set_visible(False)
fig.savefig(os.path.join(out_dir, "annotated.png"), bbox_inches="tight")
plt.close(fig)
print(months[peak].strftime("%B %Y"), rupees(revenue[peak]))
```

Output:

```
October 2025 ₹83 L
```

![Monthly revenue line chart for a financial year with a dashed target line at 60 lakh, a yellow shaded festive-season band, and an arrow labelling the Diwali-month peak](/img/data-visualization-with-matplotlib-and-seaborn/annotated.png)

| Tool | What it draws |
|---|---|
| `ax.axhline(y)` / `ax.axvline(x)` | A line across the whole Axes at one value: targets, averages, launch dates |
| `ax.axhspan(y1, y2)` / `ax.axvspan(x1, x2)` | A shaded band: a period, a safe range |
| `ax.text(x, y, "...")` | Text at a data position |
| `ax.annotate("...", xy=..., xytext=..., arrowprops=...)` | Text at `xytext` with an arrow pointing at `xy` |

Notice the title. It says what the reader should see ("crossed the target in the festive season") instead of what the axes are ("Revenue by month"). You'll practise this in [Styling Charts for Communication](../07-seaborn-and-storytelling/styling-charts-for-communication.md).

### 8. Legends

A legend collects every Artist that has a `label=`. The options you will need:

- **`loc`**: `"upper left"`, `"lower right"`, `"center"` and so on, or `"best"` (the default, which picks a spot with few points; it can be slow on big data).
- **`ncols`**: lay entries out in columns, useful for a legend across the top.
- **`bbox_to_anchor`**: place the legend relative to the Axes, including *outside* it. `ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1))` puts it just right of the plot area.
- **`frameon=False`, `title="..."`** for a cleaner look and a heading.

Often the best legend is no legend: write the series name at the end of each line with `ax.text`. [Styling Charts for Communication](../07-seaborn-and-storytelling/styling-charts-for-communication.md) shows how.

### 9. Two y-axes: know it, rarely use it

`ax.twinx()` creates a second Axes that shares the x axis but has its own y axis on the right. It is a common request ("revenue and number of orders on one chart") and a common way to mislead, because the reader can't tell which line belongs to which scale, and you can make the lines cross anywhere by changing either scale. Better options are two Axes stacked with `sharex=True`, or indexing both series to 100 at the start so they share one scale.

```python
orders = np.array([900, 950, 930, 1010, 1080, 1150, 1700, 1260, 1210, 1250, 1320, 1440])
indexed = pd.DataFrame({"Revenue": revenue / revenue[0] * 100,
                        "Orders": orders / orders[0] * 100}, index=months)
print(indexed.iloc[[0, 6, 11]].round(1).to_string())
```

Output:

```
            Revenue  Orders
2025-04-01    100.0   100.0
2025-10-01    197.6   188.9
2026-03-01    166.7   160.0
```

Both now start at 100, so "Revenue grew 67% over the year and orders grew 60%" is one honest chart on one axis.

### 10. Plotting straight from pandas

`DataFrame.plot` is a thin wrapper around Matplotlib that returns an Axes, and it accepts `ax=` so it fits the explicit style:

```python
fig, ax = plt.subplots(figsize=(8, 3.8), layout="constrained")
returned = indexed.plot(ax=ax, linewidth=2, color=["#1F4E8C", "#DD8452"])
print(returned is ax)
ax.axhline(100, color="grey", linewidth=0.8)
ax.set_ylabel("Index (April = 100)")
ax.set_xlabel("")
ax.set_title("Revenue and orders grew together")
ax.legend(frameon=False)
fig.savefig(os.path.join(out_dir, "pandas-indexed.png"), bbox_inches="tight")
plt.close(fig)
```

Output:

```
True
```

![Two lines indexed to 100 in April, revenue and orders, both rising over the year with a shared spike in October](/img/data-visualization-with-matplotlib-and-seaborn/pandas-indexed.png)

Use pandas plotting for speed, then finish with `ax.` methods exactly as you would for any other chart.

### 11. Built-in style sheets

Matplotlib ships with style sheets that change many defaults at once. `plt.style.available` lists them. Use one for a single chart with a context manager:

```python
print(len(plt.style.available) > 10, "ggplot" in plt.style.available)
with plt.style.context("ggplot"):
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(months, revenue / 1e5)
    ax.set_title("Same data, ggplot style")
    fig.savefig(os.path.join(out_dir, "style-ggplot.png"), bbox_inches="tight")
    plt.close(fig)
```

Output:

```
True True
```

Styles are a good starting point. Seaborn's themes, covered in [Styling Charts for Communication](../07-seaborn-and-storytelling/styling-charts-for-communication.md), are a better one.

---

## Try It Yourself

1. **Busiest weekday.** Using `upi`, compute the average payments per weekday (`upi["date"].dt.day_name()`) and draw a bar chart in Monday-to-Sunday order. Which day is highest?
2. **Error bars.** Three chai blends were rated by tasters: means `[4.1, 3.6, 4.4]`, standard errors `[0.2, 0.3, 0.15]`. Draw them with `ax.errorbar` and print which blend has the highest mean.
3. **A thousands formatter.** Write `def k_format(value, pos=None)` that turns `12500` into `"12.5k"` and `800` into `"800"`. Test it on both.
4. **Highlight a weekend.** On the line chart from section 2, shade the first weekend (3 and 4 January 2026) with `axvspan`.

<details>
<summary>Show answers</summary>

```python
order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
by_day = upi.groupby(upi["date"].dt.day_name())["payments"].mean().reindex(order)
fig, ax = plt.subplots(figsize=(7, 3.5), layout="constrained")
ax.bar([d[:3] for d in order], by_day.values, color="#4C72B0")
fig.savefig(os.path.join(out_dir, "ex-weekday.png"))
plt.close(fig)
print("busiest:", by_day.idxmax())

blends = ["Masala", "Ginger", "Elaichi"]
means, errors = [4.1, 3.6, 4.4], [0.2, 0.3, 0.15]
fig, ax = plt.subplots()
ax.errorbar(blends, means, yerr=errors, fmt="o", capsize=4)
ax.set_ylim(0, 5)
fig.savefig(os.path.join(out_dir, "ex-errorbar.png"))
plt.close(fig)
print("best blend:", blends[int(np.argmax(means))])

def k_format(value, pos=None):
    return f"{value / 1000:g}k" if value >= 1000 else f"{value:g}"
print(k_format(12500), k_format(800))

fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(upi["date"], upi["payments"])
ax.axvspan(pd.Timestamp("2026-01-03"), pd.Timestamp("2026-01-05"), color="orange", alpha=0.3)
fig.savefig(os.path.join(out_dir, "ex-weekend.png"))
plt.close(fig)
```

Output:

```
busiest: Saturday
best blend: Elaichi
12.5k 800
```

1. A weekend day wins, because the data has a weekend boost built in. `reindex(order)` restores the natural weekday order that `groupby` loses.
2. Elaichi. With `fmt="o"`, points aren't joined, which is right for separate categories.
3. The `:g` format drops trailing zeros, so 12500 becomes `12.5k`.
4. The span ends at the start of 5 January so it covers both weekend days completely.

</details>

---

## Real-World Examples

### Example 1: A startup's investor update

Monthly revenue goes into a line chart with a dashed target line and an annotation on the month a big customer signed. Investors see the trend, the goal and the reason for the jump without reading a paragraph.

### Example 2: Comparing branches

A bank compares loan approvals across 25 branches. A vertical bar chart with rotated names is unreadable; a sorted horizontal bar chart with `bar_label` values lets the regional manager find the bottom five instantly.

### Example 3: Operations dashboards

A delivery company plots average delivery time by hour with a shaded band for the 10th to 90th percentile. The band shows that evenings aren't just slower on average, they are also far less predictable, which changes how many riders are scheduled.

---

## Common Misconceptions

### Misconception 1: "Bar charts can start wherever the data starts"

A bar's length is its message. Starting the axis at 180 makes 200 look twice as big as 190. Line charts can zoom in on a range because readers read the line's position and slope, not its length; bars cannot.

### Misconception 2: "More colours make a chart clearer"

Each colour asks the reader to look up what it means. Use one colour for a single series, a few distinct colours for a few series, and grey plus one highlight colour when one item matters most.

### Misconception 3: "Pie charts are the way to show parts of a whole"

People compare angles badly. With more than three slices, a sorted bar chart of shares is easier to read. Keep pies for "this one part is about half" messages.

### Misconception 4: "Tick labels will sort themselves out"

Default ticks show raw numbers like `4000000.0` or crowded dates. A formatter that writes `₹40 L` or `Feb` is one line of code and often the biggest readability win on the chart.

---

## Interview Relevance

Interviewers often hand you a dataset and ask for a chart, then probe your choices:

- *"Which chart would you use to show X?"* Name the question type (trend, comparison, relationship, distribution, composition) and the chart that answers it, and say why the alternatives are worse.
- *"How would you show uncertainty?"* Error bars for separate estimates, shaded bands for continuous ranges, and say what the band represents (standard error, percentile range).
- *"This chart has two y-axes. What's wrong?"* The relationship between the lines depends on arbitrary scale choices. Offer stacked panels or indexing to a common base.
- *"How do you format currency or large numbers on an axis?"* A `FuncFormatter` (or `StrMethodFormatter`) on the axis.
- *"How would you draw grouped bars in Matplotlib?"* Offset each series' x positions by a fraction of the bar width and set the tick labels at the group centres.

---

## Key Takeaways

- **The question picks the chart**: line for change, bar for comparison, scatter for relationship, bands or error bars for uncertainty.
- **Bars start at zero and are sorted** unless the categories have a natural order; horizontal bars suit long labels.
- **Locators place ticks, formatters write them.** A custom `FuncFormatter` makes rupees, lakh and percentages readable.
- **Annotate the story**: reference lines (`axhline`), highlighted periods (`axvspan`) and labelled points (`annotate`), plus a title that states the finding.
- **Avoid two y-axes**; index to a common base or stack panels instead.
- **pandas `.plot(ax=ax)` and style sheets** are shortcuts that still end in ordinary Axes you can customise.

---

**Up next:** [Lab: Recreate a published chart](lab-recreate-a-published-chart.md)
