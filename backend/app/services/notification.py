"""
Pehchan Unisex Salon & Beauty Parlour - Automated Notification Service
Handles WhatsApp Business Cloud API and Email notifications with automated logging,
delivery tracking, and failover/mock support for development environments.
"""

import os
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import httpx
from backend.app.db.connection import get_db_connection


def log_notification(
    appointment_id: Optional[str],
    channel: str,
    recipient: str,
    subject: str,
    message_content: str,
    status: str,
    provider_response: Optional[str] = None
):
    """Save an immutable record into the notification_logs table."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            INSERT INTO notification_logs (
                id, appointment_id, channel, recipient, subject,
                message_content, status, provider_response
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                appointment_id,
                channel,
                recipient,
                subject,
                message_content,
                status,
                provider_response
            )
        )
        conn.commit()
    except Exception as e:
        print(f"[Notification Log Error] Failed to write notification log: {e}")
    finally:
        conn.close()


def send_whatsapp_message(to_phone: str, message: str, appointment_id: Optional[str] = None) -> bool:
    """
    Sends WhatsApp message via WhatsApp Cloud API.
    If live credentials are not set or are mock, records message safely.
    """
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    is_live = bool(token and phone_id and not token.startswith("mock_") and not phone_id.startswith("mock_"))

    clean_phone = "".join(c for c in to_phone if c.isdigit() or c == "+")
    if not clean_phone.startswith("+"):
        clean_phone = "+91" + clean_phone.lstrip("0")

    if is_live:
        try:
            url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone.replace("+", ""),
                "type": "text",
                "text": {"body": message}
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, headers=headers, json=payload)
                provider_resp = res.text
                status = "sent" if res.status_code in (200, 201) else "failed"

            log_notification(appointment_id, "whatsapp", clean_phone, "WhatsApp Notification", message, status, provider_resp)
            return status == "sent"
        except Exception as ex:
            log_notification(appointment_id, "whatsapp", clean_phone, "WhatsApp Notification", message, "failed", str(ex))
            return False
    else:
        # Development / Sandbox Mode Log
        print(f"[WHATSAPP DISPATCH] To: {clean_phone}\n{message}\n" + "-"*50)
        log_notification(
            appointment_id,
            "whatsapp",
            clean_phone,
            "WhatsApp Message (Dev/Sandbox Mode)",
            message,
            "logged",
            "Simulated dispatch in development mode"
        )
        return True


def send_email_message(to_email: str, subject: str, html_body: str, appointment_id: Optional[str] = None) -> bool:
    """
    Sends HTML email via SMTP.
    If SMTP credentials are not configured or are mock, records safely.
    """
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("FROM_EMAIL", "Pehchan Unisex Salon <bookings@pehchansalon.com>")

    is_live = bool(smtp_host and smtp_user and smtp_pass and not smtp_pass.startswith("mock_"))

    if is_live:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to_email
            part = MIMEText(html_body, "html")
            msg.attach(part)

            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, [to_email], msg.as_string())

            log_notification(appointment_id, "email", to_email, subject, html_body, "sent", "SMTP 250 OK")
            return True
        except Exception as ex:
            log_notification(appointment_id, "email", to_email, subject, html_body, "failed", str(ex))
            return False
    else:
        # Development / Sandbox Mode Log
        print(f"[EMAIL DISPATCH] To: {to_email} | Subject: {subject}\nContent: {html_body[:100]}...\n" + "-"*50)
        log_notification(
            appointment_id,
            "email",
            to_email,
            subject,
            html_body,
            "logged",
            "Simulated email in development mode"
        )
        return True


def dispatch_booking_confirmation(app: Dict[str, Any]):
    """Send immediate WhatsApp and Email confirmation for a newly created booking."""
    cust_name = app.get("customer_name", "Valued Guest")
    ref = app.get("booking_reference", "PH-0000")
    service = app.get("service_name", "Salon Service")
    date_str = app.get("appointment_date", "")
    time_str = app.get("start_time", "")
    staff = app.get("staff_name") or "Senior Stylist"
    price = app.get("total_price", 0)

    # 1. WhatsApp Message
    wa_text = (
        f"✨ *Appointment Confirmed - Pehchan Unisex Salon* ✨\n\n"
        f"Dear *{cust_name}*,\n"
        f"Your salon appointment has been received with reference *#{ref}*.\n\n"
        f"📋 *Service:* {service}\n"
        f"📅 *Date:* {date_str}\n"
        f"⏰ *Time:* {time_str}\n"
        f"👤 *Stylist:* {staff}\n"
        f"💰 *Estimated Price:* ₹{price}\n\n"
        f"📍 *Location:* Pehchan Unisex Salon, Shop 104-106 Luxury Promenade, High Street Avenue.\n"
        f"📞 *Assistance:* +91 98765 43210\n\n"
        f"Please arrive 5-10 minutes prior to your slot. We look forward to pampering you!"
    )
    if app.get("customer_phone"):
        send_whatsapp_message(app["customer_phone"], wa_text, app.get("id"))

    # 2. Email Notification
    if app.get("customer_email"):
        email_html = f"""
        <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e8e2d8; border-radius: 8px; overflow: hidden;">
            <div style="background-color: #1a1a1a; padding: 30px; text-align: center; border-bottom: 3px solid #d4af37;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 2px;">PEHCHAN UNISEX SALON</h1>
                <p style="color: #d4af37; margin: 5px 0 0 0; font-size: 13px; text-transform: uppercase;">Luxury Grooming & Bridal Lounge</p>
            </div>
            <div style="padding: 30px;">
                <h2 style="color: #1a1a1a; margin-top: 0;">Appointment Confirmation</h2>
                <p>Dear <strong>{cust_name}</strong>,</p>
                <p>Thank you for choosing Pehchan Unisex Salon. Your appointment is officially scheduled.</p>
                <div style="background: #faf8f5; border-left: 4px solid #d4af37; padding: 18px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 6px 0;"><strong>Booking Reference:</strong> <span style="color: #d4af37; font-weight: bold;">#{ref}</span></p>
                    <p style="margin: 6px 0;"><strong>Service:</strong> {service}</p>
                    <p style="margin: 6px 0;"><strong>Date:</strong> {date_str}</p>
                    <p style="margin: 6px 0;"><strong>Time:</strong> {time_str}</p>
                    <p style="margin: 6px 0;"><strong>Stylist / Specialist:</strong> {staff}</p>
                    <p style="margin: 6px 0;"><strong>Total Amount:</strong> ₹{price}</p>
                </div>
                <p style="font-size: 14px; color: #555555;">
                    Need to reschedule or have special requirements? Reply directly to this email or reach us on WhatsApp at <strong>+91 98765 43210</strong>.
                </p>
            </div>
            <div style="background: #111111; color: #999999; padding: 20px; text-align: center; font-size: 12px;">
                <p style="margin: 0;">Pehchan Unisex Salon & Luxury Spa &bull; Shop 104-106 Luxury Promenade, High Street</p>
            </div>
        </div>
        """
        send_email_message(app["customer_email"], f"Booking Confirmed #{ref} - Pehchan Unisex Salon", email_html, app.get("id"))


def dispatch_status_change(app: Dict[str, Any], new_status: str, reason: Optional[str] = None):
    """Notify customer when an appointment status is changed by the salon."""
    cust_name = app.get("customer_name", "Valued Guest")
    ref = app.get("booking_reference", "")
    service = app.get("service_name", "")

    status_messages = {
        "confirmed": f"Your appointment #{ref} for {service} has been formally confirmed by our team.",
        "completed": f"Thank you for visiting Pehchan Unisex Salon! We hope you loved your {service}. Please consider leaving us a quick review.",
        "cancelled": f"Your appointment #{ref} for {service} has been cancelled." + (f" Reason: {reason}" if reason else ""),
        "rescheduled": f"Your appointment #{ref} has been rescheduled to {app.get('appointment_date')} at {app.get('start_time')}."
    }

    msg = (
        f"✨ *Pehchan Unisex Salon Update* ✨\n\n"
        f"Hello {cust_name},\n"
        f"{status_messages.get(new_status, f'Status updated to: {new_status}')}\n\n"
        f"For any queries, contact us at +91 98765 43210."
    )

    if app.get("customer_phone"):
        send_whatsapp_message(app["customer_phone"], msg, app.get("id"))
