import os
import tempfile
from unittest import mock

from scout.datastore import DataStore
from scout.cli import main_run_export


def test_run_export_creates_bundle(tmp_path):
    db = os.path.join(tmp_path, "scout.db")
    ds = DataStore(db)
    try:
        run_id = ds.create_run(mode="CORE", run_date="02022025")
        ds.append_research_log(run_id, "Test entry")
        ds.add_registry_item(run_id, repo_url="https://github.com/a/b", name="a/b", link="https://github.com/a/b", inferred_primitives="decoder", novelty=8.0, maturity=6.0, weirdness=8.0, notes="note", meta=None)
        ds.add_scorecard_item(run_id, idea="Idea", weighted_score=8.9, rubric_json='{"novelty":9.5}', mode="CORE")
        ds.save_report(run_id, title="Report", content_md="# Content", kind="trends_and_potential")
        ds.save_topic_graph(run_id, '{"nodes": [], "edges": []}')
        ds.save_cluster_points(run_id, [("https://github.com/a/b", "a", "b", 0.0, 0.1, 0, None)])
        ds.save_portfolio_update(run_id, "Summary")
    finally:
        ds.close()

    out_dir = os.path.join(tmp_path, "exports")
    with mock.patch("sys.argv", ["run_export", "--run-id", str(run_id), "--db", db, "--out", out_dir]):
        path = None
        # main_run_export prints the folder; call directly and ignore return
        main_run_export()
    # Check contents
    # Find the run folder
    subdirs = [d for d in os.listdir(out_dir) if d.startswith("run_")]
    assert len(subdirs) == 1
    folder = os.path.join(out_dir, subdirs[0])
    assert os.path.exists(os.path.join(folder, "report.md"))
    assert os.path.exists(os.path.join(folder, "registry.csv"))
    assert os.path.exists(os.path.join(folder, "scorecard.csv"))
    assert os.path.exists(os.path.join(folder, "research_log.md"))
    assert os.path.exists(os.path.join(folder, "topic_graph.json"))
    assert os.path.exists(os.path.join(folder, "clusters.csv"))
    assert os.path.exists(os.path.join(folder, "README.md"))

