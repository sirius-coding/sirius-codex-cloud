from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from main import crawl, normalize_url


class WebCrawlerTest(unittest.TestCase):
    def test_normalize_url(self) -> None:
        self.assertEqual(normalize_url("example.com"), "https://example.com")

    @patch("main.requests.Session")
    def test_crawl_same_domain_only(self, session_cls: MagicMock) -> None:
        session = session_cls.return_value
        response = MagicMock()
        response.status_code = 200
        response.ok = True
        response.text = "<html><title>Home</title><a href='/about'>About</a><a href='https://other.com'>Other</a></html>"
        session.get.return_value = response

        items = crawl("https://example.com", max_pages=1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Home")
        self.assertEqual(items[0].links_found, 1)

    def test_rejects_non_positive_page_limit(self) -> None:
        with self.assertRaises(ValueError):
            crawl("https://example.com", max_pages=0)


if __name__ == "__main__":
    unittest.main()
