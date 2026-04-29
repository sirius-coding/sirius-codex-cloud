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


class ItemApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.TemporaryDirectory()
        os.environ["API_TOKEN"] = "test-token"
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(cls.tempdir.name) / 'test.db'}"
        sys.modules.pop("app.main", None)
        sys.modules.pop("app", None)
        cls.module = importlib.import_module("app.main")
        cls.client_context = TestClient(cls.module.app)
        cls.client = cls.client_context.__enter__()
        cls.headers = {"X-API-Token": "test-token"}

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
        response = self.client.get("/api/v1/items")
        self.assertEqual(response.status_code, 401)

    def test_crud_flow(self) -> None:
        create_response = self.client.post(
            "/api/v1/items",
            headers=self.headers,
            json={
                "name": "示例记录",
                "description": "用于测试",
                "owner": "ops",
                "status": "active",
            },
        )
        self.assertEqual(create_response.status_code, 200)
        record_id = create_response.json()["id"]

        list_response = self.client.get("/api/v1/items", headers=self.headers)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        detail_response = self.client.get(f"/api/v1/items/{record_id}", headers=self.headers)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["name"], "示例记录")

        update_response = self.client.patch(
            f"/api/v1/items/{record_id}",
            headers=self.headers,
            json={"status": "archived"},
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["status"], "archived")


if __name__ == "__main__":
    unittest.main()
