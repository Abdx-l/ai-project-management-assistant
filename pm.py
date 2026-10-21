from contextlib import contextmanager
import math
import re
import sqlite3


@contextmanager
def database(path):
    con = sqlite3.connect(path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript("""
    CREATE TABLE IF NOT EXISTS project(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, budget REAL NOT NULL CHECK(budget>=0));
    CREATE TABLE IF NOT EXISTS task(id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES project(id),
        title TEXT NOT NULL, cost REAL NOT NULL CHECK(cost>=0), status TEXT NOT NULL CHECK(status IN ('todo','doing','done')));
    CREATE TABLE IF NOT EXISTS note(id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES project(id), body TEXT NOT NULL);
    """)
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally: con.close()


def create_project(con, name, budget):
    if not isinstance(name, str) or not name.strip(): raise ValueError("name required")
    cur = con.execute("INSERT INTO project(name,budget) VALUES(?,?)", (name.strip(), budget))
    return cur.lastrowid


def add_task(con, project_id, title, cost, status="todo"):
    if not isinstance(title, str) or not title.strip(): raise ValueError("title required")
    cur = con.execute("INSERT INTO task(project_id,title,cost,status) VALUES(?,?,?,?)", (project_id, title.strip(), cost, status))
    return cur.lastrowid


def add_note(con, project_id, body):
    if not isinstance(body, str) or not body.strip(): raise ValueError("note required")
    cur = con.execute("INSERT INTO note(project_id,body) VALUES(?,?)", (project_id, body.strip()))
    return cur.lastrowid


def summary(con, project_id):
    row = con.execute("""SELECT p.id,p.name,p.budget,COALESCE(SUM(t.cost),0) AS spent,
        COUNT(t.id) AS task_count,COALESCE(SUM(CASE WHEN t.status='done' THEN 1 ELSE 0 END),0) AS done_count
        FROM project p LEFT JOIN task t ON t.project_id=p.id WHERE p.id=? GROUP BY p.id""", (project_id,)).fetchone()
    if row is None: return None
    value = dict(row)
    value["remaining"] = round(value["budget"] - value["spent"], 2)
    return value


def terms(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def ask(con, query, limit=3):
    query_terms = set(terms(query))
    if not query_terms: raise ValueError("query needs words")
    docs = con.execute("""SELECT n.id,n.body,p.id AS project_id,p.name
        FROM note n JOIN project p ON p.id=n.project_id ORDER BY n.id""").fetchall()
    count = len(docs)
    frequency = {word: sum(word in set(terms(doc["body"] + " " + doc["name"])) for doc in docs) for word in query_terms}
    ranked = []
    for doc in docs:
        words = terms(doc["body"] + " " + doc["name"])
        overlap = query_terms.intersection(words)
        value = sum((1 + math.log(words.count(word))) * math.log((count + 1) / (frequency[word] + 0.5)) for word in overlap)
        if value > 0: ranked.append((value, doc))
    ranked.sort(key=lambda item: (-item[0], item[1]["id"]))
    results = []
    for value, doc in ranked[:limit]:
        results.append({"citation": f"note:{doc['id']}", "project": doc["name"], "excerpt": doc["body"],
                        "cost": summary(con, doc["project_id"]), "score": round(value, 3)})
    return {"query": query, "matches": results, "answer": "No matching project note." if not results else
            "\n".join(f"[{item['citation']}] {item['project']}: {item['excerpt']}" for item in results)}

