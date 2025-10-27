import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Intake, Provider, Application
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


@app.route('/test-intake', methods=['GET', 'POST'])
@login_required
def test_intake():
    """Create a test intake for demonstration purposes"""
    if request.method == 'POST':
        test_intake = Intake(
            client_name=request.form.get('client_name', 'Test Client'),
            email=request.form.get('email', 'test@example.com'),
            medical_history=request.form.get('medical_history', 'No known medical conditions'),
            pregnancy_stage=request.form.get('pregnancy_stage'),
            booking_id=f'TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            confirmed=False
        )
        db.session.add(test_intake)
        db.session.commit()
        
        send_booking_notification(test_intake)
        
        flash(f'✓ Test intake created for {test_intake.client_name}', 'success')
        return redirect(url_for('provider_portal'))
    
    return render_template('test_intake.html')


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
    unconfirmed_intakes = Intake.query.filter_by(confirmed=False).all()
    return render_template('provider_portal.html', intakes=unconfirmed_intakes)

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
    
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if admin_email and admin_password and Provider.query.count() == 0:
        initial_provider = Provider(
            username=admin_email,
            password_hash=generate_password_hash(admin_password)
        )
        db.session.add(initial_provider)
        db.session.commit()
        print(f"✓ Created initial provider account: {admin_email}")
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
