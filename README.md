# AI Project Management Assistant

A local project tracking and cost-analysis API with a retrieval-based assistant. Projects, tasks, budgets, and actual costs live in SQLite. `/ask?q=...` retrieves relevant notes and returns a cited extract with project cost context. The local assistant does not call an LLM; this makes its answers repeatable and prevents invented project facts.

```sh
python app.py --db projects.db
python -m unittest discover -s tests -v
```

API: `POST /projects`, `POST /projects/{id}/tasks`, `POST /projects/{id}/notes`, `GET /projects/{id}`, `GET /ask?q=budget`. JSON request examples are in `examples/requests.http`. A future PGVector/LangGraph adapter can replace the local term-frequency retriever after credentials and deployment are available; that integration is not claimed as verified here.

