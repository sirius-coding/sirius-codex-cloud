from __future__ import annotations

import unittest
from unittest.mock import patch

from douyin_comment_crawler.doctor import DoctorCheck, explain_doctor_checks, format_doctor_checks, run_doctor


class DoctorTests(unittest.TestCase):
    def test_format_doctor_checks_is_table_like(self) -> None:
        output = format_doctor_checks(
            [
                DoctorCheck("config", "ok", "base_url configured"),
                DoctorCheck("openapi", "failed", "timed out"),
            ]
        )

        self.assertIn("config", output)
        self.assertIn("openapi", output)
        self.assertIn("failed", output)

    def test_run_doctor_reports_missing_base_url(self) -> None:
        class Config:
            douyin_api_base_url = None
            douyin_comments_path = ""

        checks = run_doctor(Config(), aweme_id="0")

        self.assertEqual(checks[0].status, "failed")
        self.assertIn("DOUYIN_API_BASE_URL", checks[0].detail)

    def test_run_doctor_reports_openapi_and_comment_probe(self) -> None:
        class Config:
            douyin_api_base_url = "https://api.example.test"
            douyin_comments_path = "/comments?aweme_id={aweme_id}&cursor={cursor}&count={count}"

        with patch("douyin_comment_crawler.doctor.probe_url", side_effect=[("ok", "200 0.010s"), ("failed", "HTTP 400 20.000s")]):
            checks = run_doctor(Config(), aweme_id="0")

        self.assertEqual([check.name for check in checks], ["config", "openapi", "comments"])
        self.assertEqual(checks[1].status, "ok")
        self.assertEqual(checks[2].status, "failed")

    def test_explain_doctor_checks_points_to_download_api_upstream_empty_response(self) -> None:
        checks = [
            DoctorCheck("config", "ok", "base_url configured"),
            DoctorCheck("openapi", "ok", "HTTP 200 0.010s"),
            DoctorCheck("comments", "failed", "HTTP 500 Download API upstream returned empty/invalid response"),
        ]

        explanation = explain_doctor_checks(checks)

        self.assertIn("Download API", explanation)
        self.assertIn("Cookie", explanation)


if __name__ == "__main__":
    unittest.main()
