import argparse
import json
import os
import time
from collections import deque
from dataclasses import dataclass, asdict
from typing import Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class CrawlResult:
    url: str
    title: str
    status_code: int
    links_found: int


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        return f"https://{url}"
    return url


def crawl(start_url: str, max_pages: int, timeout: int = 10) -> list[CrawlResult]:
    if max_pages <= 0:
        raise ValueError("max_pages 必须大于 0")
    base = urlparse(start_url)
    visited: Set[str] = set()
    queue = deque([start_url])
    results: list[CrawlResult] = []

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": os.getenv("CRAWLER_USER_AGENT", "sirius-codex-crawler/1.0 (+https://localhost)"),
            "Accept": "text/html,application/xhtml+xml",
        }
    )

    while queue and len(visited) < max_pages:
        current = queue.popleft()
        if current in visited:
            continue

        visited.add(current)
        try:
            resp = session.get(current, timeout=timeout)
            status_code = resp.status_code
            html = resp.text if resp.ok else ""
        except requests.RequestException:
            results.append(CrawlResult(url=current, title="", status_code=0, links_found=0))
            continue

        soup = BeautifulSoup(html, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else ""

        links = 0
        for a in soup.find_all("a", href=True):
            candidate = urljoin(current, a["href"])
            parsed = urlparse(candidate)
            if parsed.netloc != base.netloc:
                continue
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            if normalized and normalized not in visited:
                queue.append(normalized)
                links += 1

        results.append(
            CrawlResult(
                url=current,
                title=title,
                status_code=status_code,
                links_found=links,
            )
        )

    return results


def run_once(url: str, max_pages: int) -> None:
    items = crawl(url, max_pages=max_pages)
    print(json.dumps([asdict(i) for i in items], ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple domain crawler")
    parser.add_argument("--url", required=True, help="Start URL to crawl")
    parser.add_argument("--max-pages", type=int, default=10, help="Max pages to visit")
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=0,
        help="Run continuously with this interval; 0 means run once",
    )
    args = parser.parse_args()
    if args.max_pages <= 0:
        raise SystemExit("max-pages 必须大于 0")
    if args.interval_seconds < 0:
        raise SystemExit("interval-seconds 不能小于 0")

    start_url = normalize_url(args.url)
    if args.interval_seconds <= 0:
        run_once(start_url, args.max_pages)
        return

    while True:
        run_once(start_url, args.max_pages)
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
