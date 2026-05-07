from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    detail: str


def run_doctor(config, aweme_id: str = "0", timeout_seconds: float = 5) -> list[DoctorCheck]:
    base_url = (config.douyin_api_base_url or "").rstrip("/")
    if not base_url:
        return [DoctorCheck("config", "failed", "missing DOUYIN_API_BASE_URL")]

    checks = [DoctorCheck("config", "ok", "base_url configured")]
    status, detail = probe_url(f"{base_url}/openapi.json", timeout_seconds)
    checks.append(DoctorCheck("openapi", status, detail))

    comments_path = config.douyin_comments_path.format(aweme_id=aweme_id, cursor="0", count="1")
    status, detail = probe_url(f"{base_url}{comments_path}", timeout_seconds)
    checks.append(DoctorCheck("comments", status, detail))
    return checks


def probe_url(url: str, timeout_seconds: float) -> tuple[str, str]:
    started = monotonic()
    try:
        with urlopen(url, timeout=timeout_seconds) as response:
            response.read(256)
            elapsed = monotonic() - started
            return "ok", f"HTTP {response.status} {elapsed:.3f}s"
    except HTTPError as exc:
        elapsed = monotonic() - started
        return "failed", f"HTTP {exc.code} {elapsed:.3f}s"
    except (TimeoutError, URLError) as exc:
        elapsed = monotonic() - started
        return "failed", f"{type(exc).__name__}: {exc} {elapsed:.3f}s"


def format_doctor_checks(checks: list[DoctorCheck]) -> str:
    lines = [
        "check        status   detail",
        "------------ -------- ----------------------------------------",
    ]
    for check in checks:
        lines.append(f"{check.name:<12} {check.status:<8} {check.detail}")
    explanation = explain_doctor_checks(checks)
    if explanation:
        lines.extend(["", "diagnosis", "---------", explanation])
    return "\n".join(lines)


def explain_doctor_checks(checks: list[DoctorCheck]) -> str:
    by_name = {check.name: check for check in checks}
    openapi = by_name.get("openapi")
    comments = by_name.get("comments")
    if openapi and openapi.status == "ok" and comments and comments.status == "failed":
        detail = comments.detail
        if "empty/invalid response" in detail or "NoneType" in detail or "HTTP 500" in detail:
            return (
                "Download API service is reachable, but its Douyin upstream comment request returned "
                "an empty/invalid response. Check the Download API Cookie/msToken/X-Bogus generation, "
                "upstream Douyin connectivity, and whether the aweme_id is public and has accessible comments."
            )
        if "Timeout" in detail or "timed out" in detail:
            return (
                "Download API service is reachable, but the comment endpoint is slow or blocked while calling "
                "Douyin upstream. Check proxy/network, Cookie validity, and server logs around the comment request."
            )
        return "Download API service is reachable, but the comment endpoint failed. Check Download API logs."
    if openapi and openapi.status == "failed":
        return "Download API is not reachable from this machine. Check host, port, firewall, and service binding."
    return ""
