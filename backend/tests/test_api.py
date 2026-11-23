"""
Pehchan Unisex Salon & Beauty Parlour - Comprehensive API & Automation Test Suite
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.connection import get_db_connection

client = TestClient(app)


def test_health_check():
    """Verify health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_seo_endpoints():
    """Verify robots.txt and sitemap.xml."""
    rob = client.get("/robots.txt")
    assert rob.status_code == 200
    assert "User-agent" in rob.text

    site = client.get("/sitemap.xml")
    assert site.status_code == 200
    assert "urlset" in site.text


def test_get_categories():
    """Verify fetching service categories."""
    response = client.get("/api/v1/services/categories")
    assert response.status_code == 200
    cats = response.json()
    assert len(cats) >= 5
    assert any(c["slug"] == "hair-styling" for c in cats)


def test_get_services_and_filter():
    """Verify fetching services and category filtering."""
    response = client.get("/api/v1/services")
    assert response.status_code == 200
    servs = response.json()
    assert len(servs) >= 8

    # Test filtering by category
    filter_resp = client.get("/api/v1/services?category_slug=hair-styling")
    assert filter_resp.status_code == 200
    filtered = filter_resp.json()
    assert len(filtered) > 0
    assert all("Hair" in s["name"] or s["category_name"] == "Hair Styling & Cuts" for s in filtered)


def test_get_staff():
    """Verify fetching staff members with availability."""
    response = client.get("/api/v1/staff")
    assert response.status_code == 200
    staff = response.json()
    assert len(staff) >= 4
    assert any("Vikram" in s["name"] for s in staff)
    assert len(staff[0]["availability"]) == 7


def test_slot_calculation():
    """Verify slot calculation for a service."""
    # Get a service id
    serv_resp = client.get("/api/v1/services")
    serv_id = serv_resp.json()[0]["id"]

    # Inquire slots for future date
    target_date = "2026-12-15"
    slot_resp = client.get(f"/api/v1/bookings/slots?service_id={serv_id}&date={target_date}")
    assert slot_resp.status_code == 200
    slot_data = slot_resp.json()
    assert slot_data["date"] == target_date
    assert len(slot_data["slots"]) > 0
    assert any(s["available"] for s in slot_data["slots"])


def test_booking_workflow_and_duplicate_prevention():
    """Test full booking lifecycle, slot reservation, and duplicate booking prevention."""
    import uuid
    serv_resp = client.get("/api/v1/services")
    serv_id = serv_resp.json()[0]["id"]

    unique_phone = f"+9198{uuid.uuid4().int % 100000000:08d}"
    booking_payload = {
        "service_id": serv_id,
        "appointment_date": "2026-12-22",
        "start_time": "11:00",
        "customer_name": "Aarav Mehra",
        "customer_email": "aarav.mehra@example.com",
        "customer_phone": unique_phone,
        "customer_notes": "First time visit, prefer gentle wash"
    }

    # 1. First booking should succeed
    book_resp = client.post("/api/v1/bookings", json=booking_payload)
    assert book_resp.status_code == 201
    booking_data = book_resp.json()
    assert booking_data["status"] == "confirmed"
    assert booking_data["booking_reference"].startswith("PH-")
    assert booking_data["customer_name"] == "Aarav Mehra"
    app_id = booking_data["id"]

    # 2. Tracking booking by reference
    track_resp = client.get(f"/api/v1/bookings/track/{booking_data['booking_reference']}")
    assert track_resp.status_code == 200
    assert track_resp.json()["id"] == app_id

    # 3. Duplicate booking attempt by same customer at overlapping time should be rejected (409)
    dup_resp = client.post("/api/v1/bookings", json=booking_payload)
    assert dup_resp.status_code == 409


def test_admin_authentication_and_dashboard():
    """Test admin login, token generation, and protected dashboard stats."""
    # 1. Invalid login attempt
    bad_login = client.post("/api/v1/auth/login", json={"email": "admin@pehchansalon.com", "password": "WrongPassword"})
    assert bad_login.status_code == 401

    # 2. Successful login with default seed credentials
    good_login = client.post("/api/v1/auth/login", json={"email": "admin@pehchansalon.com", "password": "AdminPehchan@2026"})
    assert good_login.status_code == 200
    token_data = good_login.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Access protected summary
    summary_resp = client.get("/api/v1/admin/summary", headers=headers)
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_appointments"] >= 1
    assert summary["total_customers"] >= 1

    # 4. Access without token should be 401
    unauth_resp = client.get("/api/v1/admin/summary")
    assert unauth_resp.status_code == 401


def test_admin_status_update_and_notifications():
    """Test admin updating booking status to completed and notification log generation."""
    # Login to get token
    login_resp = client.post("/api/v1/auth/login", json={"email": "admin@pehchansalon.com", "password": "AdminPehchan@2026"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get recent appointment
    apps_resp = client.get("/api/v1/admin/appointments", headers=headers)
    assert apps_resp.status_code == 200
    apps = apps_resp.json()
    assert len(apps) > 0
    target_app_id = apps[0]["id"]

    # Update status to completed
    patch_resp = client.patch(
        f"/api/v1/admin/appointments/{target_app_id}/status",
        headers=headers,
        json={"status": "completed", "admin_notes": "Service rendered exceptionally well."}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "completed"

    # Check notification logs
    logs_resp = client.get("/api/v1/admin/notification-logs", headers=headers)
    assert logs_resp.status_code == 200
    logs = logs_resp.json()
    assert len(logs) > 0
    assert any(log["appointment_id"] == target_app_id for log in logs)
