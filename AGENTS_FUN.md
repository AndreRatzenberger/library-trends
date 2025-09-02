# AGENTS_FUN — Novelty/Out‑of‑The‑Box Research Mode

Purpose: a fast, historically‑aware scouting loop that prioritizes weird, creative, paradigm‑shifting LLM/Agent/AI primitives. This mode intentionally ignores enterprise concerns (observability, infra, compliance, SLOs). Use when you want boundary‑pushing ideas over production readiness.

Mode switch: set `RESEARCH_MODE=FUN` (novelty) vs `RESEARCH_MODE=CORE` (serious). FUN uses this playbook; CORE follows AGENTS.md.

---

## What FUN Optimizes For
- Novel primitives and surprising combinations learned from data (no fixed categories): the taxonomy emerges per run from clustering terms mined in results (repos, docs, code).
- “Serious but strange” repos, papers, DSLs, and prototypes with non‑obvious payoffs.
- Early weak signals across global communities (non‑English sources encouraged).

## What FUN Ignores (on purpose)
- Enterprise/infra topics: observability/OTel/K8s/cost KPIs/serving pipelines/SBOM/compliance.
- Production hardening and roadmap polish.
- Benchmarking rigor beyond what’s needed to falsify novelty claims.

---

## Filesystem Contract (same as CORE)
– Replaced by a persistence contract (no per‑run folders by default). Use the CLIs to persist all artifacts into the datastore.
– Start: `uv run start_run --mode FUN` → returns `run_id`.
– Persist:
  - Logs: `uv run save_research_log --run-id <id> --entry "..."`
  - Registry: `uv run save_registry_item --run-id <id> ...`
  - Scorecard: `uv run save_scorecard_item --run-id <id> --idea ... --weighted-score ... --rubric '{...}' --mode FUN`
  - Report: `uv run save_report --run-id <id> --title ... --content "..."`
  - Visuals: `uv run generate_visual_report --run-id <id> --persist` (exports HTML/CSV/JSON for review only)
  - Portfolio: `uv run save_portfolio_update --run-id <id> --summary "..."`

---

## FUN Workflow (Weird‑First, Dynamic)
1) Create `DDMMYYYY/` and `research_results/`.
2) Ingest history: parse prior runs’ `trends_and_potential.md`, `ideas_scorecard.csv`, and `research_log.md`.
   - Build a deduped registry with tags: `category`, `novelty`, `weirdness`, `maturity`, last‑seen date, link to run folder.
   - Note open questions and ideas that failed falsification last time.
3) Plan the delta (append in `save_research_log`):
   - Use history to compute novelty gaps and unexplored adjacencies in `topic_graph.json`.
   - Explicitly write “why now” for each planned dig.
4) Broad sweep (dynamic, no hardcoded queries):
   - If history exists: bootstrap from the top‑K unexplored terms in `topic_graph.json` and high‑novelty repos in `registry.csv` not yet deep‑dived.
   - Else: collect a small, diverse initial sample from trending LLM/agent repos/topics across languages; extract terms from their topics/READMEs and start from those.
   - Persist candidates via `save_registry_item` capturing `name, link, inferred_primitives, novelty, maturity, weirdness, notes`.
5) Triage & cluster (emergent):
   - Drop memes/vapor; keep “strange but serious” (code/docs/paper exist and compile/run or are clearly implementable).
   - Infer primitives by clustering extracted terms; attach each repo to 1–2 strongest primitives with confidence. Persist to `primitives.json`.
6) Deep dives (`research_results/notes.md`):
   - For cluster leaders: strengths, limits, what everyone is missing, and links to issues/PRs/benchmarks.
7) Trend synthesis (10–20 trends):
   - For each trend: signals (repos/commits/issues/users), counter‑signals (perf walls, theory limits), and “why now”.
8) Idea generation + scoring (≥10 ideas):
   - Combine under‑exploited primitives across clusters discovered this run. Prefer odd fusions that appear in `topic_graph.json` as low‑frequency but high‑weight edges.
   - Score using the FUN rubric (below) via `save_scorecard_item` (rubric JSON + weighted score).
9) Falsify the top 3 (two independent attempts each):
   - Check literature/prior art duplication, runtime integration blockers, theory impossibility, or obvious negative results.
10) Stop when ≥1 idea hits the FUN 10/10 bar and survives falsification; mark it by saving a report and a portfolio summary.

---

## FUN Scoring Rubric (and CSV schema)
Columns (`ideas_scorecard.csv`):
`idea, novelty(0-10), weirdness(0-10), zeitgeist(0-10), value_unlock(0-10), demoability(0-10), evidence(0-10), fusion_potential(0-10), weighted_score(0-10), notes`

Weights:
- Novelty: 0.30 — new primitive or surprising combo.
- Weirdness: 0.20 — genuine out‑of‑distribution thinking, not meme.
- Zeitgeist: 0.15 — cultural/tech tailwinds suggest attention/surface area.
- Value Unlock: 0.10 — possible 10× gains (reliability, speed, cost, new UX).
- Demoability: 0.10 — plausible weekend prototype with today’s libs.
- Evidence: 0.10 — code, papers, perf hints, or early users.
- Fusion Potential: 0.05 — composes with other primitives into platforms.

FUN 10/10 bar:
- Weighted score ≥ 9.0, AND Novelty ≥ 9, Weirdness ≥ 8, Zeitgeist ≥ 8.
- Two falsification attempts (integration/theory/duplication) documented; idea still stands.

Note: do not penalize for lack of production readiness. Demoability matters; ops polish does not.

---

## Deliverables (per run)
1) `trends_and_potential.md`
   - Executive summary (key trends; top ideas + provisional scores)
   - Method & scope (sources; inclusion/exclusion; bias checks)
   - Landscape table (~30–60 items) with novelty/maturity/weirdness/inferred primitives/verdict
   - Trends (10–20) with signals and counter‑signals
   - High‑leverage ideas (≥10) using the FUN template
   - The FUN 10/10 idea — full write‑up + two falsification attempts
   - Appendices linking `research_log.md`, `ideas_scorecard.csv`, and `research_results/`
2) `ideas_scorecard.csv` (FUN rubric columns/weights above)
3) `research_log.md`: timestamped queries, leads kept/dropped, reasons, pivots
4) `research_results/`: registries, notes, dumps, snapshots, inventories, plus `primitives.json`, `topic_graph.json`, `frontier.csv`
5) Root `REPORT.MD`: append a new dated section (summary, trend tracker, best ideas, post‑mortems, 10/10 ledger)

---

## Adaptive Primitive Discovery (FUN flavor)
- No predefined category list. The agent derives primitives by clustering extracted terms from current‑run evidence and merges them with history (with decaying weights).
- Keep a compact description per primitive: 1–2 sentence gloss, 3–5 exemplar repos, confidence score, novelty Δ since last run.

Explicitly de‑prioritized in FUN: observability & reliability plumbing, serving infra/throughput, cost ops, SBOM/provenance.

---

## Dynamic Adjacency Search (FUN frontier policy)
Frontier scoring emphasizes: Novelty (0.35), Weirdness (0.25), Zeitgeist (0.20), Uncertainty (0.20). At each expansion step:
- Choose terms that are new (unseen in history), weird (low overlap with mainstream), and timely (recent pushes/commits, paper buzz).
- Log reasoning in `research_log.md` for every pivot:
  - Example: "Based on <repo/issue/doc> showing <signal, e.g., PEG + speculative decoding>, <adjacent_term> looks promising (novelty=0.82, weirdness=0.77). Pivoting to it next."
- Update `frontier.csv` with term, source signals, scores, and decision (explored/parked/dropped) plus rationale.

---

## Bias & Quality Controls
- Prefer primary sources (repos, docs, papers) over aggregators.
- Capture negative findings (why a lead was dropped) in `research_log.md`.
- Include global sources; avoid US/EU monoculture.
- Write for senior engineers: terse, precise, evidence‑backed.
- Keep the tone: fun, weird, and serious about novelty — not about ops.

---

## Operational Tools (Persist + Visualize)

FUN agents MUST persist discoveries and generate visuals using the provided CLIs:

- Persist each discovered repo once per cooldown window (default 30 days):
  - `uv run save_repository --url <owner/name|https://github.com/...> --notes "<agent summary>" --source <frontier|seed|adjacent>`
  - The tool stores URL, owner/name, description, README text/HTML, agent notes, tags (optional), timestamps, and an embedding. Cooldown prevents re-visiting inside the window; `--force` only for explicit reasons (log it).
- Periodically generate a visual map to steer the weirdness frontier:
  - `uv run generate_visual_report --db <optional custom db path> --out <optional out dir>`
  - Use clusters + topic graph to pick next adjacencies and to summarize runs.
- Persist ideas when they crystallize:
  - `uv run save_idea --title "..." --description "..." --score <float> --repo <url> [--repo <url>...]`

Every `save_repository` call must be followed by a reasoning log entry capturing: observation → inference → decision → outcome. Reference the saved repo URL and frontier change.

---

## Reasoned Logging Format
Append to `research_log.md` throughout the run:
- [timestamp] Observation: short quote/snippet + link
- [timestamp] Inference: the inferred primitive/term and why it’s interesting
- [timestamp] Decision: the next search term(s) chosen, with scores and rationale
- [timestamp] Outcome: what was found and how it updates `topic_graph.json`

---

## FUN 10/10 Template (inline in report)
- Title: <idea>
- One‑liner: what primitive it manipulates and why it’s new
- Why now: tailwinds and enabling tech
- Building blocks: existing libs/papers/runtimes it composes
- Technical outline: minimal architecture/API and feasibility path
- Falsification attempts (2x): method, result, conclusion
- Next steps: what to prototype in a week

---

## Mode Notes
- Use FUN mode when you need maximal surface area for invention and taste‑testing.
- When a FUN idea matures and shows traction, upstream into CORE mode for production‑grade evaluation.
- Drive the weirdness frontier:
  - `uv run frontier_step --run-id <id> --max-new 3 --languages "Python,TypeScript,Rust"` — derives dynamic terms from the DB, finds adjacent weird repos, persists them, and logs reasoning.

- Export the run bundle for review (optional):
  - `uv run run_export --run-id <id> --out exports/`
