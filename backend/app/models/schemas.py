"""
Pehchan Unisex Salon & Beauty Parlour - Pydantic Request & Response Schemas
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field


# ==============================================================================
# Authentication Schemas
# ==============================================================================
class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin: dict


# ==============================================================================
# Category & Service Schemas
# ==============================================================================
class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class ServiceResponse(BaseModel):
    id: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    name: str
    slug: str
    description: Optional[str] = None
    gender_target: str = "unisex"
    duration_minutes: int
    price: int
    discount_price: Optional[int] = None
    is_featured: bool = False
    is_popular: bool = False
    image_url: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class ServiceCreateUpdate(BaseModel):
    category_id: Optional[str] = None
    name: str = Field(..., min_length=2)
    slug: Optional[str] = None
    description: Optional[str] = None
    gender_target: str = "unisex"
    duration_minutes: int = Field(..., ge=10, le=480)
    price: int = Field(..., ge=0)
    discount_price: Optional[int] = None
    is_featured: bool = False
    is_popular: bool = False
    image_url: Optional[str] = None
    is_active: bool = True


# ==============================================================================
# Staff Schemas
# ==============================================================================
class StaffAvailabilityItem(BaseModel):
    weekday: int
    start_time: str
    end_time: str
    is_off_day: bool = False


class StaffResponse(BaseModel):
    id: str
    name: str
    designation: str
    bio: Optional[str] = None
    specialization: Optional[str] = None
    photo_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    rating: float = 5.0
    experience_years: int = 3
    is_active: bool = True
    availability: Optional[List[StaffAvailabilityItem]] = None


class StaffCreateUpdate(BaseModel):
    name: str = Field(..., min_length=2)
    designation: str
    bio: Optional[str] = None
    specialization: Optional[str] = None
    photo_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    rating: float = 5.0
    experience_years: int = 3
    is_active: bool = True


# ==============================================================================
# Appointment & Booking Schemas
# ==============================================================================
class TimeSlotItem(BaseModel):
    time: str                # "10:00"
    display_time: str        # "10:00 AM"
    available: bool
    reason: Optional[str] = None


class AvailableSlotsResponse(BaseModel):
    date: str
    service_id: str
    service_name: str
    duration_minutes: int
    staff_id: Optional[str] = None
    slots: List[TimeSlotItem]


class BookingCreateRequest(BaseModel):
    service_id: str
    staff_id: Optional[str] = None
    appointment_date: str    # "YYYY-MM-DD"
    start_time: str          # "10:30"
    customer_name: str = Field(..., min_length=2)
    customer_email: Optional[str] = None
    customer_phone: str = Field(..., min_length=8)
    customer_notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: str
    booking_reference: str
    service_id: str
    service_name: str
    duration_minutes: int
    total_price: int
    staff_id: Optional[str] = None
    staff_name: Optional[str] = None
    customer_id: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    appointment_date: str
    start_time: str
    end_time: str
    status: str
    payment_status: str
    customer_notes: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: str


class AppointmentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|completed|cancelled|rescheduled)$")
    admin_notes: Optional[str] = None
    cancelled_reason: Optional[str] = None


class AppointmentReschedule(BaseModel):
    appointment_date: str
    start_time: str
    staff_id: Optional[str] = None


# ==============================================================================
# Customer Schemas
# ==============================================================================
class CustomerResponse(BaseModel):
    id: str
    full_name: str
    email: Optional[str] = None
    phone: str
    gender: str = "unspecified"
    notes: Optional[str] = None
    total_visits: int = 0
    created_at: str


# ==============================================================================
# Review & Offer Schemas
# ==============================================================================
class ReviewCreate(BaseModel):
    reviewer_name: str = Field(..., min_length=2)
    reviewer_location: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=5)
    service_id: Optional[str] = None


class ReviewResponse(BaseModel):
    id: str
    reviewer_name: str
    reviewer_location: Optional[str] = None
    rating: int
    comment: str
    is_featured: bool
    is_approved: bool
    created_at: str


class OfferResponse(BaseModel):
    id: str
    title: str
    slug: str
    badge_text: Optional[str] = None
    description: Optional[str] = None
    included_services: Optional[str] = None
    original_price: Optional[int] = None
    discounted_price: int
    discount_percentage: Optional[int] = None
    valid_from: str
    valid_until: str
    image_url: Optional[str] = None
    is_active: bool = True


class OfferCreateUpdate(BaseModel):
    title: str
    slug: Optional[str] = None
    badge_text: Optional[str] = None
    description: Optional[str] = None
    included_services: Optional[str] = None
    original_price: Optional[int] = None
    discounted_price: int
    discount_percentage: Optional[int] = None
    valid_from: str
    valid_until: str
    image_url: Optional[str] = None
    is_active: bool = True


# ==============================================================================
# Gallery & Settings Schemas
# ==============================================================================
class GalleryImageResponse(BaseModel):
    id: str
    title: str
    category: str
    image_url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    is_bridal_special: bool = False
    sort_order: int = 0


class GalleryImageCreate(BaseModel):
    title: str
    category: str = "hair"
    image_url: str
    caption: Optional[str] = None
    is_bridal_special: bool = False
    sort_order: int = 0


class BusinessSettingsResponse(BaseModel):
    salon_name: str
    tagline: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    google_maps_embed_url: Optional[str] = None
    currency_symbol: str = "₹"
    currency_code: str = "INR"
    slot_interval_minutes: int = 30
    allow_online_booking: bool = True
    whatsapp_notifications_enabled: bool = True
    email_notifications_enabled: bool = True


class BusinessSettingsUpdate(BaseModel):
    salon_name: Optional[str] = None
    tagline: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    google_maps_embed_url: Optional[str] = None
    slot_interval_minutes: Optional[int] = None
    allow_online_booking: Optional[bool] = None
    whatsapp_notifications_enabled: Optional[bool] = None
    email_notifications_enabled: Optional[bool] = None


# ==============================================================================
# Admin Dashboard Summary Schemas
# ==============================================================================
class AdminSummaryResponse(BaseModel):
    total_appointments: int
    today_appointments: int
    pending_appointments: int
    confirmed_appointments: int
    completed_appointments: int
    total_customers: int
    total_revenue: int
    today_revenue: int
    active_services_count: int
    active_staff_count: int
    recent_bookings: List[AppointmentResponse]
