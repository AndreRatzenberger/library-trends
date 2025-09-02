import os
import tempfile
import unittest

from scout.datastore import DataStore
from scout.reporting import generate_visual_report


class TestReporting(unittest.TestCase):
    def test_generate_visual_report_outputs_files(self):
        with tempfile.TemporaryDirectory() as td:
            db = os.path.join(td, "scout.db")
            out = os.path.join(td, "reports")
            ds = DataStore(db)
            try:
                # Insert two repos sans embeddings; reporting will compute embeddings
                ds.upsert_repository(
                    url="https://github.com/x/y",
                    owner="x",
                    name="y",
                    description="first desc",
                    readme_text="# readme one",
                    readme_html=None,
                    agent_notes=None,
                    tags=None,
                    embedding=None,
                    embedding_dim=None,
                )
                ds.upsert_repository(
                    url="https://github.com/u/v",
                    owner="u",
                    name="v",
                    description="second desc",
                    readme_text="# readme two",
                    readme_html=None,
                    agent_notes=None,
                    tags=None,
                    embedding=None,
                    embedding_dim=None,
                )
            finally:
                ds.close()

            html_path = generate_visual_report(db_path=db, out_dir=out)
            self.assertTrue(os.path.exists(html_path))
            # Topic graph and clusters should exist too
            files = os.listdir(out)
            self.assertTrue(any(f.startswith("clusters_") and f.endswith(".csv") for f in files))
            self.assertTrue(any(f.startswith("topic_graph_") and f.endswith(".json") for f in files))
