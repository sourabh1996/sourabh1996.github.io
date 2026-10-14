---
title: "Update, Delete and Drop"
course: "Databases: SQL and NoSQL"
module: "4. NoSQL with MongoDB Atlas"
type: Article
level: Beginner
reading_time: 32 min
---

# Update, Delete and Drop: The Complete Guide

> 📚 **Before you start**
>
> - [Insert, Find, Query and Sort](insert-find-query-and-sort.md), for filters, query operators and the `MiniCollection` stand-in
> - [Databases and Collections](databases-and-collections.md), for collections, `_id`, and TTL and unique indexes
> - [Writing SQL Queries](../02-relational-databases-and-sql/writing-sql-queries.md), for the SQL `UPDATE` and `DELETE` these map to
> - [Functions and Iterators](../../python-programming/course.md#m6) (Python Programming)

## Introduction

A chai chain runs a loyalty programme in MongoDB. Every visit adds 10 points and bumps the visit count. Customers add and remove favourite drinks. Someone moves house. A customer asks for their account to be deleted. At the end of the season, the old "promo_2025" collection should disappear entirely.

Each of these is a different kind of change, and MongoDB gives each its own tool. **Updates** don't send the whole document back; they send small instructions like "add 10 to `points`" or "push `'lassi'` onto `favourites`", which the server applies **atomically** to the document. **Deletes** remove documents that match a filter. **Drops** remove whole collections or databases.

By the end of this article you'll be able to use `update_one`, `update_many` and `replace_one`; every common update operator (`$set`, `$unset`, `$inc`, `$mul`, `$min`, `$max`, `$rename`, `$push`, `$addToSet`, `$pull`, `$pop`); **upserts**; `find_one_and_update` for counters and queues; `delete_one`, `delete_many` and `find_one_and_delete`; and `drop` at collection and database level. You'll also understand why `$inc` is safe when two app servers update the same customer at the same moment and "read, change, write back" is not.

> 💡 **Key Insight**
>
> An update has two parts: a **filter** (which documents, exactly like `find`) and an **update document of operators** (what to change). Say *what to change*, not *what the result should be*: `{"$inc": {"points": 10}}` instead of reading the points, adding 10 in Python and writing them back. The server applies the change atomically, so concurrent updates never overwrite each other.

---

## Core Explanation

### 1. A collection to practise on

We use the same `MiniCollection` stand-in as the last lesson, now with update and delete methods named exactly like pymongo's. As before, it implements a subset, for learning only. With Atlas, replace the stand-in with `client["loyalty"]["customers"]` and the rest of the code is unchanged.

<details>
<summary>Show the code of MiniCollection (run it, then carry on)</summary>

```python
import copy
import re
from types import SimpleNamespace

ASCENDING, DESCENDING = 1, -1


class DuplicateKeyError(Exception):
    pass


def _lookup(doc, path):
    """Every value found at a dotted path (arrays of sub-documents are searched)."""
    values = [doc]
    for part in path.split("."):
        found = []
        for v in values:
            if isinstance(v, dict) and part in v:
                found.append(v[part])
            elif isinstance(v, list):
                if part.isdigit() and int(part) < len(v):
                    found.append(v[int(part)])
                else:
                    found += [e[part] for e in v if isinstance(e, dict) and part in e]
        values = found
    return values


def _candidates(values):
    """A field matches if the value itself, or any element of an array value, matches."""
    out = []
    for v in values:
        out.append(v)
        if isinstance(v, list):
            out.extend(v)
    return out


def _comparable(a, b):
    num = (int, float)
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool)
    return (isinstance(a, num) and isinstance(b, num)) or type(a) is type(b)


def _check(values, ops):
    cands = _candidates(values)
    for op, arg in ops.items():
        if op == "$eq":
            ok = (not values or None in cands) if arg is None else arg in cands
        elif op == "$ne":
            ok = not _check(values, {"$eq": arg})
        elif op in ("$gt", "$gte", "$lt", "$lte"):
            test = {"$gt": lambda c: c > arg, "$gte": lambda c: c >= arg,
                    "$lt": lambda c: c < arg, "$lte": lambda c: c <= arg}[op]
            ok = any(_comparable(c, arg) and test(c) for c in cands)
        elif op == "$in":
            ok = any(_check(values, {"$eq": a}) for a in arg)
        elif op == "$nin":
            ok = not _check(values, {"$in": arg})
        elif op == "$exists":
            ok = bool(values) == bool(arg)
        elif op == "$regex":
            flags = re.IGNORECASE if "i" in ops.get("$options", "") else 0
            ok = any(isinstance(c, str) and re.search(arg, c, flags) for c in cands)
        elif op == "$options":
            continue
        elif op == "$all":
            ok = any(isinstance(v, list) and all(a in v for a in arg) for v in values)
        elif op == "$size":
            ok = any(isinstance(v, list) and len(v) == arg for v in values)
        elif op == "$elemMatch":
            ok = any(isinstance(v, list) and any(_elem_matches(e, arg) for e in v) for v in values)
        elif op == "$not":
            ok = not _check(values, arg)
        else:
            raise ValueError(f"operator {op} is not supported by this mini version")
        if not ok:
            return False
    return True


def _is_ops(cond):
    return isinstance(cond, dict) and cond and all(k.startswith("$") for k in cond)


def _elem_matches(elem, cond):
    if _is_ops(cond):
        return _check([elem], cond)
    return isinstance(elem, dict) and matches(elem, cond)


def matches(doc, filt):
    """True if the document satisfies the filter (a subset of MongoDB's rules)."""
    for key, cond in (filt or {}).items():
        if key == "$and":
            ok = all(matches(doc, f) for f in cond)
        elif key == "$or":
            ok = any(matches(doc, f) for f in cond)
        elif key == "$nor":
            ok = not any(matches(doc, f) for f in cond)
        else:
            ok = _check(_lookup(doc, key), cond if _is_ops(cond) else {"$eq": cond})
        if not ok:
            return False
    return True


def _pick(value, parts):
    """Keep only the sub-field named by parts (used for projections like "rating.avg")."""
    if not parts:
        return value
    if isinstance(value, dict) and parts[0] in value:
        inner = _pick(value[parts[0]], parts[1:])
        return {} if inner is None else {parts[0]: inner}
    if isinstance(value, list):
        return [x for x in (_pick(e, parts) for e in value if isinstance(e, dict)) if x]
    return None


def _merge(a, b):
    for k, v in b.items():
        a[k] = _merge(a[k], v) if isinstance(a.get(k), dict) and isinstance(v, dict) else v
    return a


def _project(doc, projection):
    if not projection:
        return doc
    include = [k for k, v in projection.items() if v and k != "_id"]
    if include:
        out = {"_id": doc["_id"]} if projection.get("_id", 1) and "_id" in doc else {}
        for path in include:
            picked = _pick(doc, path.split("."))
            if picked:
                _merge(out, picked)
        return {k: out[k] for k in doc if k in out}      # keep the document's field order
    return {k: v for k, v in doc.items() if projection.get(k, 1)}


def _sort_key(value):
    # MongoDB puts missing/null values before numbers, and numbers before strings
    if value is None:
        return (0, 0)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return (1, value)
    if isinstance(value, str):
        return (2, value)
    return (3, str(value))


def _sorted(docs, spec):
    for field, direction in reversed(spec):
        docs = sorted(docs, key=lambda d: _sort_key((_lookup(d, field) or [None])[0]),
                      reverse=direction == -1)
    return docs


class MiniCursor:
    def __init__(self, docs, projection):
        self._docs, self._projection = docs, projection
        self._sort, self._skip, self._limit = [], 0, 0

    def sort(self, key, direction=ASCENDING):
        self._sort = key if isinstance(key, list) else [(key, direction)]
        return self

    def skip(self, n):
        self._skip = n
        return self

    def limit(self, n):
        self._limit = n
        return self

    def __iter__(self):
        docs = _sorted(self._docs, self._sort)[self._skip:]
        if self._limit:
            docs = docs[:self._limit]
        return iter([_project(copy.deepcopy(d), self._projection) for d in docs])


def _value(doc, expr):
    """Evaluate an aggregation expression: '$field', a constant, or $multiply/$add/$round."""
    if isinstance(expr, str) and expr.startswith("$"):
        found = _lookup(doc, expr[1:])
        return found[0] if found else None
    if isinstance(expr, dict) and len(expr) == 1:
        (op, args), = expr.items()
        vals = [_value(doc, a) for a in args]
        if op == "$multiply":
            result = 1
            for v in vals:
                result *= v
            return result
        if op == "$add":
            return sum(vals)
        if op == "$round":
            return round(vals[0], vals[1] if len(vals) > 1 else 0)
        raise ValueError(f"expression {op} is not supported by this mini version")
    if isinstance(expr, dict):
        return {k: _value(doc, v) for k, v in expr.items()}
    return expr


def _group(docs, spec):
    groups = {}
    for d in docs:
        key = _value(d, spec["_id"])
        groups.setdefault(repr(key), (key, []))[1].append(d)
    out = []
    for key, members in groups.values():
        row = {"_id": key}
        for field, acc in spec.items():
            if field == "_id":
                continue
            (op, expr), = acc.items()
            vals = [_value(m, expr) for m in members]
            nums = [v for v in vals if isinstance(v, (int, float))]
            if op == "$sum":
                row[field] = sum(nums)
            elif op == "$avg":
                row[field] = sum(nums) / len(nums) if nums else None
            elif op == "$min":
                row[field] = min(nums) if nums else None
            elif op == "$max":
                row[field] = max(nums) if nums else None
            elif op == "$push":
                row[field] = vals
            elif op == "$addToSet":
                row[field] = list(dict.fromkeys(vals))
            else:
                raise ValueError(f"accumulator {op} is not supported by this mini version")
        out.append(row)
    return out


def _reshape(doc, spec):
    """$project: keep fields marked 1, compute fields given an expression."""
    out = {"_id": doc["_id"]} if spec.get("_id", 1) and "_id" in doc else {}
    for field, how in spec.items():
        if field == "_id" or how in (0, False):
            continue
        if how in (1, True):
            if field in doc:
                out[field] = doc[field]
        else:
            out[field] = _value(doc, how)
    return out


class MiniCollection:
    """A tiny in-memory stand-in for a pymongo Collection (a subset, for learning only)."""

    def __init__(self, name):
        self.name = name
        self._docs = []
        self._next_id = 1

    def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = self._next_id          # pymongo would add an ObjectId here
            self._next_id += 1
        if any(d["_id"] == doc["_id"] for d in self._docs):
            raise DuplicateKeyError(f"E11000 duplicate key error: _id {doc['_id']!r}")
        self._docs.append(copy.deepcopy({"_id": doc["_id"], **doc}))   # _id is stored first
        return SimpleNamespace(inserted_id=doc["_id"], acknowledged=True)

    def insert_many(self, docs):
        return SimpleNamespace(inserted_ids=[self.insert_one(d).inserted_id for d in docs],
                               acknowledged=True)

    def find(self, filter=None, projection=None):
        return MiniCursor([d for d in self._docs if matches(d, filter)], projection)

    def find_one(self, filter=None, projection=None):
        return next(iter(self.find(filter, projection)), None)

    def count_documents(self, filter):
        return sum(1 for d in self._docs if matches(d, filter))

    def distinct(self, key, filter=None):
        values = []
        for d in self._docs:
            if matches(d, filter):
                for v in _candidates(_lookup(d, key)):
                    if not isinstance(v, list) and v not in values:
                        values.append(v)
        return sorted(values, key=_sort_key)

    def aggregate(self, pipeline):
        docs = [copy.deepcopy(d) for d in self._docs]
        for stage in pipeline:
            (name, spec), = stage.items()
            if name == "$match":
                docs = [d for d in docs if matches(d, spec)]
            elif name == "$group":
                docs = _group(docs, spec)
            elif name == "$sort":
                docs = _sorted(docs, list(spec.items()))
            elif name == "$limit":
                docs = docs[:spec]
            elif name == "$skip":
                docs = docs[spec:]
            elif name == "$unwind":
                field = spec[1:]
                docs = [{**d, field: v} for d in docs for v in (d.get(field) or [])]
            elif name == "$project":
                docs = [_reshape(d, spec) for d in docs]
            elif name == "$count":
                docs = [{spec: len(docs)}]
            else:
                raise ValueError(f"stage {name} is not supported by this mini version")
        return iter(docs)


# ---------- updates, deletes and drop ----------

class ReturnDocument:
    BEFORE, AFTER = False, True


def _parent(doc, path, create):
    """Return (container, last_key) for a dotted path, creating sub-documents if asked."""
    parts = path.split(".")
    for part in parts[:-1]:
        if part not in doc:
            if not create:
                return None, parts[-1]
            doc[part] = {}
        doc = doc[part]
    return doc, parts[-1]


def _apply_update(doc, update, inserting=False):
    if not update or not all(k.startswith("$") for k in update):
        raise ValueError("update only works with $ operators")
    for op, fields in update.items():
        if op == "$setOnInsert" and not inserting:
            continue
        for path, arg in fields.items():
            parent, key = _parent(doc, path, create=op != "$unset")
            if parent is None:
                continue
            if op in ("$set", "$setOnInsert"):
                parent[key] = copy.deepcopy(arg)
            elif op == "$unset":
                parent.pop(key, None)
            elif op == "$inc":
                parent[key] = parent.get(key, 0) + arg
            elif op == "$mul":
                parent[key] = parent.get(key, 0) * arg
            elif op == "$min":
                parent[key] = arg if key not in parent else min(parent[key], arg)
            elif op == "$max":
                parent[key] = arg if key not in parent else max(parent[key], arg)
            elif op == "$rename":
                if key in parent:
                    doc[arg] = parent.pop(key)
            elif op in ("$push", "$addToSet"):
                items = arg["$each"] if isinstance(arg, dict) and "$each" in arg else [arg]
                target = parent.setdefault(key, [])
                for item in items:
                    if op == "$push" or item not in target:
                        target.append(copy.deepcopy(item))
            elif op == "$pull":
                if isinstance(parent.get(key), list):
                    def pulled(e):
                        return _elem_matches(e, arg) if isinstance(arg, dict) else e == arg
                    parent[key] = [e for e in parent[key] if not pulled(e)]
            elif op == "$pop":
                if parent.get(key):
                    parent[key].pop(0 if arg == -1 else -1)
            else:
                raise ValueError(f"operator {op} is not supported by this mini version")


def _seed_from_filter(filt):
    """An upsert starts from the filter's plain equality fields."""
    return {k: copy.deepcopy(v) for k, v in (filt or {}).items()
            if not k.startswith("$") and not _is_ops(v) and "." not in k}


def _update(self, filt, update, upsert, many):
    matched = modified = 0
    for d in self._docs:
        if matches(d, filt):
            before = copy.deepcopy(d)
            _apply_update(d, update)
            matched += 1
            modified += d != before
            if not many:
                break
    upserted_id = None
    if matched == 0 and upsert:
        new = _seed_from_filter(filt)
        _apply_update(new, update, inserting=True)
        upserted_id = self.insert_one(new).inserted_id
    return SimpleNamespace(matched_count=matched, modified_count=modified, upserted_id=upserted_id)


def update_one(self, filter, update, upsert=False):
    return _update(self, filter, update, upsert, many=False)


def update_many(self, filter, update, upsert=False):
    return _update(self, filter, update, upsert, many=True)


def replace_one(self, filter, replacement, upsert=False):
    if any(k.startswith("$") for k in replacement):
        raise ValueError("replacement can not include $ operators")
    for i, d in enumerate(self._docs):
        if matches(d, filter):
            new = {"_id": d["_id"], **copy.deepcopy(replacement)}
            changed = new != d
            self._docs[i] = new
            return SimpleNamespace(matched_count=1, modified_count=int(changed), upserted_id=None)
    upserted_id = self.insert_one(dict(replacement)).inserted_id if upsert else None
    return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=upserted_id)


def find_one_and_update(self, filter, update, projection=None, sort=None, upsert=False,
                        return_document=ReturnDocument.BEFORE):
    candidates = _sorted([d for d in self._docs if matches(d, filter)], sort or [])
    if not candidates:
        if upsert:
            result = update_one(self, filter, update, upsert=True)
            return self.find_one({"_id": result.upserted_id}, projection) if return_document else None
        return None
    target = candidates[0]
    before = copy.deepcopy(target)
    _apply_update(target, update)
    return _project(copy.deepcopy(target if return_document else before), projection)


def delete_one(self, filter):
    for i, d in enumerate(self._docs):
        if matches(d, filter):
            del self._docs[i]
            return SimpleNamespace(deleted_count=1)
    return SimpleNamespace(deleted_count=0)


def delete_many(self, filter):
    keep = [d for d in self._docs if not matches(d, filter)]
    deleted = len(self._docs) - len(keep)
    self._docs = keep
    return SimpleNamespace(deleted_count=deleted)


def find_one_and_delete(self, filter, sort=None):
    candidates = _sorted([d for d in self._docs if matches(d, filter)], sort or [])
    if not candidates:
        return None
    self._docs.remove(candidates[0])
    return candidates[0]


def drop(self):
    self._docs = []


for _f in (update_one, update_many, replace_one, find_one_and_update,
           delete_one, delete_many, find_one_and_delete, drop):
    setattr(MiniCollection, _f.__name__, _f)
```

</details>

```python
customers = MiniCollection("customers")
customers.insert_many([
    {"_id": "C1", "name": "Asha", "city": "Mumbai", "points": 120, "visits": 8,
     "favourites": ["masala chai", "samosa"], "address": {"area": "Andheri", "pincode": "400053"},
     "status": "active"},
    {"_id": "C2", "name": "Ravi", "city": "Delhi", "points": 40, "visits": 2,
     "favourites": ["lassi"], "status": "active"},
    {"_id": "C3", "name": "Meera", "city": "Bengaluru", "points": 300, "visits": 25,
     "favourites": ["filter coffee", "idli", "masala chai"], "status": "active", "phone": "98450 00000"},
    {"_id": "C4", "name": "Kabir", "city": "Delhi", "points": 0, "visits": 0,
     "favourites": [], "status": "inactive"},
])

def show(_id):
    print(customers.find_one({"_id": _id}))

show("C1")
```

Output:

```
{'_id': 'C1', 'name': 'Asha', 'city': 'Mumbai', 'points': 120, 'visits': 8, 'favourites': ['masala chai', 'samosa'], 'address': {'area': 'Andheri', 'pincode': '400053'}, 'status': 'active'}
```

### 2. update_one and $set

**`update_one(filter, update)`** changes the **first** document that matches the filter. **`$set`** sets fields to new values, creating them if they don't exist:

```python
result = customers.update_one({"_id": "C2"}, {"$set": {"city": "Gurugram", "email": "ravi@example.com"}})
print("matched:", result.matched_count, "| modified:", result.modified_count)
show("C2")
```

Output:

```
matched: 1 | modified: 1
{'_id': 'C2', 'name': 'Ravi', 'city': 'Gurugram', 'points': 40, 'visits': 2, 'favourites': ['lassi'], 'status': 'active', 'email': 'ravi@example.com'}
```

The result is an **`UpdateResult`**:

| Attribute | Meaning |
|---|---|
| `matched_count` | documents that matched the filter |
| `modified_count` | documents that actually changed |
| `upserted_id` | the `_id` of a newly inserted document, if this was an upsert (else `None`) |

`matched_count` and `modified_count` differ when the update changes nothing. Run the same `$set` again:

```python
result = customers.update_one({"_id": "C2"}, {"$set": {"city": "Gurugram"}})
print("matched:", result.matched_count, "| modified:", result.modified_count)
result = customers.update_one({"_id": "C99"}, {"$set": {"city": "Pune"}})
print("matched:", result.matched_count, "| modified:", result.modified_count)
```

Output:

```
matched: 1 | modified: 0
matched: 0 | modified: 0
```

A `matched_count` of 0 is how you detect "no such customer". No exception is raised.

Use dot notation to change one field inside a sub-document **without replacing the rest of it**:

```python
customers.update_one({"_id": "C1"}, {"$set": {"address.area": "Bandra"}})
print(customers.find_one({"_id": "C1"}, {"address": 1, "_id": 0}))
customers.update_one({"_id": "C1"}, {"$set": {"address": {"area": "Powai"}}})   # replaces the whole sub-document!
print(customers.find_one({"_id": "C1"}, {"address": 1, "_id": 0}))
```

Output:

```
{'address': {'area': 'Bandra', 'pincode': '400053'}}
{'address': {'area': 'Powai'}}
```

Setting `"address"` to a new dict threw away the pincode. Setting `"address.area"` only touched the area. This is one of the most common MongoDB bugs.

### 3. The classic mistake, and replace_one

In SQL you write `SET col = value`. In MongoDB, beginners often pass a plain document as the update:

```python
try:
    customers.update_one({"_id": "C4"}, {"status": "active"})
except ValueError as e:
    print("ValueError:", e)
```

Output:

```
ValueError: update only works with $ operators
```

pymongo raises the same `ValueError` with the same message, because an update must consist of operators. If you really mean "replace the entire document", use **`replace_one`**. It keeps the `_id` and swaps everything else:

```python
customers.replace_one({"_id": "C4"}, {"name": "Kabir Khan", "city": "Delhi", "points": 0, "status": "active"})
show("C4")
```

Output:

```
{'_id': 'C4', 'name': 'Kabir Khan', 'city': 'Delhi', 'points': 0, 'status': 'active'}
```

Kabir's `visits` and `favourites` fields are gone, because the replacement didn't include them. Use `replace_one` only when you deliberately have the whole new document, for example when saving an edited form that contains every field.

### 4. Field update operators

| Operator | Does | Example |
|---|---|---|
| `$set` | set a field's value | `{"$set": {"status": "gold"}}` |
| `$unset` | remove a field | `{"$unset": {"phone": ""}}` (the value is ignored) |
| `$inc` | add to a number (negative to subtract) | `{"$inc": {"points": 10, "visits": 1}}` |
| `$mul` | multiply a number | `{"$mul": {"points": 2}}` |
| `$min` / `$max` | set only if the new value is smaller / larger | `{"$max": {"best_streak": 7}}` |
| `$rename` | rename a field | `{"$rename": {"phone": "mobile"}}` |
| `$currentDate` | set a field to the server's current date | `{"$currentDate": {"updated_at": True}}` |
| `$setOnInsert` | set only when an upsert inserts | see section 7 |

One update document can use several operators at once, each on different fields:

```python
customers.update_one(
    {"_id": "C3"},
    {"$inc": {"points": 10, "visits": 1}, "$max": {"best_bill": 450}, "$rename": {"phone": "mobile"}},
)
show("C3")

customers.update_one({"_id": "C3"}, {"$max": {"best_bill": 200}, "$unset": {"mobile": ""}})
print(customers.find_one({"_id": "C3"}, {"best_bill": 1, "mobile": 1}))
```

Output:

```
{'_id': 'C3', 'name': 'Meera', 'city': 'Bengaluru', 'points': 310, 'visits': 26, 'favourites': ['filter coffee', 'idli', 'masala chai'], 'status': 'active', 'best_bill': 450, 'mobile': '98450 00000'}
{'_id': 'C3', 'best_bill': 450}
```

`$max` with 200 did nothing because 450 is larger, and `$unset` removed `mobile`. `$inc` on a field that doesn't exist creates it, starting from 0. (`$currentDate` isn't in our stand-in, because it uses the server's clock; with real MongoDB it's the usual way to stamp `updated_at`.)

### 5. Array update operators

| Operator | Does | Example |
|---|---|---|
| `$push` | append a value (duplicates allowed) | `{"$push": {"favourites": "lassi"}}` |
| `$push` + `$each` | append several values | `{"$push": {"favourites": {"$each": ["poha", "chai"]}}}` |
| `$addToSet` | append only if not already present | `{"$addToSet": {"favourites": "lassi"}}` |
| `$pull` | remove every element equal to a value, or matching a condition | `{"$pull": {"favourites": "samosa"}}` |
| `$pop` | remove the last (`1`) or first (`-1`) element | `{"$pop": {"favourites": 1}}` |

```python
customers.update_one({"_id": "C1"}, {"$push": {"favourites": "lassi"}})
customers.update_one({"_id": "C1"}, {"$addToSet": {"favourites": "lassi"}})          # already there: no change
customers.update_one({"_id": "C1"}, {"$addToSet": {"favourites": {"$each": ["poha", "lassi"]}}})
print(customers.find_one({"_id": "C1"})["favourites"])

customers.update_one({"_id": "C1"}, {"$pull": {"favourites": "samosa"}})
customers.update_one({"_id": "C1"}, {"$pop": {"favourites": -1}})                     # remove the first
print(customers.find_one({"_id": "C1"})["favourites"])
```

Output:

```
['masala chai', 'samosa', 'lassi', 'poha']
['lassi', 'poha']
```

`$pull` can also take a condition, which is handy for arrays of numbers or sub-documents:

```python
scores = MiniCollection("scores")
scores.insert_one({"_id": 1, "marks": [35, 92, 48, 77, 20]})
scores.update_one({"_id": 1}, {"$pull": {"marks": {"$lt": 40}}})
print(scores.find_one({"_id": 1}))
```

Output:

```
{'_id': 1, 'marks': [92, 48, 77]}
```

To change **one particular element** of an array, real MongoDB has the **positional operator `$`**: the filter finds the element, and `$` in the update path refers to it. Our stand-in doesn't support it, so here's the pymongo form:

```python
# not-run: needs a MongoDB Atlas cluster
orders.update_one(
    {"_id": "A1", "items.sku": "tea"},          # find the order AND the item
    {"$inc": {"items.$.qty": 1}},                # $ = the item that matched
)
```

### 6. update_many

**`update_many(filter, update)`** applies the update to **every** matching document. "Double points for all active Delhi customers this Diwali week":

```python
result = customers.update_many({"city": {"$in": ["Delhi", "Gurugram"]}, "status": "active"}, {"$mul": {"points": 2}})
print("matched:", result.matched_count, "| modified:", result.modified_count)
for c in customers.find({}, {"name": 1, "city": 1, "points": 1, "_id": 0}):
    print(c)
```

Output:

```
matched: 2 | modified: 1
{'name': 'Asha', 'city': 'Mumbai', 'points': 120}
{'name': 'Ravi', 'city': 'Gurugram', 'points': 80}
{'name': 'Meera', 'city': 'Bengaluru', 'points': 310}
{'name': 'Kabir Khan', 'city': 'Delhi', 'points': 0}
```

> ⚠️ `update_many({}, {...})` with an empty filter updates **every document in the collection**, the same as an SQL `UPDATE` without `WHERE`. Run `count_documents(filter)` with the same filter first to see how many documents you're about to change.

### 7. Upserts: update, or insert if missing

Pass **`upsert=True`** and, if nothing matches the filter, MongoDB **inserts** a new document instead. The new document is built from the filter's equality fields plus the update. **`$setOnInsert`** sets fields only in that insert case, which is perfect for creation-time defaults:

```python
def record_visit(customer_id, name, city):
    return customers.update_one(
        {"_id": customer_id},
        {
            "$inc": {"visits": 1, "points": 10},
            "$setOnInsert": {"name": name, "city": city, "favourites": [], "status": "active"},
        },
        upsert=True,
    )

r = record_visit("C5", "Zoya", "Mumbai")      # new customer: inserted
print("matched:", r.matched_count, "| upserted_id:", r.upserted_id)
r = record_visit("C5", "Zoya", "Mumbai")      # existing customer: updated
print("matched:", r.matched_count, "| upserted_id:", r.upserted_id)
show("C5")
```

Output:

```
matched: 0 | upserted_id: C5
matched: 1 | upserted_id: None
{'_id': 'C5', 'visits': 2, 'points': 20, 'name': 'Zoya', 'city': 'Mumbai', 'favourites': [], 'status': 'active'}
```

The same function handles first and repeat visits, with no "does it exist?" check. That check would be a race condition anyway: two requests could both see "doesn't exist" and both insert. An upsert on a uniquely indexed field (here `_id`) avoids the race. It's MongoDB's equivalent of `INSERT … ON CONFLICT DO UPDATE` in PostgreSQL.

### 8. find_one_and_update: change and get the document back

`update_one` tells you counts, not the document. **`find_one_and_update`** applies the update and returns the document, either **before** the change (the default) or **after** it with `return_document=ReturnDocument.AFTER`. It's the standard way to build a **counter**, such as order numbers that must never repeat:

```python
counters = MiniCollection("counters")

def next_order_number(store):
    doc = counters.find_one_and_update(
        {"_id": store},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return f"{store}-{doc['seq']:05d}"

print(next_order_number("MUM"), next_order_number("MUM"), next_order_number("DEL"), next_order_number("MUM"))
```

Output:

```
MUM-00001 MUM-00002 DEL-00001 MUM-00003
```

In pymongo, `ReturnDocument` is imported with `from pymongo import ReturnDocument`. `find_one_and_update` also accepts `sort=` (which document to pick if several match) and `projection=`.

### 9. Why operators beat read-modify-write

Imagine two app servers record a visit for Asha at the same moment. The tempting Python approach reads the document, adds 10 in Python, and writes the result back. Here's what happens when the two requests interleave:

```python
customers.update_one({"_id": "C1"}, {"$set": {"points": 100}})

# Read-modify-write, two servers interleaved:
a = customers.find_one({"_id": "C1"})["points"]       # server A reads 100
b = customers.find_one({"_id": "C1"})["points"]       # server B reads 100
customers.update_one({"_id": "C1"}, {"$set": {"points": a + 10}})   # A writes 110
customers.update_one({"_id": "C1"}, {"$set": {"points": b + 10}})   # B writes 110
print("read-modify-write:", customers.find_one({"_id": "C1"})["points"], "(one visit was lost)")

# Atomic operator, same interleaving:
customers.update_one({"_id": "C1"}, {"$set": {"points": 100}})
customers.update_one({"_id": "C1"}, {"$inc": {"points": 10}})        # A
customers.update_one({"_id": "C1"}, {"$inc": {"points": 10}})        # B
print("$inc:", customers.find_one({"_id": "C1"})["points"])
```

Output:

```
read-modify-write: 110 (one visit was lost)
$inc: 120
```

This bug is called a **lost update**. With `$inc` the server applies each change to whatever the current value is, so both visits count. In MongoDB, **every update to a single document is atomic**: no other operation sees it half-applied. That's another reason to keep data that changes together in one document. When a change truly must span several documents, MongoDB supports multi-document transactions (`with client.start_session() as s: with s.start_transaction(): ...`), but they're slower and best kept for rare cases.

### 10. Deleting documents

| Method | Deletes | Returns |
|---|---|---|
| `delete_one(filter)` | the first matching document | `DeleteResult` with `deleted_count` (0 or 1) |
| `delete_many(filter)` | every matching document | `DeleteResult` with `deleted_count` |
| `find_one_and_delete(filter, sort=...)` | the first match | the deleted document (or `None`) |

```python
customers.update_one({"_id": "C4"}, {"$set": {"status": "inactive"}})
print("inactive:", customers.count_documents({"status": "inactive"}))
r = customers.delete_many({"status": "inactive"})
print("deleted:", r.deleted_count)
r = customers.delete_one({"_id": "nobody"})
print("deleted:", r.deleted_count)
print("left:", [c["_id"] for c in customers.find()])
```

Output:

```
inactive: 1
deleted: 1
deleted: 0
left: ['C1', 'C2', 'C3', 'C5']
```

**`find_one_and_delete`** with a `sort` is a simple **job queue**: each worker atomically takes the oldest job, and no two workers can take the same one:

```python
jobs = MiniCollection("jobs")
jobs.insert_many([{"task": "send bill", "created": 3}, {"task": "send OTP", "created": 1},
                  {"task": "update stock", "created": 2}])
while (job := jobs.find_one_and_delete({}, sort=[("created", 1)])) is not None:
    print("worker took:", job["task"])
```

Output:

```
worker took: send OTP
worker took: update stock
worker took: send bill
```

**`delete_many({})`** deletes every document but **keeps the collection and its indexes**, like `DELETE FROM table` in SQL. On large collections it's slow, because each document is deleted one by one. To remove everything, `drop` is faster.

**Deleting is permanent.** Many applications prefer a **soft delete**: set `{"$set": {"deleted_at": <date>}}` and filter those out in queries, so data can be restored and audited. Data that should vanish after a fixed time (sessions, OTPs, temporary carts) is best handled with a **TTL index**, which deletes documents automatically ([Databases and Collections](databases-and-collections.md)).

### 11. Dropping collections and databases

**Dropping** removes the container itself: every document, every index and any validation rules.

```python
customers.drop()
print("documents after drop:", customers.count_documents({}))
```

Output:

```
documents after drop: 0
```

With pymongo there are three ways, all permanent and with **no confirmation prompt**:

```python
# not-run: needs a MongoDB Atlas cluster
db = client["loyalty"]

db["promo_2025"].drop()               # drop one collection via its handle
db.drop_collection("promo_2025")      # the same, by name
client.drop_database("loyalty_test")  # drop a whole database and all its collections

print(db.list_collection_names())
print(client.list_database_names())
```

Example output:

```
['customers']
['admin', 'local', 'loyalty']
```

Dropping something that doesn't exist is not an error; it simply does nothing. Free Atlas clusters don't include the automatic backups that paid tiers offer, so on the free tier a drop really is forever. A common safety habit is to put the database name in an environment variable and refuse to run destructive scripts unless it ends in `_test` or `_dev`.

| SQL | MongoDB |
|---|---|
| `UPDATE t SET a = 1 WHERE …` (one row) | `update_one({...}, {"$set": {"a": 1}})` |
| `UPDATE t SET a = 1 WHERE …` (many rows) | `update_many({...}, {"$set": {"a": 1}})` |
| `UPDATE t SET n = n + 1 …` | `{"$inc": {"n": 1}}` |
| `INSERT … ON CONFLICT DO UPDATE` | `update_one(..., upsert=True)` |
| `UPDATE … RETURNING *` | `find_one_and_update(..., return_document=ReturnDocument.AFTER)` |
| `DELETE FROM t WHERE …` | `delete_one` / `delete_many` |
| `DELETE FROM t` / `TRUNCATE t` | `delete_many({})` / `drop()` then recreate indexes |
| `DROP TABLE t` | `db.drop_collection("t")` |
| `DROP DATABASE d` | `client.drop_database("d")` |

---

## Try It Yourself

Start fresh with this collection:

```python
library = MiniCollection("library")
library.insert_many([
    {"_id": "B1", "title": "The Guide", "copies": 3, "borrowers": ["asha"]},
    {"_id": "B2", "title": "Wings of Fire", "copies": 1, "borrowers": []},
    {"_id": "B3", "title": "Malgudi Days", "copies": 0, "borrowers": ["ravi", "meera"], "damaged": True},
])
```

1. Ravi returns *Malgudi Days*: remove `"ravi"` from its `borrowers` and add 1 to `copies`, in one update. Print the document.
2. Meera borrows *The Guide*, but only if a copy is available. Write one `update_one` whose filter checks `copies > 0`, then decrement `copies` and add her to `borrowers` without duplicates. Print `matched_count`.
3. Remove the `damaged` field from every book that has it, and print how many were modified.
4. Add a new book with an upsert, `_id` `"B4"`, title *Swami and Friends*, 2 copies, setting `title` and `borrowers` only on insert. Then delete every book with zero copies and print the remaining titles.

<details>
<summary>Show answers</summary>

**1.**

```python
library.update_one({"_id": "B3"}, {"$pull": {"borrowers": "ravi"}, "$inc": {"copies": 1}})
print(library.find_one({"_id": "B3"}))
```

Output:

```
{'_id': 'B3', 'title': 'Malgudi Days', 'copies': 1, 'borrowers': ['meera'], 'damaged': True}
```

**2.** Putting the availability check in the filter makes "check and take a copy" one atomic step:

```python
r = library.update_one(
    {"_id": "B1", "copies": {"$gt": 0}},
    {"$inc": {"copies": -1}, "$addToSet": {"borrowers": "meera"}},
)
print("matched:", r.matched_count, "|", library.find_one({"_id": "B1"}))
```

Output:

```
matched: 1 | {'_id': 'B1', 'title': 'The Guide', 'copies': 2, 'borrowers': ['asha', 'meera']}
```

**3.**

```python
r = library.update_many({"damaged": {"$exists": True}}, {"$unset": {"damaged": ""}})
print("modified:", r.modified_count)
```

Output:

```
modified: 1
```

**4.**

```python
library.update_one(
    {"_id": "B4"},
    {"$set": {"copies": 2}, "$setOnInsert": {"title": "Swami and Friends", "borrowers": []}},
    upsert=True,
)
library.update_one({"_id": "B2"}, {"$set": {"copies": 0}})
print("deleted:", library.delete_many({"copies": 0}).deleted_count)
print([b["title"] for b in library.find().sort("title", 1)])
```

Output:

```
deleted: 1
['Malgudi Days', 'Swami and Friends', 'The Guide']
```

</details>

---

## Real-World Examples

### Example 1: Shopping carts

A cart is one document per user. "Add to cart" is `$push` (or `$inc` on the quantity of an existing line with the positional operator), "remove" is `$pull`, and a TTL index on `updated_at` clears abandoned carts after a few days.

### Example 2: Likes and view counters

Social apps record likes with `$addToSet` on a list of user ids (so double-tapping can't like twice) and keep a count with `$inc`. Because both are atomic operators, thousands of simultaneous likes are counted exactly.

### Example 3: "Delete my account" requests

Privacy laws such as India's Digital Personal Data Protection Act require deleting personal data on request. Teams implement this with `delete_many` across every collection holding that user's id, often after a soft-delete grace period, and log the deletion for audit.

---

## Common Misconceptions

### Misconception 1: "update_one with a plain document updates those fields"

It raises an error in pymongo; updates need operators like `$set`. To swap the whole document, use `replace_one`.

### Misconception 2: "Setting a sub-document updates just the fields I pass"

`{"$set": {"address": {...}}}` replaces the entire `address`. Use dot notation, `{"$set": {"address.area": "..."}}`, to change one field.

### Misconception 3: "matched_count == 0 raises an exception"

Updates and deletes that match nothing succeed quietly with zero counts. Check the counts yourself when "not found" matters.

### Misconception 4: "delete_many({}) and drop() are the same"

`delete_many({})` removes documents one by one and keeps the collection, its indexes and validation. `drop()` removes all of it at once.

---

## Interview Relevance

- *"How do you increment a counter safely under concurrency?"* `$inc` (or `find_one_and_update` with `$inc`), never read-modify-write; single-document updates are atomic.
- *"What is an upsert?"* Update if a match exists, insert otherwise; `$setOnInsert` for creation-only fields; pair with a unique index.
- *"$push vs $addToSet?"* Duplicates allowed versus prevented.
- *"update_one vs replace_one?"* Partial change with operators versus whole-document replacement keeping `_id`.
- *"How would you implement a job queue in MongoDB?"* `find_one_and_delete` or `find_one_and_update` (setting `status: "taken"`) with a sort.
- *"Soft delete vs hard delete?"* Recoverability and audit versus storage and privacy obligations.

---

## Key Takeaways

- **Updates = filter + operators.** `$set`, `$unset`, `$inc`, `$mul`, `$min`, `$max`, `$rename` change fields; `$push`, `$addToSet`, `$pull`, `$pop` change arrays. Use dot notation for nested fields.
- **`UpdateResult`** reports `matched_count`, `modified_count` and `upserted_id`; zero matches is not an error.
- **Upserts** (`upsert=True` plus `$setOnInsert`) and **`find_one_and_update`** replace "check then write" code, which is racy.
- **Single-document updates are atomic**: prefer `$inc` over read-modify-write to avoid lost updates.
- **`delete_one` / `delete_many`** remove documents; **`drop`** removes a whole collection or database, permanently, with no prompt.

---

**Up next:** [Lab: Store chat history in MongoDB](lab-store-chat-history-in-mongodb.md)
