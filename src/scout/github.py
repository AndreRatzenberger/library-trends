import base64
import os
from typing import Dict, Optional, Tuple, List

import requests


API = "https://api.github.com"


def parse_repo_url(url: str) -> Tuple[str, str]:
    url = url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    # Accept shortcuts like owner/name
    if not url.startswith("http") and len(url.split("/")) == 2:
        owner, name = url.split("/")
        return owner, name
    for host in ("github.com/", "www.github.com/"):
        if host in url:
            path = url.split(host, 1)[1]
            parts = path.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
    raise ValueError(f"Unrecognized GitHub URL: {url}")


def _headers() -> Dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    tok = os.getenv("GITHUB_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    return headers


def fetch_repo(owner: str, name: str) -> Dict:
    r = requests.get(f"{API}/repos/{owner}/{name}", headers=_headers(), timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_readme(owner: str, name: str) -> Tuple[Optional[str], Optional[str]]:
    # Try to fetch README via API (base64 encoded)
    r = requests.get(f"{API}/repos/{owner}/{name}/readme", headers=_headers(), timeout=20)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    data = r.json()
    content = data.get("content")
    if not content:
        return None, None
    try:
        raw = base64.b64decode(content).decode("utf-8", errors="ignore")
    except Exception:
        raw = None
    # Optionally convert to HTML
    html = None
    if raw:
        try:
            import markdown  # type: ignore

            html = markdown.markdown(raw)
        except Exception:
            html = None
    return raw, html


def search_repositories(query: str, language: Optional[str] = None, per_page: int = 10, sort: str = "stars", order: str = "desc") -> List[Dict]:
    q = query
    if language:
        q += f" language:{language}"
    url = f"{API}/search/repositories"
    params = {
        "q": q,
        "sort": sort,
        "order": order,
        "per_page": per_page,
    }
    r = requests.get(url, headers=_headers(), params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data.get("items", [])
