"""
Pehchan Unisex Salon & Beauty Parlour - Appointment Booking Router
Handles slot inquiries, booking workflow, conflict prevention, and notifications.
"""

import random
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.models.schemas import (
    BookingCreateRequest,
    AvailableSlotsResponse,
    AppointmentResponse,
)
from backend.app.db.connection import get_db_connection
from backend.app.services.calendar import (
    calculate_available_slots,
    assign_available_staff,
    time_to_minutes,
    minutes_to_time,
)
from backend.app.services.notification import dispatch_booking_confirmation

router = APIRouter(prefix="/api/v1/bookings", tags=["Bookings & Appointments"])


def generate_booking_reference(app_date_str: str) -> str:
    """Generate human-readable unique reference: e.g. PH-20261128-4821."""
    clean_date = app_date_str.replace("-", "")
    suffix = random.randint(1000, 9999)
    return f"PH-{clean_date}-{suffix}"


@router.get("/slots", response_model=AvailableSlotsResponse)
def get_available_slots(
    service_id: str = Query(..., description="Service UUID"),
    date: str = Query(..., description="Target date in YYYY-MM-DD"),
    staff_id: Optional[str] = Query(None, description="Optional Staff UUID")
):
    """Retrieve all available appointment time slots for a given service and date."""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD")

    result = calculate_available_slots(service_id=service_id, target_date_str=date, staff_id=staff_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_booking(booking: BookingCreateRequest):
    """
    Submit a new appointment booking.
    Performs real-time slot conflict check, assigns staff, records customer,
    and dispatches confirmation messages.
    """
    # 1. Validate Date Format
    try:
        app_date = datetime.strptime(booking.appointment_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid appointment_date format. Use YYYY-MM-DD.")

    if app_date < datetime.now().date():
        raise HTTPException(status_code=400, detail="Cannot book an appointment for a past date.")

    conn = get_db_connection()
    try:
        # 2. Fetch and Validate Service
        service = conn.execute(
            "SELECT id, name, duration_minutes, price, discount_price, is_active FROM services WHERE id = ?",
            (booking.service_id,)
        ).fetchone()

        if not service or not service["is_active"]:
            raise HTTPException(status_code=404, detail="Selected service is not available.")

        duration = service["duration_minutes"]
        service_price = service["discount_price"] if service["discount_price"] else service["price"]

        # 3. Calculate start and end minutes
        try:
            start_min = time_to_minutes(booking.start_time)
            end_min = start_min + duration
            end_time_str = minutes_to_time(end_min)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid start_time format. Use HH:MM in 24hr.")

        # 4. Conflict Check & Staff Assignment
        assigned_staff_id = assign_available_staff(
            service_id=booking.service_id,
            target_date_str=booking.appointment_date,
            start_time_str=booking.start_time,
            requested_staff_id=booking.staff_id
        )

        if not assigned_staff_id:
            raise HTTPException(
                status_code=409,
                detail="The requested time slot is no longer available. Please select another time slot or stylist."
            )

        # 5. Prevent Duplicate Booking for the same customer (same phone on same date overlapping)
        existing_cust_app = conn.execute(
            """
            SELECT a.id FROM appointments a
            JOIN customers c ON a.customer_id = c.id
            WHERE c.phone = ? AND a.appointment_date = ? AND a.status != 'cancelled'
            AND (
                (strftime('%H', a.start_time)*60 + strftime('%M', a.start_time)) < ? AND
                (strftime('%H', a.end_time)*60 + strftime('%M', a.end_time)) > ?
            )
            """,
            (booking.customer_phone.strip(), booking.appointment_date, end_min, start_min)
        ).fetchone()

        if existing_cust_app:
            raise HTTPException(
                status_code=409,
                detail="You already have an active appointment scheduled during this time window."
            )

        # 6. Customer Upsert / Lookup
        clean_phone = booking.customer_phone.strip()
        customer = conn.execute(
            "SELECT id, total_visits FROM customers WHERE phone = ?",
            (clean_phone,)
        ).fetchone()

        if customer:
            cust_id = customer["id"]
            conn.execute(
                """
                UPDATE customers
                SET full_name = ?, email = COALESCE(?, email), total_visits = total_visits + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (booking.customer_name.strip(), booking.customer_email, cust_id)
            )
        else:
            cust_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO customers (id, full_name, email, phone, total_visits)
                VALUES (?, ?, ?, ?, 1)
                """,
                (cust_id, booking.customer_name.strip(), booking.customer_email, clean_phone)
            )

        # 7. Create Appointment Record
        app_id = str(uuid.uuid4())
        ref_code = generate_booking_reference(booking.appointment_date)

        conn.execute(
            """
            INSERT INTO appointments (
                id, booking_reference, customer_id, service_id, staff_id,
                appointment_date, start_time, end_time, total_price,
                status, payment_status, customer_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'confirmed', 'unpaid', ?)
            """,
            (
                app_id,
                ref_code,
                cust_id,
                booking.service_id,
                assigned_staff_id,
                booking.appointment_date,
                booking.start_time,
                end_time_str,
                service_price,
                booking.customer_notes
            )
        )
        conn.commit()

        # 8. Fetch staff name for response and notification
        staff_row = conn.execute("SELECT name FROM staff WHERE id = ?", (assigned_staff_id,)).fetchone()
        staff_name = staff_row["name"] if staff_row else None

        appointment_data = {
            "id": app_id,
            "booking_reference": ref_code,
            "service_id": booking.service_id,
            "service_name": service["name"],
            "duration_minutes": duration,
            "total_price": service_price,
            "staff_id": assigned_staff_id,
            "staff_name": staff_name,
            "customer_id": cust_id,
            "customer_name": booking.customer_name.strip(),
            "customer_phone": clean_phone,
            "customer_email": str(booking.customer_email) if booking.customer_email else None,
            "appointment_date": booking.appointment_date,
            "start_time": booking.start_time,
            "end_time": end_time_str,
            "status": "confirmed",
            "payment_status": "unpaid",
            "customer_notes": booking.customer_notes,
            "admin_notes": None,
            "created_at": datetime.now().isoformat()
        }

        # 9. Trigger Automated Confirmation Dispatch
        try:
            dispatch_booking_confirmation(appointment_data)
        except Exception as e:
            print(f"[Dispatch Warning] Failed to trigger notification: {e}")

        return appointment_data

    finally:
        conn.close()


@router.get("/track/{reference}", response_model=AppointmentResponse)
def track_booking(reference: str):
    """Retrieve live booking details by unique reference number."""
    conn = get_db_connection()
    try:
        row = conn.execute(
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
            WHERE a.booking_reference = ?
            """,
            (reference.upper().strip(),)
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Appointment reference not found")

        return dict(row)
    finally:
        conn.close()
