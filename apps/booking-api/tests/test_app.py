from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


class BookingApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.TemporaryDirectory()
        os.environ["API_TOKEN"] = "test-token"
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(cls.tempdir.name) / 'booking.db'}"
        sys.modules.pop("app.main", None)
        sys.modules.pop("app", None)
        cls.module = importlib.import_module("app.main")
        cls.client_context = TestClient(cls.module.app)
        cls.client = cls.client_context.__enter__()
        cls.headers = {"X-API-Token": "test-token"}
        cls.payload = {
            "client_name": "张三",
            "service_name": "网站维护",
            "start_at": "2026-05-01T10:00:00",
            "end_at": "2026-05-01T11:00:00",
            "notes": "远程会议",
        }

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)
        cls.tempdir.cleanup()
        os.environ.pop("API_TOKEN", None)
        os.environ.pop("DATABASE_URL", None)
        sys.modules.pop("app.main", None)
        sys.modules.pop("app", None)

    def test_health_endpoints(self) -> None:
        self.assertEqual(self.client.get("/health/live").status_code, 200)
        self.assertEqual(self.client.get("/health/ready").status_code, 200)

    def test_requires_api_token(self) -> None:
        self.assertEqual(self.client.get("/api/v1/bookings").status_code, 401)

    def test_booking_flow_and_conflict_detection(self) -> None:
        create_response = self.client.post("/api/v1/bookings", headers=self.headers, json=self.payload)
        self.assertEqual(create_response.status_code, 200)
        booking_id = create_response.json()["id"]

        conflict_response = self.client.post("/api/v1/bookings", headers=self.headers, json=self.payload)
        self.assertEqual(conflict_response.status_code, 409)

        list_response = self.client.get("/api/v1/bookings", headers=self.headers)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        update_response = self.client.patch(
            f"/api/v1/bookings/{booking_id}/status",
            headers=self.headers,
            json={"status": "confirmed"},
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["status"], "confirmed")


if __name__ == "__main__":
    unittest.main()
