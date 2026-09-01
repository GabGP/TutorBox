"""Tests for GET /api/v1/quiz/generation-logs and /api/v1/quiz/generation-metrics endpoints."""

from fastapi.testclient import TestClient

from db.quiz_telemetry import record_generation_log
from tests.conftest import auth_headers


def test_generation_logs_rbac_unauthenticated(client: TestClient):
    """GET /api/v1/quiz/generation-logs returns 401 Unauthorized for unauthenticated callers."""
    response = client.get("/api/v1/quiz/generation-logs")
    assert response.status_code == 401


def test_generation_logs_rbac_student_forbidden(staff_db, client: TestClient):
    """GET /api/v1/quiz/generation-logs returns 403 Forbidden for students."""
    headers = auth_headers(client, "student1", "1234")
    response = client.get("/api/v1/quiz/generation-logs", headers=headers)
    assert response.status_code == 403


def test_generation_logs_teacher_success_with_filters(staff_db, client: TestClient):
    """Teacher lists generation logs filtered by topic, success, and pagination."""
    _, conn = staff_db
    user_id_cursor = conn.execute("SELECT id FROM users WHERE username = 'teacher1'")
    teacher_id = user_id_cursor.fetchone()["id"]

    record_generation_log(
        conn,
        user_id=teacher_id,
        topic="fractions",
        subconcept="addition",
        model_name="qwen2.5-coder-1.5b",
        attempts=1,
        duration_ms=320.0,
        success=True,
    )
    record_generation_log(
        conn,
        user_id=teacher_id,
        topic="fractions",
        subconcept="subtraction",
        model_name="qwen2.5-coder-1.5b",
        attempts=3,
        duration_ms=1200.0,
        success=False,
        rejection_history=["Math mismatch"],
    )
    record_generation_log(
        conn,
        user_id=teacher_id,
        topic="pre_algebra",
        subconcept="linear_equations",
        model_name="qwen2.5-coder-1.5b",
        attempts=1,
        duration_ms=400.0,
        success=True,
    )
    conn.commit()

    headers = auth_headers(client, "teacher1", "1234")

    # Fetch all logs
    all_res = client.get("/api/v1/quiz/generation-logs", headers=headers)
    assert all_res.status_code == 200
    all_data = all_res.json()
    assert all_data["total"] == 3
    assert len(all_data["logs"]) == 3

    # Filter by topic
    topic_res = client.get(
        "/api/v1/quiz/generation-logs?topic=fractions", headers=headers
    )
    assert topic_res.status_code == 200
    topic_data = topic_res.json()
    assert topic_data["total"] == 2
    assert all(log["topic"] == "fractions" for log in topic_data["logs"])

    # Filter by success
    success_res = client.get(
        "/api/v1/quiz/generation-logs?success=true", headers=headers
    )
    assert success_res.status_code == 200
    success_data = success_res.json()
    assert success_data["total"] == 2
    assert all(log["success"] is True for log in success_data["logs"])

    # Filter by failure
    fail_res = client.get("/api/v1/quiz/generation-logs?success=false", headers=headers)
    assert fail_res.status_code == 200
    fail_data = fail_res.json()
    assert fail_data["total"] == 1
    assert fail_data["logs"][0]["rejection_history"] == ["Math mismatch"]


def test_generation_metrics_rbac_unauthenticated(client: TestClient):
    """GET /api/v1/quiz/generation-metrics returns 401 Unauthorized for unauthenticated callers."""
    response = client.get("/api/v1/quiz/generation-metrics")
    assert response.status_code == 401


def test_generation_metrics_rbac_student_forbidden(staff_db, client: TestClient):
    """GET /api/v1/quiz/generation-metrics returns 403 Forbidden for students."""
    headers = auth_headers(client, "student1", "1234")
    response = client.get("/api/v1/quiz/generation-metrics", headers=headers)
    assert response.status_code == 403


def test_generation_metrics_teacher_success(staff_db, client: TestClient):
    """Teacher computes summary generation metrics with optional filters."""
    _, conn = staff_db
    user_id_cursor = conn.execute("SELECT id FROM users WHERE username = 'admin1'")
    admin_id = user_id_cursor.fetchone()["id"]

    record_generation_log(
        conn,
        user_id=admin_id,
        topic="arithmetic",
        model_name="model_x",
        attempts=1,
        duration_ms=100.0,
        success=True,
    )
    record_generation_log(
        conn,
        user_id=admin_id,
        topic="arithmetic",
        model_name="model_x",
        attempts=2,
        duration_ms=200.0,
        success=False,
    )
    conn.commit()

    headers = auth_headers(client, "teacher1", "1234")

    res = client.get("/api/v1/quiz/generation-metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_generations"] == 2
    assert data["successful_generations"] == 1
    assert data["failed_generations"] == 1
    assert data["success_rate"] == 0.5
    assert data["avg_attempts"] == 1.5
    assert data["avg_duration_ms"] == 150.0

    # Filtered by topic
    filt_res = client.get(
        "/api/v1/quiz/generation-metrics?topic=arithmetic&model_name=model_x",
        headers=headers,
    )
    assert filt_res.status_code == 200
    assert filt_res.json()["total_generations"] == 2
