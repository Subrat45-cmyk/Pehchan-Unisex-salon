"""
Pehchan Unisex Salon & Beauty Parlour - FastAPI Application Entrypoint
Provides RESTful APIs, static file delivery for public site & admin dashboard,
CORS handling, health checks, and SEO sitemap/robots endpoints.
"""

import os
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse

from backend.app.routers.auth import router as auth_router
from backend.app.routers.services import router as services_router
from backend.app.routers.staff import router as staff_router
from backend.app.routers.bookings import router as bookings_router
from backend.app.routers.public_content import router as public_router
from backend.app.routers.admin import router as admin_router
from backend.app.db.connection import init_db, get_db_connection

# Initialize database tables and seeds
init_db()

app = FastAPI(
    title="Pehchan Unisex Salon & Beauty Parlour API",
    description="Complete enterprise REST API for unisex salon, bridal lounge, online booking and management.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend and API consumers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(services_router)
app.include_router(staff_router)
app.include_router(bookings_router)
app.include_router(public_router)
app.include_router(admin_router)

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


# Health Check
@app.get("/health", tags=["System"])
def health_check():
    """System health check endpoint."""
    return {"status": "healthy", "service": "Pehchan Unisex Salon API", "version": "1.0.0"}


# SEO: robots.txt
@app.get("/robots.txt", response_class=PlainTextResponse, tags=["SEO"])
def robots_txt():
    """Robots.txt for web search engines."""
    content = """User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/
Sitemap: /sitemap.xml
"""
    return content


# SEO: sitemap.xml
@app.get("/sitemap.xml", tags=["SEO"])
def sitemap_xml():
    """Dynamic XML sitemap listing all public salon pages."""
    pages = [
        "", "about.html", "services.html", "service-details.html", "pricing.html",
        "gallery.html", "bridal.html", "offers.html", "booking.html",
        "testimonials.html", "contact.html", "faq.html", "privacy-policy.html", "terms.html"
    ]
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for page in pages:
        loc = f"https://pehchansalon.com/{page}"
        xml_lines.append(f"  <url><loc>{loc}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")
    xml_lines.append("</urlset>")
    return Response(content="\n".join(xml_lines), media_type="application/xml")


# Mount static assets if frontend directory exists
if FRONTEND_DIR.exists():
    # Mount assets folder
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Admin Portal Direct Route
    @app.get("/admin", tags=["Admin Frontend"])
    @app.get("/admin/", tags=["Admin Frontend"])
    def admin_dashboard():
        admin_index = FRONTEND_DIR / "admin" / "index.html"
        if admin_index.exists():
            return FileResponse(str(admin_index))
        return {"error": "Admin portal index not found"}

    # Mount admin static assets
    admin_dir = FRONTEND_DIR / "admin"
    if admin_dir.exists():
        app.mount("/admin-static", StaticFiles(directory=str(admin_dir)), name="admin_static")

    # Serve public root
    @app.get("/", tags=["Frontend"])
    def serve_home():
        home_file = FRONTEND_DIR / "index.html"
        if home_file.exists():
            return FileResponse(str(home_file))
        return {"message": "Pehchan Unisex Salon Backend is Running"}

    # Fallback to serve static html pages directly
    @app.get("/{page_name}.html", tags=["Frontend"])
    def serve_page(page_name: str):
        file_path = FRONTEND_DIR / f"{page_name}.html"
        if file_path.exists():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
