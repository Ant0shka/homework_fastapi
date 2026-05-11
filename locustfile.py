from __future__ import annotations

import random
import string
import uuid

from locust import HttpUser, between, task


def _rand_suffix(n: int = 10) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


class TaskApiUser(HttpUser):
    wait_time = between(0.05, 0.25)

    def on_start(self) -> None:
        username = f"locust_{uuid.uuid4().hex[:8]}_{_rand_suffix(6)}"
        password = "password1"
        self.client.post("/auth/register", json={"username": username, "password": password})
        r = self.client.post(
            "/auth/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        self.token = r.json()["access_token"]

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    @task(6)
    def create_task(self) -> None:
        payload = {
            "title": f"load_{_rand_suffix(12)}",
            "description": "locust",
            "status": "pending",
            "priority": random.randint(0, 50),
        }
        self.client.post("/tasks", json=payload, headers=self._auth_headers(), name="POST /tasks")

    @task(3)
    def list_tasks(self) -> None:
        self.client.get("/tasks", headers=self._auth_headers(), name="GET /tasks")

    @task(2)
    def list_top(self) -> None:
        n = random.choice([5, 10, 20])
        self.client.get(f"/tasks/top?n={n}", headers=self._auth_headers(), name="GET /tasks/top")

    @task(1)
    def health(self) -> None:
        self.client.get("/health", name="GET /health")
