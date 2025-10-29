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
│   ├── home.html          # Minimalist split-screen landing page
│   ├── locations/         # Location-specific page structure
│   │   ├── holliston/     # Holliston location pages
│   │   │   ├── landing.html    # Holliston homepage with storefront hero
│   │   │   ├── services.html   # Services menu with real pricing
│   │   │   ├── booking.html    # FullSlate booking integration
│   │   │   ├── team.html       # Meet the therapists
│   │   │   └── info.html       # Contact, hours, policies, map
│   │   └── worcester/     # Worcester location pages
│   │       ├── landing.html    # Worcester homepage with reception hero
│   │       ├── services.html   # Services menu with real pricing
│   │       ├── booking.html    # FullSlate booking integration
│   │       ├── team.html       # Meet the therapists
│   │       └── info.html       # Contact, hours, policies, map
│   ├── gift_cards.html
│   ├── join_team.html
│   ├── policies.html
│   ├── provider_portal.html
│   ├── login.html
│   └── book.html
├── static/
│   ├── css/style.css      # Luxury spa styling (Cormorant Garamond, Montserrat, #7eb89e green)
│   ├── js/main.js         # Client-side interactions
│   ├── holliston-storefront.png  # Holliston exterior hero image
│   ├── holliston-room.png        # Holliston treatment room
│   ├── worcester-room.png        # Worcester reception area
│   └── uploads/           # File upload storage
└── replit.md              # This file
```

## Features Implemented

### Public Pages
- **Landing Page**: Minimalist split-screen design with Worcester (left) and Holliston (right) location photos, animated sideways arrows, brand green (#7eb89e) heading
- **Holliston Location Pages**: 
  - Landing: Storefront hero image, welcome section, quick info cards
  - Services: New client special ($90), therapeutic massage pricing, service descriptions
  - Booking: Embedded FullSlate iframe (toughlovemassage.fullslate.com)
  - Team: Therapist profiles and specializations
  - Info: Address (21A Charles St), hours (Mon-Fri 8AM-8PM, Sat-Sun 8AM-5PM), phone (774-233-0365), Google Maps, policies
- **Worcester Location Pages**:
  - Landing: Reception room hero image, welcome section, quick info cards
  - Services: New client specials ($80/$110), comprehensive service menu (30/60/90 min), prenatal, Thai massage, cupping
  - Booking: Embedded FullSlate iframe (toughlovemassage22.fullslate.com)
  - Team: Therapist profiles and diverse specializations
  - Info: Address (130 Millbury St), hours (Mon-Fri 8AM-8PM, Sat 8AM-7PM, Sun 8AM-3PM), phone (508-373-2830), Google Maps, policies
- **Gift Cards**: Purchase $50/$100/$200 gift cards with Stripe integration
- **Join Our Team**: Application form with resume upload, stores in database
- **Policies**: GDPR/HIPAA-compliant privacy policy, cancellation policy (24-hour notice), accordion UI

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
- **Typography**: Cormorant Garamond (headings), Montserrat (body) - luxury spa aesthetic
- **Colors**: Brand green (#7eb89e primary), soft neutrals (#2C2C2C dark, #f9f7f4 light backgrounds)
- **Spa Styling**: Premium spacing, elegant cards with subtle shadows, hover effects, sticky navigation
- **Animations**: Split-screen hover expansion, animated arrows (slideLeft/slideRight)
- **Layout**: Bootstrap 5 responsive grid, mobile-first design
- **Images**: Real business photos (Holliston storefront, Worcester reception, Holliston treatment room)

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

## Recent Changes

### 2025-10-29 - Enhanced Provider Portal with Practice Management
- **Major database expansion**: Added 5 new models (Client, Appointment, SOAPNote, MedicalAlert, PerformanceMetric, Treatment)
- **HIPAA-compliant architecture**: Full audit trails with created_by, updated_by, timestamps on all records
- **Provider Portal redesigned**: 6-tab luxury spa interface (Dashboard, Schedule, SOAP Notes, Clients, Analytics, Intakes)
- **Dashboard features**: Quick stats cards, today's schedule preview, active medical alerts, quick actions
- **Schedule management**: Today's and upcoming appointments with client prep cards, medical alert badges
- **SOAP Notes system**: Structured clinical documentation (Subjective, Objective, Assessment, Plan) with pain tracking
- **Analytics dashboard**: Performance metrics with Chart.js visualizations, session/revenue tracking
- **Medical alerts**: Severity-based contraindication tracking with active/inactive status
- **Data migration tools**: Helper functions for backward compatibility, seed_data.py for sample data
- **Custom Jinja2 filters**: Safe medical alert counting and display
- **Mobile-optimized**: Responsive design with luxury spa styling throughout

### 2025-10-29 - Luxury Spa Location Pages
- **Complete redesign** of location pages with Forbes 5-star spa aesthetic
- Created **10 new pages** (5 per location: Landing, Services, Booking, Team, Info)
- Integrated **real business data**: accurate addresses, hours, phone numbers, pricing from official sources
- Added **luxury spa CSS** with Cormorant Garamond typography, brand green (#7eb89e), premium spacing
- Embedded **FullSlate booking** with separate iframes for each location
- Updated home page navigation to use new location routes
- Added Holliston storefront hero image
- Service cards with hover effects, special offer highlighting
- Location-specific sticky navigation between subpages
- Google Maps integration for both locations
- Comprehensive service menus with real pricing

### 2025-10-27 - Security Hardening
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
