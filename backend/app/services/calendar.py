"""
Pehchan Unisex Salon & Beauty Parlour - Slot & Calendar Availability Engine
Calculates conflict-free available appointment slots taking into account:
- Salon opening hours & weekend timings
- Official holidays and closures
- Specific staff working hours and scheduled off-days
- Service duration and slot intervals
- Non-overlapping existing bookings
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Dict
from backend.app.db.connection import get_db_connection


def time_to_minutes(t_str: str) -> int:
    """Convert 'HH:MM' string to total minutes from midnight."""
    parts = t_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def minutes_to_time(minutes: int) -> str:
    """Convert minutes from midnight to 'HH:MM' 24-hr string."""
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def format_display_time(time_str: str) -> str:
    """Convert '14:30' to '02:30 PM'."""
    try:
        dt = datetime.strptime(time_str, "%H:%M")
        return dt.strftime("%I:%M %p")
    except Exception:
        return time_str


def calculate_available_slots(
    service_id: str,
    target_date_str: str,
    staff_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main slot calculation engine.
    Returns:
    {
        "date": "2026-11-25",
        "service_id": "...",
        "service_name": "...",
        "duration_minutes": 45,
        "staff_id": "...",
        "slots": [
            {"time": "10:00", "display_time": "10:00 AM", "available": True, "reason": None},
            ...
        ]
    }
    """
    conn = get_db_connection()
    try:
        # 1. Fetch Service Info
        service = conn.execute(
            "SELECT id, name, duration_minutes, is_active FROM services WHERE id = ?",
            (service_id,)
        ).fetchone()

        if not service or not service["is_active"]:
            return {
                "date": target_date_str,
                "service_id": service_id,
                "service_name": "Unknown Service",
                "duration_minutes": 0,
                "staff_id": staff_id,
                "slots": [],
                "error": "Service not found or inactive"
            }

        duration = service["duration_minutes"]
        service_name = service["name"]

        # Parse target date
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        weekday = target_date.weekday()  # 0 = Monday, ..., 6 = Sunday

        # 2. Check Salon Holiday
        holiday = conn.execute(
            "SELECT title, is_full_day_closed FROM holidays WHERE holiday_date = ?",
            (target_date_str,)
        ).fetchone()

        if holiday and holiday["is_full_day_closed"]:
            return {
                "date": target_date_str,
                "service_id": service_id,
                "service_name": service_name,
                "duration_minutes": duration,
                "staff_id": staff_id,
                "slots": [],
                "message": f"Salon is closed on {target_date_str} for: {holiday['title']}"
            }

        # 3. Check Salon Hours for this weekday
        salon_day = conn.execute(
            "SELECT open_time, close_time, is_closed FROM salon_hours WHERE weekday = ?",
            (weekday,)
        ).fetchone()

        if not salon_day or salon_day["is_closed"]:
            return {
                "date": target_date_str,
                "service_id": service_id,
                "service_name": service_name,
                "duration_minutes": duration,
                "staff_id": staff_id,
                "slots": [],
                "message": f"Salon is closed on this day of the week."
            }

        salon_open = time_to_minutes(salon_day["open_time"])
        salon_close = time_to_minutes(salon_day["close_time"])

        # Fetch slot interval from settings
        settings = conn.execute("SELECT slot_interval_minutes FROM business_settings LIMIT 1").fetchone()
        slot_interval = settings["slot_interval_minutes"] if settings else 30

        # 4. Determine Eligible Staff
        if staff_id:
            staff_rows = conn.execute(
                """
                SELECT s.id, s.name, sa.start_time, sa.end_time, sa.is_off_day
                FROM staff s
                JOIN staff_availability sa ON s.id = sa.staff_id
                WHERE s.id = ? AND s.is_active = 1 AND sa.weekday = ?
                """,
                (staff_id, weekday)
            ).fetchall()
        else:
            staff_rows = conn.execute(
                """
                SELECT s.id, s.name, sa.start_time, sa.end_time, sa.is_off_day
                FROM staff s
                JOIN staff_availability sa ON s.id = sa.staff_id
                WHERE s.is_active = 1 AND sa.weekday = ? AND sa.is_off_day = 0
                """,
                (weekday,)
            ).fetchall()

        if not staff_rows:
            return {
                "date": target_date_str,
                "service_id": service_id,
                "service_name": service_name,
                "duration_minutes": duration,
                "staff_id": staff_id,
                "slots": [],
                "message": "Selected staff member is not working on this date."
            }

        # Filter out staff who have an off day
        active_staff = [s for s in staff_rows if not s["is_off_day"]]
        if not active_staff:
            return {
                "date": target_date_str,
                "service_id": service_id,
                "service_name": service_name,
                "duration_minutes": duration,
                "staff_id": staff_id,
                "slots": [],
                "message": "No stylists available on this date."
            }

        # 5. Fetch Existing Appointments for the target date
        existing_apps = conn.execute(
            """
            SELECT id, staff_id, start_time, end_time
            FROM appointments
            WHERE appointment_date = ? AND status != 'cancelled'
            """,
            (target_date_str,)
        ).fetchall()

        # Build list of busy intervals per staff
        staff_busy_map = {}
        for s in active_staff:
            s_id = s["id"]
            s_start = max(salon_open, time_to_minutes(s["start_time"]))
            s_end = min(salon_close, time_to_minutes(s["end_time"]))
            staff_busy_map[s_id] = {
                "shift_start": s_start,
                "shift_end": s_end,
                "booked": []
            }

        for app in existing_apps:
            s_id = app["staff_id"]
            app_start = time_to_minutes(app["start_time"])
            app_end = time_to_minutes(app["end_time"])
            if s_id and s_id in staff_busy_map:
                staff_busy_map[s_id]["booked"].append((app_start, app_end))
            elif not s_id:
                # If an appointment has no designated staff, all staff might share salon capacity
                for sid in staff_busy_map:
                    staff_busy_map[sid]["booked"].append((app_start, app_end))

        # 6. Generate Potential Slots
        slots = []
        now_dt = datetime.now()
        is_today = (target_date == now_dt.date())
        current_minute_today = (now_dt.hour * 60 + now_dt.minute + 30) if is_today else -1

        # We step every `slot_interval` minutes from salon open to (close - duration)
        curr_min = salon_open
        while curr_min + duration <= salon_close:
            slot_start = curr_min
            slot_end = curr_min + duration
            time_str = minutes_to_time(slot_start)
            disp_str = format_display_time(time_str)

            # Check if in past
            if is_today and slot_start < current_minute_today:
                slots.append({
                    "time": time_str,
                    "display_time": disp_str,
                    "available": False,
                    "reason": "Past time"
                })
                curr_min += slot_interval
                continue

            # Check if at least one staff member is free for the entire duration
            available = False
            for sid, sdata in staff_busy_map.items():
                # Check within staff working hours
                if slot_start < sdata["shift_start"] or slot_end > sdata["shift_end"]:
                    continue

                # Check overlaps with existing bookings:
                # Two intervals [A, B] and [C, D] overlap if max(A, C) < min(B, D)
                overlap = False
                for b_start, b_end in sdata["booked"]:
                    if max(slot_start, b_start) < min(slot_end, b_end):
                        overlap = True
                        break

                if not overlap:
                    available = True
                    break

            slots.append({
                "time": time_str,
                "display_time": disp_str,
                "available": available,
                "reason": None if available else "Fully booked"
            })

            curr_min += slot_interval

        return {
            "date": target_date_str,
            "service_id": service_id,
            "service_name": service_name,
            "duration_minutes": duration,
            "staff_id": staff_id,
            "slots": slots
        }

    finally:
        conn.close()


def assign_available_staff(
    service_id: str,
    target_date_str: str,
    start_time_str: str,
    requested_staff_id: Optional[str] = None
) -> Optional[str]:
    """
    Finds and assigns a qualified, available staff member for the requested slot.
    If requested_staff_id is provided, checks if they are free.
    If not provided, finds the first available active staff member.
    """
    conn = get_db_connection()
    try:
        service = conn.execute("SELECT duration_minutes FROM services WHERE id = ?", (service_id,)).fetchone()
        if not service:
            return None
        duration = service["duration_minutes"]

        slot_start = time_to_minutes(start_time_str)
        slot_end = slot_start + duration
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        weekday = target_date.weekday()

        if requested_staff_id:
            # Check requested staff
            avail = conn.execute(
                """
                SELECT sa.start_time, sa.end_time, sa.is_off_day
                FROM staff_availability sa
                JOIN staff s ON s.id = sa.staff_id
                WHERE s.id = ? AND s.is_active = 1 AND sa.weekday = ?
                """,
                (requested_staff_id, weekday)
            ).fetchone()

            if not avail or avail["is_off_day"]:
                return None

            s_start = time_to_minutes(avail["start_time"])
            s_end = time_to_minutes(avail["end_time"])
            if slot_start < s_start or slot_end > s_end:
                return None

            # Check existing conflicts
            conflict = conn.execute(
                """
                SELECT id FROM appointments
                WHERE staff_id = ? AND appointment_date = ? AND status != 'cancelled'
                AND MAX(?, (strftime('%H', start_time)*60 + strftime('%M', start_time))) < 
                    MIN(?, (strftime('%H', end_time)*60 + strftime('%M', end_time)))
                """,
                (requested_staff_id, target_date_str, slot_start, slot_end)
            ).fetchall()

            # For safety, manual interval comparison:
            existing = conn.execute(
                """
                SELECT start_time, end_time FROM appointments
                WHERE staff_id = ? AND appointment_date = ? AND status != 'cancelled'
                """,
                (requested_staff_id, target_date_str)
            ).fetchall()

            for ex in existing:
                b_start = time_to_minutes(ex["start_time"])
                b_end = time_to_minutes(ex["end_time"])
                if max(slot_start, b_start) < min(slot_end, b_end):
                    return None

            return requested_staff_id

        # No specific staff requested, find any free staff
        candidates = conn.execute(
            """
            SELECT s.id, sa.start_time, sa.end_time
            FROM staff s
            JOIN staff_availability sa ON s.id = sa.staff_id
            WHERE s.is_active = 1 AND sa.weekday = ? AND sa.is_off_day = 0
            """,
            (weekday,)
        ).fetchall()

        for cand in candidates:
            s_id = cand["id"]
            s_start = time_to_minutes(cand["start_time"])
            s_end = time_to_minutes(cand["end_time"])
            if slot_start < s_start or slot_end > s_end:
                continue

            existing = conn.execute(
                """
                SELECT start_time, end_time FROM appointments
                WHERE staff_id = ? AND appointment_date = ? AND status != 'cancelled'
                """,
                (s_id, target_date_str)
            ).fetchall()

            has_conflict = False
            for ex in existing:
                b_start = time_to_minutes(ex["start_time"])
                b_end = time_to_minutes(ex["end_time"])
                if max(slot_start, b_start) < min(slot_end, b_end):
                    has_conflict = True
                    break

            if not has_conflict:
                return s_id

        return None
    finally:
        conn.close()
