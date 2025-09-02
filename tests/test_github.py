import base64
import unittest
from unittest import mock

from scout.github import parse_repo_url, fetch_repo, fetch_readme


class TestGithubModule(unittest.TestCase):
    def test_parse_repo_url_variants(self):
        self.assertEqual(parse_repo_url("owner/name"), ("owner", "name"))
        self.assertEqual(parse_repo_url("https://github.com/owner/name"), ("owner", "name"))
        self.assertEqual(parse_repo_url("https://github.com/owner/name/"), ("owner", "name"))
        self.assertEqual(parse_repo_url("https://github.com/owner/name.git"), ("owner", "name"))

    @mock.patch("requests.get")
    def test_fetch_repo_and_readme(self, mock_get):
        # Repo metadata response
        repo_resp = mock.Mock()
        repo_resp.status_code = 200
        repo_resp.json.return_value = {"full_name": "o/n", "description": "desc", "topics": ["x", "y"]}
        # README response
        md = "# Title\nhello"
        content = base64.b64encode(md.encode()).decode()
        readme_resp = mock.Mock()
        readme_resp.status_code = 200
        readme_resp.json.return_value = {"content": content}

        def side_effect(url, headers=None, timeout=20):
            if url.endswith("/readme"):
                return readme_resp
            return repo_resp

        mock_get.side_effect = side_effect

        repo = fetch_repo("o", "n")
        self.assertEqual(repo["description"], "desc")
        text, html = fetch_readme("o", "n")
        self.assertIn("hello", text)
        self.assertIn("<h1>Title</h1>", html)
