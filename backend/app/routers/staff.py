"""
Pehchan Unisex Salon & Beauty Parlour - Staff Router
"""

from fastapi import APIRouter, HTTPException
from typing import List
from backend.app.models.schemas import StaffResponse
from backend.app.db.connection import get_db_connection

router = APIRouter(prefix="/api/v1/staff", tags=["Staff"])


@router.get("", response_model=List[StaffResponse])
def get_staff_members():
    """Retrieve all active staff members with specialties and ratings."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, name, designation, bio, specialization, photo_url,
                   email, phone, rating, experience_years, is_active
            FROM staff
            WHERE is_active = 1
            ORDER BY experience_years DESC, name ASC
            """
        ).fetchall()

        staff_list = []
        for r in rows:
            s_dict = dict(r)
            s_dict["is_active"] = bool(r["is_active"])
            # Load availability
            avail = conn.execute(
                """
                SELECT weekday, start_time, end_time, is_off_day
                FROM staff_availability
                WHERE staff_id = ?
                ORDER BY weekday ASC
                """,
                (r["id"],)
            ).fetchall()
            s_dict["availability"] = [
                {**dict(a), "is_off_day": bool(a["is_off_day"])}
                for a in avail
            ]
            staff_list.append(s_dict)

        return staff_list
    finally:
        conn.close()


@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff_detail(staff_id: str):
    """Retrieve details for a single staff member."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            """
            SELECT id, name, designation, bio, specialization, photo_url,
                   email, phone, rating, experience_years, is_active
            FROM staff
            WHERE id = ? AND is_active = 1
            """,
            (staff_id,)
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Staff member not found")

        s_dict = dict(row)
        s_dict["is_active"] = bool(row["is_active"])
        avail = conn.execute(
            """
            SELECT weekday, start_time, end_time, is_off_day
            FROM staff_availability
            WHERE staff_id = ?
            ORDER BY weekday ASC
            """,
            (staff_id,)
        ).fetchall()
        s_dict["availability"] = [
            {**dict(a), "is_off_day": bool(a["is_off_day"])}
            for a in avail
        ]
        return s_dict
    finally:
        conn.close()
