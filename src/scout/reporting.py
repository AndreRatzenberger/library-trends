import json
import os
from datetime import datetime
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from .datastore import DataStore
from .embeddings import embed_text, to_blob


def _ensure_embeddings(ds: DataStore) -> pd.DataFrame:
    import sqlite3

    con = ds.conn
    df = pd.read_sql_query(
        "SELECT id, owner, name, url, description, readme_text, embedding, embedding_dim FROM repositories",
        con,
    )
    needs = df[df["embedding"].isna() | df["embedding_dim"].isna()]
    for _, row in needs.iterrows():
        text = (row["readme_text"] or "")
        if not text:
            text = (row["description"] or "")
        vec = embed_text(text)
        blob = to_blob(vec)
        cur = con.cursor()
        cur.execute(
            "UPDATE repositories SET embedding=?, embedding_dim=? WHERE id=?",
            (blob, int(vec.shape[0]), int(row["id"])),
        )
    if len(needs) > 0:
        con.commit()
        df = pd.read_sql_query(
            "SELECT id, owner, name, url, description, readme_text, embedding, embedding_dim FROM repositories",
            con,
        )
    return df


def _unpack_embeddings(df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
    embs: List[np.ndarray] = []
    for _, row in df.iterrows():
        blob = row["embedding"]
        dim = row["embedding_dim"] or 0
        if blob is None or dim == 0:
            embs.append(np.zeros((768,), dtype="float32"))
        else:
            embs.append(np.frombuffer(blob, dtype="float32")[: int(dim)])
    X = np.vstack(embs)
    return df, X


def generate_visual_report(db_path: str = None, out_dir: str = None, *, run_id: int | None = None, persist: bool = False) -> str:
    ds = DataStore(db_path)
    try:
        df = _ensure_embeddings(ds)
        df, X = _unpack_embeddings(df)
        # Project
        if X.shape[0] >= 2:
            pca = PCA(n_components=2, random_state=42)
            coords = pca.fit_transform(X)
        else:
            coords = np.zeros((X.shape[0], 2), dtype="float32")
        # Cluster
        k = min(8, max(2, int(np.sqrt(max(2, X.shape[0]) / 2))))
        if X.shape[0] >= k:
            km = KMeans(n_clusters=k, n_init=10, random_state=42)
            labels = km.fit_predict(X)
        else:
            labels = np.zeros((X.shape[0],), dtype=int)

        df_out = df.copy()
        df_out["x"], df_out["y"], df_out["cluster"] = coords[:, 0], coords[:, 1], labels

        out_dir = out_dir or os.path.join("reports")
        os.makedirs(out_dir, exist_ok=True)
        date_str = datetime.utcnow().strftime("%Y%m%d")

        # Save CSV (export for convenience)
        clusters_csv = os.path.join(out_dir, f"clusters_{date_str}.csv")
        df_out.to_csv(clusters_csv, index=False)

        # Simple topic graph from token co-occurrence (naive)
        from sklearn.feature_extraction.text import TfidfVectorizer

        texts = (df["readme_text"].fillna("") + " \n" + df["description"].fillna("")).tolist()
        vec = TfidfVectorizer(stop_words="english", max_features=400)
        M = vec.fit_transform(texts)
        vocab = np.array(vec.get_feature_names_out())
        # term-term co-occurrence via top loadings per cluster (approximate)
        topic_graph = {"nodes": [], "edges": []}
        for idx, term in enumerate(vocab):
            topic_graph["nodes"].append({"id": int(idx), "term": term})
        # Edges by cosine similarity > threshold among terms
        from sklearn.metrics.pairwise import cosine_similarity

        term_sims = cosine_similarity(M.T)
        thresh = 0.25
        n_terms = term_sims.shape[0]
        for i in range(n_terms):
            for j in range(i + 1, n_terms):
                w = float(term_sims[i, j])
                if w >= thresh:
                    topic_graph["edges"].append({"source": int(i), "target": int(j), "weight": w})

        tg_path = os.path.join(out_dir, f"topic_graph_{date_str}.json")
        with open(tg_path, "w") as f:
            json.dump(topic_graph, f)

        if persist and run_id is not None:
            # Persist topic graph and cluster points into DB
            ds.save_topic_graph(run_id, json.dumps(topic_graph))
            points = []
            for _, r in df_out.iterrows():
                points.append((
                    r.get("url"),
                    r.get("owner"),
                    r.get("name"),
                    float(r.get("x", 0.0)),
                    float(r.get("y", 0.0)),
                    int(r.get("cluster", 0)),
                    None,
                ))
            ds.save_cluster_points(run_id, points)

        # HTML scatter via plotly
        import plotly.express as px

        fig = px.scatter(
            df_out,
            x="x",
            y="y",
            color="cluster",
            hover_data={"url": True, "owner": True, "name": True, "description": True},
            title="Repository Embedding Map",
        )
        html_path = os.path.join(out_dir, f"visual_report_{date_str}.html")
        fig.write_html(html_path, include_plotlyjs="cdn")
        return html_path
    finally:
        ds.close()
