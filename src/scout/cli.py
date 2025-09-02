import argparse
import json
import os
from datetime import datetime

from .datastore import DataStore
from .embeddings import embed_text, to_blob
from .github import parse_repo_url, fetch_repo, fetch_readme, search_repositories


def _desc_from_repo(repo_json: dict) -> str:
    parts = [repo_json.get("description") or ""]
    topics = repo_json.get("topics") or []
    if topics:
        parts.append("topics: " + ", ".join(topics))
    return ("; ".join([p for p in parts if p])).strip()


def main_save_repository():
    p = argparse.ArgumentParser(description="Save a repository and README to the datastore")
    p.add_argument("--url", required=True, help="GitHub repo URL or owner/name")
    p.add_argument("--notes", default=None, help="Short agent notes/description")
    p.add_argument("--source", default="manual", help="Provenance of this discovery")
    p.add_argument("--force", action="store_true", help="Ignore cooldown and force visit")
    p.add_argument("--tags", default=None, help="Comma-separated tags (optional)")
    args = p.parse_args()

    ds = DataStore()
    try:
        owner, name = parse_repo_url(args.url)
        url = f"https://github.com/{owner}/{name}"
        if not args.force and not ds.can_visit(url):
            print(f"Skipping (cooldown): {url}")
            return
        repo = fetch_repo(owner, name)
        readme_text, readme_html = fetch_readme(owner, name)
        short_desc = _desc_from_repo(repo)
        # Choose notes: agent-provided notes override inferred summary
        notes = args.notes or short_desc
        # Embed readme or description
        text_for_embed = (readme_text or short_desc or "").strip()
        emb = embed_text(text_for_embed) if text_for_embed else None
        blob = to_blob(emb) if emb is not None else None
        emb_dim = int(emb.shape[0]) if emb is not None else None
        tags = None
        if args.tags:
            tags = json.dumps([t.strip() for t in args.tags.split(",") if t.strip()])
        repo_id, created = ds.upsert_repository(
            url=url,
            owner=owner,
            name=name,
            description=repo.get("description"),
            readme_text=readme_text,
            readme_html=readme_html,
            agent_notes=notes,
            tags=tags,
            embedding=blob,
            embedding_dim=emb_dim,
            visit_source=args.source,
            visit_reason="save_repository",
        )
        stamp = datetime.utcnow().isoformat()
        status = "CREATED" if created else "UPDATED"
        print(json.dumps({
            "status": status,
            "repo_id": repo_id,
            "url": url,
            "owner": owner,
            "name": name,
            "timestamp": stamp,
        }))
    finally:
        ds.close()


def main_generate_visual_report():
    from .reporting import generate_visual_report

    p = argparse.ArgumentParser(description="Generate visual report from persisted data")
    p.add_argument("--db", default=os.getenv("SCOUT_DB_PATH"), help="Path to SQLite DB (optional)")
    p.add_argument("--out", default=None, help="Output directory (default: reports/")
    p.add_argument("--run-id", type=int, default=None, help="Persist artifacts under run ID (optional)")
    p.add_argument("--persist", action="store_true", help="Persist topic graph + clusters into DB under run ID")
    args = p.parse_args()

    path = generate_visual_report(db_path=args.db, out_dir=args.out, run_id=args.run_id, persist=args.persist)
    print(path)


def main_save_idea():
    p = argparse.ArgumentParser(description="Persist a high-leverage idea")
    p.add_argument("--title", required=True)
    p.add_argument("--description", default=None)
    p.add_argument("--score", type=float, default=None)
    p.add_argument("--attrs", default=None, help="JSON string of extra attributes")
    p.add_argument("--repo", action="append", default=None, help="Associate by repo URL (repeatable)")
    args = p.parse_args()

    attrs = args.attrs
    if attrs:
        try:
            json.loads(attrs)
        except Exception:
            raise SystemExit("--attrs must be valid JSON if provided")

    ds = DataStore()
    try:
        idea_id = ds.save_idea(
            title=args.title,
            description=args.description,
            score=args.score,
            attrs=attrs,
            repo_urls=args.repo,
        )
        print(json.dumps({"status": "CREATED", "idea_id": idea_id, "title": args.title}))
    finally:
        ds.close()


def main_start_run():
    p = argparse.ArgumentParser(description="Create a new run record")
    p.add_argument("--mode", choices=["CORE", "FUN"], required=True)
    p.add_argument("--date", default=None, help="DDMMYYYY (optional, defaults to today)")
    args = p.parse_args()

    ds = DataStore()
    try:
        run_id = ds.create_run(mode=args.mode, run_date=args.date)
        print(json.dumps({"status": "CREATED", "run_id": run_id}))
    finally:
        ds.close()


def main_save_research_log():
    p = argparse.ArgumentParser(description="Append a research log entry to a run")
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--entry", required=True)
    p.add_argument("--timestamp", default=None)
    args = p.parse_args()
    ds = DataStore()
    try:
        log_id = ds.append_research_log(args.run_id, args.entry, args.timestamp)
        print(json.dumps({"status": "APPENDED", "log_id": log_id}))
    finally:
        ds.close()


def main_save_registry_item():
    p = argparse.ArgumentParser(description="Save a registry item for a run")
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--repo-url", default=None)
    p.add_argument("--name", default=None)
    p.add_argument("--link", default=None)
    p.add_argument("--inferred-primitives", default=None)
    p.add_argument("--novelty", type=float, default=None)
    p.add_argument("--maturity", type=float, default=None)
    p.add_argument("--weirdness", type=float, default=None)
    p.add_argument("--notes", default=None)
    p.add_argument("--meta", default=None, help="JSON string of extra attrs")
    args = p.parse_args()

    ds = DataStore()
    try:
        rid = ds.add_registry_item(
            args.run_id,
            repo_url=args.repo_url,
            name=args.name,
            link=args.link,
            inferred_primitives=args.inferred_primitives,
            novelty=args.novelty,
            maturity=args.maturity,
            weirdness=args.weirdness,
            notes=args.notes,
            meta=args.meta,
        )
        print(json.dumps({"status": "CREATED", "registry_item_id": rid}))
    finally:
        ds.close()


def main_save_scorecard_item():
    p = argparse.ArgumentParser(description="Save an idea scorecard item for a run")
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--idea", required=True)
    p.add_argument("--weighted-score", type=float, required=True)
    p.add_argument("--rubric", required=True, help="JSON object of rubric fields and values")
    p.add_argument("--mode", default=None)
    args = p.parse_args()

    # Validate rubric JSON
    try:
        json.loads(args.rubric)
    except Exception:
        raise SystemExit("--rubric must be valid JSON")

    ds = DataStore()
    try:
        sid = ds.add_scorecard_item(
            args.run_id,
            idea=args.idea,
            weighted_score=args.weighted_score,
            rubric_json=args.rubric,
            mode=args.mode,
        )
        print(json.dumps({"status": "CREATED", "scorecard_item_id": sid}))
    finally:
        ds.close()


def main_save_report():
    p = argparse.ArgumentParser(description="Save a markdown report for a run")
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--kind", default="trends_and_potential")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--from-file", dest="from_file", default=None)
    group.add_argument("--content", dest="content", default=None)
    args = p.parse_args()

    content = args.content
    if args.from_file:
        with open(args.from_file, "r") as f:
            content = f.read()
    ds = DataStore()
    try:
        rep_id = ds.save_report(args.run_id, args.title, content or "", kind=args.kind)
        print(json.dumps({"status": "CREATED", "report_id": rep_id}))
    finally:
        ds.close()


def main_save_portfolio_update():
    p = argparse.ArgumentParser(description="Save a portfolio summary update for the run")
    p.add_argument("--run-id", type=int, required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--summary", default=None)
    group.add_argument("--from-file", dest="from_file", default=None)
    args = p.parse_args()
    text = args.summary
    if args.from_file:
        with open(args.from_file, "r") as f:
            text = f.read()
    ds = DataStore()
    try:
        pid = ds.save_portfolio_update(args.run_id, text or "")
        print(json.dumps({"status": "CREATED", "portfolio_update_id": pid}))
    finally:
        ds.close()


def _extract_terms_from_db(ds: DataStore, top_k: int = 20) -> list[str]:
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer

    df = pd.read_sql_query(
        "SELECT description, readme_text FROM repositories",
        ds.conn,
    )
    texts = (df["readme_text"].fillna("") + " \n" + df["description"].fillna("")).tolist()
    vec = TfidfVectorizer(stop_words="english", max_features=800, ngram_range=(1, 2))
    X = vec.fit_transform(texts)
    idf = vec.idf_
    terms = vec.get_feature_names_out()
    # Higher idf → rarer terms; pick top_k
    import numpy as np

    idx = np.argsort(-idf)[:top_k]
    cand = [terms[i] for i in idx if len(terms[i]) >= 4]
    return cand[:top_k]


def main_frontier_step():
    p = argparse.ArgumentParser(description="Frontier step: derive terms, search GitHub, persist discoveries, and log reasoning")
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--db", default=os.getenv("SCOUT_DB_PATH"), help="Path to SQLite DB (optional)")
    p.add_argument("--max-new", type=int, default=3)
    p.add_argument("--languages", default="Python,TypeScript,Rust")
    p.add_argument("--seed-term", action="append", default=None, help="Seed search term (repeatable)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    ds = DataStore(args.db)
    try:
        # Build terms
        terms = args.seed_term or []
        if not terms:
            try:
                terms = _extract_terms_from_db(ds, top_k=20)
            except Exception:
                terms = []
        langs = [s.strip() for s in args.languages.split(",") if s.strip()]

        discoveries = []
        for term in terms:
            if len(discoveries) >= args.max_new:
                break
            for lang in langs:
                items = []
                try:
                    items = search_repositories(term, language=lang, per_page=10)
                except Exception:
                    continue
                for it in items:
                    html_url = it.get("html_url")
                    if not html_url:
                        continue
                    # Simple domain filter: prefer repos mentioning LLM/agent/grammar/etc.
                    desc = (it.get("description") or "").lower()
                    topics = it.get("topics") or []
                    if not any(k in desc for k in ["llm", "agent", "language model", "grammar", "browser", "schema", "peg", "earley", "glr", "society", "simulation", "graph"]):
                        if not any(any(k in t.lower() for k in ["llm", "agent", "grammar", "browser", "schema"]) for t in topics):
                            continue
                    # skip if known and within cooldown
                    if not ds.can_visit(html_url):
                        continue
                    # Save via internal calls (equivalent to save_repository)
                    try:
                        owner, name = parse_repo_url(html_url)
                        repo = fetch_repo(owner, name)
                        readme_text, readme_html = fetch_readme(owner, name)
                    except Exception:
                        continue
                    # Embed and persist
                    text_for_embed = (readme_text or repo.get("description") or "").strip()
                    emb = embed_text(text_for_embed) if text_for_embed else None
                    blob = to_blob(emb) if emb is not None else None
                    emb_dim = int(emb.shape[0]) if emb is not None else None
                    notes = (repo.get("description") or "").strip()
                    rid, created = ds.upsert_repository(
                        url=html_url,
                        owner=owner,
                        name=name,
                        description=repo.get("description"),
                        readme_text=readme_text,
                        readme_html=readme_html,
                        agent_notes=notes,
                        tags=None,
                        embedding=blob,
                        embedding_dim=emb_dim,
                        visit_source="frontier",
                        visit_reason=f"term={term}",
                    )
                    # Registry item heuristic scores
                    stars = int(repo.get("stargazers_count") or 0)
                    if stars > 1000:
                        maturity = 9
                    elif stars > 500:
                        maturity = 8
                    elif stars > 100:
                        maturity = 6
                    elif stars > 20:
                        maturity = 4
                    else:
                        maturity = 2
                    novelty = 8 if str(repo.get("pushed_at", "")).startswith("2025-") else 7
                    weird = 6
                    if any(k in desc for k in ["peg", "earley", "glr", "society", "browser", "grammar", "schema"]):
                        weird = 8
                    ds.add_registry_item(
                        args.run_id,
                        repo_url=html_url,
                        name=repo.get("full_name"),
                        link=html_url,
                        inferred_primitives=None,
                        novelty=novelty,
                        maturity=maturity,
                        weirdness=weird,
                        notes=repo.get("description"),
                        meta=None,
                    )
                    # Reasoning log
                    ds.append_research_log(
                        args.run_id,
                        entry=(
                            f"Because TF-IDF/high-interest term '{term}' yielded {html_url} (lang={lang}, stars={stars}), "
                            f"persisted it and will explore adjacent terms from its README next."
                        ),
                    )
                    discoveries.append({"url": html_url, "term": term, "lang": lang})
                    if len(discoveries) >= args.max_new:
                        break
                if len(discoveries) >= args.max_new:
                    break

        print(json.dumps({"status": "OK", "discoveries": discoveries}))
    finally:
        ds.close()


def main_run_export():
    import csv
    import pandas as pd

    p = argparse.ArgumentParser(description="Export a run's persisted artifacts to a shareable folder")
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--db", default=os.getenv("SCOUT_DB_PATH"))
    p.add_argument("--out", default="exports")
    args = p.parse_args()

    ds = DataStore(args.db)
    try:
        cur = ds.conn.cursor()
        cur.execute("SELECT run_date, mode, created_at FROM runs WHERE id=?", (args.run_id,))
        row = cur.fetchone()
        if not row:
            raise SystemExit(f"No such run: {args.run_id}")
        run_date, mode, created_at = row
        folder = os.path.join(args.out, f"run_{args.run_id}_{run_date or 'unknown'}")
        os.makedirs(folder, exist_ok=True)

        # Export registry_items
        reg_path = os.path.join(folder, "registry.csv")
        df_reg = pd.read_sql_query(
            "SELECT repo_url, name, link, inferred_primitives, novelty, maturity, weirdness, notes, meta FROM registry_items WHERE run_id=?",
            ds.conn,
            params=(args.run_id,),
        )
        df_reg.to_csv(reg_path, index=False)

        # Export scorecard_items with flattened rubric
        sc_path = os.path.join(folder, "scorecard.csv")
        df_sc = pd.read_sql_query(
            "SELECT idea, weighted_score, mode, rubric, created_at FROM scorecard_items WHERE run_id=?",
            ds.conn,
            params=(args.run_id,),
        )
        # flatten rubric JSON
        rows = []
        rubric_keys = set()
        for _, r in df_sc.iterrows():
            try:
                rub = json.loads(r["rubric"]) if r["rubric"] else {}
            except Exception:
                rub = {}
            rubric_keys.update(rub.keys())
            base = {
                "idea": r["idea"],
                "weighted_score": r["weighted_score"],
                "mode": r["mode"],
                "created_at": r["created_at"],
            }
            base.update(rub)
            rows.append(base)
        cols = ["idea", "weighted_score", "mode", "created_at"] + sorted(list(rubric_keys))
        with open(sc_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for row in rows:
                w.writerow({k: row.get(k) for k in cols})

        # Export research_log.md
        log_md = os.path.join(folder, "research_log.md")
        df_log = pd.read_sql_query(
            "SELECT timestamp, entry FROM research_logs WHERE run_id=? ORDER BY id ASC",
            ds.conn,
            params=(args.run_id,),
        )
        with open(log_md, "w") as f:
            for _, r in df_log.iterrows():
                f.write(f"- [{r['timestamp']}] {r['entry']}\n")

        # Export report.md (latest)
        rep_md = os.path.join(folder, "report.md")
        df_rep = pd.read_sql_query(
            "SELECT title, content_md, kind, created_at FROM reports WHERE run_id=? ORDER BY id DESC LIMIT 1",
            ds.conn,
            params=(args.run_id,),
        )
        if len(df_rep) > 0:
            with open(rep_md, "w") as f:
                f.write(f"# {df_rep.iloc[0]['title']}\n\n")
                f.write(df_rep.iloc[0]["content_md"] or "")

        # Export topic_graph.json (latest)
        df_tg = pd.read_sql_query(
            "SELECT json FROM topic_graphs WHERE run_id=? ORDER BY id DESC LIMIT 1",
            ds.conn,
            params=(args.run_id,),
        )
        if len(df_tg) > 0:
            tg_path = os.path.join(folder, "topic_graph.json")
            with open(tg_path, "w") as f:
                f.write(df_tg.iloc[0]["json"])

        # Export clusters.csv
        cl_path = os.path.join(folder, "clusters.csv")
        df_cl = pd.read_sql_query(
            "SELECT url, owner, name, x, y, cluster_label, meta FROM cluster_points WHERE run_id=?",
            ds.conn,
            params=(args.run_id,),
        )
        if len(df_cl) > 0:
            df_cl.to_csv(cl_path, index=False)

        # Export portfolio update
        df_pf = pd.read_sql_query(
            "SELECT summary_md FROM portfolio_updates WHERE run_id=? ORDER BY id DESC LIMIT 1",
            ds.conn,
            params=(args.run_id,),
        )
        if len(df_pf) > 0:
            pf_path = os.path.join(folder, "portfolio.md")
            with open(pf_path, "w") as f:
                f.write(df_pf.iloc[0]["summary_md"] or "")

        # Write a minimal README
        with open(os.path.join(folder, "README.md"), "w") as f:
            f.write(
                f"# Run {args.run_id} Export\n\n- Date: {run_date}\n\n- Mode: {mode}\n\n- Created: {created_at}\n\n- Files: report.md, registry.csv, scorecard.csv, research_log.md, topic_graph.json, clusters.csv, portfolio.md (if present)\n"
            )

        print(folder)
    finally:
        ds.close()
