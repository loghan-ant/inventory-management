"""
Tests for tasks API endpoints (in-memory CRUD).
"""
import pytest


class TestTasksEndpoints:
    """Test suite for /api/tasks endpoints."""

    def _create(self, client, title="Test task", priority="high", due="2026-06-01"):
        """Helper to create a task and return the response."""
        return client.post(
            "/api/tasks",
            json={"title": title, "priority": priority, "dueDate": due},
        )

    def test_get_all_tasks_returns_list(self, client):
        """GET /api/tasks returns a list."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_task_success(self, client):
        """POST /api/tasks creates a task with a generated id and pending status."""
        response = self._create(client, title="Review Q4 levels", priority="high", due="2026-07-01")
        assert response.status_code == 200

        task = response.json()
        assert task.get("id")  # non-empty id generated
        assert task["title"] == "Review Q4 levels"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2026-07-01"
        assert task["status"] == "pending"

    def test_created_task_appears_in_list(self, client):
        """A created task is returned by GET /api/tasks."""
        created = self._create(client, title="Unique task ABC").json()
        ids = [t["id"] for t in client.get("/api/tasks").json()]
        assert created["id"] in ids

    def test_create_task_defaults_priority_medium(self, client):
        """Priority defaults to 'medium' when omitted."""
        response = client.post("/api/tasks", json={"title": "No priority", "dueDate": "2026-06-10"})
        assert response.status_code == 200
        assert response.json()["priority"] == "medium"

    def test_create_task_missing_title_rejected(self, client):
        """Missing required title returns 422."""
        response = client.post("/api/tasks", json={"dueDate": "2026-06-10"})
        assert response.status_code == 422

    def test_create_task_missing_due_date_rejected(self, client):
        """Missing required dueDate returns 422."""
        response = client.post("/api/tasks", json={"title": "No due date"})
        assert response.status_code == 422

    def test_toggle_task_flips_status(self, client):
        """PATCH toggles status between pending and completed."""
        tid = self._create(client).json()["id"]

        r1 = client.patch(f"/api/tasks/{tid}")
        assert r1.status_code == 200
        assert r1.json()["status"] == "completed"

        r2 = client.patch(f"/api/tasks/{tid}")
        assert r2.status_code == 200
        assert r2.json()["status"] == "pending"

    def test_toggle_nonexistent_task_404(self, client):
        """PATCH on an unknown id returns 404."""
        response = client.patch("/api/tasks/nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_task_removes_it(self, client):
        """DELETE removes the task so it no longer appears in the list."""
        tid = self._create(client).json()["id"]

        response = client.delete(f"/api/tasks/{tid}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        ids = [t["id"] for t in client.get("/api/tasks").json()]
        assert tid not in ids

    def test_delete_nonexistent_task_404(self, client):
        """DELETE on an unknown id returns 404."""
        response = client.delete("/api/tasks/nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
