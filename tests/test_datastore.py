import os
import tempfile
import unittest
from datetime import datetime, timedelta

from scout.datastore import DataStore


class TestDataStore(unittest.TestCase):
    def test_upsert_and_cooldown_logic(self):
        with tempfile.TemporaryDirectory() as td:
            db = os.path.join(td, "scout.db")
            ds = DataStore(db)
            try:
                repo_id, created = ds.upsert_repository(
                    url="https://github.com/foo/bar",
                    owner="foo",
                    name="bar",
                    description="desc",
                    readme_text="# readme",
                    readme_html="<h1>readme</h1>",
                    agent_notes="notes",
                    tags=None,
                    embedding=None,
                    embedding_dim=None,
                    visit_source="test",
                    visit_reason="unit",
                )
                self.assertTrue(created)
                self.assertGreater(repo_id, 0)

                # Immediately after insert, cooldown should block
                self.assertFalse(ds.can_visit("https://github.com/foo/bar"))

                # Manually rewind last_visited to older than 30 days
                old = (datetime.utcnow() - timedelta(days=31)).isoformat()
                ds.conn.execute(
                    "UPDATE repositories SET last_visited=? WHERE id=?",
                    (old, repo_id),
                )
                ds.conn.commit()
                self.assertTrue(ds.can_visit("https://github.com/foo/bar"))

                # Update path should not create a new row
                repo_id2, created2 = ds.upsert_repository(
                    url="https://github.com/foo/bar",
                    owner="foo",
                    name="bar",
                    description="desc2",
                    readme_text="# readme2",
                    readme_html=None,
                    agent_notes="notes2",
                    tags=None,
                    embedding=None,
                    embedding_dim=None,
                    visit_source="test2",
                    visit_reason="unit2",
                )
                self.assertFalse(created2)
                self.assertEqual(repo_id2, repo_id)
            finally:
                ds.close()

    def test_save_idea_and_link(self):
        with tempfile.TemporaryDirectory() as td:
            db = os.path.join(td, "scout.db")
            ds = DataStore(db)
            try:
                rid, _ = ds.upsert_repository(
                    url="https://github.com/a/b",
                    owner="a",
                    name="b",
                    description=None,
                    readme_text=None,
                    readme_html=None,
                    agent_notes=None,
                    tags=None,
                    embedding=None,
                    embedding_dim=None,
                )
                iid = ds.save_idea(
                    title="An Idea",
                    description="desc",
                    score=9.0,
                    attrs="{}",
                    repo_urls=["https://github.com/a/b"],
                )
                self.assertGreater(iid, 0)
                # Verify link exists
                cur = ds.conn.cursor()
                cur.execute("SELECT repo_id FROM idea_links WHERE idea_id=?", (iid,))
                row = cur.fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], rid)
            finally:
                ds.close()

