# Library Trends & Potential — Portfolio

This repository tracks an ongoing, historically-aware scouting of novel LLM/Agent/AI libraries, focusing on primitives that reshape how we program or operate models and agents. Each run has a dated folder (DDMMYYYY) with a detailed report, research log, scratch artifacts, and a scorecard of ideas. We iterate until a 10/10 idea survives falsification.

Cadence: ad-hoc, research-driven. Methodology emphasizes primary sources (repos, docs, papers), reproducible evidence, and global sources beyond US/EU. Enterprise/infra topics are de-emphasized; we prioritize weird, experimental, and high-leverage primitives.

---


## 02092025

- Run summary: 39 new libraries cataloged (weird-first). Notable additions: dynamic/grammar-constrained decoders (GAD, Earley prototypes), emergent society simulators, ACI/browser agent ecosystems. Highest novelty delta: structured_decoding, DSL/meta, interfaces_aci.

- Trend tracker:
  - Decoder-as-Compiler: ↑↑
  - JSON-Schema→Decoder toolchains: ↑
  - OS-like agent memory: ↑
  - Agent-Computer Interfaces: ↑
  - Society-scale ABMs: ↑
  - Planner-as-Compiler: ↑
  - Neurosymbolic constraints: ↑
  - Graph-aware retrieval drives decoding: →

- Best ideas so far:
  - Dynamic Grammar Overlays (DGO) — hot-swap constraints mid-decode; 9.1; see 02092025/
  - Lookahead Earley Hybrid (LEH) — speculative+Earley; 8.5; see 02092025/
  - OpenMemory ABI — portable paging/interrupts; 8.0; see 02092025/
  - ACI Synthesizer — DOM→Task IR; 7.9; see 02092025/
  - GraphGuard Decoding — KG-constrained tokens; 7.6; see 02092025/

- Post-mortems: first run — none.

- 10/10 ledger:
  - 02092025 — Dynamic Grammar Overlays (DGO) for In-Flight Decoding — enables mid-turn constraint changes without restart; see 02092025/trends_and_potential.md
