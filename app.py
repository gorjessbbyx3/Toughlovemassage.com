import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Intake, Provider, Application, Location, Treatment, ProviderTreatment, ProviderAvailability, ProviderDailyLimit, ClientNote
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import stripe

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "dev-secret-key-change-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    provider = Provider.query.get(int(user_id))
    if provider:
        return User(provider.id, provider.username)
    return None

def send_email(to_email, subject, body):
    """Send HTML email with professional formatting and error handling"""
    try:
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME', 'no-reply@toughlovemassage.com')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        if not smtp_password:
            print(f"📧 [DEV MODE] Email would be sent to {to_email}")
            print(f"   Subject: {subject}")
            print(f"   Body preview: {body[:100]}...")
            return True
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f"Tough Love Massage <{smtp_username}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Create professional HTML wrapper
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Montserrat', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #2c7a7b 0%, #1a4d4d 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-family: 'Playfair Display', serif; font-size: 28px;">Tough Love Massage</h1>
                <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">Discover Ultimate Rejuvenation</p>
            </div>
            <div style="background: #ffffff; padding: 30px; border: 1px solid #e0f2f1; border-top: none; border-radius: 0 0 10px 10px;">
                {body}
            </div>
            <div style="text-align: center; margin-top: 20px; padding: 20px; color: #666; font-size: 12px;">
                <p>Tough Love Massage | Downtown Studio & Suburban Retreat</p>
                <p style="margin: 5px 0;">
                    <a href="mailto:info@toughlovemassage.com" style="color: #2c7a7b; text-decoration: none;">Contact Us</a> | 
                    <a href="https://toughlovemassage.com/policies" style="color: #2c7a7b; text-decoration: none;">Privacy Policy</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_template, 'html'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print(f"✓ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"✗ Email error: {e}")
        return False

def send_booking_notification(intake):
    """Notify providers of new booking"""
    provider_emails = [p.username for p in Provider.query.all()]
    subject = f"New Booking: {intake.client_name}"
    body = f"""
    <h2 style="color: #2c7a7b;">New Client Booking Received</h2>
    <p>A new client has submitted their intake form and needs confirmation.</p>
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <tr style="background: #e0f2f1;">
            <td style="padding: 10px; font-weight: bold; border: 1px solid #2c7a7b;">Client Name</td>
            <td style="padding: 10px; border: 1px solid #2c7a7b;">{intake.client_name}</td>
        </tr>
        <tr>
            <td style="padding: 10px; font-weight: bold; border: 1px solid #2c7a7b;">Email</td>
            <td style="padding: 10px; border: 1px solid #2c7a7b;">{intake.email}</td>
        </tr>
        <tr style="background: #e0f2f1;">
            <td style="padding: 10px; font-weight: bold; border: 1px solid #2c7a7b;">Booking ID</td>
            <td style="padding: 10px; border: 1px solid #2c7a7b;">{intake.booking_id or 'Pending'}</td>
        </tr>
        <tr>
            <td style="padding: 10px; font-weight: bold; border: 1px solid #2c7a7b;">Pregnancy</td>
            <td style="padding: 10px; border: 1px solid #2c7a7b;">{intake.pregnancy_stage or 'N/A'}</td>
        </tr>
    </table>
    <p><strong>Medical History:</strong></p>
    <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #2c7a7b; margin: 10px 0;">
        {intake.medical_history or 'No medical history provided'}
    </div>
    <div style="margin-top: 30px; text-align: center;">
        <a href="https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')}/provider-portal" 
           style="background: #2c7a7b; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
            Review in Provider Portal
        </a>
    </div>
    """
    for email in provider_emails:
        send_email(email, subject, body)

def send_confirmation_email(intake):
    """Send confirmation to client"""
    subject = "Your Massage Appointment is Confirmed!"
    body = f"""
    <h2 style="color: #2c7a7b;">Booking Confirmed</h2>
    <p>Dear {intake.client_name},</p>
    <p>Great news! Your massage appointment has been confirmed by our team.</p>
    <div style="background: #e0f2f1; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 5px 0;"><strong>Booking ID:</strong> {intake.booking_id or 'TBD'}</p>
        <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #2c7a7b; font-weight: bold;">✓ Confirmed</span></p>
    </div>
    <h3 style="color: #2c7a7b;">What to Expect</h3>
    <ul>
        <li>Arrive 10 minutes early to complete any remaining paperwork</li>
        <li>Wear comfortable, loose-fitting clothing</li>
        <li>Communicate any areas of concern with your therapist</li>
        <li>Relax and enjoy your rejuvenating experience</li>
    </ul>
    <h3 style="color: #2c7a7b;">Cancellation Policy</h3>
    <p>Please provide 24-hour notice if you need to reschedule or cancel. See our <a href="https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')}/policies" style="color: #2c7a7b;">cancellation policy</a> for details.</p>
    <p style="margin-top: 30px;">We look forward to seeing you soon!</p>
    <p><em>The Tough Love Massage Team</em></p>
    """
    send_email(intake.email, subject, body)

def send_gift_card_email(recipient_email, amount, message, sender_name="A Friend"):
    """Send gift card to recipient"""
    subject = "You've Received a Tough Love Massage Gift Card!"
    body = f"""
    <h2 style="color: #2c7a7b;">Congratulations! 🎁</h2>
    <p>You've received a special gift from {sender_name}!</p>
    <div style="background: linear-gradient(135deg, #2c7a7b 0%, #1a4d4d 100%); color: white; padding: 40px; text-align: center; border-radius: 10px; margin: 30px 0;">
        <h1 style="margin: 0; font-size: 48px; font-family: 'Playfair Display', serif;">Gift Card</h1>
        <p style="font-size: 36px; font-weight: bold; margin: 20px 0;">${amount}</p>
        <p style="font-size: 14px; opacity: 0.9;">Tough Love Massage</p>
    </div>
    {f'<div style="background: #f5f5f5; padding: 20px; border-left: 4px solid #2c7a7b; margin: 20px 0;"><p style="margin: 0;"><strong>Personal Message:</strong></p><p style="margin: 10px 0 0 0; font-style: italic;">"{message}"</p></div>' if message else ''}
    <h3 style="color: #2c7a7b;">How to Redeem</h3>
    <ol>
        <li>Visit our booking page or call us directly</li>
        <li>Mention you have a gift card</li>
        <li>Schedule your luxurious massage experience</li>
    </ol>
    <div style="margin-top: 30px; text-align: center;">
        <a href="https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')}/book" 
           style="background: #2c7a7b; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
            Book Your Appointment
        </a>
    </div>
    <p style="margin-top: 30px; font-size: 12px; color: #666;">Gift cards are valid for one year from the date of purchase and can be used at any of our locations.</p>
    """
    send_email(recipient_email, subject, body)

def send_application_notification(application):
    """Notify admin of new job application"""
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@toughlovemassage.com')
    subject = f"New Job Application: {application.name}"
    body = f"""
    <h2 style="color: #2c7a7b;">New Team Application Received</h2>
    <p>A new candidate has applied to join the Tough Love Massage team!</p>
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <tr style="background: #e0f2f1;">
            <td style="padding: 10px; font-weight: bold; border: 1px solid #2c7a7b;">Name</td>
            <td style="padding: 10px; border: 1px solid #2c7a7b;">{application.name}</td>
        </tr>
        <tr>
            <td style="padding: 10px; font-weight: bold; border: 1px solid #2c7a7b;">Email</td>
            <td style="padding: 10px; border: 1px solid #2c7a7b;">{application.email}</td>
        </tr>
        <tr style="background: #e0f2f1;">
            <td style="padding: 10px; font-weight: bold; border: 1px solid #2c7a7b;">Resume</td>
            <td style="padding: 10px; border: 1px solid #2c7a7b;">
                {f'<a href="https://{os.environ.get("REPLIT_DEV_DOMAIN", "localhost:5000")}{application.resume_url}" style="color: #2c7a7b;">View Resume</a>' if application.resume_url else 'Not provided'}
            </td>
        </tr>
        <tr>
            <td style="padding: 10px; font-weight: bold; border: 1px solid #2c7a7b;">Applied</td>
            <td style="padding: 10px; border: 1px solid #2c7a7b;">{application.submitted_at.strftime('%B %d, %Y at %I:%M %p') if application.submitted_at else 'N/A'}</td>
        </tr>
    </table>
    <p><strong>Experience & Qualifications:</strong></p>
    <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #2c7a7b; margin: 10px 0;">
        {application.experience or 'No experience details provided'}
    </div>
    """
    send_email(admin_email, subject, body)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/location-downtown')
def location_downtown():
    return render_template('location_downtown.html')

@app.route('/location-suburban')
def location_suburban():
    return render_template('location_suburban.html')

@app.route('/gift-cards', methods=['GET', 'POST'])
def gift_cards():
    if request.method == 'POST':
        amount = request.form.get('amount')
        recipient_email = request.form.get('recipient_email')
        message = request.form.get('message', '')
        sender_name = request.form.get('sender_name', 'A Friend')
        
        try:
            YOUR_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN') if os.environ.get('REPLIT_DEPLOYMENT') else os.environ.get('REPLIT_DOMAINS', 'localhost:5000').split(',')[0]
            
            if stripe.api_key and stripe.api_key != 'your_stripe_secret_key_here':
                checkout_session = stripe.checkout.Session.create(
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f'Tough Love Massage Gift Card - ${amount}',
                                'description': f'Gift card for {recipient_email}',
                            },
                            'unit_amount': int(amount) * 100,
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=f'https://{YOUR_DOMAIN}/gift-cards?success=true&amount={amount}&email={recipient_email}&message={message}&sender={sender_name}',
                    cancel_url=f'https://{YOUR_DOMAIN}/gift-cards',
                    metadata={
                        'recipient_email': recipient_email,
                        'message': message,
                        'sender_name': sender_name,
                    }
                )
                return redirect(checkout_session.url, code=303)
            else:
                flash('💳 Demo Mode: Gift card payment simulation (Stripe not configured)', 'info')
                send_gift_card_email(recipient_email, amount, message, sender_name)
                flash(f'🎁 Gift card for ${amount} sent to {recipient_email}!', 'success')
                return redirect(url_for('gift_cards'))
                
        except Exception as e:
            flash(f'❌ Error processing payment: {str(e)}', 'error')
            return redirect(url_for('gift_cards'))
    
    # Handle successful payment return
    if request.args.get('success') == 'true':
        amount = request.args.get('amount')
        recipient_email = request.args.get('email')
        message = request.args.get('message', '')
        sender_name = request.args.get('sender', 'A Friend')
        
        if amount and recipient_email:
            send_gift_card_email(recipient_email, amount, message, sender_name)
            flash(f'🎁 Payment successful! Gift card sent to {recipient_email}', 'success')
    
    return render_template('gift_cards.html')

@app.route('/admin-dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard with reports and management"""
    provider = Provider.query.get(current_user.id)
    if not provider or not provider.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('provider_portal'))
    
    # Get statistics
    total_providers = Provider.query.filter_by(active=True).count()
    total_intakes = Intake.query.count()
    pending_intakes = Intake.query.filter_by(confirmed=False).count()
    total_applications = Application.query.count()
    
    # Recent activity
    recent_intakes = Intake.query.order_by(Intake.created_at.desc()).limit(10).all()
    recent_applications = Application.query.order_by(Application.submitted_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html',
                         total_providers=total_providers,
                         total_intakes=total_intakes,
                         pending_intakes=pending_intakes,
                         total_applications=total_applications,
                         recent_intakes=recent_intakes,
                         recent_applications=recent_applications)

@app.route('/admin/providers')
@login_required
def admin_providers():
    """Manage providers"""
    provider = Provider.query.get(current_user.id)
    if not provider or not provider.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('provider_portal'))
    
    providers = Provider.query.all()
    locations = Location.query.all()
    treatments = Treatment.query.filter_by(active=True).all()
    
    return render_template('admin_providers.html', providers=providers, locations=locations, treatments=treatments)

@app.route('/admin/provider/create', methods=['POST'])
@login_required
def admin_create_provider():
    """Create new provider"""
    provider = Provider.query.get(current_user.id)
    if not provider or not provider.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    username = request.form.get('username')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    location_id = request.form.get('location_id')
    is_admin = request.form.get('is_admin') == 'on'
    
    if Provider.query.filter_by(username=username).first():
        flash('Username already exists', 'error')
        return redirect(url_for('admin_providers'))
    
    new_provider = Provider(
        username=username,
        password_hash=generate_password_hash(password),
        full_name=full_name,
        email=email,
        phone=phone,
        location_id=location_id if location_id else None,
        is_admin=is_admin
    )
    db.session.add(new_provider)
    db.session.commit()
    
    flash(f'✓ Provider {full_name} created successfully', 'success')
    return redirect(url_for('admin_providers'))

@app.route('/admin/provider/<int:provider_id>/update', methods=['POST'])
@login_required
def admin_update_provider(provider_id):
    """Update provider details"""
    admin = Provider.query.get(current_user.id)
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    provider = Provider.query.get_or_404(provider_id)
    
    provider.full_name = request.form.get('full_name')
    provider.email = request.form.get('email')
    provider.phone = request.form.get('phone')
    provider.location_id = request.form.get('location_id') or None
    provider.active = request.form.get('active') == 'on'
    
    db.session.commit()
    
    flash(f'✓ Provider {provider.full_name} updated successfully', 'success')
    return redirect(url_for('admin_providers'))

@app.route('/admin/provider/<int:provider_id>/reset-password', methods=['POST'])
@login_required
def admin_reset_password(provider_id):
    """Reset provider password"""
    admin = Provider.query.get(current_user.id)
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    provider = Provider.query.get_or_404(provider_id)
    new_password = request.form.get('new_password')
    
    provider.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    flash(f'✓ Password reset for {provider.full_name}', 'success')
    return redirect(url_for('admin_providers'))

@app.route('/admin/provider/<int:provider_id>/treatments', methods=['POST'])
@login_required
def admin_assign_treatments(provider_id):
    """Assign treatments to provider"""
    admin = Provider.query.get(current_user.id)
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    provider = Provider.query.get_or_404(provider_id)
    treatment_ids = request.form.getlist('treatment_ids')
    
    # Remove existing assignments
    ProviderTreatment.query.filter_by(provider_id=provider_id).delete()
    
    # Add new assignments
    for treatment_id in treatment_ids:
        pt = ProviderTreatment(provider_id=provider_id, treatment_id=int(treatment_id))
        db.session.add(pt)
    
    db.session.commit()
    
    flash(f'✓ Treatments updated for {provider.full_name}', 'success')
    return redirect(url_for('admin_providers'))

@app.route('/admin/locations')
@login_required
def admin_locations():
    """Manage locations"""
    provider = Provider.query.get(current_user.id)
    if not provider or not provider.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('provider_portal'))
    
    locations = Location.query.all()
    return render_template('admin_locations.html', locations=locations)

@app.route('/admin/location/create', methods=['POST'])
@login_required
def admin_create_location():
    """Create new location"""
    provider = Provider.query.get(current_user.id)
    if not provider or not provider.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    location = Location(
        name=request.form.get('name'),
        address=request.form.get('address'),
        phone=request.form.get('phone'),
        hours=request.form.get('hours')
    )
    db.session.add(location)
    db.session.commit()
    
    flash(f'✓ Location {location.name} created', 'success')
    return redirect(url_for('admin_locations'))

@app.route('/admin/treatments')
@login_required
def admin_treatments():
    """Manage treatments"""
    provider = Provider.query.get(current_user.id)
    if not provider or not provider.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('provider_portal'))
    
    treatments = Treatment.query.all()
    return render_template('admin_treatments.html', treatments=treatments)

@app.route('/admin/treatment/create', methods=['POST'])
@login_required
def admin_create_treatment():
    """Create new treatment"""
    provider = Provider.query.get(current_user.id)
    if not provider or not provider.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    treatment = Treatment(
        name=request.form.get('name'),
        description=request.form.get('description'),
        duration_minutes=int(request.form.get('duration_minutes', 60)),
        price=float(request.form.get('price', 0))
    )
    db.session.add(treatment)
    db.session.commit()
    
    flash(f'✓ Treatment {treatment.name} created', 'success')
    return redirect(url_for('admin_treatments'))

@app.route('/admin/reports')
@login_required
def admin_reports():
    """View detailed reports"""
    provider = Provider.query.get(current_user.id)
    if not provider or not provider.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('provider_portal'))
    
    from sqlalchemy import func
    from datetime import timedelta
    
    # Bookings by provider
    bookings_by_provider = db.session.query(
        Provider.full_name,
        func.count(Intake.id).label('count')
    ).join(Intake, Provider.id == Intake.assigned_provider_id, isouter=True)\
     .group_by(Provider.full_name).all()
    
    # Bookings by status
    confirmed_count = Intake.query.filter_by(confirmed=True).count()
    pending_count = Intake.query.filter_by(confirmed=False).count()
    
    # Recent 30 days activity
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_bookings = Intake.query.filter(Intake.created_at >= thirty_days_ago).count()
    
    return render_template('admin_reports.html',
                         bookings_by_provider=bookings_by_provider,
                         confirmed_count=confirmed_count,
                         pending_count=pending_count,
                         recent_bookings=recent_bookings)

@app.route('/provider/availability')
@login_required
def provider_availability():
    """Manage provider availability"""
    provider = Provider.query.get(current_user.id)
    availabilities = ProviderAvailability.query.filter_by(provider_id=current_user.id).all()
    
    return render_template('provider_availability.html', provider=provider, availabilities=availabilities)

@app.route('/provider/availability/add', methods=['POST'])
@login_required
def provider_add_availability():
    """Add availability slot"""
    from datetime import datetime
    
    day_of_week = int(request.form.get('day_of_week'))
    start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
    end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
    
    availability = ProviderAvailability(
        provider_id=current_user.id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time
    )
    db.session.add(availability)
    db.session.commit()
    
    flash('✓ Availability added', 'success')
    return redirect(url_for('provider_availability'))

@app.route('/provider/availability/<int:availability_id>/delete', methods=['POST'])
@login_required
def provider_delete_availability(availability_id):
    """Delete availability slot"""
    availability = ProviderAvailability.query.get_or_404(availability_id)
    
    if availability.provider_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('provider_availability'))
    
    db.session.delete(availability)
    db.session.commit()
    
    flash('✓ Availability deleted', 'success')
    return redirect(url_for('provider_availability'))

@app.route('/provider/preferences', methods=['GET', 'POST'])
@login_required
def provider_preferences():
    """Manage booking preferences"""
    provider = Provider.query.get(current_user.id)
    treatments = Treatment.query.filter_by(active=True).all()
    daily_limits = ProviderDailyLimit.query.filter_by(provider_id=current_user.id).all()
    
    if request.method == 'POST':
        # Update buffer time
        provider.buffer_time_minutes = int(request.form.get('buffer_time_minutes', 15))
        db.session.commit()
        
        flash('✓ Preferences updated', 'success')
        return redirect(url_for('provider_preferences'))
    
    return render_template('provider_preferences.html', 
                         provider=provider, 
                         treatments=treatments,
                         daily_limits=daily_limits)

@app.route('/provider/daily-limit/set', methods=['POST'])
@login_required
def provider_set_daily_limit():
    """Set daily limit for a treatment"""
    treatment_id = int(request.form.get('treatment_id'))
    max_per_day = int(request.form.get('max_per_day'))
    
    # Check if limit already exists
    existing = ProviderDailyLimit.query.filter_by(
        provider_id=current_user.id,
        treatment_id=treatment_id
    ).first()
    
    if existing:
        existing.max_per_day = max_per_day
    else:
        limit = ProviderDailyLimit(
            provider_id=current_user.id,
            treatment_id=treatment_id,
            max_per_day=max_per_day
        )
        db.session.add(limit)
    
    db.session.commit()
    
    flash('✓ Daily limit updated', 'success')
    return redirect(url_for('provider_preferences'))

@app.route('/provider/client-notes/<string:client_email>')
@login_required
def provider_view_client_notes(client_email):
    """View/edit client notes"""
    note = ClientNote.query.filter_by(
        provider_id=current_user.id,
        client_email=client_email
    ).first()
    
    client_intakes = Intake.query.filter_by(email=client_email).all()
    
    return render_template('provider_client_notes.html', 
                         client_email=client_email,
                         note=note,
                         client_intakes=client_intakes)

@app.route('/provider/client-notes/save', methods=['POST'])
@login_required
def provider_save_client_notes():
    """Save client notes"""
    client_email = request.form.get('client_email')
    notes = request.form.get('notes')
    
    existing = ClientNote.query.filter_by(
        provider_id=current_user.id,
        client_email=client_email
    ).first()
    
    if existing:
        existing.notes = notes
        existing.updated_at = datetime.utcnow()
    else:
        note = ClientNote(
            provider_id=current_user.id,
            client_email=client_email,
            notes=notes
        )
        db.session.add(note)
    
    db.session.commit()
    
    flash('✓ Client notes saved', 'success')
    return redirect(url_for('provider_view_client_notes', client_email=client_email))

@app.route('/provider/intake/<int:intake_id>/add-note', methods=['POST'])
@login_required
def provider_add_intake_note(intake_id):
    """Add note to specific appointment"""
    intake = Intake.query.get_or_404(intake_id)
    note = request.form.get('note')
    
    intake.provider_notes = note
    db.session.commit()
    
    flash('✓ Appointment note added', 'success')
    return redirect(url_for('provider_portal'))

@app.route('/join-team', methods=['GET', 'POST'])
def join_team():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        experience = request.form.get('experience')
        resume_url = ''
        
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                resume_url = f'/static/uploads/{filename}'
        
        application = Application(
            name=name,
            email=email,
            experience=experience,
            resume_url=resume_url
        )
        db.session.add(application)
        db.session.commit()
        
        # Notify admin
        send_application_notification(application)
        
        # Send confirmation to applicant
        applicant_body = f"""
        <h2 style="color: #2c7a7b;">Thank You for Your Application!</h2>
        <p>Dear {name},</p>
        <p>We've received your application to join the Tough Love Massage team and are excited to review your qualifications.</p>
        <div style="background: #e0f2f1; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>Application Status:</strong> <span style="color: #2c7a7b;">Under Review</span></p>
            <p style="margin: 5px 0;"><strong>Submitted:</strong> {application.submitted_at.strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        <h3 style="color: #2c7a7b;">What Happens Next?</h3>
        <ol>
            <li>Our team will carefully review your application and resume</li>
            <li>If your qualifications match our current needs, we'll reach out within 5-7 business days</li>
            <li>Selected candidates will be invited for an interview</li>
        </ol>
        <p>Thank you for your interest in joining our team of skilled massage therapists!</p>
        <p><em>The Tough Love Massage Team</em></p>
        """
        send_email(email, 'Application Received - Tough Love Massage', applicant_body)
        
        flash('✓ Thank you for your application! We will review it and get back to you soon.', 'success')
        return redirect(url_for('join_team'))
    
    return render_template('join_team.html')

@app.route('/policies')
def policies():
    return render_template('policies.html')

@app.route('/book')
def book():
    return render_template('book.html')

@app.route('/provider-portal')
@login_required
def provider_portal():
    provider = Provider.query.get(current_user.id)
    unconfirmed_intakes = Intake.query.filter_by(confirmed=False).all()
    return render_template('provider_portal.html', intakes=unconfirmed_intakes, provider=provider)

@app.route('/confirm-intake/<int:intake_id>')
@login_required
def confirm_intake(intake_id):
    intake = Intake.query.get_or_404(intake_id)
    intake.confirmed = True
    db.session.commit()
    
    send_confirmation_email(intake)
    
    flash(f'✓ Intake confirmed for {intake.client_name} and notification email sent!', 'success')
    return redirect(url_for('provider_portal'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        provider = Provider.query.filter_by(username=username).first()
        
        if provider and check_password_hash(provider.password_hash, password):
            user = User(provider.id, provider.username)
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('provider_portal'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/webhook/fullslate', methods=['POST'])
def fullslate_webhook():
    """Handle incoming bookings from FullSlate"""
    try:
        data = request.json
        intake = Intake(
            client_name=data.get('client_name'),
            email=data.get('email'),
            medical_history=data.get('medical_history', ''),
            pregnancy_stage=data.get('pregnancy_stage'),
            booking_id=data.get('booking_id'),
            confirmed=False
        )
        db.session.add(intake)
        db.session.commit()
        
        # Send notifications to all providers
        send_booking_notification(intake)
        
        # Send acknowledgment to client
        client_body = f"""
        <h2 style="color: #2c7a7b;">Booking Received!</h2>
        <p>Dear {intake.client_name},</p>
        <p>Thank you for choosing Tough Love Massage. We've received your booking request and intake form.</p>
        <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
            <p style="margin: 0;"><strong>⏳ Pending Confirmation</strong></p>
            <p style="margin: 10px 0 0 0;">Our team is reviewing your information and will confirm your appointment shortly.</p>
        </div>
        <p>You'll receive a confirmation email once your appointment has been reviewed and approved.</p>
        <p>If you have any questions, please don't hesitate to contact us.</p>
        <p><em>The Tough Love Massage Team</em></p>
        """
        send_email(intake.email, 'Booking Request Received - Tough Love Massage', client_body)
        
        return jsonify({'status': 'success', 'intake_id': intake.id}), 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

with app.app_context():
    db.create_all()
    
    # Initialize default locations
    if Location.query.count() == 0:
        downtown = Location(
            name="Downtown Studio",
            address="123 City Street, Downtown",
            phone="(123) 456-7890",
            hours="Mon-Fri 9AM-8PM, Sat 10AM-6PM"
        )
        suburban = Location(
            name="Suburban Retreat",
            address="456 Peaceful Lane, Suburbs",
            phone="(123) 456-7891",
            hours="Mon-Sat 10AM-7PM, Sun 12PM-5PM"
        )
        db.session.add(downtown)
        db.session.add(suburban)
        db.session.commit()
        print("✓ Created default locations")
    
    # Initialize default treatments
    if Treatment.query.count() == 0:
        treatments_data = [
            {"name": "Swedish Massage", "description": "Classic relaxation massage", "duration": 60, "price": 120},
            {"name": "Deep Tissue Massage", "description": "Therapeutic deep muscle work", "duration": 60, "price": 130},
            {"name": "Hot Stone Massage", "description": "Heated stones for deep relaxation", "duration": 90, "price": 150},
            {"name": "Prenatal Massage", "description": "Specialized care for expecting mothers", "duration": 60, "price": 125},
        ]
        for t_data in treatments_data:
            treatment = Treatment(
                name=t_data["name"],
                description=t_data["description"],
                duration_minutes=t_data["duration"],
                price=t_data["price"]
            )
            db.session.add(treatment)
        db.session.commit()
        print("✓ Created default treatments")
    
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if admin_email and admin_password and Provider.query.count() == 0:
        initial_provider = Provider(
            username=admin_email,
            password_hash=generate_password_hash(admin_password),
            full_name="Administrator",
            email=admin_email,
            is_admin=True
        )
        db.session.add(initial_provider)
        db.session.commit()
        print(f"✓ Created initial admin account: {admin_email}")
        print("⚠ IMPORTANT: Change your password immediately after first login!")
    elif Provider.query.count() == 0:
        print("\n" + "="*70)
        print("⚠ WARNING: No provider accounts exist!")
        print("To create your first provider account, set these environment variables:")
        print("  ADMIN_EMAIL=your-email@example.com")
        print("  ADMIN_PASSWORD=your-secure-password")
        print("Then restart the application.")
        print("="*70 + "\n")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
