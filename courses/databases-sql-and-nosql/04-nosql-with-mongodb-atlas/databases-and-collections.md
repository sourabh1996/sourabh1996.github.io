---
title: "Databases and Collections"
course: "Databases: SQL and NoSQL"
module: "4. NoSQL with MongoDB Atlas"
type: Article
level: Beginner
reading_time: 28 min
---

# Databases and Collections: The Complete Guide

> 📚 **Before you start**
>
> - [What is a Document Database?](what-is-a-document-database.md), for documents, BSON, `_id` and flexible schemas
> - [Setting Up Supabase](../03-postgresql-on-supabase/setting-up-supabase.md), for keeping connection secrets in a `.env` file (the same habit applies here)
> - [Primary and Foreign Keys](../02-relational-databases-and-sql/primary-and-foreign-keys.md), for what an index is and what it costs
> - [Dictionaries and Dictionary Views](../../python-fundamentals/course.md#m5) (Python Fundamentals), because pymongo uses dictionaries for everything

## Introduction

A library has buildings, each building has shelves, and each shelf holds books. You don't need to build a shelf before putting a book on it in MongoDB's world: the moment you put the first book down, the shelf appears.

That's how MongoDB organises data. A **cluster** (the servers) holds **databases**, each database holds **collections**, and each collection holds **documents**. Collections and databases are created automatically the first time you write to them, which is wonderfully convenient and occasionally dangerous (a typo creates a brand-new, empty collection rather than an error).

In this article you'll create a free **MongoDB Atlas** cluster, connect to it from Python with **pymongo**, and learn how databases and collections work: naming, lazy creation, listing, the `_id` field and ObjectIds, schema validation, and **indexes**, which decide whether your queries take a millisecond or a minute. The parts that need Atlas are marked; the ideas are demonstrated offline with plain Python so you can run them now.

> 💡 **Key Insight**
>
> In MongoDB, **asking for a database or collection never fails and never creates anything**. `client["shop"]["products"]` just gives you a handle. The collection springs into existence on the first insert (or an explicit `create_collection`). So spelling matters: `client["shop"]["prodcuts"]` is a different, empty collection, and no error will tell you.

---

## Core Explanation

### 1. The hierarchy: cluster, database, collection, document

```mermaid
flowchart TB
  CL["Atlas cluster<br/>(a replica set of 3 servers)"] --> DB1[("database: shop")]
  CL --> DB2[("database: chatbot")]
  DB1 --> C1["collection: products"]
  DB1 --> C2["collection: orders"]
  DB2 --> C3["collection: conversations"]
  DB2 --> C4["collection: messages"]
  C1 --> D1["{ _id: ..., name: 'Nova 5G', price: 17999 }"]
  C1 --> D2["{ _id: ..., name: 'Silk saree', fabric: 'silk' }"]
```

| Level | Holds | Relational equivalent |
|---|---|---|
| **Cluster** | databases | a database server |
| **Database** | collections | a database (or a PostgreSQL schema) |
| **Collection** | documents | a table |
| **Document** | fields | a row |

A typical application uses **one database** with several collections. Separate databases are for separate applications or environments (`shop_dev`, `shop_prod`).

### 2. Create a free Atlas cluster

**MongoDB Atlas** is MongoDB's own cloud service. It runs and backs up MongoDB for you on AWS, Google Cloud or Azure. Its **Free** cluster tier (shown as **M0** in the UI) is free forever and is meant for learning and small prototypes. As of October 2026 it allows 0.5 GB of storage, up to 500 connections and about 100 operations per second, and you can have one free cluster per project.

1. Go to [mongodb.com/cloud/atlas/register](https://www.mongodb.com/cloud/atlas/register) and sign up with an email address or a Google or GitHub account. Atlas creates an **organization** and a **project** for you.
2. Click **Create** to make a cluster, and choose the **M0** (Free) option.
3. Pick a **provider** (AWS, Google Cloud or Azure) and a **region** near you, for example Mumbai. Only regions that support free clusters are listed.
4. Give the cluster a name (letters, numbers and hyphens; it can't be changed later), such as `Cluster0`, and click **Create**.
5. A **security quickstart** appears:
   - **Create a database user** with a username and password. This is the login your Python code will use, separate from your Atlas website login. Use the suggested secure password and save it in your password manager.
   - **Add your IP address** to the **IP access list** with **Add My Current IP Address**. Atlas refuses connections from any address not on this list. (If your home IP changes, you'll need to add the new one; you can also manage the list later under the project's network access settings in the **Security** section of the sidebar. Avoid `0.0.0.0/0`, "allow from anywhere", except for short experiments.)
6. When the cluster is ready, click **Connect** on it, choose **Drivers**, select **Python**, and copy the connection string.

The connection string looks like this, with your own cluster host and username:

```
mongodb+srv://asha:<db_password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
```

Replace `<db_password>` with the database user's password (if the password has special characters such as `@` or `:`, percent-encode them, for example with `urllib.parse.quote_plus`). The `mongodb+srv://` scheme tells the driver to look up the cluster's three servers from DNS, so you only need one host name.

Put it in your `.env` file, never in code:

```
# .env
MONGODB_URI=mongodb+srv://asha:YOUR-PASSWORD@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
```

### 3. Install pymongo and connect

**pymongo** is MongoDB's official Python driver (version 4.x; it requires Python 3.9 or newer).

```bash
pip install pymongo python-dotenv
```

```python
# not-run: needs a MongoDB Atlas cluster and MONGODB_URI in .env
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()
client = MongoClient(os.environ["MONGODB_URI"], server_api=ServerApi("1"))

client.admin.command("ping")          # raises an exception if the cluster can't be reached
print("Connected!")
```

Example output:

```
Connected!
```

- **`MongoClient`** manages a pool of connections to the cluster. Create **one** per application and reuse it everywhere; it's safe to share between threads. Call `client.close()` when the program finishes.
- **`ServerApi("1")`** pins the behaviour to MongoDB's Stable API version 1, so a server upgrade won't change how your commands behave.
- **`ping`** is a tiny command that proves the connection, credentials and IP access list all work. If it hangs and then raises `ServerSelectionTimeoutError`, the usual cause is that your IP address isn't on the access list. An `OperationFailure` saying authentication failed means a wrong username or password.

### 4. Getting a database and a collection

You reach a database through the client, and a collection through the database, with either dictionary-style or attribute-style access:

```python
# not-run: needs a MongoDB Atlas cluster
db = client["shop"]              # or client.shop
products = db["products"]        # or db.products

print(db.name, products.name, products.full_name)
print(client.list_database_names())
print(db.list_collection_names())
```

Example output:

```
shop products shop.products
['admin', 'local']
[]
```

The `shop` database doesn't appear in the list, and `products` isn't in the collection list. **Nothing exists yet.** `db` and `products` are only handles. The first insert creates both:

```python
# not-run: needs a MongoDB Atlas cluster
products.insert_one({"name": "Masala Chai", "price": 15})
print(client.list_database_names())
print(db.list_collection_names())
```

Example output:

```
['admin', 'local', 'shop']
['products']
```

Dictionary-style access (`db["order-items"]`) works for any valid name; attribute style (`db.order_items`) only works for names that are valid Python identifiers. Many teams always use the dictionary style for consistency.

### 5. Lazy creation, demonstrated offline

To see exactly how lazy creation behaves, here's a pretend client built from Python dictionaries. Getting a handle stores nothing; inserting does. This mimics only the behaviour discussed here, not the real driver:

```python
class PretendCollection:
    def __init__(self, storage, db_name, name):
        self._storage, self.db_name, self.name = storage, db_name, name

    def insert_one(self, doc):
        # Only now do the database and collection come into existence
        self._storage.setdefault(self.db_name, {}).setdefault(self.name, []).append(doc)

class PretendDatabase:
    def __init__(self, storage, name):
        self._storage, self.name = storage, name

    def __getitem__(self, coll_name):
        return PretendCollection(self._storage, self.name, coll_name)

    def list_collection_names(self):
        return sorted(self._storage.get(self.name, {}))

class PretendClient:
    def __init__(self):
        self._storage = {}

    def __getitem__(self, db_name):
        return PretendDatabase(self._storage, db_name)

    def list_database_names(self):
        return sorted(self._storage)

client = PretendClient()
products = client["shop"]["products"]
typo = client["shop"]["prodcuts"]
print("after getting handles:", client.list_database_names())

products.insert_one({"name": "Masala Chai", "price": 15})
print("after one insert:     ", client.list_database_names(), client["shop"].list_collection_names())

typo.insert_one({"name": "Samosa", "price": 12})
print("after the typo insert:", client["shop"].list_collection_names())
```

Output:

```
after getting handles: []
after one insert:      ['shop'] ['products']
after the typo insert: ['prodcuts', 'products']
```

The typo created a second collection silently. A good habit is to keep collection names in constants (`PRODUCTS = "products"`) or in one module, so a misspelling becomes a Python `NameError` instead of a phantom collection.

### 6. Naming rules

| | Rules (simplified) | Good examples |
|---|---|---|
| **Database** | not empty; no spaces or the characters `/ \ . " $` (Windows also forbids `* < > : \| ?`); fewer than 64 characters; names differing only by case can't coexist | `shop`, `chatbot_prod` |
| **Collection** | not empty; can't contain `$` or the null character; can't start with `system.` (reserved for MongoDB); best to start with a letter or underscore | `products`, `order_items` |
| **Field** | can't be empty; avoid starting with `$`, and avoid `.` inside names, since dots are used for nested paths in queries | `price`, `created_at` |

Use lowercase plural nouns for collections and `snake_case` for fields (or camelCase, if your team prefers; just be consistent). The `admin`, `local` and `config` databases are MongoDB's own; don't store data in them.

### 7. The `_id` field and ObjectId

Every document must have an `_id` that is unique within its collection. MongoDB automatically creates a **unique index** on `_id` for every collection, so lookups by id are always fast and duplicates are impossible.

You can use your own value (an email, a PNR, an order number), or leave it out and let the driver generate an **ObjectId**. An ObjectId is 12 bytes, usually shown as 24 hexadecimal characters:

| Bytes | Meaning |
|---|---|
| 4 | seconds since 1 January 1970 (creation time) |
| 5 | a random value, unique to the machine and process |
| 3 | a counter that increases with each id |

So ObjectIds created later are (roughly) larger, and **each id carries its creation time**. Here's a decoder in plain Python:

```python
from datetime import datetime, timezone

def decode_object_id(hex_id):
    assert len(hex_id) == 24, "an ObjectId is 12 bytes = 24 hex characters"
    seconds = int(hex_id[:8], 16)
    return {
        "created": datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat(),
        "random": hex_id[8:18],
        "counter": int(hex_id[18:], 16),
    }

print(decode_object_id("6acb5718a1b2c3d4e500002a"))
print(decode_object_id("6acb5718a1b2c3d4e500002b")["counter"])   # the next id from the same process
```

Output:

```
{'created': '2026-10-11T09:30:00+00:00', 'random': 'a1b2c3d4e5', 'counter': 42}
43
```

With pymongo you'd write `from bson import ObjectId` (the `bson` package is installed with pymongo), and an `ObjectId` object has a `.generation_time` property that does the same decoding. Two things that trip up beginners:

- An ObjectId is **not a string**. `products.find_one({"_id": "6acb57..."})` finds nothing if the stored `_id` is an ObjectId; use `find_one({"_id": ObjectId("6acb57...")})`.
- `insert_one` **adds `_id` to your Python dict** in place if it didn't have one. Inserting the same dict object twice therefore fails the second time with a duplicate key error.

### 8. Creating collections explicitly, with validation

Usually you let collections appear on first insert. You create one explicitly when you want options, the most useful being **schema validation**: rules, written in JSON Schema, that MongoDB checks on every insert and update.

```python
# not-run: needs a MongoDB Atlas cluster
db.create_collection(
    "customers",
    validator={
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "phone"],
            "properties": {
                "name":  {"bsonType": "string", "minLength": 1},
                "phone": {"bsonType": "string", "pattern": "^[6-9][0-9]{9}$"},
                "age":   {"bsonType": "int", "minimum": 0},
            },
        }
    },
)
db["customers"].insert_one({"name": "Asha", "phone": "9820011111"})    # ok
db["customers"].insert_one({"name": "Ravi"})                            # no phone
```

Example output:

```
pymongo.errors.WriteError: Document failed validation, full error: {...}
```

The second insert raises `WriteError` (a subclass of `pymongo.errors.OperationFailure`). Validation gives you back some of the safety of a relational schema while keeping flexibility for fields you didn't list. Calling `create_collection` on a name that already exists raises `CollectionInvalid`.

### 9. Indexes: making queries fast

Without an index, `products.find({"category": "phone"})` must look at **every document** in the collection, a **collection scan** (`COLLSCAN`). An **index** is a sorted structure (a B-tree, like in PostgreSQL) on one or more fields, so MongoDB can jump straight to matching documents (`IXSCAN`).

Here's the idea in plain Python, counting how many documents each approach has to examine:

```python
import bisect, random

random.seed(7)
categories = ["phone", "saree", "book", "rice", "tea"]
docs = [{"_id": i, "category": random.choice(categories), "price": random.randint(100, 20000)}
        for i in range(10_000)]

# Collection scan: examine every document
examined = 0
scan_hits = []
for d in docs:
    examined += 1
    if d["category"] == "tea":
        scan_hits.append(d["_id"])
print(f"collection scan examined {examined} docs, found {len(scan_hits)}")

# Index on category: a sorted list of (value, _id) pairs, searched by binary search
index = sorted((d["category"], d["_id"]) for d in docs)
start = bisect.bisect_left(index, ("tea", -1))
end = bisect.bisect_right(index, ("tea", float("inf")))
index_hits = [doc_id for _, doc_id in index[start:end]]
print(f"index lookup examined {end - start} entries, found {len(index_hits)}")
print("same answer:", sorted(scan_hits) == index_hits)
```

Output:

```
collection scan examined 10000 docs, found 1950
index lookup examined 1950 entries, found 1950
same answer: True
```

The index went straight to the "tea" entries. The real thing works the same way at a much larger scale. With pymongo:

```python
# not-run: needs a MongoDB Atlas cluster
from pymongo import ASCENDING, DESCENDING

products = db["products"]
print(products.create_index("category"))                                        # single field
print(products.create_index([("category", ASCENDING), ("price", DESCENDING)]))  # compound
print(products.create_index("sku", unique=True))                                # no duplicate SKUs
print(sorted(products.index_information()))
```

Example output:

```
category_1
category_1_price_-1
sku_1
['_id_', 'category_1', 'category_1_price_-1', 'sku_1']
```

- `create_index` returns the index's **name**, built from the fields and directions (`1` ascending, `-1` descending). Running it again when the index exists does nothing, so it's safe to call at application start-up.
- A **compound index** on `(category, price)` serves queries on `category` alone, and on `category` with a sort or filter on `price`. Field order matters: it does *not* help a query on `price` alone. The usual rule of thumb is: fields you match exactly first, then fields you sort on, then range filters.
- A **unique index** makes MongoDB reject duplicates, like `UNIQUE` in SQL. It's the main way to enforce uniqueness on fields other than `_id`.
- A **TTL index** (time to live) deletes documents automatically after a time: `create_index("created_at", expireAfterSeconds=86400)` removes documents a day after their `created_at` date. Perfect for sessions, OTPs and temporary logs.
- `drop_index("category_1")` removes one; `list_indexes()` iterates over them.

To check whether a query uses an index, call `.explain()` on a cursor: `products.find({"category": "tea"}).explain()` returns a dictionary describing the plan, and you look for `IXSCAN` (good) rather than `COLLSCAN` in its winning plan. Atlas also shows slow queries and suggests indexes in its **Performance Advisor**.

Like in SQL, every index **slows down writes** and uses storage (which counts towards the free tier's 0.5 GB). Index the fields your real queries filter and sort on, nothing more.

### 10. Looking at your data in Atlas

Your cluster's page in Atlas has a **Data Explorer** (look for **Browse Collections**) where you can see databases, collections and documents, run filters, edit documents and manage indexes in the browser. **MongoDB Compass**, a free desktop app, does the same using your connection string. Both are useful for checking what your Python code actually wrote.

---

## Try It Yourself

1. Using the `PretendClient` from section 5, create a `school` database with `students` and `teachers` collections, insert one document into each, and print the collection names.
2. Decode the ObjectId `6acb5718a1b2c3d4e50000ff`. What is the counter value, and what does it tell you compared with `...00002a`?
3. You often run `orders.find({"customer_id": X}).sort("created_at", -1)`. Which index would you create, in pymongo syntax?
4. Write a pymongo call that makes `users.email` unique, and say what happens when you insert two users with the same email.

<details>
<summary>Show answers</summary>

**1.**

```python
school = client["school"]
school["students"].insert_one({"name": "Asha", "class": 8})
school["teachers"].insert_one({"name": "Mr. Iyer", "subject": "Maths"})
print(school.list_collection_names(), client.list_database_names())
```

Output:

```
['students', 'teachers'] ['school', 'shop']
```

**2.**

```python
print(decode_object_id("6acb5718a1b2c3d4e50000ff"))
```

Output:

```
{'created': '2026-10-11T09:30:00+00:00', 'random': 'a1b2c3d4e5', 'counter': 255}
```

The same second and process as before, but the counter is 255 instead of 42: it was generated 213 ids later.

**3.** A compound index with the exact-match field first and the sort field second:

```python
# not-run: needs a MongoDB Atlas cluster
orders.create_index([("customer_id", ASCENDING), ("created_at", DESCENDING)])
```

**4.**

```python
# not-run: needs a MongoDB Atlas cluster
db["users"].create_index("email", unique=True)
db["users"].insert_one({"email": "asha@example.com"})
db["users"].insert_one({"email": "asha@example.com"})   # raises DuplicateKeyError
```

The second insert raises `pymongo.errors.DuplicateKeyError`. If documents already contain duplicate emails, creating the index itself fails until you clean them up.

</details>

---

## Real-World Examples

### Example 1: One database per environment

Teams commonly use the same cluster code with different database names per environment (`shop_dev`, `shop_staging`, `shop_prod`), chosen from an environment variable, so a test run can never write into production data.

### Example 2: Sessions and OTPs that expire

Login sessions and one-time passwords are stored with a `created_at` date and a TTL index. MongoDB deletes them automatically after a few minutes or days, with no clean-up job to write.

### Example 3: Unique usernames

A sign-up flow relies on a unique index on `username` rather than "check, then insert" in Python. Two people clicking "Sign up" with the same name at the same instant can't both succeed; the second gets a `DuplicateKeyError`, which the app turns into "that name is taken".

---

## Common Misconceptions

### Misconception 1: "I need to create a collection before using it"

You don't. The first insert creates it. Create one explicitly only when you need options such as validation.

### Misconception 2: "An ObjectId is just a random string"

It's a 12-byte value whose first 4 bytes are a timestamp, and it's a distinct type. Querying with its string form won't match.

### Misconception 3: "MongoDB doesn't need indexes because it's NoSQL"

Every database needs indexes for large collections. Without them, every query is a collection scan, and on the free tier you'll also hit the operations-per-second limit sooner.

### Misconception 4: "Allowing access from anywhere (0.0.0.0/0) is fine because I have a password"

Passwords leak and get guessed. The IP access list is a second lock. Keep it as narrow as you can.

---

## Interview Relevance

- *"How is data organised in MongoDB?"* Cluster → databases → collections → documents, with the relational equivalents.
- *"What is an ObjectId?"* A 12-byte id: timestamp, random value, counter; roughly sortable by creation time.
- *"How do you enforce uniqueness or structure in MongoDB?"* Unique indexes and JSON Schema validation.
- *"What is a compound index and does field order matter?"* Yes: it supports queries on a prefix of its fields; equality, then sort, then range.
- *"What is a TTL index?"* An index that deletes documents after a set time.
- *"How do you check that a query uses an index?"* `explain()`, looking for `IXSCAN` vs `COLLSCAN`.

---

## Key Takeaways

- MongoDB organises data as **cluster → database → collection → document**; **Atlas** hosts it, with a free **M0** tier.
- Connect with **one `MongoClient`** per application, using a `mongodb+srv://` string from `.env`, and check it with `client.admin.command("ping")`.
- **Databases and collections are created lazily** on first insert, so typos create new collections silently.
- Every document has a unique **`_id`**; the default **ObjectId** encodes its creation time and isn't a string.
- **Indexes** (single, compound, unique, TTL) turn collection scans into fast lookups, at a cost to writes and storage; **validation** adds structure where you need it.

---

**Up next:** [Insert, Find, Query and Sort](insert-find-query-and-sort.md)
