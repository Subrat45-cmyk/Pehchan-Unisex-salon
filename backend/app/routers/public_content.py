"""
Pehchan Unisex Salon & Beauty Parlour - Public Content Router
Powers packages, gallery, reviews, and salon information for the public website.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.models.schemas import (
    OfferResponse,
    GalleryImageResponse,
    ReviewResponse,
    ReviewCreate,
    BusinessSettingsResponse,
)
from backend.app.db.connection import get_db_connection

router = APIRouter(prefix="/api/v1/public", tags=["Public Website Content"])


@router.get("/settings", response_model=BusinessSettingsResponse)
def get_public_settings():
    """Retrieve salon contact details, operating hours, and location info."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM business_settings LIMIT 1").fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Settings not configured")
        return {
            **dict(row),
            "allow_online_booking": bool(row["allow_online_booking"]),
            "whatsapp_notifications_enabled": bool(row["whatsapp_notifications_enabled"]),
            "email_notifications_enabled": bool(row["email_notifications_enabled"])
        }
    finally:
        conn.close()


@router.get("/offers", response_model=List[OfferResponse])
def get_active_offers():
    """Retrieve all current promotional packages and festive deals."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, title, slug, badge_text, description, included_services,
                   original_price, discounted_price, discount_percentage, valid_from,
                   valid_until, image_url, is_active
            FROM offers
            WHERE is_active = 1
            ORDER BY discounted_price ASC
            """
        ).fetchall()
        return [{**dict(r), "is_active": bool(r["is_active"])} for r in rows]
    finally:
        conn.close()


@router.get("/gallery", response_model=List[GalleryImageResponse])
def get_gallery_images(
    category: Optional[str] = Query(None),
    bridal_only: Optional[bool] = Query(False)
):
    """Retrieve portfolio showcase images with category or bridal filters."""
    conn = get_db_connection()
    try:
        query = """
        SELECT id, title, category, image_url, thumbnail_url, caption,
               is_bridal_special, sort_order
        FROM gallery_images
        WHERE 1=1
        """
        params = []
        if category:
            query += " AND category = ?"
            params.append(category.lower())
        if bridal_only:
            query += " AND is_bridal_special = 1"

        query += " ORDER BY sort_order ASC, created_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [
            {**dict(r), "is_bridal_special": bool(r["is_bridal_special"])}
            for r in rows
        ]
    finally:
        conn.close()


@router.get("/reviews", response_model=List[ReviewResponse])
def get_customer_reviews(featured_only: Optional[bool] = Query(False)):
    """Retrieve approved customer reviews."""
    conn = get_db_connection()
    try:
        query = """
        SELECT id, reviewer_name, reviewer_location, rating, comment,
               is_featured, is_approved, created_at
        FROM reviews
        WHERE is_approved = 1
        """
        if featured_only:
            query += " AND is_featured = 1"

        query += " ORDER BY rating DESC, created_at DESC"
        rows = conn.execute(query).fetchall()
        return [
            {
                **dict(r),
                "is_featured": bool(r["is_featured"]),
                "is_approved": bool(r["is_approved"])
            }
            for r in rows
        ]
    finally:
        conn.close()


@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def submit_review(review: ReviewCreate):
    """Submit a client feedback review."""
    conn = get_db_connection()
    try:
        review_id = str(uuid.uuid4())
        # Default approved = 1 so real clients can see their review immediately
        conn.execute(
            """
            INSERT INTO reviews (
                id, reviewer_name, reviewer_location, rating, comment,
                is_featured, is_approved
            ) VALUES (?, ?, ?, ?, ?, 0, 1)
            """,
            (
                review_id,
                review.reviewer_name.strip(),
                review.reviewer_location.strip() if review.reviewer_location else None,
                review.rating,
                review.comment.strip()
            )
        )
        conn.commit()

        row = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
        return {
            **dict(row),
            "is_featured": bool(row["is_featured"]),
            "is_approved": bool(row["is_approved"])
        }
    finally:
        conn.close()
