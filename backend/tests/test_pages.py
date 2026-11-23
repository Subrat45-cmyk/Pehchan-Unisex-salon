"""
Pehchan Unisex Salon - Static Pages & Admin Portal Verification Tests
Verifies that all 14 public HTML pages and the Admin Dashboard exist and return 200 OK.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

PUBLIC_PAGES = [
    "/",
    "/about.html",
    "/services.html",
    "/service-details.html",
    "/pricing.html",
    "/gallery.html",
    "/bridal.html",
    "/offers.html",
    "/booking.html",
    "/testimonials.html",
    "/contact.html",
    "/faq.html",
    "/privacy-policy.html",
    "/terms.html"
]


def test_all_public_pages_load():
    """Verify all 14 required public pages return HTTP 200 and contain branding."""
    for page in PUBLIC_PAGES:
        resp = client.get(page)
        assert resp.status_code == 200, f"Page {page} failed to load (HTTP {resp.status_code})"
        assert "PEHCHAN" in resp.text, f"Page {page} does not contain brand name PEHCHAN"


def test_admin_portal_loads():
    """Verify admin portal index loads."""
    resp = client.get("/admin/")
    assert resp.status_code == 200
    assert "PEHCHAN SALON" in resp.text or "Executive Control Panel" in resp.text
