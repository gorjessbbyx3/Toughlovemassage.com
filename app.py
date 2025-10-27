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
    try:
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_username = os.environ.get('SMTP_USERNAME', 'no-reply@toughlovemassage.com')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        if not smtp_password:
            print(f"Email would be sent to {to_email}: {subject}")
            return True
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

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
        
        try:
            YOUR_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN') if os.environ.get('REPLIT_DEPLOYMENT') else os.environ.get('REPLIT_DOMAINS', 'localhost:5000').split(',')[0]
            
            if stripe.api_key and stripe.api_key != 'your_stripe_secret_key_here':
                checkout_session = stripe.checkout.Session.create(
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f'Tough Love Massage Gift Card - ${amount}',
                            },
                            'unit_amount': int(amount) * 100,
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=f'https://{YOUR_DOMAIN}/gift-cards?success=true',
                    cancel_url=f'https://{YOUR_DOMAIN}/gift-cards',
                )
                return redirect(checkout_session.url, code=303)
            else:
                flash('Gift card payment simulation (Stripe not configured)', 'info')
                email_body = f"""
                <h2>Congratulations! You've received a gift card!</h2>
                <p>Amount: ${amount}</p>
                <p>Message: {message}</p>
                <p>Redeem at Tough Love Massage.</p>
                """
                send_email(recipient_email, 'Your Tough Love Massage Gift Card', email_body)
                flash(f'Gift card for ${amount} sent to {recipient_email}!', 'success')
                return redirect(url_for('gift_cards'))
                
        except Exception as e:
            flash(f'Error processing payment: {str(e)}', 'error')
            return redirect(url_for('gift_cards'))
    
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
        
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@toughlovemassage.com')
        email_body = f"""
        <h2>New Team Application</h2>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Experience:</strong> {experience}</p>
        <p><strong>Resume:</strong> {resume_url if resume_url else 'Not provided'}</p>
        """
        send_email(admin_email, 'New Job Application', email_body)
        
        flash('Thank you for your application! We will review it and get back to you soon.', 'success')
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
    
    email_body = f"""
    <h2>Booking Confirmation</h2>
    <p>Dear {intake.client_name},</p>
    <p>Your booking has been confirmed by our team!</p>
    <p>We look forward to seeing you at Tough Love Massage.</p>
    """
    send_email(intake.email, 'Booking Confirmed', email_body)
    
    flash('Intake confirmed and client notified!', 'success')
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
    try:
        data = request.json
        intake = Intake(
            client_name=data.get('client_name'),
            email=data.get('email'),
            medical_history=data.get('medical_history'),
            pregnancy_stage=data.get('pregnancy_stage'),
            booking_id=data.get('booking_id'),
            confirmed=False
        )
        db.session.add(intake)
        db.session.commit()
        
        provider_emails = [p.username for p in Provider.query.all()]
        for email in provider_emails:
            send_email(email, 'New Booking Received', 
                      f'New booking from {intake.client_name}. Please review in the provider portal.')
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
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
