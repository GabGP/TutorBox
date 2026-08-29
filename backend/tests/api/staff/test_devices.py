from tests.conftest import auth_headers, get_user_id


def test_list_devices_empty_and_populated(staff_db, client):
    """Test listing devices when empty and after registering devices."""
    headers = auth_headers(client, "teacher1")

    # Empty fleet
    resp = client.get("/devices", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"devices": []}

    # Register 2 devices
    client.post("/devices", json={"device_id": "1"}, headers=headers)
    client.post("/devices", json={"device_id": "ESP32_02"}, headers=headers)

    resp = client.get("/devices", headers=headers)
    assert resp.status_code == 200
    devices = resp.json()["devices"]
    assert len(devices) == 2
    assert devices[0]["device_id"] == "1"
    assert devices[0]["assigned_user_id"] is None
    assert devices[0]["assigned_username"] is None
    assert devices[1]["device_id"] == "ESP32_02"


def test_register_device_success_and_conflict(staff_db, client):
    """Test registering a new clicker and rejecting duplicate IDs."""
    headers = auth_headers(client, "teacher1")

    # Success
    resp = client.post("/devices", json={"device_id": "CLICKER_01"}, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["device_id"] == "CLICKER_01"
    assert data["assigned_user_id"] is None

    # Conflict on duplicate ID
    resp2 = client.post("/devices", json={"device_id": "CLICKER_01"}, headers=headers)
    assert resp2.status_code == 409
    assert resp2.json()["detail"] == "Device ID already registered."

    # Validation failure on empty or invalid format
    resp3 = client.post("/devices", json={"device_id": ""}, headers=headers)
    assert resp3.status_code == 422


def test_assign_device_success_and_reassignment(staff_db, client):
    """Test assigning a device to a student and handling reassignments."""
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    s1_id = get_user_id(conn, "student1")
    s2_id = get_user_id(conn, "student2")

    client.post("/devices", json={"device_id": "1"}, headers=headers)
    client.post("/devices", json={"device_id": "2"}, headers=headers)

    # Assign clicker 1 to student1
    resp = client.post("/devices/1/assign", json={"user_id": s1_id}, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {
        "device_id": "1",
        "assigned_user_id": s1_id,
        "assigned_username": "student1",
    }

    # Reassign student1 to clicker 2: clicker 1 must automatically become unassigned
    resp2 = client.post("/devices/2/assign", json={"user_id": s1_id}, headers=headers)
    assert resp2.status_code == 200

    list_resp = client.get("/devices", headers=headers)
    devices = {d["device_id"]: d for d in list_resp.json()["devices"]}
    assert devices["1"]["assigned_user_id"] is None
    assert devices["2"]["assigned_user_id"] == s1_id

    # Overwrite clicker 2 with student2
    resp3 = client.post("/devices/2/assign", json={"user_id": s2_id}, headers=headers)
    assert resp3.status_code == 200
    assert resp3.json()["assigned_user_id"] == s2_id


def test_assign_device_error_cases(staff_db, client):
    """Test assign validation: missing device, missing user, non-student user."""
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    s1_id = get_user_id(conn, "student1")
    t1_id = get_user_id(conn, "teacher1")

    # Missing device (404)
    resp = client.post("/devices/999/assign", json={"user_id": s1_id}, headers=headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Device not found."

    client.post("/devices", json={"device_id": "1"}, headers=headers)

    # Non-existent user (404)
    resp2 = client.post("/devices/1/assign", json={"user_id": 9999}, headers=headers)
    assert resp2.status_code == 404
    assert resp2.json()["detail"] == "Student user not found."

    # Non-student role (422)
    resp3 = client.post("/devices/1/assign", json={"user_id": t1_id}, headers=headers)
    assert resp3.status_code == 422
    assert "Only student accounts" in resp3.json()["detail"]


def test_unassign_device(staff_db, client):
    """Test unassigning a device."""
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    s1_id = get_user_id(conn, "student1")

    client.post("/devices", json={"device_id": "1"}, headers=headers)
    client.post("/devices/1/assign", json={"user_id": s1_id}, headers=headers)

    # Unassign assigned device
    resp = client.post("/devices/1/unassign", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Device unassigned successfully."

    # Verify state
    list_resp = client.get("/devices", headers=headers)
    assert list_resp.json()["devices"][0]["assigned_user_id"] is None

    # Idempotent unassign on already unassigned device
    resp2 = client.post("/devices/1/unassign", headers=headers)
    assert resp2.status_code == 200

    # Unassign non-existent device (404)
    resp3 = client.post("/devices/999/unassign", headers=headers)
    assert resp3.status_code == 404


def test_delete_device(staff_db, client):
    """Test deleting a device from the fleet."""
    headers = auth_headers(client, "teacher1")

    client.post("/devices", json={"device_id": "1"}, headers=headers)

    # Delete existing
    resp = client.delete("/devices/1", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Device removed from fleet."

    # Verify empty
    list_resp = client.get("/devices", headers=headers)
    assert list_resp.json()["devices"] == []

    # Delete non-existent device (404)
    resp2 = client.delete("/devices/1", headers=headers)
    assert resp2.status_code == 404


def test_device_cascade_on_user_deletion(staff_db, client):
    """Test that soft-deleting a student unlinks their assigned device."""
    _, conn = staff_db
    headers = auth_headers(client, "teacher1")
    s1_id = get_user_id(conn, "student1")

    client.post("/devices", json={"device_id": "1"}, headers=headers)
    client.post("/devices/1/assign", json={"user_id": s1_id}, headers=headers)

    # Soft delete student1
    del_resp = client.delete(f"/users/{s1_id}", headers=headers)
    assert del_resp.status_code == 200

    # Device 1 must now have assigned_user_id = None
    list_resp = client.get("/devices", headers=headers)
    assert list_resp.json()["devices"][0]["assigned_user_id"] is None
    assert list_resp.json()["devices"][0]["assigned_username"] is None


def test_device_rbac_and_pin_rotation_gating(staff_db, client):
    """Test that students are rejected and pending PIN rotations are blocked."""
    _, conn = staff_db
    student_headers = auth_headers(client, "student1")
    admin_headers = auth_headers(client, "admin1")

    # Students cannot list, register, or modify devices (403)
    assert client.get("/devices", headers=student_headers).status_code == 403
    assert (
        client.post(
            "/devices", json={"device_id": "1"}, headers=student_headers
        ).status_code
        == 403
    )

    # Reset admin1 PIN to force rotation
    admin_id = get_user_id(conn, "admin1")
    reset_resp = client.post(f"/users/{admin_id}/reset-pin", headers=admin_headers)
    assert reset_resp.status_code == 200
    temp_pin = reset_resp.json()["temporary_pin"]

    # Login as admin1 with forced rotation
    login_resp = client.post("/login", json={"username": "admin1", "pin": temp_pin})
    assert login_resp.status_code == 200
    assert login_resp.json()["must_change_pin"] is True
    gated_headers = {"Authorization": f"Bearer {login_resp.json()['session_id']}"}

    # Gated by pending PIN rotation (403)
    assert client.get("/devices", headers=gated_headers).status_code == 403


def test_device_audit_trail_recorded(staff_db, client):
    """Test that device actions are logged in the audit trail."""
    _, conn = staff_db
    headers = auth_headers(client, "admin1")
    s1_id = get_user_id(conn, "student1")

    client.post("/devices", json={"device_id": "1"}, headers=headers)
    client.post("/devices/1/assign", json={"user_id": s1_id}, headers=headers)
    client.post("/devices/1/unassign", headers=headers)
    client.delete("/devices/1", headers=headers)

    audit_resp = client.get("/audit-logs", headers=headers)
    assert audit_resp.status_code == 200
    actions = [log["action"] for log in audit_resp.json()["logs"]]

    assert "device_registered" in actions
    assert "device_assigned" in actions
    assert "device_unassigned" in actions
    assert "device_deleted" in actions
