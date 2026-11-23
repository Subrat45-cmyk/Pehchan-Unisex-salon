# Pehchan Unisex Salon & Beauty Parlour Management System

> **A premium, enterprise-ready unisex salon website, online slot booking engine, and salon owner management system.**

Built with **HTML5, CSS3, Vanilla JavaScript, Python, FastAPI, and Supabase PostgreSQL / SQLite dual-engine**.

---

## 🌟 System Features & Deliverables

### 1. Customer-Facing Luxury Website (14 Public Pages)
- **Home (`index.html`)**: Regal hero section, master stylists highlight, clinical hygiene standards, featured signature rituals, VIP bridal spotlight, special offers, real customer reviews, and floating WhatsApp contact.
- **About Us (`about.html`)**: Salon story, philosophy of identity, 12+ years heritage, and master team profiles.
- **Services (`services.html`)**: Complete service menu with category tabs (Hair Cuts, Keratin & Color, Skin & Facials, Bridal Lounge, Men's Grooming, Nails, Body Spa) and gender filtering (Women, Men, All).
- **Service Details (`service-details.html`)**: Deep dive into individual treatments, duration, pricing, and 1-click booking.
- **Pricing & Rate Card (`pricing.html`)**: Transparent rate card, all-inclusive GST pricing, and custom group booking inquiries.
- **Portfolio Gallery (`gallery.html`)**: Interactive filterable photo gallery with modal lightbox preview.
- **Bridal Makeup Portfolio (`bridal.html`)**: Dedicated luxury showcase for HD airbrush bridal looks, groom makeover suite, pre-wedding preparation rituals, and WhatsApp consultation.
- **Offers & Packages (`offers.html`)**: Festive discount packages, couple spa bundles, validity dates, and instant package claiming.
- **Appointment Booking (`booking.html`)**: Interactive multi-step booking wizard with real-time slot conflict detection, staff selection, zero-friction reservation, instant confirmation slip, and reference tracking.
- **Testimonials (`testimonials.html`)**: Verified client reviews and real-time review submission form.
- **Contact Us (`contact.html`)**: Salon location, opening hours, interactive inquiry form, direct WhatsApp chat, and interactive Google Map.
- **FAQ (`faq.html`)**: Categorized accordion FAQs addressing bookings, cancellations, payments, and sterilization.
- **Privacy Policy (`privacy-policy.html`)**: Comprehensive legal data protection policy.
- **Terms & Conditions (`terms.html`)**: Salon etiquette, arrival guidelines, and cancellation rules.

---

### 2. Salon Owner & Manager Admin Dashboard (`/admin/`)
- **Single-Page Application (SPA)** protected by secure **PBKDF2-HMAC-SHA256** password hashing and **RFC 7519 HMAC-SHA256 JWT** authentication.
- **Overview & Statistics**: Live KPI cards (Today's Bookings, Pending Confirmations, Today's Revenue, Total Customers) and recent bookings table.
- **Appointment Management**: Filter by status (`pending`, `confirmed`, `completed`, `cancelled`, `rescheduled`), live search, 1-click status update, modal for rescheduling date/time/staff, and cancellation logs.
- **Customer CRM**: Complete customer directory with visit counts, registration date, and 1-click direct WhatsApp chat link.
- **Service Menu Management**: Add, edit, price, set duration, and toggle featured treatments.
- **Staff Roster Management**: Add stylists, manage bios, experience, ratings, and weekly shift schedules.
- **Offers & Packages**: Create seasonal discounts, set validity windows, and publish promotional banners.
- **Gallery Manager**: Upload photographs, assign categories, and tag bridal specials.
- **Reviews Moderation**: Approve, reject, or feature reviews on the homepage.
- **Salon Business Settings**: Edit salon name, contact numbers, address, slot intervals, and toggle online bookings.
- **Notification Delivery Audit Trail**: Live log viewer for automated WhatsApp and Email dispatch records.

---

### 3. Business Automation & Real-Time Slot Engine
- **Slot Availability Engine (`backend/app/services/calendar.py`)**:
  - Dynamically computes available slots considering salon opening hours, holidays, staff shifts, service duration, and existing non-overlapping bookings.
  - Prevents duplicate bookings (same customer on overlapping time).
- **Notification Dispatcher (`backend/app/services/notification.py`)**:
  - **WhatsApp Business Cloud API** integration for automated confirmation, reminder, and status update messages.
  - **Email Service (SMTP)** with branded HTML confirmation slips.
  - Development / sandbox failover mode that logs all dispatches to `notification_logs` table for complete auditability without requiring paid third-party accounts during testing.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (ES6+), FontAwesome 6, Google Fonts (*Cormorant Garamond* & *Montserrat*) |
| **Backend** | Python 3.14, FastAPI, Pydantic, Starlette, Uvicorn |
| **Database** | Supabase PostgreSQL (`scripts/supabase_schema.sql`) & SQLite out-of-the-box (`backend/app/pehchan_salon.db`) |
| **Security** | PBKDF2-HMAC-SHA256 password hashing, RFC 7519 HS256 JWT tokens, CORS, SQL injection prevention |
| **Integrations** | WhatsApp Business Cloud API, SMTP Email, Google Maps Embed |

---

## 🚀 Quick Start & Running Locally

### 1. Prerequisites
- Python 3.10+ installed
- Dependencies pre-installed: `fastapi`, `uvicorn`, `pydantic`, `pytest`, `httpx`

### 2. Start the Application
Run the command from the project root directory:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open in Browser
- **Public Customer Website**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Online Booking Wizard**: [http://127.0.0.1:8000/booking.html](http://127.0.0.1:8000/booking.html)
- **Salon Owner Admin Dashboard**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **Interactive Swagger REST API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔐 Default Admin Credentials

| Parameter | Value |
|---|---|
| **Email** | `admin@pehchansalon.com` |
| **Password** | `AdminPehchan@2026` |
| **Role** | Salon Owner (`owner`) |

*(You can change these credentials or add new managers via the admin dashboard settings or environment variables).*

---

## 🧪 Running Automated Tests

Run the full automated test suite covering authentication, API endpoints, slot calculations, duplicate prevention, and page routing:

```powershell
python -m pytest backend/tests/ -v
```

All 11 tests pass with zero errors.

---

## 🗄️ Supabase PostgreSQL Deployment

To deploy on **Supabase**:
1. Create a new Supabase project at [https://supabase.com](https://supabase.com).
2. Open the **SQL Editor** in your Supabase project dashboard.
3. Paste the contents of [`scripts/supabase_schema.sql`](file:///d:/Pehchan%20Unisex%20Salon/scripts/supabase_schema.sql) and click **Run**.
4. In your `.env` file, add your connection string:
   ```env
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
   SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
   ```

---

## 📱 WhatsApp & Email Notification Setup

In [`.env`](file:///d:/Pehchan%20Unisex%20Salon/.env):

```env
# WhatsApp Business Cloud API
WHATSAPP_ENABLED=true
WHATSAPP_PHONE_NUMBER_ID=your_facebook_developer_phone_id
WHATSAPP_ACCESS_TOKEN=your_permanent_system_user_token

# Email SMTP
EMAIL_NOTIFICATIONS_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=bookings@pehchansalon.com
SMTP_PASSWORD=your_gmail_app_password
FROM_EMAIL="Pehchan Unisex Salon <bookings@pehchansalon.com>"
```
When mock values are present, notifications are automatically logged to the `notification_logs` table without failing requests.

---

## 📁 Project Directory Structure

```
d:\Pehchan Unisex Salon\
├── backend\
│   ├── app\
│   │   ├── db\
│   │   │   ├── connection.py     # SQLite/Postgres DB connector & auto-seed
│   │   │   └── pehchan_salon.db  # Initialized database
│   │   ├── models\
│   │   │   └── schemas.py        # Pydantic request & response models
│   │   ├── routers\
│   │   │   ├── admin.py          # Admin KPI & CRUD management endpoints
│   │   │   ├── auth.py           # JWT Authentication & RBAC
│   │   │   ├── bookings.py       # Online slot booking & conflict check
│   │   │   ├── public_content.py # Public offers, gallery & reviews
│   │   │   ├── services.py       # Service catalog & categories
│   │   │   └── staff.py          # Staff roster & availability
│   │   ├── services\
│   │   │   ├── calendar.py       # Dynamic conflict-free slot calculation engine
│   │   │   └── notification.py   # WhatsApp & Email notification service
│   │   ├── utils\
│   │   │   └── security.py       # PBKDF2 hashing & HS256 JWT tokens
│   │   └── main.py               # FastAPI entrypoint, static mounting & SEO
│   └── tests\
│       ├── test_api.py           # Backend API & automation test suite
│       └── test_pages.py         # Static pages HTTP 200 verification
├── frontend\
│   ├── admin\
│   │   ├── css\admin.css         # Admin dashboard dark luxury styles
│   │   ├── js\admin.js           # Admin SPA logic & state management
│   │   └── index.html            # Salon Owner Admin Portal
│   ├── assets\
│   │   ├── css\style.css         # Main luxury salon stylesheet
│   │   └── js\main.js            # Core frontend API integration & UI
│   ├── index.html                # 1. Home
│   ├── about.html                # 2. About Us
│   ├── services.html             # 3. Services Menu
│   ├── service-details.html      # 4. Service Details
│   ├── pricing.html              # 5. Pricing Rate Card
│   ├── gallery.html              # 6. Portfolio Gallery
│   ├── bridal.html               # 7. Bridal & Groom Lounge
│   ├── offers.html               # 8. Offers & Packages
│   ├── booking.html              # 9. Appointment Booking Wizard
│   ├── testimonials.html         # 10. Reviews & Testimonials
│   ├── contact.html              # 11. Contact Us & Location Map
│   ├── faq.html                  # 12. FAQ Accordion
│   ├── privacy-policy.html       # 13. Privacy Policy
│   └── terms.html                # 14. Terms and Conditions
├── scripts\
│   └── supabase_schema.sql       # Production Supabase PostgreSQL schema
├── .env                          # Local environment variables
├── .env.example                  # Environment configuration template
└── README.md                     # Comprehensive documentation
```
