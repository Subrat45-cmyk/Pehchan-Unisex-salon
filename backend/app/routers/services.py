"""
Pehchan Unisex Salon & Beauty Parlour - Services & Categories Router
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.app.models.schemas import ServiceResponse, CategoryResponse
from backend.app.db.connection import get_db_connection

router = APIRouter(prefix="/api/v1/services", tags=["Services"])


@router.get("/categories", response_model=List[CategoryResponse])
def get_categories():
    """Retrieve all active service categories."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, name, slug, description, icon, sort_order, is_active
            FROM service_categories
            WHERE is_active = 1
            ORDER BY sort_order ASC, name ASC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get("", response_model=List[ServiceResponse])
def get_services(
    category_slug: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    featured_only: Optional[bool] = Query(False)
):
    """Retrieve active salon services with optional category/gender filtering."""
    conn = get_db_connection()
    try:
        query = """
        SELECT s.id, s.category_id, sc.name AS category_name, s.name, s.slug,
               s.description, s.gender_target, s.duration_minutes, s.price,
               s.discount_price, s.is_featured, s.is_popular, s.image_url,
               s.is_active, s.sort_order
        FROM services s
        LEFT JOIN service_categories sc ON s.category_id = sc.id
        WHERE s.is_active = 1
        """
        params = []

        if category_slug:
            query += " AND sc.slug = ?"
            params.append(category_slug)

        if gender:
            query += " AND (s.gender_target = ? OR s.gender_target = 'unisex')"
            params.append(gender.lower())

        if featured_only:
            query += " AND s.is_featured = 1"

        query += " ORDER BY s.sort_order ASC, s.name ASC"

        rows = conn.execute(query, params).fetchall()
        return [
            {
                **dict(r),
                "is_featured": bool(r["is_featured"]),
                "is_popular": bool(r["is_popular"]),
                "is_active": bool(r["is_active"])
            }
            for r in rows
        ]
    finally:
        conn.close()


@router.get("/{id_or_slug}", response_model=ServiceResponse)
def get_service_detail(id_or_slug: str):
    """Retrieve detailed service information by ID or slug."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            """
            SELECT s.id, s.category_id, sc.name AS category_name, s.name, s.slug,
                   s.description, s.gender_target, s.duration_minutes, s.price,
                   s.discount_price, s.is_featured, s.is_popular, s.image_url,
                   s.is_active, s.sort_order
            FROM services s
            LEFT JOIN service_categories sc ON s.category_id = sc.id
            WHERE (s.id = ? OR s.slug = ?) AND s.is_active = 1
            """,
            (id_or_slug, id_or_slug)
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Service not found")

        return {
            **dict(row),
            "is_featured": bool(row["is_featured"]),
            "is_popular": bool(row["is_popular"]),
            "is_active": bool(row["is_active"])
        }
    finally:
        conn.close()
