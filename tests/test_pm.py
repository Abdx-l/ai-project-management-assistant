import unittest
from pm import add_note, add_task, ask, create_project, database, summary


class ProjectTests(unittest.TestCase):
    def test_costs_and_cited_retrieval(self):
        with database(":memory:") as con:
            project = create_project(con, "Bridge", 1000)
            add_task(con, project, "Inspect", 200, "done")
            add_task(con, project, "Repair", 300)
            note_id = add_note(con, project, "Foundation inspection requires reinforcement.")
            add_note(con, project, "Lighting replacement is complete.")
            self.assertEqual(summary(con, project)["remaining"], 500)
            result = ask(con, "foundation reinforcement")
            self.assertEqual(result["matches"][0]["citation"], f"note:{note_id}")
            self.assertIn("Foundation inspection", result["answer"])
            self.assertEqual(ask(con, "unrelated")["matches"], [])

    def test_constraints(self):
        with database(":memory:") as con:
            project = create_project(con, "Bridge", 10)
            with self.assertRaises(ValueError): add_task(con, project, "", 1)
            with self.assertRaises(ValueError): ask(con, " ")


if __name__ == "__main__": unittest.main()

