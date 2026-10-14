---
title: "Array Manipulation and Arithmetic"
course: "Data Analysis and Visualisation with Python"
module: "2. NumPy Essentials"
type: Article
level: Beginner
reading_time: 35 min
---

# Array Manipulation and Arithmetic: The Complete Guide

> 📚 **Before you start**
>
> - [Creating, Indexing and Slicing Arrays](creating-indexing-and-slicing-arrays.md), for building and selecting arrays
> - [Data Types and Array Attributes](data-types-and-array-attributes.md), for dtypes, `nan` and strides
> - [Broadcasting and Iterating over Arrays](broadcasting-and-iterating-over-arrays.md), for how shapes combine

## Introduction

A cricket analyst receives ball-by-ball data as one long list: 120 deliveries in a T20 innings. To see the innings over by over, she needs it as 20 rows of 6 balls. Then she wants to put two innings side by side, split the innings into powerplay, middle and death overs, flip the table so overs run across the top, and compute run rates, running totals and strike rates. None of that changes the numbers themselves; it changes their **arrangement** and then does **arithmetic** on them.

That is what this lesson covers. The first half is **manipulation**: reshaping, transposing, adding and removing axes, joining, splitting, repeating, flipping and rolling arrays. The second half is **arithmetic and maths**: every arithmetic operator and its function form, rounding (including a rounding rule that surprises almost everyone), powers, logs, trigonometry, clipping, and the extra powers of universal functions such as `reduce`, `accumulate`, `outer` and `at`.

By the end you will be able to take any array and reshape it into the layout a calculation needs, combine and split arrays confidently, and apply the full range of NumPy maths functions correctly.

> 💡 **Key Insight**
>
> Most manipulation functions **do not move data**; they return a **view** with a new shape or new strides. Joining functions (`concatenate`, `stack`) and element-adding functions (`append`, `insert`) always **allocate a new array**, which is why building an array one element at a time in a loop is slow.

---

## Core Explanation

### 1. Reshaping

`reshape` gives the same elements a new shape. The total number of elements must stay the same. One dimension may be `-1`, meaning "work this out for me".

```python
import numpy as np

balls = np.array([1, 0, 4, 1, 6, 0,   0, 1, 1, 2, 0, 4,   6, 1, 0, 0, 1, 1,
                  2, 4, 0, 1, 1, 6])          # runs off 24 balls (4 overs)
overs = balls.reshape(4, 6)
print(overs)
print(balls.reshape(-1, 6).shape, balls.reshape(2, -1).shape)
```

Output:

```
[[1 0 4 1 6 0]
 [0 1 1 2 0 4]
 [6 1 0 0 1 1]
 [2 4 0 1 1 6]]
(4, 6) (2, 12)
```

Reshape fills rows first (called **C order** or row-major). Pass `order="F"` to fill columns first (Fortran order), which is rarely needed but explains odd results when data was saved column by column.

```python
try:
    balls.reshape(5, 5)
except ValueError as err:
    print("ValueError:", err)
print(np.arange(6).reshape(2, 3, order="F"))
```

Output:

```
ValueError: cannot reshape array of size 24 into shape (5,5)
[[0 2 4]
 [1 3 5]]
```

To go back to 1-D there are two methods with an important difference:

- **`ravel()`** returns a **view** when it can (no copy).
- **`flatten()`** **always** returns a copy.

```python
flat_view = overs.ravel()
flat_copy = overs.flatten()
print(np.shares_memory(overs, flat_view), np.shares_memory(overs, flat_copy))
```

Output:

```
True False
```

`np.resize(a, new_shape)` is different from `reshape`: it allows a different total size, repeating the data to fill a bigger shape or cutting it to fit a smaller one.

```python
print(np.resize(np.array([1, 2, 3]), (2, 4)))
```

Output:

```
[[1 2 3 1]
 [2 3 1 2]]
```

### 2. Transposing and reordering axes

`.T` swaps rows and columns. For more than two axes, `np.transpose(a, axes)` puts the axes in any order, `np.swapaxes` swaps two of them, and `np.moveaxis` moves one axis to a new position. All of these return **views**.

```python
print(overs.T.shape)                       # balls as rows, overs as columns

images = np.zeros((10, 32, 32, 3))         # 10 images, height, width, channels
print(np.transpose(images, (0, 3, 1, 2)).shape)   # channels first, as PyTorch expects
print(np.moveaxis(images, -1, 1).shape)           # same result, moving one axis
print(np.swapaxes(images, 1, 2).shape)            # swap height and width
```

Output:

```
(6, 4)
(10, 3, 32, 32)
(10, 3, 32, 32)
(10, 32, 32, 3)
```

Converting between "channels last" `(N, H, W, C)` and "channels first" `(N, C, H, W)` is one of the most common reshaping jobs in deep learning, and `moveaxis` is the clearest way to write it.

### 3. Adding and removing length-1 axes

`np.expand_dims(a, axis)` inserts a length-1 axis (the same as indexing with `np.newaxis`). `np.squeeze(a)` removes **all** length-1 axes, or just the one you name.

```python
v = np.array([5, 7, 9])
print(np.expand_dims(v, 0).shape, np.expand_dims(v, 1).shape)

batch = np.zeros((1, 3, 1))
print(np.squeeze(batch).shape, np.squeeze(batch, axis=0).shape)
```

Output:

```
(1, 3) (3, 1)
(3,) (3, 1)
```

### 4. Joining arrays

| Function | What it does | Shapes example |
|---|---|---|
| `np.concatenate([a, b], axis=k)` | join along an **existing** axis | `(2, 3)` + `(2, 3)` on axis 0 → `(4, 3)` |
| `np.stack([a, b], axis=k)` | join along a **new** axis | `(3,)` + `(3,)` → `(2, 3)` |
| `np.vstack` | stack vertically (rows) | `(3,)` + `(3,)` → `(2, 3)` |
| `np.hstack` | stack horizontally | `(3,)` + `(3,)` → `(6,)`; `(2, 3)` + `(2, 1)` → `(2, 4)` |
| `np.column_stack` | 1-D arrays become columns | `(3,)` + `(3,)` → `(3, 2)` |
| `np.dstack` | stack along a third axis | `(2, 2)` + `(2, 2)` → `(2, 2, 2)` |
| `np.block` | assemble from a nested list of blocks | build a matrix from tiles |

```python
inn1 = np.array([[8, 6], [12, 4]])      # two overs: runs, dots
inn2 = np.array([[10, 3], [7, 5]])

print(np.concatenate([inn1, inn2], axis=0))      # more rows
print(np.concatenate([inn1, inn2], axis=1))      # more columns
print(np.stack([inn1, inn2]).shape)              # new first axis: (innings, over, stat)

a, b = np.array([1, 2, 3]), np.array([4, 5, 6])
print(np.vstack([a, b]))
print(np.hstack([a, b]))
print(np.column_stack([a, b]))
print(np.block([[np.eye(2, dtype=int), np.zeros((2, 1), dtype=int)],
                [np.ones((1, 2), dtype=int), np.array([[9]])]]))
```

Output:

```
[[ 8  6]
 [12  4]
 [10  3]
 [ 7  5]]
[[ 8  6 10  3]
 [12  4  7  5]]
(2, 2, 2)
[[1 2 3]
 [4 5 6]]
[1 2 3 4 5 6]
[[1 4]
 [2 5]
 [3 6]]
[[1 0 0]
 [0 1 0]
 [1 1 9]]
```

For `concatenate`, all axes except the joining one must match. For `stack`, all shapes must match exactly. NumPy 2 also offers `np.concat` as an alias of `concatenate` (matching the Python array API standard) and removed `np.row_stack`; use `np.vstack`.

### 5. Splitting arrays

The reverse of joining. `np.split(a, n_or_positions, axis)` cuts into equal parts (it raises an error if they cannot be equal) or at the positions you list. `np.array_split` allows unequal parts. `hsplit`, `vsplit` and `dsplit` are shortcuts for axes 1, 0 and 2.

```python
innings = np.arange(1, 21)                     # overs 1 to 20
powerplay, middle, death = np.split(innings, [6, 15])
print(powerplay, middle, death, sep="\n")

print([part.tolist() for part in np.array_split(np.arange(7), 3)])
left, right = np.hsplit(overs, 2)              # first 3 balls / last 3 balls of each over
print(left.shape, right.shape)
```

Output:

```
[1 2 3 4 5 6]
[ 7  8  9 10 11 12 13 14 15]
[16 17 18 19 20]
[[0, 1, 2], [3, 4], [5, 6]]
(4, 3) (4, 3)
```

`np.unstack(a, axis=0)` (added in NumPy 2.1) is the exact opposite of `np.stack`: it returns a tuple of the slices along an axis.

### 6. Adding, removing, repeating and rearranging elements

These functions **always return a new array**. None of them changes the input.

```python
scores = np.array([45, 67, 12, 89])
print(np.append(scores, [33, 50]))           # add to the end
print(np.insert(scores, 1, 99))              # insert 99 at position 1
print(np.delete(scores, [0, 2]))             # remove positions 0 and 2
print(np.trim_zeros(np.array([0, 0, 3, 5, 0])))   # strip leading/trailing zeros
print(scores)                                # unchanged
```

Output:

```
[45 67 12 89 33 50]
[45 99 67 12 89]
[67 89]
[3 5]
[45 67 12 89]
```

`np.append` without an `axis` flattens 2-D input first, which surprises people; pass `axis=0` or use `concatenate`. And because each call copies the whole array, appending in a loop is slow (each step copies everything again). Collect values in a Python list and convert once at the end.

Repeating and tiling:

```python
print(np.repeat(np.array([1, 2, 3]), 2))          # each element twice
print(np.repeat(np.array([[1, 2], [3, 4]]), [1, 3], axis=0))   # row 1 once, row 2 three times
print(np.tile(np.array([1, 2]), 3))               # the whole array three times
print(np.tile(np.array([1, 2]), (2, 2)))
```

Output:

```
[1 1 2 2 3 3]
[[1 2]
 [3 4]
 [3 4]
 [3 4]]
[1 2 1 2 1 2]
[[1 2 1 2]
 [1 2 1 2]]
```

Flipping, rotating and rolling (these return views where possible):

```python
m = np.array([[1, 2, 3], [4, 5, 6]])
print(np.flip(m))                # reverse along every axis
print(np.fliplr(m))              # left-right (columns reversed)
print(np.flipud(m))              # up-down (rows reversed)
print(np.rot90(m))               # rotate 90 degrees anticlockwise
print(np.roll(np.array([1, 2, 3, 4, 5]), 2))   # shift right by 2, wrapping around
```

Output:

```
[[6 5 4]
 [3 2 1]]
[[3 2 1]
 [6 5 4]]
[[4 5 6]
 [1 2 3]]
[[3 6]
 [2 5]
 [1 4]]
[4 5 1 2 3]
```

`np.roll` is useful for comparing each value with the previous one (`a - np.roll(a, 1)`), though for that job `np.diff` (next lesson) is cleaner.

### 7. Arithmetic operators and their functions

Every operator maps to a ufunc. The function forms accept extra arguments (`out`, `where`, `dtype`), which the operators cannot.

| Operator | Function | Notes |
|---|---|---|
| `a + b` | `np.add` | |
| `a - b` | `np.subtract` | |
| `a * b` | `np.multiply` | element-wise, **not** matrix product |
| `a / b` | `np.divide` (`np.true_divide`) | always float |
| `a // b` | `np.floor_divide` | rounds toward minus infinity |
| `a % b` | `np.mod` (`np.remainder`) | sign follows the divisor, like Python |
| `a ** b` | `np.power` | |
| `-a` | `np.negative` | |
| `abs(a)` | `np.abs` (`np.absolute`) | |
| `a @ b` | `np.matmul` | matrix product, covered in the matrix lesson |

```python
a = np.array([7, -7, 10])
b = np.array([2, 2, 3])
print(a / b)
print(a // b, a % b)          # floor division and modulo, Python-style
print(np.fmod(a, b))          # C-style remainder: sign follows a
print(np.divmod(a, b))        # both at once
print(np.power(b, 3), np.reciprocal(np.array([1.0, 4.0, 0.5])))
```

Output:

```
[ 3.5        -3.5         3.33333333]
[ 3 -4  3] [1 1 1]
[ 1 -1  1]
(array([ 3, -4,  3]), array([1, 1, 1]))
[ 8  8 27] [1.   0.25 2.  ]
```

`-7 // 2` is `-4`, not `-3`, because floor division rounds down. Python's own `//` does the same.

**Division by zero** does not raise an exception in NumPy. Float division gives `inf`, `-inf` or `nan` and prints a `RuntimeWarning`; integer division by zero gives 0 with a warning. You can silence or escalate those warnings with `np.errstate`:

```python
with np.errstate(divide="ignore", invalid="ignore"):
    print(np.array([1.0, 0.0, -1.0]) / 0)

try:
    with np.errstate(divide="raise"):
        np.array([1.0]) / 0
except FloatingPointError as err:
    print("FloatingPointError:", err)
```

Output:

```
[ inf  nan -inf]
FloatingPointError: divide by zero encountered in divide
```

Turning warnings into errors inside a `with np.errstate(all="raise")` block is a good debugging habit when `nan`s appear and you don't know where from.

### 8. Rounding

| Function | What it does | `[-2.5, -1.5, 1.5, 2.5, 2.7]` becomes |
|---|---|---|
| `np.round(a, d)` | round to `d` decimals, **halves to even** | `[-2, -2, 2, 2, 3]` |
| `np.floor` | down, toward minus infinity | `[-3, -2, 1, 2, 2]` |
| `np.ceil` | up, toward plus infinity | `[-2, -1, 2, 3, 3]` |
| `np.trunc` | toward zero (drop the decimals) | `[-2, -1, 1, 2, 2]` |
| `np.rint` | to nearest integer, halves to even | `[-2, -2, 2, 2, 3]` |

```python
x = np.array([-2.5, -1.5, 1.5, 2.5, 2.7])
for f in [np.round, np.floor, np.ceil, np.trunc, np.rint]:
    print(f"{f.__name__:6}", f(x))
print(np.round(np.array([1234.5678]), 2), np.round(np.array([1234.5678]), -2))
```

Output:

```
round  [-2. -2.  2.  2.  3.]
floor  [-3. -2.  1.  2.  2.]
ceil   [-2. -1.  2.  3.  3.]
trunc  [-2. -1.  1.  2.  2.]
rint   [-2. -2.  2.  2.  3.]
[1234.57] [1200.]
```

The surprise is `np.round(2.5) == 2.0`. NumPy (like Python's built-in `round`) uses **round half to even**, also called **banker's rounding**: exact halves go to the nearest even number. Over many values this avoids the upward bias of always rounding halves up. If a bill must round ₹2.50 up to ₹3, use `np.floor(x + 0.5)` for positive amounts. Negative decimals round to tens, hundreds and so on. (`np.round_` was removed in NumPy 2; use `np.round` or `np.around`.)

### 9. Powers, logs, trigonometry and other maths

```python
v = np.array([1.0, 4.0, 9.0, 100.0])
print(np.sqrt(v), np.cbrt(np.array([8.0, 27.0])), np.square(np.array([3, 4])))
print(np.exp(np.array([0.0, 1.0])).round(4))
print(np.log(np.array([1.0, np.e])), np.log10(v), np.log2(np.array([8.0, 1024.0])))
print(np.log1p(np.array([0.0, 1e-10])))      # log(1 + x), accurate for tiny x

angles = np.array([0, 30, 90, 180])
rad = np.deg2rad(angles)
print(np.sin(rad).round(3), np.cos(rad).round(3))
print(np.rad2deg(np.arctan2(1, 1)), np.hypot(3, 4))
print(np.sign(np.array([-5, 0, 3])), np.abs(np.array([-5, 0, 3])))
```

Output:

```
[ 1.  2.  3. 10.] [2. 3.] [ 9 16]
[1.     2.7183]
[0. 1.] [0.         0.60205999 0.95424251 2.        ] [ 3. 10.]
[0.e+00 1.e-10]
[0.  0.5 1.  0. ] [ 1.     0.866  0.    -1.   ]
45.0 5.0
[-1  0  1] [5 0 3]
```

Trigonometric functions work in **radians**; convert with `np.deg2rad` and `np.rad2deg` (or `np.radians`, `np.degrees`). The constants `np.pi` and `np.e` are built in. Logs of zero give `-inf` and of negative numbers give `nan`, with a warning.

**Clipping** limits values to a range, which is the safe way to cap things:

```python
speeds = np.array([35, 52, 81, 120, 64])
print(np.clip(speeds, 40, 100))              # below 40 -> 40, above 100 -> 100
print(np.minimum(speeds, 100), np.maximum(speeds, 40))
```

Output:

```
[ 40  52  81 100  64]
[ 35  52  81 100  64] [ 40  52  81 120  64]
```

`np.minimum`/`np.maximum` compare two arrays element by element and return the smaller/larger. Their `nan`-ignoring versions are `np.fmin` and `np.fmax`.

### 10. Advanced ufunc powers

Every binary ufunc (one that takes two inputs, such as `np.add`) has extra methods:

```python
print(np.add.reduce(np.array([1, 2, 3, 4])))          # 1+2+3+4, same as sum
print(np.multiply.accumulate(np.array([1, 2, 3, 4])))  # running product
print(np.add.accumulate(balls[:6]))                    # running total over one over
print(np.multiply.outer(np.array([1, 2, 3]), np.array([10, 100])))
```

Output:

```
10
[ 1  2  6 24]
[ 1  1  5  6 12 12]
[[ 10 100]
 [ 20 200]
 [ 30 300]]
```

`np.cumsum` and `np.cumprod` are the everyday names for `add.accumulate` and `multiply.accumulate`. NumPy 2.1 added `np.cumulative_sum` and `np.cumulative_prod` (from the array API standard), which also accept `include_initial=True` to start with 0 or 1.

```python
print(np.cumsum(balls[:6]))
print(np.cumulative_sum(balls[:6], include_initial=True))
```

Output:

```
[ 1  1  5  6 12 12]
[ 0  1  1  5  6 12 12]
```

**`out=`** writes the result into an existing array instead of allocating a new one, and **`where=`** applies the operation only where a mask is true:

```python
totals = np.zeros(3)
np.add(np.array([1.0, 2.0, 3.0]), 10, out=totals)
print(totals)

values = np.array([4.0, -1.0, 9.0])
result = np.full(3, np.nan)
np.sqrt(values, out=result, where=values >= 0)     # skip the negative one
print(result)
```

Output:

```
[11. 12. 13.]
[ 2. nan  3.]
```

**`ufunc.at`** applies an operation at given positions and, unlike `a[idx] += 1`, handles **repeated** positions correctly. This is how you count events per bucket:

```python
counts = np.zeros(4, dtype=int)
hits = np.array([0, 2, 2, 3, 2])
counts[hits] += 1                 # repeated index 2 is only incremented once
print(counts)

counts = np.zeros(4, dtype=int)
np.add.at(counts, hits, 1)        # every occurrence counts
print(counts)
```

Output:

```
[1 0 1 1]
[1 0 3 1]
```

`np.bincount(hits)` gives the same counts directly; you will meet it in the next lesson.

### 11. Putting it together: an innings summary

```python
innings = np.array([
    [1, 0, 4, 1, 6, 0], [0, 1, 1, 2, 0, 4], [6, 1, 0, 0, 1, 1], [2, 4, 0, 1, 1, 6],
    [0, 0, 1, 1, 4, 1], [1, 6, 6, 0, 1, 2],
])                                              # 6 overs x 6 balls

per_over = innings.sum(axis=1)
print("runs per over :", per_over)
print("running total :", np.cumsum(per_over))
print("run rate      :", np.round(np.cumsum(per_over) / np.arange(1, 7), 2))
print("boundaries    :", np.isin(innings, [4, 6]).sum())
print("dot-ball %    :", np.round((innings == 0).mean() * 100, 1))
print("strike rate   :", np.round(innings.sum() / innings.size * 100, 1))
```

Output:

```
runs per over : [12  8  9 14  7 16]
running total : [12 20 29 43 50 66]
run rate      : [12.   10.    9.67 10.75 10.   11.  ]
boundaries    : 9
dot-ball %    : 27.8
strike rate   : 183.3
```

`np.isin(a, values)` returns a mask of elements that appear in `values`. (Its old name `np.in1d` was removed in NumPy 2.)

---

## Try It Yourself

1. Turn `np.arange(1, 13)` into a 3 × 4 array, then into a 4 × 3 array in **column** order, then flatten it back, and check whether `ravel` gave you a view.
2. Monthly sales of two shops are `a = [10, 12, 15]` and `b = [8, 9, 14]`. Build (a) a `(2, 3)` array with shops as rows, (b) a `(3, 2)` array with shops as columns, using two different functions.
3. Round the GST amounts `[12.5, 13.5, 7.25, 0.5]` to whole rupees: once with `np.round`, once always rounding halves up. Explain the difference.
4. A list of order ids per customer number is `customer = np.array([3, 1, 3, 0, 3, 1])`. Count orders per customer (0 to 3) using `np.add.at`.

<details>
<summary>Show answers</summary>

```python
g = np.arange(1, 13).reshape(3, 4)
f = g.reshape(4, 3, order="F")
print(f)
print(f.ravel(order="F"), np.shares_memory(f, f.ravel(order="F")))

a, b = np.array([10, 12, 15]), np.array([8, 9, 14])
print(np.vstack([a, b]))
print(np.column_stack([a, b]))

gst = np.array([12.5, 13.5, 7.25, 0.5])
print(np.round(gst), np.floor(gst + 0.5))

customer = np.array([3, 1, 3, 0, 3, 1])
per_customer = np.zeros(4, dtype=int)
np.add.at(per_customer, customer, 1)
print(per_customer)
```

Output:

```
[[ 1  6 11]
 [ 5 10  4]
 [ 9  3  8]
 [ 2  7 12]]
[ 1  5  9  2  6 10  3  7 11  4  8 12] True
[[10 12 15]
 [ 8  9 14]]
[[10  8]
 [12  9]
 [15 14]]
[12. 14.  7.  0.] [13. 14.  7.  1.]
[1 2 0 3]
```

**1.** With `order="F"`, NumPy reads the 3 × 4 grid column by column (1, 5, 9, 2, 6, 10, ...) and fills the new shape column by column too, so the values look shuffled compared with a plain `reshape(4, 3)`. Flattening in the same column order only reinterprets the same memory, so `ravel` returned a view (`True`). Try `f.ravel()` (row order) and the answer becomes `False`: that order cannot be expressed with strides, so NumPy has to copy.

**3.** `np.round` sends exact halves to the even neighbour (12.5 → 12, 0.5 → 0); `floor(x + 0.5)` always rounds halves up.

</details>

---

## Real-World Examples

### Example 1: Batching data for deep learning

A 1-D audio stream is cut into fixed-length windows with `reshape(-1, window_size)`, and images are converted from channels-last to channels-first with `np.moveaxis(batch, -1, 1)` before entering a PyTorch model.

### Example 2: Time-based splits

Analysts split a year of daily data into quarters with `np.array_split(daily, 4)` and stack the quarterly totals with `np.stack` to compare them side by side.

### Example 3: Financial rounding

Payment systems often require round-half-up for invoices but use round-half-even for statistical aggregation. Knowing that `np.round` uses banker's rounding prevents off-by-one-paisa reconciliation errors.

---

## Common Misconceptions

### Misconception 1: "`np.append` changes my array, like `list.append`"

It returns a new array and leaves the original alone. If you ignore the return value, nothing happens.

### Misconception 2: "`reshape` reorders my data"

It only changes how the same sequence is grouped (row by row by default). To reorder axes, use `transpose`/`moveaxis`.

### Misconception 3: "`np.round(2.5)` is 3"

It is 2.0, because NumPy rounds halves to the nearest even number.

### Misconception 4: "`a[idx] += 1` adds once per occurrence in `idx`"

Repeated positions are only updated once. Use `np.add.at` or `np.bincount`.

### Misconception 5: "Dividing by zero raises an error"

NumPy returns `inf` or `nan` with a warning. Use `np.errstate` to make it raise when you want to catch the source.

---

## Interview Relevance

- *"Difference between `ravel` and `flatten`?"* View when possible vs always a copy.
- *"Difference between `concatenate`, `stack`, `vstack` and `hstack`?"* Existing axis vs new axis, and the shortcuts' handling of 1-D input.
- *"What does `-1` mean in `reshape`?"* Infer that dimension from the total size.
- *"How does NumPy round 0.5 and 1.5?"* Half to even: 0.0 and 2.0.
- *"Why is appending to a NumPy array in a loop slow?"* Each append allocates and copies the whole array, making the loop quadratic; collect in a list and convert once.
- *"How do you convert NHWC images to NCHW?"* `np.transpose(x, (0, 3, 1, 2))` or `np.moveaxis(x, -1, 1)`.

---

## Key Takeaways

- **Reshape, transpose, moveaxis, expand_dims and squeeze** change the shape or axis order, usually as **views**.
- **Join** with `concatenate` (existing axis) or `stack` (new axis) and their shortcuts; **split** with `split`, `array_split` and `h/v/dsplit`.
- **`append`, `insert` and `delete` return new arrays**; avoid them in loops.
- **Every operator has a ufunc** with extra powers: `out`, `where`, `reduce`, `accumulate`, `outer` and `at`.
- **Rounding is half-to-even**; `floor`, `ceil` and `trunc` cover the other directions, and `clip` caps values safely.
- **Division by zero gives inf/nan with a warning**; control it with `np.errstate`.

---

**Up next:** [Statistical, Sorting, Searching and Counting Functions](statistical-sorting-searching-and-counting-functions.md)
