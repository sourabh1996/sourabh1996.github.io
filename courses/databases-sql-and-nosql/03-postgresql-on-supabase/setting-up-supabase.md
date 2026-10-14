---
title: "Setting Up Supabase"
course: "Databases: SQL and NoSQL"
module: "3. PostgreSQL on Supabase"
type: Article
level: Beginner
reading_time: 28 min
---

# Setting Up Supabase: The Complete Guide

> 📚 **Before you start**
>
> - [Writing SQL Queries](../02-relational-databases-and-sql/writing-sql-queries.md) and [Primary and Foreign Keys](../02-relational-databases-and-sql/primary-and-foreign-keys.md), because you'll write `CREATE TABLE`, constraints and queries in PostgreSQL
> - [Joins and Unions](../02-relational-databases-and-sql/joins-and-unions.md), for the query at the end of the walkthrough
> - [Functions and Iterators](../../python-programming/course.md#m6) (Python Programming), for the helper functions in the code

## Introduction

Everything in module 2 ran inside your own Python process with SQLite. That's perfect for learning and for apps that live on one device. But the moment two people on two phones need to see the same data, say a shared expense tracker for a Goa trip or a notes app you use on your laptop and your phone, the database has to live on a server that both can reach, and it has to be backed up, secured and always on.

Running that server yourself means renting a machine, installing PostgreSQL, configuring passwords and firewalls, setting up backups and keeping it patched. **Supabase** does all of that for you. You get a real, full PostgreSQL database in the cloud in about two minutes, a web dashboard to manage it, and an automatic web API to reach it from any app.

By the end of this article you will have a free Supabase project, know your way around the dashboard, have created a table with PostgreSQL types and constraints in the SQL Editor, understand the security model (roles, grants and Row Level Security), know which API key and which connection string to use, and have your secrets stored safely for the Python code in the next lesson.

> 💡 **Key Insight**
>
> Supabase is **not a different kind of database**. It is PostgreSQL, the same SQL you already know, plus tools around it: a dashboard, an auto-generated HTTP API, authentication and file storage. Anything you can do in PostgreSQL you can do in Supabase, and anything you learn here works on any other PostgreSQL server.

---

## Core Explanation

### 1. PostgreSQL in one page

**PostgreSQL** (often just "Postgres") is a free, open-source relational database that has been developed since the 1980s. It's consistently among the most used databases in developer surveys, and it's the default choice for new web applications. Compared with SQLite:

| | SQLite | PostgreSQL |
|---|---|---|
| Runs as | a library inside your program | a separate server you connect to over the network |
| Users at once | many readers, one writer at a time | many readers and writers at once |
| Types | flexible (type affinity) | strict, with many types: `uuid`, `jsonb`, `timestamptz`, arrays, ranges |
| Users and permissions | none (file permissions only) | roles, `GRANT`, `REVOKE`, row-level security |
| Extensions | few | many, such as `pgvector` for AI embeddings and PostGIS for maps |
| Best for | phones, desktop apps, tests, small sites | web apps, shared data, analytics |

The SQL you wrote in module 2 runs on PostgreSQL with only small changes, listed in section 6.

### 2. What Supabase adds

```mermaid
flowchart LR
  subgraph Supabase project
    PG[("PostgreSQL database")]
    API["Data API<br/>(auto-generated REST)"]
    Auth["Auth<br/>(users, logins)"]
    Store["Storage<br/>(files)"]
    RT["Realtime<br/>(live changes)"]
    API --> PG
    Auth --> PG
    Store --> PG
    RT --> PG
  end
  Dash["Dashboard<br/>(Table Editor, SQL Editor)"] --> PG
  Py["Python: supabase client"] -->|HTTPS| API
  Psy["Python: psycopg"] -->|"Postgres protocol"| PG
```

- **The database**: a full PostgreSQL server. You own the data and can connect to it with any Postgres tool.
- **Data API**: Supabase looks at your tables and automatically offers a REST API for them (using an open-source tool called PostgREST), so apps can read and write over HTTPS without you writing a backend. The `supabase` Python package talks to this API.
- **Auth**: sign-up and login (email, phone, Google, GitHub and more), with users stored in an `auth.users` table.
- **Storage**: file uploads like images and PDFs.
- **Realtime**: apps can subscribe to changes in a table and update live.
- **Dashboard**: a web UI with a spreadsheet-like Table Editor and a SQL Editor.

This course uses the database, the Data API and the dashboard.

**The free plan** (as of October 2026) gives you up to 2 active projects, a 500 MB database per project, and pauses a project after a week with no activity. A paused project keeps its data, and you can restore it from the dashboard. That's plenty for learning and small side projects; check the [pricing page](https://supabase.com/pricing) for current limits.

### 3. Create your project

1. Go to [supabase.com](https://supabase.com) and click **Start your project**. Sign up with GitHub or with an email address.
2. Supabase creates an **organization** for you (a container for projects and billing). On the free plan that's all you need.
3. Click **New project** and fill in:
   - **Project name**: for example `learning-db`.
   - **Database password**: click **Generate a password**, then **copy it into a password manager now**. This is the password of the `postgres` superuser. You'll need it for direct connections, and while you can reset it later in the dashboard, you can't view it again.
   - **Region**: pick the one closest to you and your users, such as South Asia (Mumbai) if you're in India. Data that travels a shorter distance comes back faster. The region can't be changed later.
4. Look at the **security options** on the same form. One of them is a checkbox for **automatically exposing new tables** to the Data API. Supabase changed this default in 2026 (details in section 7): new projects no longer expose new tables automatically, and on 30 October 2026 the same behaviour reaches existing projects. **This course leaves automatic exposure off** and grants access explicitly, which is the safer habit and works either way.
5. Click **Create new project** and wait a minute or two while the database starts.

Every project gets a **project ref**, a short random id like `abcdefghijklmnop`. It appears in your project's URL (`https://abcdefghijklmnop.supabase.co`) and in your connection strings.

### 4. A tour of the dashboard

The left sidebar of a project has many sections. These are the ones you'll use:

| Section | What it's for |
|---|---|
| **Table Editor** | View and edit tables like a spreadsheet; create tables with a form |
| **SQL Editor** | Write and run any SQL; save snippets |
| **Database** | Tables, functions, roles, extensions, indexes and backups |
| **Authentication** | Users, sign-in providers and policies |
| **Storage** | File buckets |
| **Advisors** | Security and performance warnings about your project, such as tables with RLS turned off |
| **Project Settings** | General settings, **API Keys**, database password and more |

At the top of the project page there's a **Connect** button. It opens a dialog with ready-made connection details: your project URL and key for app frameworks, and connection strings for direct database access. You'll use it in sections 8 and 9.

You can create tables in the **Table Editor** with a form, which is handy for exploring. This course uses the **SQL Editor** instead, because SQL is precise, repeatable, and can be saved in your project's code. Whatever you create with the form is just SQL underneath.

### 5. Create your first table in the SQL Editor

Open **SQL Editor**, start a new query, paste the following and click **Run**. It creates a small table of books for a reading club:

```sql
create table public.books (
    id          bigint generated always as identity primary key,
    title       text        not null,
    author      text        not null,
    pages       integer     check (pages > 0),
    price       numeric(8, 2) not null default 0,
    is_read     boolean     not null default false,
    tags        text[]      not null default '{}',
    added_at    timestamptz not null default now()
);

insert into public.books (title, author, pages, price, tags)
values ('The Guide', 'R. K. Narayan', 220, 299.00, '{fiction,classic}'),
       ('Wings of Fire', 'A. P. J. Abdul Kalam', 180, 350.50, '{biography}'),
       ('Malgudi Days', 'R. K. Narayan', 256, 250.00, '{fiction,short-stories}')
returning id, title;
```

Example output:

```
 id | title
----+---------------
  1 | The Guide
  2 | Wings of Fire
  3 | Malgudi Days
```

A few PostgreSQL features appear here that SQLite doesn't have in the same form:

- **`bigint generated always as identity`**: PostgreSQL generates the id. `always` means you can't accidentally insert your own value.
- **`numeric(8, 2)`**: an exact decimal with up to 8 digits, 2 after the point. Always use `numeric` for money, never floating-point.
- **`boolean`** with real `true`/`false` values.
- **`text[]`**: an **array** column. `'{fiction,classic}'` is array literal syntax. Arrays are handy for small lists like tags; for anything you'll join or search heavily, a separate table is still better.
- **`timestamptz`** stores an exact moment in time ("timestamp with time zone"), and `now()` is the current time. Use `timestamptz` rather than `timestamp` for event times.
- **`returning`** hands back the inserted rows.

Now query it. Everything from module 2 works:

```sql
select author, count(*) as books, sum(pages) as total_pages
from public.books
where 'fiction' = any(tags)
group by author
order by books desc;
```

Example output:

```
    author     | books | total_pages
---------------+-------+-------------
 R. K. Narayan |     2 |         476
```

`'fiction' = any(tags)` is true when the array contains `'fiction'`. Open the **Table Editor** now and you'll see `books` with your three rows.

To see a table's columns, PostgreSQL offers the standard `information_schema` views (SQLite used `PRAGMA table_info`):

```sql
select column_name, data_type, is_nullable
from information_schema.columns
where table_schema = 'public' and table_name = 'books'
order by ordinal_position;
```

### 6. PostgreSQL vs SQLite: the differences you'll notice

| Topic | SQLite | PostgreSQL |
|---|---|---|
| Auto ids | `INTEGER PRIMARY KEY` | `bigint generated always as identity primary key` |
| Booleans | `0` / `1` | `true` / `false` |
| Text into an integer column | accepted (type affinity) | error |
| Case-insensitive match | `LIKE` already is | `ILIKE` (`LIKE` is case-sensitive) |
| Casting | `CAST(x AS INTEGER)` | `CAST(x AS integer)` or `x::integer` |
| Current time | `CURRENT_TIMESTAMP` (text) | `now()` (a `timestamptz`) |
| NULLs in `ORDER BY … ASC` | first | last |
| Bare columns with `GROUP BY` | allowed | error |
| Foreign keys | off unless `PRAGMA foreign_keys = ON` | always on |
| Python placeholders | `?` | `%s` (psycopg) |
| Identifiers | case-insensitive | unquoted names are folded to lowercase; `"Title"` in double quotes is case-sensitive |

The last row trips people up: if you create a column as `"Title"` with quotes, you must always write `"Title"` with quotes afterwards. Stick to lowercase `snake_case` names in PostgreSQL and you'll never have to think about it.

### 7. Security: roles, grants and Row Level Security

This is the most important section of the lesson, because the Data API makes your database reachable from the internet.

**Roles.** PostgreSQL has users called **roles**. Supabase sets up several, and every Data API request runs as one of them:

| Role | Who uses it | Typical rights |
|---|---|---|
| `anon` | requests made with the publishable key and no logged-in user | read public data only |
| `authenticated` | requests from a logged-in user | read and write *their own* data |
| `service_role` | requests made with a secret key, from your servers only | full access, **bypasses Row Level Security** |
| `postgres` | you, in the SQL Editor or over a direct connection | owner of everything |

**Grants decide whether a role can touch a table at all.** Until 2026, Supabase gave `anon`, `authenticated` and `service_role` access to every new table in the `public` schema automatically. That changed: projects created from 30 May 2026 don't do this by default, and from **30 October 2026** it applies to all projects (tables that already existed keep their grants). Now, if a role has no grant, the Data API answers with a *"permission denied for table books"* error (code `42501`), whose hint tells you which `GRANT` is missing. Direct connections with psycopg are not affected, because you log in as `postgres`.

**Row Level Security (RLS) decides which rows a role can see.** When RLS is enabled on a table, the publishable key sees **no rows at all** until you write **policies**. A policy is a rule, written in SQL, that is checked for every row. RLS is the reason it's safe to put a publishable key inside a mobile app.

You need both: grants open the door to the table, policies decide which rows are behind it. For the `books` table, where everyone may read but only your server may write, run this in the SQL Editor:

```sql
-- 1. Who may use the table at all
grant select on public.books to anon, authenticated;
grant select, insert, update, delete on public.books to service_role;

-- 2. Turn on Row Level Security
alter table public.books enable row level security;

-- 3. Which rows the public may read: all of them
create policy "Books are readable by everyone"
  on public.books
  for select
  to anon, authenticated
  using (true);
```

`using (true)` means "every row passes". In a real multi-user app a policy usually compares a column with the logged-in user, such as `using (auth.uid() = owner_id)`, where `auth.uid()` is a Supabase function that returns the current user's id. The `service_role` needs no policy because it bypasses RLS, but it **does** still need its grant.

> ⚠️ Never turn RLS off on a table in the `public` schema that the Data API can reach. The **Advisors → Security Advisor** page lists tables that are exposed without RLS.

### 8. API keys: publishable and secret

Your project has two kinds of key, found in **Project Settings → API Keys** (the **Connect** dialog also shows the URL and publishable key):

| Key | Looks like | Runs as | Where it may live |
|---|---|---|---|
| **Publishable** | `sb_publishable_…` | `anon` (or `authenticated` once a user logs in) | anywhere, even in a browser or mobile app; RLS protects the data |
| **Secret** | `sb_secret_…` | `service_role` | **only** on servers and in your own scripts; never in front-end code or Git |

Older projects and tutorials use the **legacy** keys called `anon` and `service_role`, long strings starting with `eyJ`. They play the same two roles. Supabase is phasing them out by the end of 2026, so use the new publishable and secret keys for anything new.

You also need the **project URL**, `https://<project-ref>.supabase.co`.

### 9. Connection strings: talking to Postgres directly

The Data API is one way in. The other is a normal PostgreSQL connection, which tools like `psycopg`, `psql`, DBeaver and SQLAlchemy use. Click **Connect** at the top of your project to see the connection strings. There are three:

| Method | Host and port | User | Use it for |
|---|---|---|---|
| **Direct connection** | `db.<project-ref>.supabase.co:5432` | `postgres` | long-running servers, migrations, scripts, when your network supports IPv6 |
| **Session pooler** | `aws-<n>-<region>.pooler.supabase.com:5432` | `postgres.<project-ref>` | the same uses, when your network is **IPv4-only** (many home and office networks) |
| **Transaction pooler** | `aws-<n>-<region>.pooler.supabase.com:6543` | `postgres.<project-ref>` | serverless functions that open many short connections |

A **pooler** (Supabase's is called Supavisor) sits in front of the database and shares a small number of real connections among many clients, because each PostgreSQL connection uses memory on the server. The direct connection uses **IPv6** on the free plan, so if it fails to connect from your laptop, switch to the **session pooler**. Copy the host from the dialog rather than typing it: the pooler host depends on your project's region.

A connection string has this shape, and it's useful to be able to read one:

```python
from urllib.parse import urlsplit

def describe(conn_str):
    """Print the parts of a PostgreSQL connection string, hiding the password."""
    u = urlsplit(conn_str)
    if ".pooler." in u.hostname:
        mode = "transaction pooler" if u.port == 6543 else "session pooler"
    else:
        mode = "direct connection"
    print(f"{mode:<18}  user={u.username}  host={u.hostname}  port={u.port}  db={u.path.lstrip('/')}")

describe("postgresql://postgres:MyS3cret@db.abcdefghijklmnop.supabase.co:5432/postgres")
describe("postgresql://postgres.abcdefghijklmnop:MyS3cret@aws-0-ap-south-1.pooler.supabase.com:5432/postgres")
describe("postgresql://postgres.abcdefghijklmnop:MyS3cret@aws-0-ap-south-1.pooler.supabase.com:6543/postgres")
```

Output:

```
direct connection   user=postgres  host=db.abcdefghijklmnop.supabase.co  port=5432  db=postgres
session pooler      user=postgres.abcdefghijklmnop  host=aws-0-ap-south-1.pooler.supabase.com  port=5432  db=postgres
transaction pooler  user=postgres.abcdefghijklmnop  host=aws-0-ap-south-1.pooler.supabase.com  port=6543  db=postgres
```

(The project ref and pooler host above are made up; yours come from the Connect dialog.) If your password contains characters such as `@`, `:` or `/`, they must be percent-encoded in the URL, for example with `urllib.parse.quote(password, safe="")`. Generated passwords with only letters and digits avoid the problem.

### 10. Keep secrets out of your code

The secret key and the database password are as powerful as your Supabase login. **Never** paste them into a `.py` file you might commit to Git. The standard approach is **environment variables**, often kept in a file called `.env` in your project folder that is listed in `.gitignore`:

```
# .env  (add ".env" to .gitignore!)
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=sb_secret_xxxxxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=postgresql://postgres.abcdefghijklmnop:YOUR-PASSWORD@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
```

The `python-dotenv` package (`pip install python-dotenv`) loads that file into `os.environ` with one call, `load_dotenv()`. Your code then reads the values and should fail early with a clear message if something is missing:

```python
import os

def require_env(*names, env=None):
    """Return the named settings, or raise one clear error listing every missing one."""
    env = os.environ if env is None else env
    missing = [n for n in names if not env.get(n)]
    if missing:
        raise RuntimeError(f"Missing settings: {', '.join(missing)}. Add them to your .env file.")
    return {n: env[n] for n in names}

# Demonstrate with a stand-in dictionary instead of the real environment:
fake_env = {"SUPABASE_URL": "https://abcdefghijklmnop.supabase.co", "SUPABASE_KEY": ""}
try:
    require_env("SUPABASE_URL", "SUPABASE_KEY", "DATABASE_URL", env=fake_env)
except RuntimeError as e:
    print(e)

settings = require_env("SUPABASE_URL", env=fake_env)
print(settings)
```

Output:

```
Missing settings: SUPABASE_KEY, DATABASE_URL. Add them to your .env file.
{'SUPABASE_URL': 'https://abcdefghijklmnop.supabase.co'}
```

In the next lesson, `require_env("SUPABASE_URL", "SUPABASE_KEY")` is the first line of every script. If you ever commit a secret by accident, assume it's leaked: create a new secret key in **Project Settings → API Keys**, delete the old one, and reset the database password if that leaked too.

---

## Try It Yourself

Do these in your own Supabase project's SQL Editor.

1. Add a `reviews` table: id (identity), `book_id` referencing `books` with `on delete cascade`, `rating` from 1 to 5, a `comment`, and `created_at` defaulting to now. Insert two reviews for "The Guide".
2. Write a query that lists every book with its average rating (books without reviews should show `NULL`), sorted by title.
3. Give the `reviews` table the same security setup as `books`: public read, server write.
4. Use `describe()` on your own session pooler string (with the password replaced by `xxx`). Which user name does it show, and why is it different from the direct connection's?

<details>
<summary>Show answers</summary>

**1.**

```sql
create table public.reviews (
    id         bigint generated always as identity primary key,
    book_id    bigint not null references public.books (id) on delete cascade,
    rating     integer not null check (rating between 1 and 5),
    comment    text,
    created_at timestamptz not null default now()
);

insert into public.reviews (book_id, rating, comment)
select id, r.rating, r.comment
from public.books,
     (values (5, 'A classic'), (4, 'Lovely and gentle')) as r(rating, comment)
where title = 'The Guide';
```

The `insert … select` looks up the book's id instead of hard-coding it. A plain `values (1, 5, 'A classic')` also works if you know the id is 1.

**2.** A left join keeps books without reviews:

```sql
select b.title, round(avg(r.rating), 2) as avg_rating
from public.books b
left join public.reviews r on r.book_id = b.id
group by b.id, b.title
order by b.title;
```

Example output:

```
     title     | avg_rating
---------------+------------
 Malgudi Days  |
 The Guide     |       4.50
 Wings of Fire |
```

PostgreSQL's psql shows NULL as an empty cell.

**3.**

```sql
grant select on public.reviews to anon, authenticated;
grant select, insert, update, delete on public.reviews to service_role;
alter table public.reviews enable row level security;
create policy "Reviews are readable by everyone"
  on public.reviews for select to anon, authenticated using (true);
```

**4.** It shows `postgres.<your-project-ref>`. The pooler is shared by many projects, so the user name carries the project ref to tell the pooler which database to route you to. The direct connection goes to your own server, so plain `postgres` is enough.

</details>

---

## Real-World Examples

### Example 1: Startups shipping without a backend team

Many small teams build their first product on Supabase: a React or Flutter front end talks to the Data API with the publishable key, RLS policies enforce "users can only see their own rows", and there's no custom backend server at all until it's needed. Because it's plain PostgreSQL, moving to self-hosted Postgres later is a database dump and restore.

### Example 2: AI apps with pgvector

Supabase offers the `pgvector` extension, which stores AI embeddings in a PostgreSQL column and searches them by similarity. Teams building chatbots over their own documents often keep the documents, users and vectors in one Supabase database. The Retrieval-Augmented Generation (RAG) course builds on exactly this.

### Example 3: Internal tools and dashboards

Operations teams load spreadsheets into Supabase tables, then connect a BI tool through the session pooler connection string. The SQL Editor's saved snippets become the team's shared reports.

---

## Common Misconceptions

### Misconception 1: "Supabase is a NoSQL database like Firebase"

Supabase is often described as an open-source Firebase alternative, but underneath it's PostgreSQL: relational tables, SQL, joins, constraints and transactions. Firebase's Firestore is a document database, which is closer to MongoDB in module 4.

### Misconception 2: "The publishable key is a secret"

It's designed to be public and ships inside apps. What protects your data is **grants plus RLS policies**. The **secret key** is the one that must never leave your server.

### Misconception 3: "RLS is enabled, so my table is reachable"

RLS with no policies means the publishable key sees nothing, and since 2026 a missing grant means the role can't reach the table at all. If the Data API returns an empty list or a `42501` permission error, check grants and policies before debugging your Python.

### Misconception 4: "I should connect with the database password from my mobile app"

Never. Direct database credentials belong only on servers. Apps use the Data API with the publishable key and RLS.

---

## Interview Relevance

Supabase-specific questions are common in startup and full-stack interviews, and the PostgreSQL concepts behind them come up everywhere:

- *"What is Row Level Security?"* Per-row access rules written as SQL policies, checked by the database for every query; essential when clients talk to the database through an API.
- *"How do grants and RLS differ?"* Grants control access to the table; policies control which rows.
- *"Why use a connection pooler?"* Each Postgres connection costs server memory; a pooler shares a few connections among many clients, especially serverless ones.
- *"How do you store secrets?"* Environment variables or a secrets manager, never in source control, and rotate anything that leaks.
- *"PostgreSQL vs MySQL vs SQLite?"* Know the trade-offs from section 1.

A strong answer mentions defence in depth: least-privilege keys, grants, RLS and server-side validation together.

---

## Key Takeaways

- **Supabase is hosted PostgreSQL** plus a dashboard, an auto-generated Data API, auth, storage and realtime.
- **Create tables in the SQL Editor** with PostgreSQL types: `bigint generated always as identity`, `text`, `numeric`, `boolean`, `timestamptz`, arrays.
- **Security has two layers**: `GRANT` lets a role use a table (new tables need explicit grants from 2026), and **Row Level Security policies** decide which rows it sees.
- **Publishable keys** are safe in apps; **secret keys** and the **database password** stay on servers and in `.env` files that never reach Git.
- **Connect** directly (IPv6), through the **session pooler** (IPv4) or the **transaction pooler** (serverless).

---

**Up next:** [Querying Supabase from Python](querying-supabase-from-python.md)
