---
title: "Lab: Clean and summarise a messy CSV"
course: "Data Analysis and Visualisation with Python"
module: "5. Statistics and Plots in pandas"
type: Lab
level: Beginner
reading_time: 50 min
---

# Lab: Clean and Summarise a Messy CSV

> 📚 **Before you start**
>
> This lab uses the whole course. The lessons it leans on most:
> - [Working with Text Data](../04-text-dates-and-categories-in-pandas/working-with-text-data.md) and [Dates, Times and Timedeltas](../04-text-dates-and-categories-in-pandas/dates-times-and-timedeltas.md)
> - [Categorical Data](../04-text-dates-and-categories-in-pandas/categorical-data.md)
> - [Descriptive Statistics in pandas](descriptive-statistics-in-pandas.md) and [Quick Visualisation with pandas](quick-visualisation-with-pandas.md)
> - [Selecting, Sorting and Indexing Data](../03-pandas-core/selecting-sorting-and-indexing-data.md)

## What You'll Build

A small electronics shop in Hyderabad exports its order book from three different billing tools and emails you the result: one CSV, typed by hand in places, merged badly. Column names are inconsistent, some rows are duplicated, dates come in four formats, amounts carry rupee signs and commas, quantities say "2 pcs", city names are spelt five ways, a few values are missing, and at least one price has an extra zero.

You will turn it into a clean, typed, validated table and a one-page summary, following the workflow every data analyst uses:

```mermaid
flowchart LR
  R["Read raw CSV<br/>everything as text"] --> I["Inspect<br/>what is wrong?"]
  I --> N["Fix column names<br/>and duplicates"]
  N --> T["Clean text<br/>strip, case, variants"]
  T --> D["Parse dates<br/>mixed formats"]
  D --> X["Parse numbers<br/>symbols, units, blanks"]
  X --> M["Missing values<br/>and outliers"]
  M --> V["Types and<br/>validation checks"]
  V --> S["Summarise and plot"]
  S --> E["Export clean CSV"]
```

> 💡 **Key Insight**
>
> Clean data in **small, checked steps**, and never overwrite the raw data. After each step, print a count or a sample that proves the step worked. A cleaning pipeline you can re-run from the raw file is worth far more than a table you fixed by hand.

Run the blocks in order in one file or notebook.

---

## Step 1: Read the Raw File

Here is the export. With a real file you would pass its path to `read_csv`; we keep the text in the code so the lab needs no download.

```python
import io
import os
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

raw_csv = """Order ID, Order Date ,Customer Name,City,Product,Category,Qty,Unit Price,Payment Mode
1001,2026-07-03,Ravi Kumar,Hyderabad,Earbuds,Audio,2,"₹1,499",UPI
1002,04/07/2026,  anita reddy ,hyderabad,Power Bank,Accessories,1 pcs,999,upi
1003,2026-07-05,Mohammed Irfan,Secunderabad,Smart Watch,Wearables,1,"₹3,999",Card
1004,06-07-2026,Sneha Rao,HYD,Earbuds,audio,3,1499,Cash
1005,2026-07-07,Kiran Goud,Warangal,USB Cable,Accessories,4,199,UPI
1005,2026-07-07,Kiran Goud,Warangal,USB Cable,Accessories,4,199,UPI
1006,8 Jul 2026,Lakshmi Devi,Hyderabad ,Bluetooth Speaker,Audio,1,"₹2,499",card
1007,2026-07-09,Arjun Sharma,Secunderabad,Power Bank,Accessories,2 pcs,999,UPI
1008,2026-07-10,priya NAIR,Hyderabad,Smart Watch,Wearables,1,39990,UPI
1009,2026-07-11,Vikram Singh,Warangal,Earbuds,Audio,,1499,Cash
1010,12/07/2026,Fatima Begum,Hyderabad,Charger,Accessories,2,NA,UPI
1011,2026-07-13,Suresh Babu,hyd,Bluetooth Speaker,Audio,1,2499,Card
1012,2026-07-14,Deepa Menon,Secunderabad,USB Cable,Accessories,-1,199,UPI
1013,2026-07-15,Rahul Verma,Karimnagar,Earbuds,Audio,2,1499,UPI
1014,16-07-2026,Kavya Reddy,Hyderabad,Smart Watch,Wearables,1,"3,999",UPI
1015,2026-07-17,,Hyderabad,Power Bank,Accessories,1,999,Cash
1016,2026-07-18,Naveen Chary,Secunderabad,Charger,Accessories,3,649,upi
1017,2026-07-19,Meena Kumari,Warangal,Bluetooth Speaker,Audio,1,-,Card
1018,20 Jul 2026,Ajay Yadav,Hyderabad,Earbuds,Audio,1,"₹1,499",UPI
1019,2026-07-21,Sana Khan,Hyderabad,Smart Watch,Wearables,2,3999,Card
1020,2026-07-22,Gopal Rao,Secunderabad,USB Cable,Accessories,5 pcs,199,Cash
"""

raw = pd.read_csv(io.StringIO(raw_csv), dtype=str, keep_default_na=False)
print(raw.shape)
print(raw.head(4).to_string())
```

Output:

```
(21, 9)
  Order ID  Order Date    Customer Name          City      Product     Category    Qty Unit Price Payment Mode
0     1001   2026-07-03      Ravi Kumar     Hyderabad      Earbuds        Audio      2     ₹1,499          UPI
1     1002   04/07/2026    anita reddy      hyderabad   Power Bank  Accessories  1 pcs        999          upi
2     1003   2026-07-05  Mohammed Irfan  Secunderabad  Smart Watch    Wearables      1     ₹3,999         Card
3     1004   06-07-2026       Sneha Rao           HYD      Earbuds        audio      3       1499         Cash
```

Two choices in that `read_csv` call are deliberate:

- **`dtype=str`** reads every column as text. We want to see exactly what is in the file before pandas guesses types (it would read `Qty` as text anyway because of "1 pcs", and silently turn `NA` into a missing value).
- **`keep_default_na=False`** stops pandas from converting strings such as `NA` or empty fields into `NaN` on its own. We will decide what counts as missing.

---

## Step 2: Inspect

List what is wrong before fixing anything. A few quick probes:

```python
print(raw.columns.tolist())
print("duplicate rows:", raw.duplicated().sum())
for col in ["City", "Category", "Payment Mode"]:
    print(col, "->", sorted(raw[col].unique()))
print("Qty values  :", sorted(raw["Qty"].unique()))
print("Price values:", sorted(raw["Unit Price"].unique()))
```

Output:

```
['Order ID', ' Order Date ', 'Customer Name', 'City', 'Product', 'Category', 'Qty', 'Unit Price', 'Payment Mode']
duplicate rows: 1
City -> ['HYD', 'Hyderabad', 'Hyderabad ', 'Karimnagar', 'Secunderabad', 'Warangal', 'hyd', 'hyderabad']
Category -> ['Accessories', 'Audio', 'Wearables', 'audio']
Payment Mode -> ['Card', 'Cash', 'UPI', 'card', 'upi']
Qty values  : ['', '-1', '1', '1 pcs', '2', '2 pcs', '3', '4', '5 pcs']
Price values: ['-', '1499', '199', '2499', '3,999', '3999', '39990', '649', '999', 'NA', '₹1,499', '₹2,499', '₹3,999']
```

The problems, written down as a checklist:

| Problem | Example | Fix |
|---|---|---|
| Messy column names | `" Order Date "` | strip, lowercase, snake_case |
| Duplicate row | order 1005 twice | `drop_duplicates` |
| Inconsistent case and spaces | `"  anita reddy "`, `"upi"` | `str.strip`, `str.title`, `str.upper` |
| City variants | `HYD`, `hyd`, `Hyderabad ` | mapping dictionary |
| Mixed date formats | `2026-07-03`, `04/07/2026`, `06-07-2026`, `8 Jul 2026` | `to_datetime` in two passes (ISO, then day-first) |
| Symbols in numbers | `"₹1,499"`, `"5 pcs"` | regex `str.replace` and `to_numeric` |
| Missing markers | empty, `NA`, `-` | treat as missing |
| Impossible values | quantity `-1`, price `39990` | rules and outlier checks |

---

## Step 3: Fix Column Names and Duplicates

```python
df = raw.copy()                                    # never modify the raw data
df.columns = (df.columns.str.strip().str.lower()
                .str.replace(r"[^a-z0-9]+", "_", regex=True).str.strip("_"))
print(df.columns.tolist())

before = len(df)
df = df.drop_duplicates()
print("removed duplicates:", before - len(df))
print("order ids unique now:", df["order_id"].is_unique)
```

Output:

```
['order_id', 'order_date', 'customer_name', 'city', 'product', 'category', 'qty', 'unit_price', 'payment_mode']
removed duplicates: 1
order ids unique now: True
```

`drop_duplicates()` removes rows that are identical in **every** column. If two rows shared an order id but differed elsewhere, that would be a conflict to investigate, not a duplicate to drop; checking `is_unique` afterwards catches that case.

---

## Step 4: Clean the Text Columns

```python
text_cols = ["customer_name", "city", "product", "category", "payment_mode"]
for col in text_cols:
    df[col] = df[col].str.strip()

df["customer_name"] = df["customer_name"].str.title().replace("", np.nan)
df["category"] = df["category"].str.title()
df["payment_mode"] = df["payment_mode"].str.upper().replace({"CARD": "Card", "CASH": "Cash"})

city_fix = {"hyd": "Hyderabad", "hyderabad": "Hyderabad"}
df["city"] = df["city"].str.lower().replace(city_fix).str.title()

for col in ["city", "category", "payment_mode"]:
    print(col, "->", df[col].value_counts().to_dict())
print("missing names:", df["customer_name"].isna().sum())
```

Output:

```
city -> {'Hyderabad': 11, 'Secunderabad': 5, 'Warangal': 3, 'Karimnagar': 1}
category -> {'Audio': 8, 'Accessories': 8, 'Wearables': 4}
payment_mode -> {'UPI': 11, 'Card': 5, 'Cash': 4}
missing names: 1
```

Lowercasing before the replacement means the mapping needs one key per variant. The empty customer name became a proper missing value instead of an empty string, so `isna()` can see it.

---

## Step 5: Parse the Dates

The order date arrives in four formats. The slash and dash dates are day-first (Indian style), so a natural first attempt is `format="mixed"` with `dayfirst=True`, which parses each value on its own. Try it on a copy and check the result before keeping it:

```python
dates_text = df["order_date"].str.strip()
attempt = pd.to_datetime(dates_text, format="mixed", dayfirst=True)
print(attempt.dt.strftime("%d %b").tolist())
print("in order:", attempt.is_monotonic_increasing)
```

Output:

```
['07 Mar', '04 Jul', '07 May', '06 Jul', '07 Jul', '08 Jul', '07 Sep', '07 Oct', '07 Nov', '12 Jul', '13 Jul', '14 Jul', '15 Jul', '16 Jul', '17 Jul', '18 Jul', '19 Jul', '20 Jul', '21 Jul', '22 Jul']
in order: False
```

Every value parsed, but the order ids run in date order, so the dates should be increasing, and they are not. Look closely: `2026-07-03` became **7 March**. With `dayfirst=True`, the per-value parser also swaps month and day in ISO dates (`YYYY-MM-DD`), which are never day-first. No error, no warning; only the sanity check caught it.

The fix is to parse in two passes: first the unambiguous ISO dates with `format="ISO8601"`, turning everything else into `NaT`, then only the remaining values with `dayfirst=True`:

```python
iso = pd.to_datetime(dates_text, format="ISO8601", errors="coerce")
others = pd.to_datetime(dates_text[iso.isna()], format="mixed", dayfirst=True)
df["order_date"] = iso.fillna(others)

print(df["order_date"].dtype)
print(df["order_date"].dt.strftime("%d %b").tolist())
print("unparsed:", df["order_date"].isna().sum())
print("in order:", df["order_date"].is_monotonic_increasing)
```

Output:

```
datetime64[us]
['03 Jul', '04 Jul', '05 Jul', '06 Jul', '07 Jul', '08 Jul', '09 Jul', '10 Jul', '11 Jul', '12 Jul', '13 Jul', '14 Jul', '15 Jul', '16 Jul', '17 Jul', '18 Jul', '19 Jul', '20 Jul', '21 Jul', '22 Jul']
unparsed: 0
in order: True
```

All dates now fall in July and increase with the order id. The lesson generalises: **mixed formats need a check that does not depend on the parser**, such as order, range or day-of-week, because a wrong parse looks exactly like a right one.

---

## Step 6: Parse the Numbers

Quantities carry a unit and prices carry a rupee sign and commas. Remove everything that is not part of a number, then convert with `pd.to_numeric(..., errors="coerce")`, which turns anything still unparseable (`NA`, `-`, empty) into `NaN`:

```python
qty_text = df["qty"].str.replace(r"[^\d-]", "", regex=True)          # keep digits and minus
price_text = df["unit_price"].str.replace(r"[₹,\s]", "", regex=True)  # drop ₹, commas, spaces

df["qty"] = pd.to_numeric(qty_text, errors="coerce")
df["unit_price"] = pd.to_numeric(price_text, errors="coerce")

print(df[["order_id", "qty", "unit_price"]].dtypes.to_dict())
print("missing qty:", df["qty"].isna().sum(), "| missing price:", df["unit_price"].isna().sum())
print(df.loc[df["unit_price"].isna(), ["order_id", "product"]].to_string(index=False))
```

Output:

```
{'order_id': <StringDtype(storage='python', na_value=nan)>, 'qty': dtype('float64'), 'unit_price': dtype('float64')}
missing qty: 1 | missing price: 2
order_id           product
    1010           Charger
    1017 Bluetooth Speaker
```

`errors="coerce"` is safe here because we looked at every distinct value in Step 2; on unfamiliar data, compare the counts of missing values before and after to make sure nothing valid was lost.

---

## Step 7: Missing Values and Impossible Values

Each problem needs a decision, and the decision depends on the business, not on pandas. Ours:

1. **Missing unit price**: every product has a standard price, so fill it from the **median price of the same product** (`groupby` + `transform`).
2. **Missing quantity**: we cannot guess how many were bought, so keep the row but flag it and leave it out of revenue.
3. **Negative quantity**: a return, not a sale. Move it to a separate table.
4. **Price outliers**: a price far from the product's usual price is probably a typing error. Find it with the **IQR rule** within each product, then check it by eye.

```python
product_median = df.groupby("product")["unit_price"].transform("median")
filled = df["unit_price"].isna()
df["unit_price"] = df["unit_price"].fillna(product_median)
print("prices filled:", filled.sum(), "->", df.loc[filled, ["product", "unit_price"]].values.tolist())

returns = df[df["qty"] < 0]
df = df[~(df["qty"] < 0)]
print("returns moved out:", returns["order_id"].tolist())
```

Output:

```
prices filled: 2 -> [['Charger', 649.0], ['Bluetooth Speaker', 2499.0]]
returns moved out: ['1012']
```

`~(df["qty"] < 0)` keeps rows with missing quantity, because `NaN < 0` is `False`. Writing `df[df["qty"] >= 0]` would have silently dropped them too.

Now the outliers. For each product, compute the quartiles and flag prices outside Q1 − 1.5 × IQR to Q3 + 1.5 × IQR. With so few orders per product, the IQR is often zero, so we also compare with the product's median:

```python
g = df.groupby("product")["unit_price"]
q1, q3 = g.transform(lambda s: s.quantile(0.25)), g.transform(lambda s: s.quantile(0.75))
iqr = q3 - q1
outlier = (df["unit_price"] < q1 - 1.5 * iqr) | (df["unit_price"] > q3 + 1.5 * iqr)
print(df.loc[outlier, ["order_id", "product", "unit_price"]].to_string(index=False))
ratio = df["unit_price"] / g.transform("median")
print("ratio to product median:", ratio[outlier].round(1).tolist())
```

Output:

```
order_id     product  unit_price
    1008 Smart Watch     39990.0
ratio to product median: [10.0]
```

The Smart Watch at ₹39,990 is exactly ten times the usual ₹3,999: a typing error with an extra zero. Fix it, and record that you did:

```python
fix_mask = outlier & (ratio.round() == 10)
df.loc[fix_mask, "unit_price"] = df.loc[fix_mask, "unit_price"] / 10
corrections = [f"order {oid}: unit_price divided by 10" for oid in df.loc[fix_mask, "order_id"]]
print(corrections)
```

Output:

```
['order 1008: unit_price divided by 10']
```

Keeping a list of corrections (an **audit trail**) lets the shop owner see and approve every change you made to their data.

---

## Step 8: Final Types and Validation

Give every column its proper type. Quantity uses the nullable `Int64` so it can stay an integer despite the missing value; low-cardinality text becomes `category`:

```python
df = df.astype({
    "order_id": "int64",
    "qty": "Int64",
    "unit_price": "float64",
    "city": "category",
    "category": "category",
    "payment_mode": "category",
})
df["revenue"] = (df["qty"] * df["unit_price"]).astype("Float64")
df = df.reset_index(drop=True)
print(df.dtypes)
```

Output:

```
order_id                  int64
order_date       datetime64[us]
customer_name               str
city                   category
product                     str
category               category
qty                       Int64
unit_price              float64
payment_mode           category
revenue                 Float64
dtype: object
```

Now **validate**: write the rules the clean data must satisfy as checks that fail loudly. If a future export breaks one, you find out immediately instead of in a wrong report.

```python
checks = {
    "order ids unique": df["order_id"].is_unique,
    "dates in July 2026": df["order_date"].between("2026-07-01", "2026-07-31").all(),
    "quantities positive": (df["qty"].dropna() > 0).all(),
    "prices present and positive": (df["unit_price"] > 0).all(),
    "known payment modes": set(df["payment_mode"].cat.categories) <= {"UPI", "Card", "Cash"},
    "no stray spaces in names": not df["customer_name"].dropna().str.contains(r"^\s|\s$").any(),
}
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
assert all(checks.values()), "cleaning failed a validation check"
```

Output:

```
PASS  order ids unique
PASS  dates in July 2026
PASS  quantities positive
PASS  prices present and positive
PASS  known payment modes
PASS  no stray spaces in names
```

---

## Step 9: Summarise

The clean table can now answer the owner's questions.

```python
print(df.to_string(max_rows=6))
total = df["revenue"].sum()
print(f"\norders: {len(df)} | items: {df['qty'].sum()} | revenue: Rs {total:,.0f}")
print(f"orders without quantity (excluded from revenue): {df['qty'].isna().sum()}")
```

Output:

```
    order_id order_date   customer_name          city      product     category  qty  unit_price payment_mode  revenue
0       1001 2026-07-03      Ravi Kumar     Hyderabad      Earbuds        Audio    2      1499.0          UPI   2998.0
1       1002 2026-07-04     Anita Reddy     Hyderabad   Power Bank  Accessories    1       999.0          UPI    999.0
2       1003 2026-07-05  Mohammed Irfan  Secunderabad  Smart Watch    Wearables    1      3999.0         Card   3999.0
..       ...        ...             ...           ...          ...          ...  ...         ...          ...      ...
16      1018 2026-07-20      Ajay Yadav     Hyderabad      Earbuds        Audio    1      1499.0          UPI   1499.0
17      1019 2026-07-21       Sana Khan     Hyderabad  Smart Watch    Wearables    2      3999.0         Card   7998.0
18      1020 2026-07-22       Gopal Rao  Secunderabad    USB Cable  Accessories    5       199.0         Cash    995.0

orders: 19 | items: 34 | revenue: Rs 48,516
orders without quantity (excluded from revenue): 1
```

Revenue by category and city, with totals:

```python
pivot = df.pivot_table(index="category", columns="city", values="revenue",
                       aggfunc="sum", margins=True, margins_name="Total", observed=True)
print(pivot.fillna(0).round(0).astype(int))
```

Output:

```
city         Hyderabad  Karimnagar  Secunderabad  Warangal  Total
category                                                         
Accessories       3296           0          4940       796   9032
Audio            13992        2998             0      2499  19489
Wearables        15996           0          3999         0  19995
Total            33284        2998          8939      3295  48516
```

Best-selling products, and how customers pay:

```python
by_product = (df.groupby("product")
                .agg(orders=("order_id", "count"), items=("qty", "sum"), revenue=("revenue", "sum"))
                .sort_values("revenue", ascending=False))
print(by_product)
print(df["payment_mode"].value_counts(normalize=True).round(2).to_dict())
```

Output:

```
                   orders  items  revenue
product                                  
Smart Watch             4      5  19995.0
Earbuds                 5      8  11992.0
Bluetooth Speaker       3      3   7497.0
Power Bank              3      4   3996.0
Charger                 2      5   3245.0
USB Cable               2      9   1791.0
{'UPI': 0.53, 'Card': 0.26, 'Cash': 0.21}
```

Finally a weekly revenue trend, saved as a chart next to the summary:

```python
weekly = df.set_index("order_date")["revenue"].resample("W-SUN").sum()
print(weekly)

out_dir = tempfile.mkdtemp()
fig, (left, right) = plt.subplots(1, 2, figsize=(10, 3.5))
by_product["revenue"].sort_values().plot(kind="barh", ax=left, title="Revenue by product (Rs)")
weekly.plot(marker="o", ax=right, title="Weekly revenue (Rs)")
fig.tight_layout()
chart_path = os.path.join(out_dir, "summary.png")
fig.savefig(chart_path, dpi=100)
plt.close(fig)
print("chart saved:", os.path.exists(chart_path))
```

Output:

```
order_date
2026-07-05     7996.0
2026-07-12    15087.0
2026-07-19    14941.0
2026-07-26    10492.0
Freq: W-SUN, Name: revenue, dtype: Float64
chart saved: True
```

---

## Step 10: Export the Clean Data

Write the cleaned orders, the returns and the audit trail. With real files you would pass paths such as `"orders_clean.csv"`; here we write to the temporary folder and read the clean file back to prove it round-trips:

```python
clean_path = os.path.join(out_dir, "orders_clean.csv")
df.to_csv(clean_path, index=False, date_format="%Y-%m-%d")
returns.to_csv(os.path.join(out_dir, "returns.csv"), index=False)
with open(os.path.join(out_dir, "corrections.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(corrections))

check = pd.read_csv(clean_path, parse_dates=["order_date"])
print(check.shape, "| same revenue:", round(check["revenue"].sum(), 2) == round(float(total), 2))
print(sorted(os.listdir(out_dir)))
```

Output:

```
(19, 10) | same revenue: True
['corrections.txt', 'orders_clean.csv', 'returns.csv', 'summary.png']
```

Note that CSV does not store dtypes: categories come back as text and `Int64` as floats when there are gaps. To keep types between steps of a pipeline, use a typed format such as Parquet (`df.to_parquet`, which needs the `pyarrow` package).

---

## Try It Yourself

1. A new export contains the date `13/07/2026` and the price `"Rs. 2,499/-"`. Would the current pipeline handle both? Test the two cleaning expressions on a small Series.
2. Instead of leaving order 1009's missing quantity out of revenue, fill it with the **most common** quantity for Earbuds. What is the new total revenue?
3. Add a `weekday` column and find which weekday brought in the most revenue.
4. Turn Steps 3 to 6 into a function `clean_orders(raw_df)` that returns the cleaned DataFrame, and check it gives the same number of rows as `df` before the returns were removed.

<details>
<summary>Show answers</summary>

```python
print(pd.to_datetime(pd.Series(["13/07/2026"]), format="mixed", dayfirst=True).dt.date.tolist())
print(pd.Series(["Rs. 2,499/-"]).str.replace(r"[₹,\s]", "", regex=True).tolist(), "<- still has 'Rs.' and '/-'")
print(pd.to_numeric(pd.Series(["Rs. 2,499/-"]).str.replace(r"[^\d.]", "", regex=True)
                    .str.strip("."), errors="coerce").tolist())

earbud_mode = df.loc[df["product"] == "Earbuds", "qty"].mode().iloc[0]
qty_filled = df["qty"].fillna(earbud_mode)
print("mode:", earbud_mode, "| new revenue:", round(float((qty_filled * df["unit_price"]).sum()), 2))

df["weekday"] = df["order_date"].dt.day_name()
print(df.groupby("weekday")["revenue"].sum().idxmax())

def clean_orders(raw_df):
    out = raw_df.copy()
    out.columns = (out.columns.str.strip().str.lower()
                     .str.replace(r"[^a-z0-9]+", "_", regex=True).str.strip("_"))
    out = out.drop_duplicates()
    for col in ["customer_name", "city", "product", "category", "payment_mode"]:
        out[col] = out[col].str.strip()
    out["city"] = out["city"].str.lower().replace(city_fix).str.title()
    text = out["order_date"].str.strip()
    iso = pd.to_datetime(text, format="ISO8601", errors="coerce")
    out["order_date"] = iso.fillna(pd.to_datetime(text[iso.isna()], format="mixed", dayfirst=True))
    out["qty"] = pd.to_numeric(out["qty"].str.replace(r"[^\d-]", "", regex=True), errors="coerce")
    out["unit_price"] = pd.to_numeric(out["unit_price"].str.replace(r"[₹,\s]", "", regex=True),
                                      errors="coerce")
    return out

print(len(clean_orders(raw)), "==", len(df) + len(returns))
```

Output:

```
[datetime.date(2026, 7, 13)]
['Rs.2499/-'] <- still has 'Rs.' and '/-'
[2499]
mode: 2 | new revenue: 51514.0
Tuesday
20 == 20
```

**1.** The date works. The price does not: the pattern only removes `₹`, commas and spaces, so `Rs.` and `/-` remain and `to_numeric` would give `NaN`. Keeping only digits and the decimal point (and stripping a leftover leading dot from "Rs.") handles both styles; always re-run the Step 2 inspection on new exports.

</details>

---

## What You've Learned

- **Read raw data as text** (`dtype=str`, `keep_default_na=False`) so you see the real values before deciding what they mean.
- **Inspect first and write a checklist** of problems: names, duplicates, variants, formats, symbols, missing markers, impossible values.
- **Clean in small checked steps**: `str` methods and mappings for text, `to_datetime` in two passes (ISO first, then `format="mixed", dayfirst=True`) for dates, checked against the order of the data, regex plus `to_numeric(errors="coerce")` for numbers.
- **Make business decisions explicit**: group-wise filling, flags, moving returns out, and an IQR check for outliers with an audit trail of corrections.
- **Set final types** (`Int64`, `category`) and **validate with assertions** so future exports fail loudly.
- **Summarise and export** with `pivot_table`, `groupby`, `resample`, a saved chart and a round-trip check of the clean CSV.

---

**Up next:** [How Matplotlib Thinks: Figures and Axes](../course.md#m6)
