# Tough Love Massage - Luxury Spa Website

## Overview
A professional, Forbes 5-star level luxury massage spa website built with Flask, featuring responsive design, booking integration, payment processing, and HIPAA-compliant data management.

## Current State
✅ Fully functional luxury spa website with all core features implemented
✅ Running successfully on Flask development server (port 5000)
✅ Database configured with PostgreSQL (Neon)
✅ Security hardened - no default credentials

## Project Structure
```
├── app.py                  # Flask backend with all routes
├── models.py               # Database models (Intake, Provider, Application)
├── templates/              # HTML templates
│   ├── base.html          # Base template with nav/footer
│   ├── home.html          # Landing page
│   ├── location_downtown.html
│   ├── location_suburban.html
│   ├── gift_cards.html
│   ├── join_team.html
│   ├── policies.html
│   ├── provider_portal.html
│   ├── login.html
│   └── book.html
├── static/
│   ├── css/style.css      # Luxury styling (Playfair Display, Montserrat, soft blues/greens)
│   ├── js/main.js         # Client-side interactions
│   └── uploads/           # File upload storage
└── replit.md              # This file
```

## Features Implemented

### Public Pages
- **Landing Page**: Hero section with luxury spa exterior, clickable location images, Andrea L. testimonial
- **Location Pages**: Downtown Studio & Suburban Retreat with treatment menus ($120-$130), provider profiles, hours, Google Maps, FullSlate booking placeholders
- **Gift Cards**: Purchase $50/$100/$200 gift cards with Stripe integration
- **Join Our Team**: Application form with resume upload, stores in database
- **Policies**: GDPR/HIPAA-compliant privacy policy, cancellation policy (24-hour notice), accordion UI
- **Book Now**: Dedicated booking page with FullSlate integration instructions

### Provider Portal (Secure)
- **Login System**: Flask-Login authentication with hashed passwords
- **Intake Management**: View unconfirmed client intakes with medical history
- **Confirmation**: Confirm bookings and auto-email clients

### Technical Features
- **Database**: PostgreSQL with 3 tables (intakes, providers, applications)
- **Email**: SMTP integration for gift card delivery, booking confirmations, job applications
- **Payments**: Stripe checkout integration for gift cards
- **Security**: Werkzeug password hashing, secure file uploads, HIPAA-aware data handling
- **Design**: Responsive Bootstrap 5, AOS animations, luxury color palette
- **SEO**: Meta tags, semantic HTML, alt text for images

## Required Configuration

### 1. Provider Account Setup (REQUIRED)
To access the provider portal, set these environment variables:
```
ADMIN_EMAIL=your-email@example.com
ADMIN_PASSWORD=your-secure-password
```
Then restart the app. **Change the password immediately after first login!**

### 2. Stripe Integration (for Gift Cards)
Get your Stripe secret key from https://stripe.com and add:
```
STRIPE_SECRET_KEY=sk_test_...
```

### 3. Email Notifications (Optional)
For automated emails:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=no-reply@toughlovemassage.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=admin@toughlovemassage.com
```

### 4. FullSlate Booking Integration
1. Sign up at https://fullslate.com
2. Configure your services, locations, and providers
3. Add custom intake fields: "Medical History" and "Pregnancy Stage"
4. Get the widget embed code
5. Replace placeholders in `templates/location_downtown.html`, `templates/location_suburban.html`, and `templates/book.html`

## Database Schema

**intakes** (client booking data)
- id, client_name, email, medical_history, pregnancy_stage, booking_id, confirmed, created_at

**providers** (staff login credentials)
- id, username, password_hash

**applications** (job applications)
- id, name, email, experience, resume_url, submitted_at

## Design Specifications
- **Typography**: Playfair Display (headings), Montserrat (body)
- **Colors**: Soft blues/greens (#2c7a7b primary, #1a4d4d dark, #e0f2f1 light)
- **Animations**: AOS library (fade-in, zoom-in, fade-up) with 1s duration
- **Layout**: Bootstrap 5 responsive grid, mobile-first design
- **Images**: High-resolution stock photos optimized for web

## Next Steps for Customization
1. **Set ADMIN_EMAIL and ADMIN_PASSWORD** to create your first provider account
2. **Add STRIPE_SECRET_KEY** to enable real gift card payments
3. **Configure FullSlate** and embed booking widgets
4. **Replace placeholder content**: 
   - Update provider names and photos in location pages
   - Update hours, phone numbers, and addresses
   - Replace Google Maps iframes with your actual locations
5. **Add SMTP credentials** for email notifications
6. **Upload your own images** to replace stock photos
7. **Customize treatment menu** with your actual services and prices

## Security Notes
- ✅ No hard-coded credentials (environment-based initialization)
- ✅ Password hashing with Werkzeug
- ✅ Secure file upload with filename sanitization
- ✅ HIPAA-aware data storage in encrypted PostgreSQL
- ✅ Login required for provider portal access
- ⚠️ Using Flask development server - deploy with production WSGI server (Gunicorn) for live use

## Recent Changes (2025-10-27)
- Removed hard-coded default provider credentials for HIPAA compliance
- Provider accounts now created via ADMIN_EMAIL/ADMIN_PASSWORD environment variables
- Updated login page to remove default credential display
- Added security warnings when no provider accounts exist

## Tech Stack
- **Backend**: Python 3.11, Flask 3.1, Flask-Login, Flask-SQLAlchemy
- **Database**: PostgreSQL (Neon)
- **Frontend**: HTML5, CSS3, Bootstrap 5, Vanilla JavaScript
- **Libraries**: AOS (animations), Google Fonts, Stripe.js
- **Integrations**: Stripe (payments), FullSlate (booking), SMTP (email)
