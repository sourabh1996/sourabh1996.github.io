---
title: "Widgets and Layout"
course: Interactive Data Apps with Streamlit
module: "2. Streamlit Basics"
type: Article
level: Beginner
reading_time: 26 min
---

# Widgets and Layout: The Complete Guide

> 📚 **Before you start**
>
> - [What is Streamlit?](what-is-streamlit.md), for the rerun model and running an app
> - [Selecting, Sorting and Indexing Data](../../numerical-computing-and-data-analysis/course.md#m3) (Numerical Computing and Data Analysis), for filtering DataFrames with boolean masks
> - [Dates, Times and Timedeltas](../../numerical-computing-and-data-analysis/course.md#m4), for date ranges

## Introduction

Open a train-booking app. Along the side: From, To, Date, Class, Quota. In the middle: the list of trains, with tabs for "All", "Available" and "Tatkal". A pop-up to confirm. Every one of those is either a **widget** (something the user changes) or a piece of **layout** (where things sit on the page). Getting them right is the difference between an app people use and one they abandon.

In Streamlit, a widget is one function call that returns the user's current choice, and layout is a handful of containers you write into with a `with` block. This lesson covers both completely: every common widget and what it returns, how widgets are identified, keys, callbacks in brief, forms for batching input, and the full layout toolkit (sidebar, columns, tabs, expanders, containers, popovers, placeholders and dialogs).

By the end you'll be able to design a clean, well-organised app page and know which widget suits each kind of input.

> 💡 **Key Insight**
>
> A widget call does two things at once: it **draws** the control, and it **returns** its current value for this run. So `city = st.selectbox("City", cities)` is both the dropdown on the page and the variable your code filters with. Layout containers only change *where* things are drawn, never *whether* the code runs.

---

## Core Explanation

### 1. Widgets return values

Every input widget returns a normal Python value you can use immediately:

```python
# not-run: Streamlit app, run with: streamlit run app.py
import datetime as dt
import streamlit as st

name = st.text_input("Your name", placeholder="e.g. Asha")
cups = st.number_input("Cups per day", min_value=0, max_value=20, value=2, step=1)
drink = st.radio("Favourite", ["Masala chai", "Ginger chai", "Filter coffee"], horizontal=True)
sugar = st.slider("Sugar (spoons)", 0.0, 3.0, 1.0, step=0.5)
extras = st.multiselect("Extras", ["Elaichi", "Ginger", "Tulsi", "Kesar"])
date = st.date_input("Start date", value=dt.date(2026, 10, 1))
daily = st.toggle("Remind me daily")

st.write(f"{name or 'Someone'} drinks {cups} cups of {drink} with {sugar} spoons of sugar.")
st.write("Extras:", extras, "| from", date, "| reminder:", daily)
```

The full catalogue of common widgets, with what each returns:

| Widget | Returns | Notes |
|---|---|---|
| `st.button("Go")` | `True` on the run right after a click, else `False` | Momentary; see section 2 |
| `st.download_button("Download", data, file_name)` | `True` on click | Sends data as a file to the user |
| `st.link_button("Docs", url)` | Nothing | Opens a URL |
| `st.checkbox("Show raw")`, `st.toggle(...)` | `bool` | |
| `st.radio(label, options)` | One option | `horizontal=True`; `index=None` for no default |
| `st.selectbox(label, options)` | One option, or `None` with `index=None` | Best for many options |
| `st.multiselect(label, options)` | `list` of options | `default=[...]`, `max_selections` |
| `st.segmented_control(label, options)` | One option (or a list with `selection_mode="multi"`) | Button-group look |
| `st.pills(label, options)` | Same as above | Chip look |
| `st.slider(label, min, max, value)` | A number, or a **tuple** if `value` is a tuple | Works with dates and times too |
| `st.select_slider(label, options)` | One option, or a tuple | Slider over text options ("Low", "Medium", "High") |
| `st.number_input(...)` | `int` or `float` | Type follows `value` and `step` |
| `st.text_input(...)` | `str` | `type="password"`, `max_chars` |
| `st.text_area(...)` | `str` | Multi-line |
| `st.date_input(...)`, `st.time_input(...)` | `date`/`time`, or a tuple for a range | |
| `st.file_uploader(...)` | `UploadedFile` (file-like), `None`, or a list | `type=["csv"]`, `accept_multiple_files=True` |
| `st.camera_input`, `st.audio_input` | `UploadedFile` or `None` | Photo or recording from the user's device |
| `st.color_picker(...)` | Hex `str` | |
| `st.feedback("thumbs")` | Index of the choice or `None` | Also `"faces"`, `"stars"` |

Arguments shared by most widgets:

- **`label`** (required): the text above the widget. Hide it with `label_visibility="collapsed"`, but keep a meaningful label for screen readers.
- **`key`**: a unique name; see section 3.
- **`help`**: a tooltip with a question-mark icon.
- **`disabled=True`**: shows the widget greyed out.
- **`on_change` / `on_click`**: a function to call when the value changes (covered properly in [Session State](../03-state-and-responsiveness/session-state.md)).
- **`width`**: many elements accept `width="stretch"`, `"content"` or a number of pixels.

### 2. Buttons are momentary

`st.button` returns `True` **only on the rerun triggered by the click**. On the next interaction with anything else, it's `False` again. This surprises everyone once:

```python
# not-run: Streamlit app, run with: streamlit run app.py
import streamlit as st

if st.button("Show the special"):
    st.write("Today: kesar chai, ₹40")
    qty = st.number_input("How many?", 1, 10, 1)   # changing this hides everything!
```

Change the quantity and the special disappears: the number input triggers a rerun in which the button returns `False`, so the `if` block (including the number input itself) isn't drawn. The fixes are to use `st.checkbox`/`st.toggle` for "show/hide", or to remember the click in [session state](../03-state-and-responsiveness/session-state.md). Use buttons for *actions* (save, refresh, send), not for *states*.

### 3. Widget identity and keys

Streamlit needs to know that the slider on this run is "the same" slider as on the last run, so it can return the user's value instead of the default. It works this out from the widget's **identity**:

- **With a `key`**, the key is the identity. You can change the label or help text and the widget keeps its value. (Since version 1.55 every widget works this way, though a few parameters still reset a keyed widget, such as `min_value`/`max_value` on a slider. Each widget's docs list the exceptions.)
- **Without a key**, identity comes from the widget type and its parameters (label, options, min, max, default...). Change any of them and Streamlit treats it as a new widget, resetting it to the default.

Two widgets with the same identity on one page raise a `StreamlitDuplicateElementId` error. That happens with identical widgets in a loop:

```python
# not-run: Streamlit app fragment
for stall in ["Dadar", "Andheri", "Thane"]:
    st.checkbox("Open today", key=f"open_{stall}")   # unique key per stall
```

Also remember: **a widget that isn't drawn in a run is forgotten.** If a widget is inside an `if` that turns false, its value (and its session state entry) is cleaned up at the end of that run, and it reappears with its default later.

### 4. Forms: batch inputs, rerun once

Every widget change causes a rerun. When a user fills five fields, you usually don't want five reruns (and five expensive queries). A **form** groups widgets so that nothing reruns until the submit button is pressed:

```python
# not-run: Streamlit app, run with: streamlit run app.py
import streamlit as st

with st.form("order_form", clear_on_submit=True):
    name = st.text_input("Name")
    drink = st.selectbox("Drink", ["Masala chai", "Ginger chai", "Cold coffee"])
    qty = st.number_input("Quantity", 1, 20, 1)
    submitted = st.form_submit_button("Place order")

if submitted:
    st.success(f"Order placed: {qty} × {drink} for {name or 'guest'}")
```

Rules for forms:

- Every form needs at least one `st.form_submit_button`. On the submit run, all the form's widgets return their new values together.
- Widgets inside a form can't have their own `on_change` callbacks (only the submit button can have `on_click`), and `st.button` isn't allowed inside a form.
- `clear_on_submit=True` resets the fields after submission.
- Forms can't be nested.

You can also write `form = st.form("f")` and then `form.text_input(...)`, `form.form_submit_button(...)` instead of the `with` block. That object-method style works for every container in this lesson.

### 5. Layout: the sidebar

The **sidebar** is a collapsible panel on the left, the conventional place for filters and settings:

```python
# not-run: Streamlit app fragment
import streamlit as st

with st.sidebar:
    st.header("Filters")
    city = st.selectbox("City", ["Pune", "Mumbai", "Nagpur"])
    show_raw = st.checkbox("Show raw data")

# equivalent single-call form
budget = st.sidebar.slider("Budget (₹)", 0, 5000, 1000)
```

### 6. Columns

`st.columns` splits the page into side-by-side containers. Pass a number for equal widths or a list for proportions:

```python
# not-run: Streamlit app fragment
import streamlit as st

c1, c2, c3 = st.columns(3)
c1.metric("Revenue", "₹18.2 L", "+12%")
c2.metric("Orders", "14,082", "+9%")
c3.metric("Avg bill", "₹129", "-2%")

left, right = st.columns([2, 1], gap="large", vertical_alignment="center", border=True)
with left:
    st.subheader("Trend")
    st.line_chart({"cups": [120, 135, 128, 150, 190]})
with right:
    st.subheader("Notes")
    st.write("Friday promotion lifted sales.")
```

The full signature is `st.columns(spec, *, gap="small", vertical_alignment="top", border=False, width="stretch", wrap=True)`. `gap` accepts `"small"`, `"medium"`, `"large"` or a number of pixels. `st.metric(label, value, delta)` draws a big number with a coloured change arrow; it's the standard way to show key figures. On narrow screens columns wrap and stack vertically. Streamlit's guidance is to nest columns at most one level deep.

### 7. Tabs, expanders, containers and popovers

```python
# not-run: Streamlit app fragment
import streamlit as st

tab_chart, tab_table, tab_notes = st.tabs(["Chart", "Table", "Notes"])
with tab_chart:
    st.bar_chart({"Pune": [412], "Mumbai": [520]})
with tab_table:
    st.dataframe({"city": ["Pune", "Mumbai"], "sales": [412, 520]})
with tab_notes:
    st.write("Figures in ₹ lakh.")

with st.expander("How is revenue calculated?"):
    st.write("Sum of bill values after discounts, before tax.")

with st.container(border=True):
    st.write("Grouped content with a border.")

with st.container(height=200):          # fixed height, scrolls inside
    for i in range(30):
        st.write(f"Log line {i}")

with st.popover("Settings"):
    st.checkbox("Show weekends only")
```

| Container | What the user sees | Important behaviour |
|---|---|---|
| `st.tabs([...])` | Clickable tabs | **All tabs' code runs on every rerun**; switching tabs doesn't rerun |
| `st.expander(label)` | A collapsible section | Content is computed even when collapsed |
| `st.container(border=..., height=...)` | An invisible or bordered box | Lets you draw into an earlier spot on the page later |
| `st.popover(label)` | A button that opens a floating panel | Good for rarely used settings |
| `st.empty()` | A single-element placeholder | Each write *replaces* the previous one |

The first row is worth repeating: hiding something in a tab or expander doesn't save computation. If a tab holds an expensive chart, cache the computation.

**Containers let you draw out of order.** A container keeps its place on the page, so you can create it early and fill it later in the script:

```python
# not-run: Streamlit app fragment
import streamlit as st

summary_box = st.container()            # reserved near the top
data = st.file_uploader("Upload CSV")   # drawn below it
if data is not None:
    summary_box.success("File received, results below.")
```

**`st.empty()`** is for things that update in place, such as a progress message in a loop:

```python
# not-run: Streamlit app fragment
import time
import streamlit as st

status = st.empty()
for step in ["Loading", "Cleaning", "Summarising"]:
    status.info(f"{step}...")
    time.sleep(1)
status.success("Done")
```

### 8. Dialogs

A **dialog** is a modal window over the page. Decorate a function with `@st.dialog(title)` and call it to open it:

```python
# not-run: Streamlit app, run with: streamlit run app.py
import streamlit as st

@st.dialog("Confirm order")
def confirm(item, price):
    st.write(f"Order {item} for ₹{price}?")
    if st.button("Yes, place it"):
        st.session_state.last_order = item
        st.rerun()                       # closes the dialog by rerunning the app

if st.button("Buy kesar chai"):
    confirm("Kesar chai", 40)

if "last_order" in st.session_state:
    st.write("Last order:", st.session_state.last_order)
```

Widgets inside a dialog rerun only the dialog function, not the whole page, so the user can interact with it without the page behind it changing. As of version 1.65, `@st.dialog(..., position="left")` or `"right"` opens it as a side drawer instead of a centred box.

### 9. Page configuration

Call `st.set_page_config` near the top of the script:

```python
# not-run: Streamlit app fragment
import streamlit as st

st.set_page_config(page_title="Chai Junction", page_icon="☕", layout="wide",
                   initial_sidebar_state="expanded")
```

`layout="wide"` uses the full browser width, which dashboards almost always want; the default `"centered"` suits reading-style apps.

### 10. Logic first: keep widget code thin

The cleanest apps separate *what the user chose* from *what to do with it*. Write the filtering and calculations as plain functions that take ordinary values, test them without Streamlit, and let the app pass widget values in:

```python
import datetime as dt
import pandas as pd

orders = pd.DataFrame({
    "date": pd.to_datetime(["2026-10-01", "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-03", "2026-10-04"]),
    "city": ["Pune", "Mumbai", "Pune", "Nagpur", "Mumbai", "Pune"],
    "drink": ["Masala chai", "Cold coffee", "Ginger chai", "Masala chai", "Masala chai", "Cold coffee"],
    "amount": [40, 120, 45, 35, 40, 110],
})

def filter_orders(df, cities, drinks, date_range):
    """Return the rows matching the sidebar choices. Empty selections mean 'all'."""
    start, end = date_range
    mask = df["date"].between(pd.Timestamp(start), pd.Timestamp(end))
    if cities:
        mask &= df["city"].isin(cities)
    if drinks:
        mask &= df["drink"].isin(drinks)
    return df[mask]

def summarise(df):
    return {"orders": len(df), "revenue": int(df["amount"].sum()),
            "avg_bill": round(float(df["amount"].mean()), 1) if len(df) else 0.0}

picked = filter_orders(orders, ["Pune"], [], (dt.date(2026, 10, 1), dt.date(2026, 10, 3)))
print(picked.to_string(index=False))
print(summarise(picked))
print(summarise(filter_orders(orders, ["Delhi"], [], (dt.date(2026, 10, 1), dt.date(2026, 10, 4)))))
```

Output:

```
      date city       drink  amount
2026-10-01 Pune Masala chai      40
2026-10-02 Pune Ginger chai      45
{'orders': 2, 'revenue': 85, 'avg_bill': 42.5}
{'orders': 0, 'revenue': 0, 'avg_bill': 0.0}
```

The app file is then mostly layout:

```python
# not-run: Streamlit app, run with: streamlit run app.py
import datetime as dt
import streamlit as st
from logic import orders, filter_orders, summarise   # the functions above, saved as logic.py

st.set_page_config(page_title="Orders", layout="wide")
st.title("Orders explorer")

with st.sidebar:
    cities = st.multiselect("City", sorted(orders["city"].unique()))
    drinks = st.pills("Drink", sorted(orders["drink"].unique()), selection_mode="multi")
    dates = st.date_input("Dates", value=(dt.date(2026, 10, 1), dt.date(2026, 10, 4)))

if len(dates) != 2:
    st.info("Pick an end date.")
    st.stop()

picked = filter_orders(orders, cities, drinks, dates)
stats = summarise(picked)

c1, c2, c3 = st.columns(3)
c1.metric("Orders", stats["orders"])
c2.metric("Revenue", f"₹{stats['revenue']:,}")
c3.metric("Average bill", f"₹{stats['avg_bill']}")

tab_chart, tab_table = st.tabs(["Chart", "Table"])
with tab_chart:
    st.bar_chart(picked.groupby("drink")["amount"].sum())
with tab_table:
    st.dataframe(picked, hide_index=True)
```

Two details: a range `st.date_input` returns a one-item tuple while the user has picked only the start date, so the app checks for two dates; and **`st.stop()`** ends the current run immediately, which is a clean way to wait for valid input.

---

## Try It Yourself

1. **Return types.** Without running anything, write down what each returns: `st.slider("x", 0, 10, (2, 8))`, `st.selectbox("x", ["a", "b"], index=None)` before the user picks, `st.multiselect("x", ["a", "b"])` before the user picks.
2. **Fix the vanishing widget.** Rewrite the "Show the special" example from section 2 so the quantity input doesn't disappear.
3. **Test the logic.** Using `filter_orders`, how many Masala chai orders are there in Mumbai or Pune across all four days, and what is their revenue?
4. **Design a layout.** Sketch (in words or code) a page with filters in the sidebar, three metrics in a row, and a chart and table in tabs. Which containers do you use?

<details>
<summary>Show answers</summary>

```python
masala = filter_orders(orders, ["Mumbai", "Pune"], ["Masala chai"], (dt.date(2026, 10, 1), dt.date(2026, 10, 4)))
print(summarise(masala))
```

Output:

```
{'orders': 2, 'revenue': 80, 'avg_bill': 40.0}
```

1. A tuple `(2, 8)`; `None`; an empty list `[]`.
2. Replace `st.button` with `st.toggle("Show the special")` (or `st.checkbox`). A toggle keeps its value across reruns, so the block stays visible while the user changes the quantity.
3. Two orders and ₹80 of revenue: Pune on 1 October and Mumbai on 3 October. Empty `drinks` would have meant "all drinks"; passing `["Masala chai"]` narrows it.
4. `st.sidebar` for filters, `st.columns(3)` with `st.metric` in each, and `st.tabs(["Chart", "Table"])`. That's exactly the app in section 10.

</details>

---

## Real-World Examples

### Example 1: Sidebar filters, main-area results

Nearly every internal dashboard follows the same pattern: filters in the sidebar, key numbers in columns at the top, details in tabs below. Users learn it once and recognise it everywhere.

### Example 2: Forms for expensive queries

A finance tool queries a data warehouse that takes 20 seconds per query. Putting the five filter widgets in a form means one query per submission instead of one per keystroke or click.

### Example 3: Dialogs for confirmation

An operations app lets staff cancel orders. A `st.dialog` asks "Cancel order #4417 for ₹1,250?" before acting, so a mis-click can't trigger an irreversible action.

---

## Common Misconceptions

### Misconception 1: "Code inside an inactive tab doesn't run"

All tabs run on every rerun. Tabs only control what's visible. Cache any expensive work inside them.

### Misconception 2: "`st.button` can toggle something on"

A button is `True` for exactly one run. For an on/off state, use `st.toggle` or `st.checkbox`, or store the click in session state.

### Misconception 3: "Widgets keep their value no matter what"

A widget that isn't drawn in a run loses its value, and an unkeyed widget whose parameters change is treated as a new widget. Give important widgets a `key`.

### Misconception 4: "More widgets make a better app"

Every widget is a decision you're asking the user to make. Start with the two or three filters that matter, sensible defaults, and add more only when people ask.

---

## Interview Relevance

Questions here are practical, often about an app you've built:

- *"Why does my content disappear when I change another widget?"* It's inside an `if st.button(...)` block; buttons are momentary. Use a toggle or session state.
- *"How do you avoid rerunning on every input?"* Group inputs in `st.form`, so the app reruns once on submit. Also mention caching and fragments.
- *"How does Streamlit know two widgets are the same across reruns?"* Their identity: the `key` if given, otherwise type plus parameters. Duplicate identities raise an error, so loops need unique keys.
- *"How would you lay out a dashboard?"* Sidebar filters, `st.columns` with `st.metric` for KPIs, tabs or expanders for detail, `layout="wide"`.
- *"How do you keep the app testable?"* Put filtering and calculations in plain functions that take ordinary values; the Streamlit layer just passes widget values in.

---

## Key Takeaways

- **A widget is a function call that draws a control and returns its current value.** Know what each returns (tuples for ranges, `None` for empty selections, `UploadedFile` for files).
- **Buttons are momentary**; use toggles, checkboxes or session state for persistent states.
- **Give widgets keys** when they're in loops, in conditional blocks, or have labels that change.
- **Forms batch input** so the app reruns once per submission.
- **Layout containers** (sidebar, columns, tabs, expanders, containers, popovers, empty, dialogs) control placement, not execution; all tabs still run.
- **Keep logic in plain functions** and make the app file mostly layout.

---

**Up next:** [Lab: Your first dashboard](lab-your-first-dashboard.md)
