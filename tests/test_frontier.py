import json
import os
import tempfile
import unittest
from unittest import mock

from scout.cli import main_frontier_step
from scout.datastore import DataStore


class TestFrontierCLI(unittest.TestCase):
    @mock.patch("scout.cli.search_repositories")
    @mock.patch("scout.cli.fetch_readme")
    @mock.patch("scout.cli.fetch_repo")
    def test_frontier_discovers_and_persists(self, mock_fetch_repo, mock_fetch_readme, mock_search):
        with tempfile.TemporaryDirectory() as td:
            db = os.path.join(td, "scout.db")
            ds = DataStore(db)
            try:
                run_id = ds.create_run(mode="FUN", run_date="01012025")
                # Seed DB with one repo that mentions a niche term to produce a TF-IDF term
                ds.upsert_repository(
                    url="https://github.com/seed/repo",
                    owner="seed",
                    name="repo",
                    description="A toolkit for earley parsing agents",
                    readme_text="# Earley Parser for LLM agents",
                    readme_html=None,
                    agent_notes=None,
                    tags=None,
                    embedding=None,
                    embedding_dim=None,
                )
            finally:
                ds.close()

            # Mock search to return one new repo
            mock_search.return_value = [
                {
                    "html_url": "https://github.com/new/interesting",
                    "description": "GLR grammar guided decoding",
                    "topics": ["llm"],
                    "stargazers_count": 42,
                    "pushed_at": "2025-09-01T00:00:00Z",
                    "language": "Python",
                }
            ]
            mock_fetch_repo.return_value = {
                "full_name": "new/interesting",
                "description": "GLR grammar guided decoding",
                "stargazers_count": 42,
                "pushed_at": "2025-09-01T00:00:00Z",
            }
            mock_fetch_readme.return_value = ("# Title\nSome README", "<h1>Title</h1>")

            # Run frontier step with db override
            with mock.patch("sys.argv", ["frontier_step", "--run-id", str(run_id), "--db", db, "--max-new", "1"]):
                main_frontier_step()

            # Validate persistence
            ds2 = DataStore(db)
            try:
                cur = ds2.conn.cursor()
                cur.execute("SELECT count(*) FROM repositories WHERE url=?", ("https://github.com/new/interesting",))
                self.assertEqual(cur.fetchone()[0], 1)

                cur.execute("SELECT count(*) FROM registry_items WHERE run_id=?", (run_id,))
                self.assertGreaterEqual(cur.fetchone()[0], 1)

                cur.execute("SELECT count(*) FROM research_logs WHERE run_id=?", (run_id,))
                self.assertGreaterEqual(cur.fetchone()[0], 1)
            finally:
                ds2.close()

