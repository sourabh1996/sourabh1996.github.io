---
title: "Ontology-Grounded Agents"
course: "Knowledge Graphs, Ontologies and Unstructured Data"
module: "6. Knowledge Graphs for AI Agents"
type: Article
level: Advanced
reading_time: 40 min
---

# Ontology-Grounded Agents: The Complete Guide

> 📚 **Before you start**
>
> - [Text-to-Cypher Agents](text-to-cypher-agents.md): an agent that reads the graph by writing queries, checked against the schema.
> - [What is an Ontology? A Worked Example](../03-ontologies-and-semantics/what-is-an-ontology-a-worked-example.md) and [RDF, RDFS and OWL in Plain English](../03-ontologies-and-semantics/rdf-rdfs-and-owl-in-plain-english.md): classes, subclasses, domain and range, `owl:disjointWith`, SHACL shapes and inference.
> - [Taxonomies, Schemas and Ontologies Compared](../03-ontologies-and-semantics/taxonomies-schemas-and-ontologies-compared.md): SKOS labels and synonyms (`skos:altLabel`).
> - [Semantic Search, Semantic Layers and Shared Meaning](../03-ontologies-and-semantics/semantic-search-semantic-layers-and-shared-meaning.md): why agents need one agreed meaning for each business term.

## Introduction

When a new employee joins Kiran Foods, someone hands them a glossary on day one: "a *vendor* and a *supplier* are the same thing here; *raw material* means ingredients, not packaging; only our own staff can be account managers; a supplier's salesperson is a *contact*, not an employee". Without it, the newcomer files things in the wrong place for weeks.

An AI agent working on a company knowledge graph is that newcomer, every single conversation. The last lesson's text-to-Cypher agent knew the graph's *schema* (which labels and relationships exist). It didn't know what anything *means*: that "vendor" is a Supplier, that ragi flour counts as an ingredient because grains are ingredients, or that a supplier's salesperson can't manage one of our accounts. And it could only read. The moment an agent **writes** to the graph ("Bhavesh from Saurashtra is handling our orders now, please update"), misunderstandings stop being wrong answers and become wrong data.

An **ontology-grounded agent** uses the ontology from module 3 as its glossary, its map and its rulebook. By the end of this lesson you'll be able to ground a user's words in ontology terms, plan a query by finding a path through the ontology instead of letting the model improvise one, answer with subclass inference, and guard every write the agent makes with domain, range, disjointness and shape checks that return errors the agent can act on.

> 💡 **Key Insight**
>
> Use the ontology at three moments: **before** the model acts (translate the user's words into ontology terms), **while** it plans (only paths the ontology allows), and **after** it proposes a change (validate against domains, ranges, disjoint classes and shapes). The model supplies language understanding; the ontology supplies meaning and rules. Neither is reliable alone.

---

## Core Explanation

### 1. Where the ontology sits

![Ontology-grounded agent. The user's message passes through grounding, which maps words such as vendor, raw material and looks after to ontology terms using labels and synonyms. A planner finds a path through the ontology between the grounded classes and compiles it into a query, with subclass inference so that grains and spices count as ingredients. Proposed writes go through a guard that checks domain, range, disjoint classes and SHACL-style shapes; rejected writes return an explanation to the LLM, which proposes a corrected fact; accepted facts are written to the knowledge graph with provenance. The ontology feeds all three stages](/img/diagrams/knowledge-graphs-ontologies-and-unstructured-data/ontology-grounded-agent.svg)
*The LLM never talks to the graph directly. Every read goes through the planner and every write through the guard, and both consult the ontology.*

### 2. The ontology, as a file first

Here is the Kiran Foods procurement ontology the agent will use, in Turtle. Read it the way module 3 taught you: classes and their parents, properties with domain and range, synonyms as `skos:altLabel`, a disjointness rule, and a shape.

```turtle
@prefix kf:   <https://kiranfoods.example/ontology#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

kf:Person          a owl:Class ; skos:prefLabel "person" .
kf:Employee        a owl:Class ; rdfs:subClassOf kf:Person ; skos:prefLabel "employee" ; skos:altLabel "staff", "colleague" .
kf:SupplierContact a owl:Class ; rdfs:subClassOf kf:Person ; skos:prefLabel "supplier contact" ; skos:altLabel "salesperson" .
kf:Employee owl:disjointWith kf:SupplierContact .

kf:Organisation    a owl:Class ; skos:prefLabel "organisation" ; skos:altLabel "company", "firm" .
kf:Supplier        a owl:Class ; rdfs:subClassOf kf:Organisation ; skos:prefLabel "supplier" ; skos:altLabel "vendor", "seller" .
kf:Product         a owl:Class ; skos:prefLabel "product" .
kf:Ingredient      a owl:Class ; rdfs:subClassOf kf:Product ; skos:prefLabel "ingredient" ; skos:altLabel "raw material" .
kf:Grain           a owl:Class ; rdfs:subClassOf kf:Ingredient ; skos:prefLabel "grain" .
kf:Spice           a owl:Class ; rdfs:subClassOf kf:Ingredient ; skos:prefLabel "spice" .
kf:Packaging       a owl:Class ; rdfs:subClassOf kf:Product ; skos:prefLabel "packaging" ; skos:altLabel "packing material" .
kf:Project         a owl:Class ; skos:prefLabel "project" .
kf:Place           a owl:Class ; skos:prefLabel "place" ; skos:altLabel "city", "town" .

kf:managesAccount  a owl:ObjectProperty ; rdfs:domain kf:Employee ; rdfs:range kf:Supplier ;
                   skos:prefLabel "manages account" ; skos:altLabel "looks after", "handles", "account manager" .
kf:worksFor        a owl:ObjectProperty ; rdfs:domain kf:Person ; rdfs:range kf:Organisation ; skos:prefLabel "works for" .
kf:contactFor      a owl:ObjectProperty ; rdfs:domain kf:SupplierContact ; rdfs:range kf:Organisation ;
                   skos:prefLabel "contact for" ; skos:altLabel "handles orders of" .
kf:supplies        a owl:ObjectProperty ; rdfs:domain kf:Supplier ; rdfs:range kf:Product ; skos:prefLabel "supplies" .
kf:usedIn          a owl:ObjectProperty ; rdfs:domain kf:Product ; rdfs:range kf:Project ; skos:prefLabel "used in" .
kf:leads           a owl:ObjectProperty ; rdfs:domain kf:Employee ; rdfs:range kf:Project ; skos:prefLabel "leads" .
kf:locatedIn       a owl:ObjectProperty ; rdfs:domain kf:Organisation ; rdfs:range kf:Place ; skos:prefLabel "located in" .

kf:SupplierShape a sh:NodeShape ; sh:targetClass kf:Supplier ;
    sh:property [ sh:path kf:locatedIn ; sh:minCount 1 ] ;
    sh:property [ sh:path [ sh:inversePath kf:managesAccount ] ; sh:minCount 1 ; sh:maxCount 1 ] .
```

Two lines carry most of the business knowledge. `kf:Employee owl:disjointWith kf:SupplierContact` says no one can be both our employee and a supplier's contact. The shape says every supplier needs a location and **exactly one** account manager on our side (`sh:inversePath` means "count the `managesAccount` arrows pointing *at* this supplier").

### 3. The same ontology as Python data

To keep everything runnable, the agent's code holds the ontology as dictionaries. In production you'd load the Turtle file with a library such as RDFLib and read the same information out of it.

```python
import json
import re
from collections import deque

CLASSES = {  # class: (parent, preferred label, synonyms)
    "Person": (None, "person", []),
    "Employee": ("Person", "employee", ["staff", "colleague"]),
    "SupplierContact": ("Person", "supplier contact", ["salesperson"]),
    "Organisation": (None, "organisation", ["company", "firm"]),
    "Supplier": ("Organisation", "supplier", ["vendor", "seller"]),
    "Product": (None, "product", []),
    "Ingredient": ("Product", "ingredient", ["raw material"]),
    "Grain": ("Ingredient", "grain", []),
    "Spice": ("Ingredient", "spice", []),
    "Packaging": ("Product", "packaging", ["packing material"]),
    "Project": (None, "project", []),
    "Place": (None, "place", ["city", "town"]),
}
PROPERTIES = {  # property: (domain, range, preferred label, synonyms)
    "managesAccount": ("Employee", "Supplier", "manages account", ["looks after", "handles", "account manager"]),
    "worksFor": ("Person", "Organisation", "works for", []),
    "contactFor": ("SupplierContact", "Organisation", "contact for", ["handles orders of"]),
    "supplies": ("Supplier", "Product", "supplies", []),
    "usedIn": ("Product", "Project", "used in", []),
    "leads": ("Employee", "Project", "leads", []),
    "locatedIn": ("Organisation", "Place", "located in", []),
}
DISJOINT = [("Employee", "SupplierContact")]

def ancestors(cls):
    """The class itself and every class above it."""
    out = []
    while cls:
        out.append(cls)
        cls = CLASSES[cls][0]
    return out

def is_a(cls, target):
    return target in ancestors(cls)

print("Grain:", " -> ".join(ancestors("Grain")))
print("Is a Spice a Product?", is_a("Spice", "Product"), "| Is Packaging an Ingredient?", is_a("Packaging", "Ingredient"))
```

Output:

```
Grain: Grain -> Ingredient -> Product
Is a Spice a Product? True | Is Packaging an Ingredient? False
```

And the facts (the **instance data**) the agent works on. Each thing has its most specific class; the ontology supplies the rest.

```python
TYPE_OF = {
    "Ravi Iyer": "Employee", "Farhan Shaikh": "Employee", "Kavya Reddy": "Employee", "Neha Gupta": "Employee",
    "Kiran Foods": "Organisation",
    "Deccan Millets": "Supplier", "Malabar Spice House": "Supplier", "Nashik Agro Pack": "Supplier",
    "Saurashtra Groundnut": "Supplier",
    "ragi flour": "Grain", "jowar flour": "Grain", "chai masala blend": "Spice", "snack pouches": "Packaging",
    "Millet Snacks Launch": "Project", "Hyderabad": "Place", "Kochi": "Place", "Gondal": "Place",
}
GRAPH = {
    ("Ravi Iyer", "managesAccount", "Deccan Millets"), ("Kavya Reddy", "managesAccount", "Malabar Spice House"),
    ("Farhan Shaikh", "managesAccount", "Nashik Agro Pack"),
    ("Deccan Millets", "supplies", "ragi flour"), ("Deccan Millets", "supplies", "jowar flour"),
    ("Malabar Spice House", "supplies", "chai masala blend"), ("Nashik Agro Pack", "supplies", "snack pouches"),
    ("ragi flour", "usedIn", "Millet Snacks Launch"), ("jowar flour", "usedIn", "Millet Snacks Launch"),
    ("chai masala blend", "usedIn", "Millet Snacks Launch"), ("snack pouches", "usedIn", "Millet Snacks Launch"),
    ("Neha Gupta", "leads", "Millet Snacks Launch"),
    ("Deccan Millets", "locatedIn", "Hyderabad"), ("Malabar Spice House", "locatedIn", "Kochi"),
    ("Saurashtra Groundnut", "locatedIn", "Gondal"),
}
print(len(TYPE_OF), "things,", len(GRAPH), "facts")
```

Output:

```
17 things, 15 facts
```

### 4. Use 1: grounding the user's words

Users say "vendor", "raw material" and "looks after". The graph says `Supplier`, `Ingredient` and `managesAccount`. **Grounding** maps one to the other using the ontology's labels and synonyms, plus the names of known things. Longer phrases are matched first, so "raw material" wins over "material".

```python
LEXICON = {}
for cls, (_, label, syns) in CLASSES.items():
    for term in [label, label + "s", *syns, *[s + "s" for s in syns]]:
        LEXICON[term] = ("class", cls)
for prop, (_, _, label, syns) in PROPERTIES.items():
    for term in [label, *syns]:
        LEXICON[term] = ("property", prop)
for thing in TYPE_OF:
    LEXICON[thing.lower()] = ("thing", thing)

def ground(text):
    text = text.lower()
    found = []
    for term in sorted(LEXICON, key=len, reverse=True):
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, text):
            found.append((term, *LEXICON[term]))
            text = re.sub(pattern, " ", text)          # each word is used once
    return found

question = "Which staff look after vendors of raw material for the Millet Snacks Launch?"
for term, kind, target in ground(question):
    print(f"{term!r:<24} -> {kind:<8} {target}")
```

Output:

```
'millet snacks launch'   -> thing    Millet Snacks Launch
'raw material'           -> class    Ingredient
'vendors'                -> class    Supplier
'staff'                  -> class    Employee
```

Every business word now points at an exact ontology term. "Look after" didn't match (the synonym list has "looks after"), which is harmless here because the planner in the next section finds the connecting property from the classes alone, but it shows why synonym lists need maintenance from real user questions. In production, grounding usually combines this lexicon with embedding similarity over labels (so "suppliers' sales reps" can still find `SupplierContact`), and asks the user when two terms are equally likely.

### 5. Use 2: planning a query through the ontology

The grounded question mentions `Employee`, `Supplier`, `Ingredient` and a `Project`. How are they connected? Instead of letting the model guess, **search the ontology** for a path: classes are nodes, properties are edges (with domain and range, inherited by subclasses). Breadth-first search finds the shortest chain of properties through the required classes.

```python
def connects(cls_a, cls_b):
    """Properties that can link an instance of cls_a to one of cls_b, in either direction."""
    out = []
    for prop, (dom, rng, _, _) in PROPERTIES.items():
        if is_a(cls_a, dom) and (is_a(cls_b, rng) or is_a(rng, cls_b)):
            out.append((prop, "->"))
        if is_a(cls_b, dom) and (is_a(cls_a, rng) or is_a(rng, cls_a)):
            out.append((prop, "<-"))
    return out

def plan(class_sequence):
    steps = []
    for a, b in zip(class_sequence, class_sequence[1:]):
        options = connects(a, b)
        if not options:
            raise ValueError(f"the ontology has no property linking {a} and {b}")
        steps.append((a, *options[0], b))
    return steps

steps = plan(["Employee", "Supplier", "Ingredient", "Project"])
for a, prop, direction, b in steps:
    arrow = f"-[:{prop}]->" if direction == "->" else f"<-[:{prop}]-"
    print(f"({a}) {arrow} ({b})")
```

Output:

```
(Employee) -[:managesAccount]-> (Supplier)
(Supplier) -[:supplies]-> (Ingredient)
(Ingredient) -[:usedIn]-> (Project)
```

The plan is fixed by the ontology: an employee manages a supplier's account, the supplier supplies the ingredient, the ingredient is used in the project. The order of classes came from the question (in practice the LLM proposes it from the grounded terms, which is a much easier job than writing a query). Now the plan compiles into Cypher, using the most specific labels:

```python
def to_cypher(steps, project_name):
    var = {cls: cls[0].lower() + str(i) for i, cls in enumerate([steps[0][0]] + [s[3] for s in steps])}
    parts = [f"({var[steps[0][0]]}:{steps[0][0]})"]
    for a, prop, direction, b in steps:
        rel = re.sub(r"(?<!^)(?=[A-Z])", "_", prop).upper()          # managesAccount -> MANAGES_ACCOUNT
        node = f"({var[b]}:{b} {{name: '{project_name}'}})" if b == "Project" else f"({var[b]}:{b})"
        parts.append(f"-[:{rel}]->{node}" if direction == "->" else f"<-[:{rel}]-{node}")
    returns = ", ".join(f"{var[c]}.name" for c in list(var)[:-1])
    return "MATCH " + "".join(parts) + f" RETURN DISTINCT {returns}"

print(to_cypher(steps, "Millet Snacks Launch"))
```

Output:

```
MATCH (e0:Employee)-[:MANAGES_ACCOUNT]->(s1:Supplier)-[:SUPPLIES]->(i2:Ingredient)-[:USED_IN]->(p3:Project {name: 'Millet Snacks Launch'}) RETURN DISTINCT e0.name, s1.name, i2.name
```

This query can't have a wrong direction or an invented relationship: it was built from the ontology, not written freehand. That's the main difference from the last lesson. Text-to-Cypher is flexible and needs a validator; ontology planning is narrower and correct by construction. Agents often use both: a planned query when the question grounds cleanly, free generation with validation when it doesn't.

### 6. Use 3: answering with inference

Run the plan on the instance data. One detail makes or breaks it: `ragi flour` is stored as a `Grain`, not as an `Ingredient`. A plain label match finds nothing. With the ontology's subclass rule (a Grain *is an* Ingredient), it finds everything:

```python
def matches(thing, cls, use_inference):
    return is_a(TYPE_OF[thing], cls) if use_inference else TYPE_OF[thing] == cls

def run_plan(steps, project_name, use_inference=True):
    rows = [[t] for t in TYPE_OF if matches(t, steps[0][0], use_inference)]
    for a, prop, direction, b in steps:
        nxt = []
        for row in rows:
            for s, p, o in sorted(GRAPH):
                start, end = (s, o) if direction == "->" else (o, s)
                if p == prop and start == row[-1] and matches(end, b, use_inference):
                    nxt.append(row + [end])
        rows = nxt
    return [r for r in rows if r[-1] == project_name]

print("without inference:", run_plan(steps, "Millet Snacks Launch", use_inference=False))
print("with inference:")
for employee, supplier, ingredient, _ in run_plan(steps, "Millet Snacks Launch"):
    print(f"  {employee} looks after {supplier}, which supplies {ingredient} ({TYPE_OF[ingredient]})")
```

Output:

```
without inference: []
with inference:
  Ravi Iyer looks after Deccan Millets, which supplies jowar flour (Grain)
  Ravi Iyer looks after Deccan Millets, which supplies ragi flour (Grain)
  Kavya Reddy looks after Malabar Spice House, which supplies chai masala blend (Spice)
```

Farhan Shaikh and Nashik Agro Pack are correctly left out: their snack pouches are `Packaging`, which the ontology says is a Product but not an Ingredient. That's the user's own glossary rule ("raw material means ingredients, not packaging") applied automatically.

In Neo4j, the usual way to get the same effect is to **materialise** inferred labels when loading (a `Grain` node also gets the `Ingredient` and `Product` labels), so plain Cypher works. In an RDF store, a reasoner applies `rdfs:subClassOf` at query time. Either way, the ontology decides.

### 7. Use 4: guarding the agent's writes

Now the dangerous part. A user tells the agent:

> *"Bhavesh Patel from Saurashtra Groundnut is handling our orders now. Please update the graph."*

The agent's model proposes facts. The **write guard** checks each proposed fact against the ontology before anything is written:

1. The property exists.
2. The subject's class fits the property's **domain**, and the object's class fits its **range** (with subclasses).
3. New things get a declared class, and that class must not be **disjoint** with any class the thing already has.
4. After the change, the **shapes** still hold (every supplier has a location and exactly one account manager).

Every rejection explains itself in ontology terms, so the model can correct its proposal.

```python
def an(word):
    return ("an " if word[0] in "AEIOU" else "a ") + word

def check_write(facts, new_types):
    types = dict(TYPE_OF)
    problems = []
    for thing, cls in new_types.items():
        if cls not in CLASSES:
            problems.append(f"{cls} is not a class in the ontology")
            continue
        if thing in types:
            for a, b in DISJOINT:
                if {a, b} <= set(ancestors(types[thing]) + ancestors(cls)):
                    problems.append(f"{thing} is already {an(types[thing])}; {a} and {b} are disjoint")
        types.setdefault(thing, cls)
    accepted = []
    for s, p, o in facts:
        if p not in PROPERTIES:
            problems.append(f"{p} is not a property in the ontology; use one of {sorted(PROPERTIES)}")
            continue
        dom, rng = PROPERTIES[p][:2]
        if s not in types or o not in types:
            problems.append(f"declare the class of {s if s not in types else o} first")
            continue
        if not is_a(types[s], dom):
            fits = [q for q, (d, r, *_) in PROPERTIES.items() if is_a(types[s], d) and is_a(types[o], r)]
            problems.append(f"{p} needs {an(dom)} as subject, but {s} is {an(types[s])}; properties that fit: {fits}")
        elif not is_a(types[o], rng):
            problems.append(f"{p} needs {an(rng)} as object, but {o} is {an(types[o])}")
        else:
            accepted.append((s, p, o))
    graph = GRAPH | set(accepted)                     # shapes are checked on the facts that passed
    for sup in [t for t, c in types.items() if is_a(c, "Supplier")]:
        managers = [s for s, p, o in graph if p == "managesAccount" and o == sup]
        if len(managers) != 1:
            problems.append(f"shape: {sup} must have exactly one account manager, has {len(managers)}: {managers}")
    return problems

first_try = {"facts": [["Bhavesh Patel", "managesAccount", "Saurashtra Groundnut"]],
             "new_types": {"Bhavesh Patel": "SupplierContact"}}
for p in check_write([tuple(f) for f in first_try["facts"]], first_try["new_types"]):
    print("rejected:", p)
```

Output:

```
rejected: managesAccount needs an Employee as subject, but Bhavesh Patel is a SupplierContact; properties that fit: ['worksFor', 'contactFor']
rejected: shape: Saurashtra Groundnut must have exactly one account manager, has 0: []
```

Two problems, both real. The model mapped "handling our orders" to `managesAccount` (the synonym "handles" pointed it there), but Bhavesh is the *supplier's* person, and only our employees manage accounts. The guard said so and listed the properties that do fit. The second message is the shape: Saurashtra Groundnut still has no account manager on our side, a gap that existed before this conversation and that the agent should mention rather than paper over.

Now the agent loop: propose, check, and on rejection send the messages back to the model for a corrected proposal. The pretend model's second proposal is what a real model wrote after reading those two messages.

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel

writer_llm = FakeListChatModel(responses=[
    json.dumps(first_try),
    json.dumps({"facts": [["Bhavesh Patel", "worksFor", "Saurashtra Groundnut"],
                          ["Bhavesh Patel", "contactFor", "Kiran Foods"]],
                "new_types": {"Bhavesh Patel": "SupplierContact"},
                "note_to_user": "Saurashtra Groundnut has no Kiran Foods account manager. Who should it be?"}),
])

def guarded_update(message, llm, max_attempts=3):
    prompt = f"Propose facts for this update, using only the ontology.\nUpdate: {message}"
    for attempt in range(1, max_attempts + 1):
        proposal = json.loads(llm.invoke(prompt).content)
        facts = [tuple(f) for f in proposal["facts"]]
        problems = [p for p in check_write(facts, proposal["new_types"])
                    if not p.startswith("shape:") or "Saurashtra" not in p]      # a gap that pre-dates this update
        print(f"attempt {attempt}: {facts}")
        if not problems:
            GRAPH.update(facts)
            TYPE_OF.update(proposal["new_types"])
            return proposal.get("note_to_user")
        for p in problems:
            print("   rejected:", p)
        prompt += "\nYour proposal was rejected:\n" + "\n".join(problems) + "\nPropose corrected facts."
    return "Update not applied; needs a person."

note = guarded_update("Bhavesh Patel from Saurashtra Groundnut is handling our orders now.", writer_llm)
print("written. Note for the user:", note)
print("Bhavesh in graph:", sorted(f for f in GRAPH if f[0] == "Bhavesh Patel"))
```

Output:

```
attempt 1: [('Bhavesh Patel', 'managesAccount', 'Saurashtra Groundnut')]
   rejected: managesAccount needs an Employee as subject, but Bhavesh Patel is a SupplierContact; properties that fit: ['worksFor', 'contactFor']
attempt 2: [('Bhavesh Patel', 'worksFor', 'Saurashtra Groundnut'), ('Bhavesh Patel', 'contactFor', 'Kiran Foods')]
written. Note for the user: Saurashtra Groundnut has no Kiran Foods account manager. Who should it be?
Bhavesh in graph: [('Bhavesh Patel', 'contactFor', 'Kiran Foods'), ('Bhavesh Patel', 'worksFor', 'Saurashtra Groundnut')]
```

The final write says what the user meant: Bhavesh works for Saurashtra Groundnut and is their contact for Kiran Foods. The agent also turned the remaining shape violation into a question for the user instead of inventing an account manager. That's the behaviour you want from an agent with write access: precise changes, and honest questions where the rules expose a gap.

Notice how the guard treated the pre-existing gap: it's filtered out of the *blocking* problems (it isn't this update's fault) but not hidden, which is why the model could raise it. Production systems usually separate **blocking violations** (introduced by this change) from **warnings** (already present), so old data problems don't freeze every update.

### 8. Putting the ontology in front of the model

The model itself also benefits from seeing the ontology, compactly. A full OWL file is long; what helps most in a prompt is a summary of classes with their parents and synonyms, and properties with domain and range:

```python
def ontology_brief():
    lines = ["Classes (parent; also called):"]
    for cls, (parent, _, syns) in CLASSES.items():
        lines.append(f"- {cls}" + (f" (is {an(parent)})" if parent else "") + (f"; also: {', '.join(syns)}" if syns else ""))
    lines.append("Properties (domain -> range):")
    lines += [f"- {p}: {d} -> {r}" for p, (d, r, *_) in PROPERTIES.items()]
    lines.append("Rules: Employee and SupplierContact are disjoint. Every Supplier has exactly one account manager.")
    return "\n".join(lines)

brief = ontology_brief()
print(brief)
print(len(brief.split()), "words")
```

Output:

```
Classes (parent; also called):
- Person
- Employee (is a Person); also: staff, colleague
- SupplierContact (is a Person); also: salesperson
- Organisation; also: company, firm
- Supplier (is an Organisation); also: vendor, seller
- Product
- Ingredient (is a Product); also: raw material
- Grain (is an Ingredient)
- Spice (is an Ingredient)
- Packaging (is a Product); also: packing material
- Project
- Place; also: city, town
Properties (domain -> range):
- managesAccount: Employee -> Supplier
- worksFor: Person -> Organisation
- contactFor: SupplierContact -> Organisation
- supplies: Supplier -> Product
- usedIn: Product -> Project
- leads: Employee -> Project
- locatedIn: Organisation -> Place
Rules: Employee and SupplierContact are disjoint. Every Supplier has exactly one account manager.
121 words
```

About 120 words carry the glossary, the map and the rules. That brief goes into the system prompt; the full checks still run in code, because a prompt can be misread and code can't.

### 9. Ontologies in real agent stacks

| Need | Common tools |
|---|---|
| Load and query an OWL/RDFS ontology in Python | **RDFLib** (parse Turtle, query with SPARQL) |
| Validate data against SHACL shapes | **pySHACL** in Python; SHACL engines in RDF databases |
| Bring an ontology into Neo4j | **neosemantics (n10s)**, Neo4j's plugin for importing RDF/OWL and validating with SHACL |
| Reasoning (subclasses, disjointness, more) | RDFS/OWL reasoners in triple stores; materialised labels in property graphs |
| Expose the graph to any agent | Graph tools over **MCP** (Neo4j publishes MCP servers for reading the schema and running read queries), with the ontology brief in the tool descriptions |

Whatever the stack, the pattern is the one you built: ground with labels and synonyms, plan with domains and ranges, infer with subclasses, and guard writes with domain, range, disjointness and shapes.

---

## Try It Yourself

1. **A new synonym.** Users keep writing "look after" (without the s). Add it as a synonym of `managesAccount`, rebuild `LEXICON`, and ground the question from section 4 again.
2. **Plan a different question.** *"Which vendors in which cities supply spices?"* Write the class sequence, run `plan`, and run the plan on the data with a small change: the last class isn't a Project, so adapt the call (hint: `run_plan` filters on the last element; try the sequence `["Place", "Supplier", "Spice"]` and remove the project filter).
3. **A sneaky write.** The model proposes `("Kavya Reddy", "worksFor", "Malabar Spice House")` with `new_types={"Kavya Reddy": "SupplierContact"}`. Which check stops it, and why is that check important?

<details>
<summary>Show answers</summary>

**1.**

```python
PROPERTIES["managesAccount"][3].append("look after")
LEXICON["look after"] = ("property", "managesAccount")
for term, kind, target in ground(question):
    print(f"{term!r:<24} -> {kind:<8} {target}")
```

Output:

```
'millet snacks launch'   -> thing    Millet Snacks Launch
'raw material'           -> class    Ingredient
'look after'             -> property managesAccount
'vendors'                -> class    Supplier
'staff'                  -> class    Employee
```

Collect the phrases that fail to ground from real conversations and review them weekly; it's the cheapest way to improve an agent's understanding.

**2.**

```python
spice_plan = plan(["Place", "Supplier", "Spice"])
print(spice_plan)
rows = [[t] for t in TYPE_OF if is_a(TYPE_OF[t], "Place")]
for a, prop, direction, b in spice_plan:
    rows = [r + [o if direction == "->" else s] for r in rows for s, p, o in sorted(GRAPH)
            if p == prop and (s if direction == "->" else o) == r[-1] and is_a(TYPE_OF[o if direction == "->" else s], b)]
print(rows)
```

Output:

```
[('Place', 'locatedIn', '<-', 'Supplier'), ('Supplier', 'supplies', '->', 'Spice')]
[['Kochi', 'Malabar Spice House', 'chai masala blend']]
```

The planner found that a Place connects to a Supplier through `locatedIn` pointing *into* the place, so the arrow is reversed in the query. Directions come from the ontology, not from the word order of the question.

**3.**

```python
print(check_write([("Kavya Reddy", "worksFor", "Malabar Spice House")], {"Kavya Reddy": "SupplierContact"}))
```

Output:

```
['Kavya Reddy is already an Employee; Employee and SupplierContact are disjoint', 'shape: Saurashtra Groundnut must have exactly one account manager, has 0: []']
```

The disjointness rule (the second message is the old Saurashtra gap again, a warning rather than this write's fault). Without it, a misunderstanding ("Kavya works with Malabar") would quietly turn our own buyer into a supplier's salesperson, and every later query about our staff or our account managers would be wrong. Disjointness is how an ontology catches the agent confusing two kinds of thing.

</details>

---

## Real-World Examples

- **Enterprise "ontology layers"** that give operational agents one shared model of the business (customers, orders, plants, assets) with actions defined on the model, so an agent's changes respect business rules.
- **Healthcare**: agents that map clinicians' words to SNOMED CT or ICD codes (grounding), navigate the ontology's hierarchy (inference), and check that orders fit clinical rules before submission.
- **Finance**: the FIBO ontology (Financial Industry Business Ontology) used to ground terms such as "counterparty" and "derivative" consistently across systems and assistants.
- **Manufacturing and IoT**: asset ontologies so that an agent asked about "all pumps in plant 2" finds every subclass of pump and every sensor attached to them.
- **E-commerce catalogues**: product ontologies with synonyms ("chai" and "tea") and category hierarchies so that shopping assistants ground queries and keep catalogue edits valid.

---

## Common Misconceptions

### "The LLM already knows what 'supplier' means"

It knows the everyday meaning, not yours. Your rules (who can manage accounts, whether packaging counts as raw material) live only in your ontology.

### "An ontology slows the agent down"

The checks are microseconds of Python. What slows a team down is cleaning up wrong writes and explaining wrong answers.

### "Put the whole OWL file in the prompt and the model will follow it"

A compact brief helps the model propose good actions, but rules must be enforced in code. Prompts guide; guards guarantee.

### "Ontology-grounding replaces text-to-Cypher"

They suit different questions. Planned queries are safe for questions that ground cleanly; validated generation handles the rest.

---

## Interview Relevance

Expect *"How would you stop an agent from corrupting a knowledge graph?"* or *"How do ontologies help LLM agents?"* A strong answer names the three moments (grounding user terms with labels, synonyms and embeddings; planning queries as paths through the ontology's domains and ranges; validating writes with domain, range, disjointness and SHACL shapes), explains subclass inference with a concrete example, separates blocking violations from warnings, keeps rules in code with only a brief in the prompt, and mentions tools such as RDFLib, pySHACL, Neo4j's neosemantics, and graph access over MCP.

---

## Key Takeaways

- **Ground first**: map users' words to ontology terms with labels and synonyms before the model plans anything.
- **Plan through the ontology**: domains and ranges give query paths that can't have wrong directions or invented relations.
- **Infer with subclasses** so that "ingredients" includes grains and spices, and excludes packaging, exactly as the business defines them.
- **Guard every write** with domain, range, disjointness and shape checks, and return explanations the model can act on.
- **Turn rule violations into questions** for the user rather than letting the agent guess.

---

**Up next:** [Lab: A GraphRAG agent over company documents](lab-a-graphrag-agent-over-company-documents.md)
