-- ==============================================================================
-- Pehchan Unisex Salon & Beauty Parlour - Production Database Schema
-- Target: Supabase PostgreSQL (or any standard PostgreSQL 14+)
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Admin Users Table
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'owner' CHECK (role IN ('owner', 'manager', 'receptionist', 'staff')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(30) NOT NULL,
    gender VARCHAR(20) DEFAULT 'unspecified',
    notes TEXT,
    total_visits INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- 3. Service Categories
CREATE TABLE IF NOT EXISTS service_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(60),
    sort_order INT DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Services Table
CREATE TABLE IF NOT EXISTS services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES service_categories(id) ON DELETE SET NULL,
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    gender_target VARCHAR(20) DEFAULT 'unisex' CHECK (gender_target IN ('unisex', 'female', 'male', 'kids')),
    duration_minutes INT NOT NULL DEFAULT 45 CHECK (duration_minutes > 0),
    price_cents BIGINT NOT NULL DEFAULT 0 CHECK (price_cents >= 0),
    discount_price_cents BIGINT,
    is_featured BOOLEAN DEFAULT FALSE,
    is_popular BOOLEAN DEFAULT FALSE,
    image_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_services_category ON services(category_id);
CREATE INDEX IF NOT EXISTS idx_services_active ON services(is_active);

-- 5. Staff Table
CREATE TABLE IF NOT EXISTS staff (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    designation VARCHAR(120) NOT NULL,
    bio TEXT,
    specialization VARCHAR(255),
    photo_url TEXT,
    email VARCHAR(255),
    phone VARCHAR(30),
    rating NUMERIC(3, 2) DEFAULT 5.0,
    experience_years INT DEFAULT 3,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. Staff Availability (Weekly Working Hours)
-- Weekday: 0 = Monday, 1 = Tuesday, ..., 6 = Sunday
CREATE TABLE IF NOT EXISTS staff_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    staff_id UUID NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    weekday INT NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_off_day BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (staff_id, weekday)
);

-- 7. Salon Working Hours (Global Salon Schedule)
CREATE TABLE IF NOT EXISTS salon_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    weekday INT NOT NULL UNIQUE CHECK (weekday BETWEEN 0 AND 6),
    day_name VARCHAR(20) NOT NULL,
    open_time TIME NOT NULL,
    close_time TIME NOT NULL,
    is_closed BOOLEAN NOT NULL DEFAULT FALSE
);

-- 8. Salon Holidays & Closures
CREATE TABLE IF NOT EXISTS holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    holiday_date DATE NOT NULL UNIQUE,
    title VARCHAR(150) NOT NULL,
    is_full_day_closed BOOLEAN NOT NULL DEFAULT TRUE
);

-- 9. Appointments Table
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_reference VARCHAR(20) NOT NULL UNIQUE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
    staff_id UUID REFERENCES staff(id) ON DELETE SET NULL,
    appointment_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    total_price_cents BIGINT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'confirmed', 'completed', 'cancelled', 'rescheduled')),
    payment_status VARCHAR(30) NOT NULL DEFAULT 'unpaid'
        CHECK (payment_status IN ('unpaid', 'partially_paid', 'paid', 'refunded')),
    customer_notes TEXT,
    admin_notes TEXT,
    cancelled_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_end_after_start CHECK (end_time > start_time)
);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_staff ON appointments(staff_id, appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_customer ON appointments(customer_id);

-- 10. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    amount_cents BIGINT NOT NULL CHECK (amount_cents > 0),
    payment_method VARCHAR(50) NOT NULL DEFAULT 'cash' 
        CHECK (payment_method IN ('cash', 'upi', 'credit_card', 'debit_card', 'online', 'other')),
    transaction_id VARCHAR(100),
    status VARCHAR(30) NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    paid_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_payments_appointment ON payments(appointment_id);

-- 11. Customer Reviews Table
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    service_id UUID REFERENCES services(id) ON DELETE SET NULL,
    reviewer_name VARCHAR(120) NOT NULL,
    reviewer_location VARCHAR(120),
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT NOT NULL,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    is_approved BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_approved ON reviews(is_approved);

-- 12. Offers and Special Packages Table
CREATE TABLE IF NOT EXISTS offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(150) NOT NULL,
    slug VARCHAR(150) NOT NULL UNIQUE,
    badge_text VARCHAR(60),
    description TEXT,
    included_services TEXT, -- Comma or bullet list of package perks
    original_price_cents BIGINT,
    discounted_price_cents BIGINT NOT NULL,
    discount_percentage INT,
    valid_from DATE NOT NULL,
    valid_until DATE NOT NULL,
    image_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_offers_active ON offers(is_active);

-- 13. Gallery and Portfolio Images Table
CREATE TABLE IF NOT EXISTS gallery_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(150) NOT NULL,
    category VARCHAR(60) NOT NULL DEFAULT 'hair' 
        CHECK (category IN ('hair', 'bridal', 'skincare', 'makeup', 'nails', 'beard', 'salon_interior')),
    image_url TEXT NOT NULL,
    thumbnail_url TEXT,
    caption TEXT,
    is_bridal_special BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_gallery_category ON gallery_images(category);

-- 14. Business Settings Table
CREATE TABLE IF NOT EXISTS business_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    salon_name VARCHAR(150) NOT NULL DEFAULT 'Pehchan Unisex Salon & Beauty Parlour',
    tagline VARCHAR(255) DEFAULT 'Where Elegance Meets Excellence',
    phone VARCHAR(50) DEFAULT '+91 98765 43210',
    whatsapp_number VARCHAR(50) DEFAULT '+919876543210',
    email VARCHAR(100) DEFAULT 'contact@pehchansalon.com',
    address TEXT DEFAULT 'Shop 12-14, Luxury Promenade, Near Central Mall, City Centre',
    google_maps_embed_url TEXT,
    currency_symbol VARCHAR(10) DEFAULT '₹',
    currency_code VARCHAR(10) DEFAULT 'INR',
    slot_interval_minutes INT DEFAULT 30,
    allow_online_booking BOOLEAN DEFAULT TRUE,
    whatsapp_notifications_enabled BOOLEAN DEFAULT TRUE,
    email_notifications_enabled BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 15. Notification Logs Table
CREATE TABLE IF NOT EXISTS notification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID REFERENCES appointments(id) ON DELETE CASCADE,
    channel VARCHAR(30) NOT NULL CHECK (channel IN ('whatsapp', 'email', 'sms')),
    recipient VARCHAR(150) NOT NULL,
    subject VARCHAR(200),
    message_content TEXT NOT NULL,
    status VARCHAR(30) NOT NULL CHECK (status IN ('sent', 'failed', 'queued', 'logged')),
    provider_response TEXT,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_notifications_appointment ON notification_logs(appointment_id);

-- Seed default business settings
INSERT INTO business_settings (salon_name, tagline, phone, whatsapp_number, email, address)
VALUES (
    'Pehchan Unisex Salon & Beauty Parlour',
    'Where Elegance Meets Perfection - Luxury Unisex Grooming & Bridal Lounge',
    '+91 98765 43210',
    '+919876543210',
    'hello@pehchansalon.com',
    'Plot 45, Luxury Boulevard, Opposite Central Galleria, Main Road'
) ON CONFLICT DO NOTHING;
