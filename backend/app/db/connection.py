"""
Pehchan Unisex Salon & Beauty Parlour - Database Connection & Initialization
Supports SQLite out-of-the-box for instant zero-config operation and provides full
compatibility with Supabase PostgreSQL via the provided schema in /scripts.
"""

import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.utils.security import hash_password

DB_PATH = Path(__file__).resolve().parent.parent / "pehchan_salon.db"


def get_db_connection():
    """Establish connection to SQLite with WAL mode, foreign keys, and dictionary cursor."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all relational tables, constraints, indexes, and initial seed data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Admin Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_users (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'owner',
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Customers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT,
        phone TEXT NOT NULL,
        gender TEXT DEFAULT 'unspecified',
        notes TEXT,
        total_visits INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cust_phone ON customers(phone)")

    # 3. Service Categories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_categories (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        slug TEXT NOT NULL UNIQUE,
        description TEXT,
        icon TEXT,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 4. Services
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id TEXT PRIMARY KEY,
        category_id TEXT REFERENCES service_categories(id) ON DELETE SET NULL,
        name TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        description TEXT,
        gender_target TEXT DEFAULT 'unisex',
        duration_minutes INTEGER NOT NULL DEFAULT 45,
        price INTEGER NOT NULL DEFAULT 0,
        discount_price INTEGER,
        is_featured INTEGER DEFAULT 0,
        is_popular INTEGER DEFAULT 0,
        image_url TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_services_category ON services(category_id)")

    # 5. Staff
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        designation TEXT NOT NULL,
        bio TEXT,
        specialization TEXT,
        photo_url TEXT,
        email TEXT,
        phone TEXT,
        rating REAL DEFAULT 5.0,
        experience_years INTEGER DEFAULT 3,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 6. Staff Availability
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff_availability (
        id TEXT PRIMARY KEY,
        staff_id TEXT NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
        weekday INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        is_off_day INTEGER NOT NULL DEFAULT 0,
        UNIQUE (staff_id, weekday)
    )
    """)

    # 7. Salon Hours
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS salon_hours (
        id TEXT PRIMARY KEY,
        weekday INTEGER NOT NULL UNIQUE,
        day_name TEXT NOT NULL,
        open_time TEXT NOT NULL,
        close_time TEXT NOT NULL,
        is_closed INTEGER NOT NULL DEFAULT 0
    )
    """)

    # 8. Holidays
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS holidays (
        id TEXT PRIMARY KEY,
        holiday_date TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        is_full_day_closed INTEGER NOT NULL DEFAULT 1
    )
    """)

    # 9. Appointments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        booking_reference TEXT NOT NULL UNIQUE,
        customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
        service_id TEXT NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
        staff_id TEXT REFERENCES staff(id) ON DELETE SET NULL,
        appointment_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        total_price INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        payment_status TEXT NOT NULL DEFAULT 'unpaid',
        customer_notes TEXT,
        admin_notes TEXT,
        cancelled_reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_date ON appointments(appointment_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_staff ON appointments(staff_id, appointment_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_status ON appointments(status)")

    # 10. Payments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id TEXT PRIMARY KEY,
        appointment_id TEXT NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
        amount INTEGER NOT NULL,
        payment_method TEXT NOT NULL DEFAULT 'cash',
        transaction_id TEXT,
        status TEXT NOT NULL DEFAULT 'completed',
        paid_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 11. Customer Reviews
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id TEXT PRIMARY KEY,
        customer_id TEXT REFERENCES customers(id) ON DELETE SET NULL,
        service_id TEXT REFERENCES services(id) ON DELETE SET NULL,
        reviewer_name TEXT NOT NULL,
        reviewer_location TEXT,
        rating INTEGER NOT NULL,
        comment TEXT NOT NULL,
        is_featured INTEGER NOT NULL DEFAULT 0,
        is_approved INTEGER NOT NULL DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 12. Offers and Special Packages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS offers (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        badge_text TEXT,
        description TEXT,
        included_services TEXT,
        original_price INTEGER,
        discounted_price INTEGER NOT NULL,
        discount_percentage INTEGER,
        valid_from TEXT NOT NULL,
        valid_until TEXT NOT NULL,
        image_url TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 13. Gallery Images
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gallery_images (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'hair',
        image_url TEXT NOT NULL,
        thumbnail_url TEXT,
        caption TEXT,
        is_bridal_special INTEGER NOT NULL DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 14. Business Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS business_settings (
        id TEXT PRIMARY KEY,
        salon_name TEXT NOT NULL,
        tagline TEXT,
        phone TEXT,
        whatsapp_number TEXT,
        email TEXT,
        address TEXT,
        google_maps_embed_url TEXT,
        currency_symbol TEXT DEFAULT '₹',
        currency_code TEXT DEFAULT 'INR',
        slot_interval_minutes INTEGER DEFAULT 30,
        allow_online_booking INTEGER DEFAULT 1,
        whatsapp_notifications_enabled INTEGER DEFAULT 1,
        email_notifications_enabled INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 15. Notification Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notification_logs (
        id TEXT PRIMARY KEY,
        appointment_id TEXT REFERENCES appointments(id) ON DELETE CASCADE,
        channel TEXT NOT NULL,
        recipient TEXT NOT NULL,
        subject TEXT,
        message_content TEXT NOT NULL,
        status TEXT NOT NULL,
        provider_response TEXT,
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    # Seed data if database is fresh
    _seed_initial_data(cursor, conn)
    conn.close()


def _seed_initial_data(cursor, conn):
    """Populate rich initial data for Pehchan Unisex Salon."""
    # 1. Admin User
    admin_count = cursor.execute("SELECT COUNT(*) FROM admin_users").fetchone()[0]
    if admin_count == 0:
        admin_id = str(uuid.uuid4())
        hashed = hash_password("AdminPehchan@2026")
        cursor.execute("""
        INSERT INTO admin_users (id, full_name, email, password_hash, role, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        """, (admin_id, "Pehchan Salon Owner", "admin@pehchansalon.com", hashed, "owner"))

    # 2. Business Settings
    settings_count = cursor.execute("SELECT COUNT(*) FROM business_settings").fetchone()[0]
    if settings_count == 0:
        cursor.execute("""
        INSERT INTO business_settings (
            id, salon_name, tagline, phone, whatsapp_number, email, address,
            google_maps_embed_url, currency_symbol, currency_code, slot_interval_minutes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            "Pehchan Unisex Salon & Luxury Spa",
            "Where Elegance Meets Excellence - Bespoke Hair, Bridal & Grooming Lounge",
            "+91 98765 43210",
            "+919876543210",
            "hello@pehchansalon.com",
            "Shop 104-106, Luxury Promenade, High Street Avenue, Near City Centre Mall",
            "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d114000.0!2d75.75!3d26.9!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjbCsDU0JzAwLjAiTiA3NcKwNDUnMDAuMCJF!5e0!3m2!1sen!2sin!4v1600000000000!5m2!1sen!2sin",
            "₹", "INR", 30
        ))

    # 3. Salon Hours (Monday=0 to Sunday=6)
    hours_count = cursor.execute("SELECT COUNT(*) FROM salon_hours").fetchone()[0]
    if hours_count == 0:
        days = [
            (0, "Monday", "09:00", "21:00", 0),
            (1, "Tuesday", "09:00", "21:00", 0),
            (2, "Wednesday", "09:00", "21:00", 0),
            (3, "Thursday", "09:00", "21:00", 0),
            (4, "Friday", "09:00", "21:00", 0),
            (5, "Saturday", "09:00", "21:30", 0),
            (6, "Sunday", "09:00", "21:30", 0),
        ]
        for day in days:
            cursor.execute("""
            INSERT INTO salon_hours (id, weekday, day_name, open_time, close_time, is_closed)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), day[0], day[1], day[2], day[3], day[4]))

    # 4. Service Categories
    cat_count = cursor.execute("SELECT COUNT(*) FROM service_categories").fetchone()[0]
    category_map = {}
    if cat_count == 0:
        categories = [
            ("Hair Styling & Cuts", "hair-styling", "Expert haircutting, styling, hair spa, and blowout treatments for men & women.", "fa-cut", 1),
            ("Hair Color & Treatments", "hair-color-treatments", "Global highlights, balayage, keratin smoothing, and Botox hair therapy.", "fa-paint-brush", 2),
            ("Skin Care & Facials", "skin-care-facials", "Hydra-facials, organic glow peels, de-tan treatments, and anti-aging therapies.", "fa-spa", 3),
            ("Bridal & Groom Lounge", "bridal-groom-lounge", "Signature high-definition bridal makeups, reception styling, and royal groom makeovers.", "fa-gem", 4),
            ("Beard & Men's Grooming", "beard-mens-grooming", "Precision beard sculpting, charcoal peel-off masks, and luxury head massages.", "fa-user-tie", 5),
            ("Nail Art & Extensions", "nail-art-extensions", "Gel polish, acrylic extensions, chrome nails, and spa manicure & pedicure.", "fa-hand-sparkles", 6),
            ("Body Spa & Wellness", "body-spa-wellness", "Aromatherapy, Swedish deep tissue massage, and rejuvenating body polishing.", "fa-hot-tub", 7)
        ]
        for name, slug, desc, icon, order in categories:
            cat_id = str(uuid.uuid4())
            category_map[slug] = cat_id
            cursor.execute("""
            INSERT INTO service_categories (id, name, slug, description, icon, sort_order, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (cat_id, name, slug, desc, icon, order))
    else:
        for row in cursor.execute("SELECT slug, id FROM service_categories").fetchall():
            category_map[row[0]] = row[1]

    # 5. Services
    serv_count = cursor.execute("SELECT COUNT(*) FROM services").fetchone()[0]
    if serv_count == 0:
        services_data = [
            # Hair Styling
            ("Signature Creative Haircut & Blowdry", "creative-haircut-blowdry", "Personalized consultation, scalp massage, tailored haircut and runway-ready blowdry finish.", "unisex", 45, 850, 750, 1, 1, "https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=800&q=80", category_map.get("hair-styling")),
            ("Royal Keratin Smooth Therapy", "royal-keratin-therapy", "Formaldehyde-free intensive smoothing treatment that eliminates frizz and delivers mirror-like shine for up to 5 months.", "unisex", 150, 4999, 4499, 1, 1, "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=800&q=80", category_map.get("hair-color-treatments")),
            ("Balayage & Dimensional Highlights", "balayage-dimensional-highlights", "Hand-painted sun-kissed hair coloring technique using premium ammonia-free L'Oréal Professional colors.", "unisex", 180, 5500, 4800, 1, 1, "https://images.unsplash.com/photo-1562322140-8baeececf3df?auto=format&fit=crop&w=800&q=80", category_map.get("hair-color-treatments")),
            ("O3+ Diamond Glow Facial", "o3-diamond-glow-facial", "Luxurious brightening therapy with diamond micro-crystals that restores radiance, removes tan, and revitalizes tired skin.", "unisex", 60, 2200, 1850, 1, 1, "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=800&q=80", category_map.get("skin-care-facials")),
            ("Hydra-Facial Deep Infusion", "hydra-facial-deep-infusion", "Multi-step vortex suction technology delivering hyaluronic acid, peptides, and antioxidants for deep pore purification and plumping.", "unisex", 75, 3500, 2999, 1, 1, "https://images.unsplash.com/photo-1512290900672-1f55b995646c?auto=format&fit=crop&w=800&q=80", category_map.get("skin-care-facials")),
            ("Signature HD Bridal Makeup", "signature-hd-bridal-makeup", "Flawless HD makeup artistry with waterproof airbrush finish, 3D eyelashes, designer hairstyling, dupatta draping, and jewelry setting.", "female", 240, 14999, 12999, 1, 1, "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=800&q=80", category_map.get("bridal-groom-lounge")),
            ("Pre-Bridal Glow & Wellness Ritual", "pre-bridal-glow-ritual", "Complete body polishing, full-body de-tan, crystal manicure & pedicure, gold facial, and therapeutic head spa.", "female", 300, 9999, 8499, 1, 0, "https://images.unsplash.com/photo-1519699047748-de8e457a634e?auto=format&fit=crop&w=800&q=80", category_map.get("bridal-groom-lounge")),
            ("Royal Groom Makeover & Styling", "royal-groom-makeover", "Executive beard styling, de-tan glow facial, haircut, hair setting, soothing scalp massage, and natural HD camera-ready finish.", "male", 120, 4999, 4200, 1, 1, "https://images.unsplash.com/photo-1621605815971-fbc98d665033?auto=format&fit=crop&w=800&q=80", category_map.get("bridal-groom-lounge")),
            ("Executive Beard Sculpting & Hot Towel Spa", "beard-sculpting-hot-towel", "Straight razor edge definition, beard softening oil treatment, hot steam towel, and revitalizing beard butter massage.", "male", 35, 450, 399, 0, 1, "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&w=800&q=80", category_map.get("beard-mens-grooming")),
            ("Crystal Gel Manicure & Luxury Pedicure", "crystal-gel-manicure-pedicure", "Dead Sea mineral soak, botanical scrub, cuticle care, reflexology foot massage, and long-lasting gel nail lacquer.", "unisex", 75, 1600, 1350, 0, 1, "https://images.unsplash.com/photo-1632345031435-8727f6897d53?auto=format&fit=crop&w=800&q=80", category_map.get("nail-art-extensions")),
            ("Swedish Aromatherapy Full Body Massage", "swedish-aromatherapy-massage", "Gentle yet deeply relaxing full body massage using warm essential oils to release chronic muscle tension and promote holistic sleep.", "unisex", 60, 2499, 2199, 1, 1, "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=800&q=80", category_map.get("body-spa-wellness")),
            ("Charcoal Detox Hair Spa & Scalp Therapy", "charcoal-detox-hair-spa", "Deep purifying scalp scrub, micro-mist hydration, and intensive nourishing hair butter mask for stressed hair.", "unisex", 60, 1200, 999, 0, 1, "https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?auto=format&fit=crop&w=800&q=80", category_map.get("hair-styling")),
        ]
        for name, slug, desc, gender, duration, price, disc_price, is_feat, is_pop, img, cat_id in services_data:
            cursor.execute("""
            INSERT INTO services (
                id, category_id, name, slug, description, gender_target,
                duration_minutes, price, discount_price, is_featured, is_popular,
                image_url, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (str(uuid.uuid4()), cat_id, name, slug, desc, gender, duration, price, disc_price, is_feat, is_pop, img))

    # 6. Staff
    staff_count = cursor.execute("SELECT COUNT(*) FROM staff").fetchone()[0]
    staff_ids = []
    if staff_count == 0:
        staff_data = [
            ("Vikram Sharma", "Creative Art Director & Master Stylist", "Celebrity hair stylist with over 12 years of experience in advanced hair cutting, precision styling, and balayage artistry.", "Hair Design & Keratin Therapy", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80", "vikram@pehchansalon.com", "+91 98765 11111", 4.9, 12),
            ("Priya Kapoor", "Lead Bridal Makeup Artist & Esthetician", "Trained at London School of Makeup, Priya is renowned for glowing, natural HD bridal looks and luxury skincare therapies.", "HD Bridal Makeup & Hydra-Facials", "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=600&q=80", "priya@pehchansalon.com", "+91 98765 22222", 5.0, 9),
            ("Rahul Verma", "Senior Grooming Specialist & Barber", "Master of razor fades, luxury beard sculpting, and customized men's grooming experiences.", "Precision Fades & Beard Architecture", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80", "rahul@pehchansalon.com", "+91 98765 33333", 4.8, 7),
            ("Ananya Sen", "Senior Skin Therapist & Spa Master", "CIDESCO certified skin specialist dedicated to therapeutic massages, holistic anti-aging rituals, and nail aesthetics.", "Deep Tissue Spa & Chemical Peels", "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=600&q=80", "ananya@pehchansalon.com", "+91 98765 44444", 4.9, 8)
        ]
        for name, desig, bio, spec, photo, email, phone, rating, exp in staff_data:
            s_id = str(uuid.uuid4())
            staff_ids.append(s_id)
            cursor.execute("""
            INSERT INTO staff (
                id, name, designation, bio, specialization, photo_url,
                email, phone, rating, experience_years, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (s_id, name, desig, bio, spec, photo, email, phone, rating, exp))

            # Add availability for this staff member (Mon-Sun, 09:30 - 20:30, Tuesday off for Vikram, Wednesday off for Priya)
            for w in range(7):
                is_off = 1 if (w == 1 and name.startswith("Vikram")) or (w == 2 and name.startswith("Priya")) else 0
                cursor.execute("""
                INSERT INTO staff_availability (id, staff_id, weekday, start_time, end_time, is_off_day)
                VALUES (?, ?, ?, '09:30', '20:30', ?)
                """, (str(uuid.uuid4()), s_id, w, is_off))

    # 7. Offers & Packages
    offer_count = cursor.execute("SELECT COUNT(*) FROM offers").fetchone()[0]
    if offer_count == 0:
        offers = [
            ("Pre-Bridal Grand Royale Package", "pre-bridal-grand-royale", "ROYAL LUXURY", "The ultimate pampering package for the bride-to-be across 2 days of pampering.", "Full Body De-Tan Polish, O3+ Diamond Facial, Keratin Hair Spa, Crystal Gel Mani-Pedi, Full Body Waxing, Brow Sculpting", 14500, 9999, 31, "2026-01-01", "2026-12-31", "https://images.unsplash.com/photo-1519699047748-de8e457a634e?auto=format&fit=crop&w=800&q=80"),
            ("Festive Glow Couple Spa & Haircut", "festive-couple-glow", "POPULAR COMBO", "Unwind together with customized hair styling, scalp massage, and brightening gold facials.", "2x Haircuts & Styling, 2x Gold Radiance Facials, 2x Deep Conditioning Scalp Therapies", 5800, 3999, 31, "2026-01-01", "2026-12-31", "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80"),
            ("Gentleman's Executive Grooming Suite", "gentlemans-executive-grooming", "MEN'S CHOICE", "Complete high-profile makeover tailored for weddings, presentations, and special occasions.", "Creative Haircut, Hot Towel Beard Sculpting, Charcoal Skin Detanning, Refreshing Eye Mask", 2100, 1499, 28, "2026-01-01", "2026-12-31", "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&w=800&q=80"),
            ("Keratin Gloss & Color Transformation", "keratin-gloss-color", "TRENDING", "Combine stunning dimensional hair highlights with intensive protein restoration.", "Balayage Highlights, Post-Color Keratin Infusion, Split End Treatment, Blowdry Styling", 9500, 6999, 26, "2026-01-01", "2026-12-31", "https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=800&q=80")
        ]
        for title, slug, badge, desc, inc, orig, disc, pct, vf, vu, img in offers:
            cursor.execute("""
            INSERT INTO offers (
                id, title, slug, badge_text, description, included_services,
                original_price, discounted_price, discount_percentage, valid_from,
                valid_until, image_url, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (str(uuid.uuid4()), title, slug, badge, desc, inc, orig, disc, pct, vf, vu, img))

    # 8. Gallery Images
    gallery_count = cursor.execute("SELECT COUNT(*) FROM gallery_images").fetchone()[0]
    if gallery_count == 0:
        gallery = [
            ("Ethereal Pastel Bridal Look", "bridal", "https://images.unsplash.com/photo-1583939003579-730e3918a45a?auto=format&fit=crop&w=800&q=80", "Traditional elegance with modern HD airbrush finish and floral hair design.", 1, 1),
            ("Modern Balayage & Beach Waves", "hair", "https://images.unsplash.com/photo-1562322140-8baeececf3df?auto=format&fit=crop&w=800&q=80", "Multi-tonal golden honey highlights on natural brunette locks.", 0, 2),
            ("Gentleman's Sharp Fade & Beard", "beard", "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&w=800&q=80", "Sculpted beard lines paired with textured crop top haircut.", 0, 3),
            ("Signature Royal Bridal Glam", "bridal", "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=800&q=80", "Smokey eyes with crimson lips and authentic bridal jewelry pairing.", 1, 4),
            ("Hydra-Facial Dewy Skin Glow", "skincare", "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=800&q=80", "Instant glass-skin hydration post our 7-step vortex skin treatment.", 0, 5),
            ("Luxury Salon Ambience & Private Suites", "salon_interior", "https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f?auto=format&fit=crop&w=800&q=80", "Relax in our private VIP styling pods designed for maximum comfort and hygiene.", 0, 6),
            ("Chrome French Tip Gel Extensions", "nails", "https://images.unsplash.com/photo-1632345031435-8727f6897d53?auto=format&fit=crop&w=800&q=80", "Bespoke almond nail extensions with glazed donut chrome finish.", 0, 7),
            ("Reception Glam with Hollywood Waves", "bridal", "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=800&q=80", "Timeless retro waves with soft champagne glow makeup.", 1, 8),
        ]
        for title, cat, img, cap, is_bridal, sort_order in gallery:
            cursor.execute("""
            INSERT INTO gallery_images (
                id, title, category, image_url, thumbnail_url, caption,
                is_bridal_special, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), title, cat, img, img, cap, is_bridal, sort_order))

    # 9. Customer Reviews
    review_count = cursor.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    if review_count == 0:
        reviews = [
            ("Meera Singhania", "Civil Lines", 5, "Priya did my bridal makeup for both my wedding and reception. I received so many compliments! My skin looked glowing and not cakey at all even after 8 hours of dancing. Truly the finest salon in town!", 1),
            ("Rohan Mathur", "C-Scheme", 5, "Vikram is a true magician with scissors. He understood my hair texture immediately and gave me the best haircut of my life. The ambience is ultra-luxurious and the coffee is great too.", 1),
            ("Dr. Kavita Bansal", "Raja Park", 5, "The Hydra-Facial here is phenomenal! Completely painless, soothing, and my skin felt so supple and clean. Top notch hygiene and very polite staff.", 1),
            ("Arjun Shekhawat", "Vaishali Nagar", 5, "I always get my beard and hair styled by Rahul before big meetings. The hot towel treatment and razor accuracy is unbeatable. Highly recommended for men's grooming.", 1),
            ("Simran Sachdeva", "Malviya Nagar", 5, "Got the Royal Keratin treatment done 2 months back and my hair still looks like I just stepped out of a shampoo commercial. Worth every single penny!", 1)
        ]
        for name, loc, rating, comment, is_feat in reviews:
            cursor.execute("""
            INSERT INTO reviews (
                id, reviewer_name, reviewer_location, rating, comment,
                is_featured, is_approved
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (str(uuid.uuid4()), name, loc, rating, comment, is_feat))

    conn.commit()


# Automatically initialize DB on import if not already created
init_db()
