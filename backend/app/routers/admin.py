"""
Pehchan Unisex Salon & Beauty Parlour - Secure Admin Dashboard Router
Provides comprehensive administrative controls for the salon owner and managers.
All endpoints require Bearer JWT authentication.
"""

import uuid
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, status
from backend.app.routers.auth import get_current_admin
from backend.app.models.schemas import (
    AdminSummaryResponse,
    AppointmentResponse,
    AppointmentStatusUpdate,
    AppointmentReschedule,
    CustomerResponse,
    ServiceCreateUpdate,
    ServiceResponse,
    StaffCreateUpdate,
    StaffResponse,
    StaffAvailabilityItem,
    OfferCreateUpdate,
    OfferResponse,
    GalleryImageCreate,
    GalleryImageResponse,
    BusinessSettingsResponse,
    BusinessSettingsUpdate,
)
from backend.app.db.connection import get_db_connection
from backend.app.services.calendar import time_to_minutes, minutes_to_time
from backend.app.services.notification import dispatch_status_change

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Dashboard"])


# ==============================================================================
# Overview & Statistics
# ==============================================================================
@router.get("/summary", response_model=AdminSummaryResponse)
def get_dashboard_summary(admin: dict = Depends(get_current_admin)):
    """Fetch high-level KPI metrics, revenue figures, and recent bookings."""
    conn = get_db_connection()
    try:
        today_str = date.today().isoformat()

        total_app = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        today_app = conn.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date = ?", (today_str,)).fetchone()[0]
        pending_app = conn.execute("SELECT COUNT(*) FROM appointments WHERE status = 'pending'").fetchone()[0]
        confirmed_app = conn.execute("SELECT COUNT(*) FROM appointments WHERE status = 'confirmed'").fetchone()[0]
        completed_app = conn.execute("SELECT COUNT(*) FROM appointments WHERE status = 'completed'").fetchone()[0]

        total_cust = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

        # Revenue
        rev_row = conn.execute("SELECT COALESCE(SUM(total_price), 0) FROM appointments WHERE status IN ('confirmed', 'completed')").fetchone()[0]
        today_rev_row = conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) FROM appointments WHERE appointment_date = ? AND status IN ('confirmed', 'completed')",
            (today_str,)
        ).fetchone()[0]

        active_serv = conn.execute("SELECT COUNT(*) FROM services WHERE is_active = 1").fetchone()[0]
        active_stf = conn.execute("SELECT COUNT(*) FROM staff WHERE is_active = 1").fetchone()[0]

        # Recent 10 bookings
        recent_rows = conn.execute(
            """
            SELECT a.id, a.booking_reference, a.service_id, s.name AS service_name,
                   s.duration_minutes, a.total_price, a.staff_id, st.name AS staff_name,
                   a.customer_id, c.full_name AS customer_name, c.phone AS customer_phone,
                   c.email AS customer_email, a.appointment_date, a.start_time, a.end_time,
                   a.status, a.payment_status, a.customer_notes, a.admin_notes, a.created_at
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN customers c ON a.customer_id = c.id
            LEFT JOIN staff st ON a.staff_id = st.id
            ORDER BY a.created_at DESC
            LIMIT 10
            """
        ).fetchall()

        return {
            "total_appointments": total_app,
            "today_appointments": today_app,
            "pending_appointments": pending_app,
            "confirmed_appointments": confirmed_app,
            "completed_appointments": completed_app,
            "total_customers": total_cust,
            "total_revenue": rev_row,
            "today_revenue": today_rev_row,
            "active_services_count": active_serv,
            "active_staff_count": active_stf,
            "recent_bookings": [dict(r) for r in recent_rows]
        }
    finally:
        conn.close()


# ==============================================================================
# Appointments Management
# ==============================================================================
@router.get("/appointments", response_model=List[AppointmentResponse])
def list_appointments(
    status_filter: Optional[str] = Query(None),
    date_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = 100,
    offset: int = 0,
    admin: dict = Depends(get_current_admin)
):
    """List appointments with filtering and search support."""
    conn = get_db_connection()
    try:
        query = """
        SELECT a.id, a.booking_reference, a.service_id, s.name AS service_name,
               s.duration_minutes, a.total_price, a.staff_id, st.name AS staff_name,
               a.customer_id, c.full_name AS customer_name, c.phone AS customer_phone,
               c.email AS customer_email, a.appointment_date, a.start_time, a.end_time,
               a.status, a.payment_status, a.customer_notes, a.admin_notes, a.created_at
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        JOIN customers c ON a.customer_id = c.id
        LEFT JOIN staff st ON a.staff_id = st.id
        WHERE 1=1
        """
        params = []
        if status_filter:
            query += " AND a.status = ?"
            params.append(status_filter.lower())
        if date_filter:
            query += " AND a.appointment_date = ?"
            params.append(date_filter)
        if search:
            query += " AND (a.booking_reference LIKE ? OR c.full_name LIKE ? OR c.phone LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])

        query += " ORDER BY a.appointment_date DESC, a.start_time DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.patch("/appointments/{app_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    app_id: str,
    update: AppointmentStatusUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update appointment status (confirmed, completed, cancelled, etc.) and notify customer."""
    conn = get_db_connection()
    try:
        app = conn.execute(
            """
            SELECT a.*, s.name AS service_name, c.full_name AS customer_name,
                   c.phone AS customer_phone, c.email AS customer_email
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN customers c ON a.customer_id = c.id
            WHERE a.id = ?
            """,
            (app_id,)
        ).fetchone()

        if not app:
            raise HTTPException(status_code=404, detail="Appointment not found")

        old_status = app["status"]
        new_status = update.status

        conn.execute(
            """
            UPDATE appointments
            SET status = ?, admin_notes = COALESCE(?, admin_notes),
                cancelled_reason = COALESCE(?, cancelled_reason),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_status, update.admin_notes, update.cancelled_reason, app_id)
        )
        conn.commit()

        # Re-fetch full updated record
        updated_row = conn.execute(
            """
            SELECT a.id, a.booking_reference, a.service_id, s.name AS service_name,
                   s.duration_minutes, a.total_price, a.staff_id, st.name AS staff_name,
                   a.customer_id, c.full_name AS customer_name, c.phone AS customer_phone,
                   c.email AS customer_email, a.appointment_date, a.start_time, a.end_time,
                   a.status, a.payment_status, a.customer_notes, a.admin_notes, a.created_at
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN customers c ON a.customer_id = c.id
            LEFT JOIN staff st ON a.staff_id = st.id
            WHERE a.id = ?
            """,
            (app_id,)
        ).fetchone()

        # Trigger notification on change
        if old_status != new_status:
            try:
                dispatch_status_change(dict(updated_row), new_status, update.cancelled_reason)
            except Exception as e:
                print(f"[Dispatch Warning] Failed status change notification: {e}")

        return dict(updated_row)
    finally:
        conn.close()


@router.patch("/appointments/{app_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    app_id: str,
    resched: AppointmentReschedule,
    admin: dict = Depends(get_current_admin)
):
    """Reschedule an existing appointment to a new date/time slot."""
    conn = get_db_connection()
    try:
        app = conn.execute(
            "SELECT a.*, s.duration_minutes FROM appointments a JOIN services s ON a.service_id = s.id WHERE a.id = ?",
            (app_id,)
        ).fetchone()

        if not app:
            raise HTTPException(status_code=404, detail="Appointment not found")

        duration = app["duration_minutes"]
        start_min = time_to_minutes(resched.start_time)
        end_time_str = minutes_to_time(start_min + duration)

        staff_to_use = resched.staff_id if resched.staff_id else app["staff_id"]

        conn.execute(
            """
            UPDATE appointments
            SET appointment_date = ?, start_time = ?, end_time = ?,
                staff_id = ?, status = 'rescheduled', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (resched.appointment_date, resched.start_time, end_time_str, staff_to_use, app_id)
        )
        conn.commit()

        updated_row = conn.execute(
            """
            SELECT a.id, a.booking_reference, a.service_id, s.name AS service_name,
                   s.duration_minutes, a.total_price, a.staff_id, st.name AS staff_name,
                   a.customer_id, c.full_name AS customer_name, c.phone AS customer_phone,
                   c.email AS customer_email, a.appointment_date, a.start_time, a.end_time,
                   a.status, a.payment_status, a.customer_notes, a.admin_notes, a.created_at
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            JOIN customers c ON a.customer_id = c.id
            LEFT JOIN staff st ON a.staff_id = st.id
            WHERE a.id = ?
            """,
            (app_id,)
        ).fetchone()

        try:
            dispatch_status_change(dict(updated_row), "rescheduled")
        except Exception as e:
            print(f"[Dispatch Warning] Failed reschedule notification: {e}")

        return dict(updated_row)
    finally:
        conn.close()


@router.delete("/appointments/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(app_id: str, admin: dict = Depends(get_current_admin)):
    """Cancel / remove an appointment."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM appointments WHERE id = ?", (app_id,))
        conn.commit()
    finally:
        conn.close()


# ==============================================================================
# Customer CRM Management
# ==============================================================================
@router.get("/customers", response_model=List[CustomerResponse])
def list_customers(
    search: Optional[str] = Query(None),
    admin: dict = Depends(get_current_admin)
):
    """Fetch customer list with visit counts."""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM customers WHERE 1=1"
        params = []
        if search:
            query += " AND (full_name LIKE ? OR phone LIKE ? OR email LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])
        query += " ORDER BY total_visits DESC, created_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ==============================================================================
# Services CRUD Management
# ==============================================================================
@router.post("/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(serv: ServiceCreateUpdate, admin: dict = Depends(get_current_admin)):
    """Create a new salon service."""
    conn = get_db_connection()
    try:
        serv_id = str(uuid.uuid4())
        slug = serv.slug or serv.name.lower().replace(" ", "-").replace("&", "and")
        # Ensure unique slug
        slug = f"{slug}-{uuid.uuid4().hex[:4]}"

        conn.execute(
            """
            INSERT INTO services (
                id, category_id, name, slug, description, gender_target,
                duration_minutes, price, discount_price, is_featured,
                is_popular, image_url, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                serv_id, serv.category_id, serv.name, slug, serv.description,
                serv.gender_target, serv.duration_minutes, serv.price,
                serv.discount_price, int(serv.is_featured), int(serv.is_popular),
                serv.image_url, int(serv.is_active)
            )
        )
        conn.commit()

        row = conn.execute(
            """
            SELECT s.*, sc.name AS category_name
            FROM services s
            LEFT JOIN service_categories sc ON s.category_id = sc.id
            WHERE s.id = ?
            """,
            (serv_id,)
        ).fetchone()

        return {
            **dict(row),
            "is_featured": bool(row["is_featured"]),
            "is_popular": bool(row["is_popular"]),
            "is_active": bool(row["is_active"])
        }
    finally:
        conn.close()


@router.put("/services/{service_id}", response_model=ServiceResponse)
def update_service(service_id: str, serv: ServiceCreateUpdate, admin: dict = Depends(get_current_admin)):
    """Update existing service pricing, duration, or details."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE services
            SET category_id = ?, name = ?, description = ?, gender_target = ?,
                duration_minutes = ?, price = ?, discount_price = ?,
                is_featured = ?, is_popular = ?, image_url = ?, is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                serv.category_id, serv.name, serv.description, serv.gender_target,
                serv.duration_minutes, serv.price, serv.discount_price,
                int(serv.is_featured), int(serv.is_popular), serv.image_url,
                int(serv.is_active), service_id
            )
        )
        conn.commit()

        row = conn.execute(
            """
            SELECT s.*, sc.name AS category_name
            FROM services s
            LEFT JOIN service_categories sc ON s.category_id = sc.id
            WHERE s.id = ?
            """,
            (service_id,)
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


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete / deactivate a service."""
    conn = get_db_connection()
    try:
        conn.execute("UPDATE services SET is_active = 0 WHERE id = ?", (service_id,))
        conn.commit()
    finally:
        conn.close()


# ==============================================================================
# Staff Management
# ==============================================================================
@router.post("/staff", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def create_staff(s: StaffCreateUpdate, admin: dict = Depends(get_current_admin)):
    """Add a new stylist or specialist."""
    conn = get_db_connection()
    try:
        staff_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO staff (
                id, name, designation, bio, specialization, photo_url,
                email, phone, rating, experience_years, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                staff_id, s.name, s.designation, s.bio, s.specialization,
                s.photo_url, str(s.email) if s.email else None, s.phone,
                s.rating, s.experience_years, int(s.is_active)
            )
        )
        # Create default availability (Mon-Sun, 09:30 - 20:30)
        for w in range(7):
            conn.execute(
                """
                INSERT INTO staff_availability (id, staff_id, weekday, start_time, end_time, is_off_day)
                VALUES (?, ?, ?, '09:30', '20:30', 0)
                """,
                (str(uuid.uuid4()), staff_id, w)
            )
        conn.commit()

        row = conn.execute("SELECT * FROM staff WHERE id = ?", (staff_id,)).fetchone()
        return {**dict(row), "is_active": bool(row["is_active"])}
    finally:
        conn.close()


@router.put("/staff/{staff_id}", response_model=StaffResponse)
def update_staff(staff_id: str, s: StaffCreateUpdate, admin: dict = Depends(get_current_admin)):
    """Update staff details."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE staff
            SET name = ?, designation = ?, bio = ?, specialization = ?,
                photo_url = ?, email = ?, phone = ?, rating = ?,
                experience_years = ?, is_active = ?
            WHERE id = ?
            """,
            (
                s.name, s.designation, s.bio, s.specialization, s.photo_url,
                str(s.email) if s.email else None, s.phone, s.rating,
                s.experience_years, int(s.is_active), staff_id
            )
        )
        conn.commit()
        row = conn.execute("SELECT * FROM staff WHERE id = ?", (staff_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Staff not found")
        return {**dict(row), "is_active": bool(row["is_active"])}
    finally:
        conn.close()


@router.put("/staff/{staff_id}/availability")
def update_staff_availability(
    staff_id: str,
    avail_list: List[StaffAvailabilityItem],
    admin: dict = Depends(get_current_admin)
):
    """Update weekly working hours for a staff member."""
    conn = get_db_connection()
    try:
        for item in avail_list:
            conn.execute(
                """
                INSERT INTO staff_availability (id, staff_id, weekday, start_time, end_time, is_off_day)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(staff_id, weekday) DO UPDATE SET
                    start_time = excluded.start_time,
                    end_time = excluded.end_time,
                    is_off_day = excluded.is_off_day
                """,
                (str(uuid.uuid4()), staff_id, item.weekday, item.start_time, item.end_time, int(item.is_off_day))
            )
        conn.commit()
        return {"status": "success", "message": "Staff schedule updated"}
    finally:
        conn.close()


# ==============================================================================
# Offers Management
# ==============================================================================
@router.post("/offers", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
def create_offer(o: OfferCreateUpdate, admin: dict = Depends(get_current_admin)):
    """Create a promotional package."""
    conn = get_db_connection()
    try:
        off_id = str(uuid.uuid4())
        slug = o.slug or f"{o.title.lower().replace(' ', '-')}-{uuid.uuid4().hex[:4]}"
        conn.execute(
            """
            INSERT INTO offers (
                id, title, slug, badge_text, description, included_services,
                original_price, discounted_price, discount_percentage, valid_from,
                valid_until, image_url, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                off_id, o.title, slug, o.badge_text, o.description,
                o.included_services, o.original_price, o.discounted_price,
                o.discount_percentage, o.valid_from, o.valid_until,
                o.image_url, int(o.is_active)
            )
        )
        conn.commit()
        row = conn.execute("SELECT * FROM offers WHERE id = ?", (off_id,)).fetchone()
        return {**dict(row), "is_active": bool(row["is_active"])}
    finally:
        conn.close()


@router.delete("/offers/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offer(offer_id: str, admin: dict = Depends(get_current_admin)):
    """Delete an offer."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
        conn.commit()
    finally:
        conn.close()


# ==============================================================================
# Gallery Management
# ==============================================================================
@router.post("/gallery", response_model=GalleryImageResponse, status_code=status.HTTP_201_CREATED)
def add_gallery_image(img: GalleryImageCreate, admin: dict = Depends(get_current_admin)):
    """Add a photograph to the gallery/portfolio."""
    conn = get_db_connection()
    try:
        img_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO gallery_images (
                id, title, category, image_url, thumbnail_url, caption,
                is_bridal_special, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                img_id, img.title, img.category, img.image_url,
                img.image_url, img.caption, int(img.is_bridal_special), img.sort_order
            )
        )
        conn.commit()
        row = conn.execute("SELECT * FROM gallery_images WHERE id = ?", (img_id,)).fetchone()
        return {**dict(row), "is_bridal_special": bool(row["is_bridal_special"])}
    finally:
        conn.close()


@router.delete("/gallery/{img_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gallery_image(img_id: str, admin: dict = Depends(get_current_admin)):
    """Remove photograph from gallery."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM gallery_images WHERE id = ?", (img_id,))
        conn.commit()
    finally:
        conn.close()


# ==============================================================================
# Reviews Moderation
# ==============================================================================
@router.get("/reviews")
def list_admin_reviews(admin: dict = Depends(get_current_admin)):
    """List all customer reviews with moderation controls."""
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM reviews ORDER BY created_at DESC").fetchall()
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


@router.patch("/reviews/{review_id}/toggle-approve")
def toggle_review_approval(review_id: str, admin: dict = Depends(get_current_admin)):
    """Toggle review public visibility."""
    conn = get_db_connection()
    try:
        conn.execute("UPDATE reviews SET is_approved = 1 - is_approved WHERE id = ?", (review_id,))
        conn.commit()
        return {"status": "success", "message": "Approval status toggled"}
    finally:
        conn.close()


@router.patch("/reviews/{review_id}/toggle-feature")
def toggle_review_feature(review_id: str, admin: dict = Depends(get_current_admin)):
    """Toggle featuring a review on the homepage."""
    conn = get_db_connection()
    try:
        conn.execute("UPDATE reviews SET is_featured = 1 - is_featured WHERE id = ?", (review_id,))
        conn.commit()
        return {"status": "success", "message": "Feature status toggled"}
    finally:
        conn.close()


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a review."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
    finally:
        conn.close()


# ==============================================================================
# Business Settings & Notification Logs
# ==============================================================================
@router.get("/settings", response_model=BusinessSettingsResponse)
def get_admin_settings(admin: dict = Depends(get_current_admin)):
    """Fetch complete salon configuration."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM business_settings LIMIT 1").fetchone()
        return {
            **dict(row),
            "allow_online_booking": bool(row["allow_online_booking"]),
            "whatsapp_notifications_enabled": bool(row["whatsapp_notifications_enabled"]),
            "email_notifications_enabled": bool(row["email_notifications_enabled"])
        }
    finally:
        conn.close()


@router.put("/settings", response_model=BusinessSettingsResponse)
def update_admin_settings(up: BusinessSettingsUpdate, admin: dict = Depends(get_current_admin)):
    """Update salon contact info, opening rules, and notification switches."""
    conn = get_db_connection()
    try:
        current = conn.execute("SELECT id FROM business_settings LIMIT 1").fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Settings not found")

        conn.execute(
            """
            UPDATE business_settings
            SET salon_name = COALESCE(?, salon_name),
                tagline = COALESCE(?, tagline),
                phone = COALESCE(?, phone),
                whatsapp_number = COALESCE(?, whatsapp_number),
                email = COALESCE(?, email),
                address = COALESCE(?, address),
                google_maps_embed_url = COALESCE(?, google_maps_embed_url),
                slot_interval_minutes = COALESCE(?, slot_interval_minutes),
                allow_online_booking = COALESCE(?, allow_online_booking),
                whatsapp_notifications_enabled = COALESCE(?, whatsapp_notifications_enabled),
                email_notifications_enabled = COALESCE(?, email_notifications_enabled),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                up.salon_name, up.tagline, up.phone, up.whatsapp_number,
                up.email, up.address, up.google_maps_embed_url,
                up.slot_interval_minutes,
                int(up.allow_online_booking) if up.allow_online_booking is not None else None,
                int(up.whatsapp_notifications_enabled) if up.whatsapp_notifications_enabled is not None else None,
                int(up.email_notifications_enabled) if up.email_notifications_enabled is not None else None,
                current["id"]
            )
        )
        conn.commit()

        row = conn.execute("SELECT * FROM business_settings LIMIT 1").fetchone()
        return {
            **dict(row),
            "allow_online_booking": bool(row["allow_online_booking"]),
            "whatsapp_notifications_enabled": bool(row["whatsapp_notifications_enabled"]),
            "email_notifications_enabled": bool(row["email_notifications_enabled"])
        }
    finally:
        conn.close()


@router.get("/notification-logs")
def get_notification_logs(limit: int = 50, admin: dict = Depends(get_current_admin)):
    """View notification logs (WhatsApp & Email delivery history)."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, appointment_id, channel, recipient, subject,
                   message_content, status, provider_response, sent_at
            FROM notification_logs
            ORDER BY sent_at DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
