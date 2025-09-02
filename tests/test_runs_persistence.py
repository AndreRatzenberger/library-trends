import json
import os
import tempfile
import unittest

from scout.datastore import DataStore


class TestRunsPersistence(unittest.TestCase):
    def test_run_lifecycle_and_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            db = os.path.join(td, "scout.db")
            ds = DataStore(db)
            try:
                run_id = ds.create_run(mode="FUN", run_date="01012025")
                self.assertGreater(run_id, 0)

                # Log
                log_id = ds.append_research_log(run_id, "Hello world")
                self.assertGreater(log_id, 0)

                # Registry item
                reg_id = ds.add_registry_item(run_id, repo_url="https://github.com/x/y", name="x/y", link="https://github.com/x/y", inferred_primitives="decoder", novelty=8.0, maturity=4.0, weirdness=8.5, notes="test", meta=json.dumps({"lang": "Python"}))
                self.assertGreater(reg_id, 0)

                # Scorecard item
                rubric = json.dumps({"novelty": 9.0, "weirdness": 8.0, "zeitgeist": 8.5, "value_unlock": 8.0, "demoability": 7.5, "evidence": 7.0, "fusion_potential": 6.5})
                sid = ds.add_scorecard_item(run_id, idea="Cool Idea", weighted_score=8.8, rubric_json=rubric, mode="FUN")
                self.assertGreater(sid, 0)

                # Report
                rep_id = ds.save_report(run_id, title="Run Report", content_md="# hello", kind="trends_and_potential")
                self.assertGreater(rep_id, 0)

                # Topic graph and clusters
                tg_id = ds.save_topic_graph(run_id, json.dumps({"nodes": [], "edges": []}))
                self.assertGreater(tg_id, 0)
                count = ds.save_cluster_points(run_id, [("https://github.com/a/b", "a", "b", 0.1, 0.2, 1, None)])
                self.assertEqual(count, 1)

                # Portfolio update
                pu_id = ds.save_portfolio_update(run_id, "Summary content")
                self.assertGreater(pu_id, 0)
            finally:
                ds.close()

