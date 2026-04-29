from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

tempdir = tempfile.TemporaryDirectory()
os.environ.setdefault("ENV", "test")
os.environ["API_TOKEN"] = "test-token"
os.environ["DATABASE_URL"] = f"sqlite:///{Path(tempdir.name) / 'freelance.db'}"

from fastapi.testclient import TestClient
from app.main import app


class FreelanceApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()
        cls.headers = {"Authorization": "Bearer test-token"}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)
        tempdir.cleanup()
        os.environ.pop("API_TOKEN", None)
        os.environ.pop("DATABASE_URL", None)

    def test_health_endpoints(self) -> None:
        self.assertEqual(self.client.get("/health/live").status_code, 200)
        self.assertEqual(self.client.get("/health/ready").status_code, 200)

    def test_requires_authorization(self) -> None:
        self.assertEqual(self.client.get("/api/v1/clients").status_code, 401)

    def test_client_and_project_flow(self) -> None:
        client_response = self.client.post(
            "/api/v1/clients",
            headers=self.headers,
            json={"name": "某某科技", "contact": "王总", "notes": "老客户"},
        )
        self.assertEqual(client_response.status_code, 200)
        client_id = client_response.json()["id"]

        project_response = self.client.post(
            "/api/v1/projects",
            headers=self.headers,
            json={
                "client_id": client_id,
                "title": "官网改版",
                "status": "doing",
                "budget": 20000,
                "deadline": "2026-12-31",
            },
        )
        self.assertEqual(project_response.status_code, 200)

        list_clients = self.client.get("/api/v1/clients", headers=self.headers)
        self.assertEqual(list_clients.status_code, 200)
        self.assertEqual(len(list_clients.json()), 1)

        list_projects = self.client.get("/api/v1/projects", headers=self.headers)
        self.assertEqual(list_projects.status_code, 200)
        self.assertEqual(len(list_projects.json()), 1)


if __name__ == "__main__":
    unittest.main()
