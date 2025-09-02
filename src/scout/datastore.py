import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, Iterable


DEFAULT_DB_PATH = os.getenv("SCOUT_DB_PATH", os.path.join("data", "scout.db"))
COOLDOWN_DAYS = int(os.getenv("SCOUT_COOLDOWN_DAYS", "30"))


SCHEMA = r"""
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    owner TEXT,
    name TEXT,
    description TEXT,
    readme_text TEXT,
    readme_html TEXT,
    agent_notes TEXT,
    tags TEXT,
    discovered_at TEXT,
    last_visited TEXT,
    embedding BLOB,
    embedding_dim INTEGER
);

CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    visited_at TEXT NOT NULL,
    source TEXT,
    reason TEXT,
    FOREIGN KEY(repo_id) REFERENCES repositories(id)
);

CREATE TABLE IF NOT EXISTS ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    score REAL,
    attrs TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS idea_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id INTEGER NOT NULL,
    repo_id INTEGER NOT NULL,
    FOREIGN KEY(idea_id) REFERENCES ideas(id),
    FOREIGN KEY(repo_id) REFERENCES repositories(id)
);

-- Runs and run-scoped artifacts
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT,
    mode TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS research_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    entry TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS registry_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    repo_url TEXT,
    name TEXT,
    link TEXT,
    inferred_primitives TEXT,
    novelty REAL,
    maturity REAL,
    weirdness REAL,
    notes TEXT,
    meta JSON,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS scorecard_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    idea TEXT NOT NULL,
    weighted_score REAL,
    rubric JSON,
    mode TEXT,
    created_at TEXT,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    kind TEXT,
    title TEXT,
    content_md TEXT,
    created_at TEXT,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS topic_graphs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    json TEXT,
    created_at TEXT,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS cluster_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    url TEXT,
    owner TEXT,
    name TEXT,
    x REAL,
    y REAL,
    cluster_label INTEGER,
    meta JSON,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS portfolio_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    summary_md TEXT,
    created_at TEXT,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);
"""


class DataStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # --- Repository operations ---
    def get_repo_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM repositories WHERE url=?", (url,))
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))

    def can_visit(self, url: str, cooldown_days: int = COOLDOWN_DAYS) -> bool:
        r = self.get_repo_by_url(url)
        if not r:
            return True
        last = r.get("last_visited")
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
        except Exception:
            return True
        return datetime.utcnow() - last_dt >= timedelta(days=cooldown_days)

    def upsert_repository(
        self,
        url: str,
        owner: str,
        name: str,
        description: Optional[str],
        readme_text: Optional[str],
        readme_html: Optional[str],
        agent_notes: Optional[str],
        tags: Optional[str],
        embedding: Optional[bytes],
        embedding_dim: Optional[int],
        visit_source: Optional[str] = None,
        visit_reason: Optional[str] = None,
    ) -> Tuple[int, bool]:
        """Insert or update repo. Returns (repo_id, created_flag). Always records a visit now.
        """
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM repositories WHERE url=?", (url,))
        row = cur.fetchone()
        if row:
            repo_id = row[0]
            cur.execute(
                """
                UPDATE repositories
                SET owner=?, name=?, description=?, readme_text=?, readme_html=?, agent_notes=?, tags=?, embedding=?, embedding_dim=?, last_visited=?
                WHERE id=?
                """,
                (
                    owner,
                    name,
                    description,
                    readme_text,
                    readme_html,
                    agent_notes,
                    tags,
                    embedding,
                    embedding_dim,
                    now,
                    repo_id,
                ),
            )
            created = False
        else:
            cur.execute(
                """
                INSERT INTO repositories (url, owner, name, description, readme_text, readme_html, agent_notes, tags, discovered_at, last_visited, embedding, embedding_dim)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    url,
                    owner,
                    name,
                    description,
                    readme_text,
                    readme_html,
                    agent_notes,
                    tags,
                    now,
                    now,
                    embedding,
                    embedding_dim,
                ),
            )
            repo_id = cur.lastrowid
            created = True
        # Visit record
        cur.execute(
            "INSERT INTO visits (repo_id, visited_at, source, reason) VALUES (?, ?, ?, ?)",
            (repo_id, now, visit_source, visit_reason),
        )
        self.conn.commit()
        return repo_id, created

    # --- Idea operations ---
    def save_idea(
        self,
        title: str,
        description: Optional[str] = None,
        score: Optional[float] = None,
        attrs: Optional[str] = None,
        repo_urls: Optional[Iterable[str]] = None,
    ) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO ideas (title, description, score, attrs, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (title, description, score, attrs, now, now),
        )
        idea_id = cur.lastrowid
        if repo_urls:
            for url in repo_urls:
                cur.execute("SELECT id FROM repositories WHERE url=?", (url,))
                r = cur.fetchone()
                if r:
                    cur.execute(
                        "INSERT INTO idea_links (idea_id, repo_id) VALUES (?, ?)",
                        (idea_id, r[0]),
                    )
        self.conn.commit()
        return idea_id

    # --- Runs & artifacts ---
    def create_run(self, mode: str, run_date: Optional[str] = None) -> int:
        now = datetime.utcnow().isoformat()
        run_date = run_date or datetime.utcnow().strftime("%d%m%Y")
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO runs (run_date, mode, created_at) VALUES (?, ?, ?)",
            (run_date, mode, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def append_research_log(self, run_id: int, entry: str, timestamp: Optional[str] = None) -> int:
        ts = timestamp or datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO research_logs (run_id, timestamp, entry) VALUES (?, ?, ?)",
            (run_id, ts, entry),
        )
        self.conn.commit()
        return cur.lastrowid

    def add_registry_item(
        self,
        run_id: int,
        *,
        repo_url: Optional[str] = None,
        name: Optional[str] = None,
        link: Optional[str] = None,
        inferred_primitives: Optional[str] = None,
        novelty: Optional[float] = None,
        maturity: Optional[float] = None,
        weirdness: Optional[float] = None,
        notes: Optional[str] = None,
        meta: Optional[str] = None,
    ) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO registry_items (run_id, repo_url, name, link, inferred_primitives, novelty, maturity, weirdness, notes, meta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, repo_url, name, link, inferred_primitives, novelty, maturity, weirdness, notes, meta),
        )
        self.conn.commit()
        return cur.lastrowid

    def add_scorecard_item(
        self,
        run_id: int,
        *,
        idea: str,
        weighted_score: float,
        rubric_json: str,
        mode: Optional[str] = None,
    ) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO scorecard_items (run_id, idea, weighted_score, rubric, mode, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, idea, weighted_score, rubric_json, mode, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def save_report(self, run_id: int, title: str, content_md: str, kind: str = "trends_and_potential") -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO reports (run_id, kind, title, content_md, created_at) VALUES (?, ?, ?, ?, ?)",
            (run_id, kind, title, content_md, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def save_topic_graph(self, run_id: int, json_text: str) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO topic_graphs (run_id, json, created_at) VALUES (?, ?, ?)",
            (run_id, json_text, now),
        )
        self.conn.commit()
        return cur.lastrowid

    def save_cluster_points(self, run_id: int, rows: Iterable[Tuple[str, str, str, float, float, int, Optional[str]]]) -> int:
        cur = self.conn.cursor()
        cur.executemany(
            "INSERT INTO cluster_points (run_id, url, owner, name, x, y, cluster_label, meta) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [(run_id, url, owner, name, x, y, int(label), meta) for (url, owner, name, x, y, label, meta) in rows],
        )
        self.conn.commit()
        return cur.rowcount

    def save_portfolio_update(self, run_id: int, summary_md: str) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO portfolio_updates (run_id, summary_md, created_at) VALUES (?, ?, ?)",
            (run_id, summary_md, now),
        )
        self.conn.commit()
        return cur.lastrowid
