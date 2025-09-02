# Scout — Persistent Research Datastore + Visual Reports

This package provides two primary CLIs for research agents:

- `save_repository`: Fetch a GitHub repo’s metadata + README, persist it (with optional embedding) into a SQLite datastore, and record a visit. A repo is only revisited if the last visit was > 30 days ago.
- `generate_visual_report`: Load persisted repos, cluster and project embeddings, and emit an HTML visualization plus JSON graphs.

Optional: persist high‑leverage ideas with `save_idea` to enable idea‑centric reporting.

Quick start

- Ensure `uv` is installed, then install deps and create a virtualenv:
  - `uv sync`
- Save a repository (supports `GITHUB_TOKEN` env to avoid rate limits):
  - `uv run save_repository --url https://github.com/eth-sri/lmql --notes "constraint-guided language"`
- Generate a visual report:
  - `uv run generate_visual_report`

Environment

- `SCOUT_DB_PATH` (default: `data/scout.db`)
- `GITHUB_TOKEN` for higher GitHub API rate limits
- `SCOUT_EMBEDDER` = `auto` (default), `hash`, or `hf` (sentence-transformers if installed)
- `SCOUT_COOLDOWN_DAYS` (default: 30)

Outputs

- Database: `data/scout.db` (SQLite)
- Reports: `reports/visual_report_YYYYMMDD.html`, `reports/topic_graph_YYYYMMDD.json`, `reports/clusters_YYYYMMDD.csv`

Agent run flow (step‑by‑step)

1) Start a run and capture the returned `run_id`:
   - `uv run start_run --mode CORE` (or `FUN`)
2) Log planning/decisions as you go:
   - `uv run save_research_log --run-id <ID> --entry "Kickoff: plan..."`
3) Discover dynamically via frontier expansion (derives terms from DB, searches GitHub, persists repos, logs reasoning):
   - `uv run frontier_step --run-id <ID> --max-new 3 --languages "Python,TypeScript,Rust"`
   - Optionally persist a specific repo: `uv run save_repository --url owner/name --notes "..." --source frontier`
4) Persist registry rows for your landscape table (if needed beyond `frontier_step`):
   - `uv run save_registry_item --run-id <ID> --repo-url https://github.com/... --name owner/name --link https://github.com/... --inferred-primitives "decoder" --novelty 8 --maturity 6 --weirdness 8 --notes "..."`
5) Add ideas/scorecard items as they form:
   - `uv run save_scorecard_item --run-id <ID> --idea "..." --weighted-score 8.9 --rubric '{"novelty":9.5,...}' --mode CORE|FUN`
6) Generate visuals and persist them to the run:
   - `uv run generate_visual_report --run-id <ID> --persist`
   - Open `reports/visual_report_YYYYMMDD.html` to view the map
7) Save the markdown report content:
   - `uv run save_report --run-id <ID> --title "Trends & Potential — <mode>" --content "# Executive Summary..."`
8) (Optional) Portfolio summary update:
   - `uv run save_portfolio_update --run-id <ID> --summary "..."`
9) Export a shareable bundle (optional; DB remains source of truth):
   - `uv run run_export --run-id <ID> --out exports/`

Agent requirements

- Execution rights in this workspace to run Python and uv:
  - Python ≥ 3.9 available; `uv sync` to install dependencies
  - Ability to create `.venv/` under the repo and write to `data/`, `reports/`, and `exports/`
- Outbound HTTPS network access to GitHub API (`api.github.com`):
  - Set `GITHUB_TOKEN` for higher rate limits
  - If you prefer/need an MCP integration for discovery, provide the GitHub MCP tool; however, Scout’s CLIs already perform GitHub API calls directly, so MCP is optional
- Optional model downloads (only if `SCOUT_EMBEDDER=hf`):
  - `sentence-transformers` will download a model like `all-MiniLM-L6-v2`; otherwise the default hashing embedder requires no downloads
- Shell access to run the CLIs:
  - `uv run <script>` commands must be allowed by the agent runtime

Nice‑to‑have

- A browser or HTML viewer to open the generated Plotly map under `reports/`
- Sufficient disk space for the SQLite DB (default `data/scout.db`) and any exports
