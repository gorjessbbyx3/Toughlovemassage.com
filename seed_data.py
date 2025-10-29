"""
Data seeding script for Tough Love Massage Provider Portal
Creates sample clients, appointments, SOAP notes, medical alerts, and performance metrics
Also migrates any existing intakes that don't have associated clients
"""
import os
import sys
from datetime import datetime, date, time, timedelta
from app import app, db
from models import (Client, Intake, Appointment, Treatment, SOAPNote, 
                    MedicalAlert, PerformanceMetric, Provider)

def migrate_existing_intakes():
    """Migrate existing intakes to have client associations"""
    print("\n=== MIGRATING EXISTING INTAKES ===")
    intakes_without_client = Intake.query.filter_by(client_id=None).all()
    
    if not intakes_without_client:
        print("✓ All intakes already have client associations")
        return
    
    print(f"Found {len(intakes_without_client)} intakes without client associations")
    
    for intake in intakes_without_client:
        # Use old client_name and email fields if they exist
        client_name = getattr(intake, 'client_name', None)
        client_email = getattr(intake, 'email', None)
        
        if not client_name or not client_email:
            print(f"  ⚠ Skipping intake {intake.id} - missing name or email")
            continue
        
        # Find or create client
        client = Client.query.filter_by(email=client_email).first()
        if not client:
            client = Client(
                name=client_name,
                email=client_email,
                phone='',
                first_visit=intake.created_at or datetime.now()
            )
            db.session.add(client)
            print(f"  + Created client: {client_name}")
        
        intake.client_id = client.id
        print(f"  ✓ Linked intake {intake.id} to client {client.name}")
    
    db.session.commit()
    print(f"✓ Migration complete: {len(intakes_without_client)} intakes migrated")

def seed_sample_data(provider_id=1):
    """Create sample data for testing the provider portal"""
    print("\n=== SEEDING SAMPLE DATA ===")
    
    # Check if provider exists
    provider = Provider.query.get(provider_id)
    if not provider:
        print(f"✗ Provider with ID {provider_id} not found")
        print("  Please create a provider account first by setting ADMIN_EMAIL and ADMIN_PASSWORD")
        return
    
    print(f"✓ Found provider: {provider.username}")
    
    # Create sample treatments
    print("\n--- Creating Treatments ---")
    treatments = [
        Treatment(name='60-Minute Therapeutic Massage', duration_minutes=60, price=95.00, description='Full body relaxation'),
        Treatment(name='90-Minute Deep Tissue', duration_minutes=90, price=125.00, description='Intense muscle work'),
        Treatment(name='30-Minute Focused Session', duration_minutes=30, price=55.00, description='Target specific areas'),
        Treatment(name='Prenatal Massage', duration_minutes=60, price=100.00, description='Safe pregnancy massage'),
        Treatment(name='Thai Massage', duration_minutes=90, price=140.00, description='Traditional Thai techniques'),
    ]
    
    for treatment in treatments:
        existing = Treatment.query.filter_by(name=treatment.name).first()
        if not existing:
            db.session.add(treatment)
            print(f"  + Created treatment: {treatment.name}")
    
    db.session.commit()
    treatments = Treatment.query.all()
    
    # Create sample clients
    print("\n--- Creating Sample Clients ---")
    sample_clients = [
        {
            'name': 'Sarah Johnson',
            'email': 'sarah.j@email.com',
            'phone': '617-555-0101',
            'preferred_pressure': 'medium',
            'focus_areas': 'lower back, shoulders',
            'notes': 'Prefers quiet environment, no music'
        },
        {
            'name': 'Michael Chen',
            'email': 'michael.chen@email.com',
            'phone': '617-555-0102',
            'preferred_pressure': 'firm',
            'focus_areas': 'neck, upper back',
            'notes': 'Marathon runner, tight IT bands'
        },
        {
            'name': 'Emily Rodriguez',
            'email': 'emily.r@email.com',
            'phone': '617-555-0103',
            'preferred_pressure': 'light',
            'focus_areas': 'full body relaxation',
            'notes': 'Pregnant (2nd trimester)'
        },
        {
            'name': 'David Thompson',
            'email': 'david.t@email.com',
            'phone': '617-555-0104',
            'preferred_pressure': 'medium-firm',
            'focus_areas': 'shoulders, legs',
            'notes': 'Office worker, sitting pain'
        },
        {
            'name': 'Lisa Park',
            'email': 'lisa.park@email.com',
            'phone': '617-555-0105',
            'preferred_pressure': 'medium',
            'focus_areas': 'full body',
            'notes': 'Monthly regular client'
        }
    ]
    
    clients = []
    for client_data in sample_clients:
        existing = Client.query.filter_by(email=client_data['email']).first()
        if existing:
            clients.append(existing)
            print(f"  ✓ Client already exists: {existing.name}")
        else:
            client = Client(
                name=client_data['name'],
                email=client_data['email'],
                phone=client_data['phone'],
                preferred_pressure=client_data['preferred_pressure'],
                focus_areas=client_data['focus_areas'],
                notes=client_data['notes'],
                first_visit=datetime.now() - timedelta(days=180),
                total_visits=5,
                lifetime_value=475.00
            )
            db.session.add(client)
            clients.append(client)
            print(f"  + Created client: {client.name}")
    
    db.session.commit()
    
    # Create medical alerts
    print("\n--- Creating Medical Alerts ---")
    medical_alerts = [
        {
            'client': clients[2],  # Emily (pregnant)
            'alert_type': 'Pregnancy',
            'severity': 'high',
            'description': 'Second trimester pregnancy - use pregnancy pillow, avoid deep abdominal work'
        },
        {
            'client': clients[1],  # Michael
            'alert_type': 'Injury',
            'severity': 'medium',
            'description': 'Recent hamstring strain (2 weeks ago) - gentle stretching only'
        }
    ]
    
    for alert_data in medical_alerts:
        alert = MedicalAlert(
            client_id=alert_data['client'].id,
            alert_type=alert_data['alert_type'],
            severity=alert_data['severity'],
            description=alert_data['description'],
            is_active=True,
            created_at=datetime.now()
        )
        db.session.add(alert)
        print(f"  + Created alert for {alert_data['client'].name}: {alert_data['alert_type']}")
    
    db.session.commit()
    
    # Create appointments
    print("\n--- Creating Appointments ---")
    today = date.today()
    
    appointments_data = [
        # Today's appointments
        {'date': today, 'time': time(9, 0), 'client': clients[0], 'treatment': treatments[0], 'status': 'confirmed'},
        {'date': today, 'time': time(11, 0), 'client': clients[2], 'treatment': treatments[3], 'status': 'confirmed'},
        {'date': today, 'time': time(14, 0), 'client': clients[1], 'treatment': treatments[1], 'status': 'scheduled'},
        
        # Tomorrow
        {'date': today + timedelta(days=1), 'time': time(10, 0), 'client': clients[4], 'treatment': treatments[0], 'status': 'confirmed'},
        {'date': today + timedelta(days=1), 'time': time(15, 0), 'client': clients[3], 'treatment': treatments[2], 'status': 'scheduled'},
        
        # Next week
        {'date': today + timedelta(days=5), 'time': time(9, 30), 'client': clients[0], 'treatment': treatments[0], 'status': 'scheduled'},
        {'date': today + timedelta(days=7), 'time': time(13, 0), 'client': clients[1], 'treatment': treatments[1], 'status': 'scheduled'},
        
        # Past completed appointments
        {'date': today - timedelta(days=1), 'time': time(10, 0), 'client': clients[4], 'treatment': treatments[0], 'status': 'completed'},
        {'date': today - timedelta(days=3), 'time': time(14, 0), 'client': clients[0], 'treatment': treatments[0], 'status': 'completed'},
        {'date': today - timedelta(days=7), 'time': time(11, 0), 'client': clients[3], 'treatment': treatments[2], 'status': 'completed'},
    ]
    
    for apt_data in appointments_data:
        appointment = Appointment(
            client_id=apt_data['client'].id,
            provider_id=provider_id,
            treatment_id=apt_data['treatment'].id,
            appointment_date=apt_data['date'],
            start_time=apt_data['time'],
            duration_minutes=apt_data['treatment'].duration_minutes,
            status=apt_data['status'],
            created_at=datetime.now() - timedelta(days=30)
        )
        db.session.add(appointment)
        print(f"  + Appointment: {apt_data['client'].name} on {apt_data['date']} at {apt_data['time']}")
    
    db.session.commit()
    
    # Create SOAP notes for completed appointments
    print("\n--- Creating SOAP Notes ---")
    completed_appointments = Appointment.query.filter_by(status='completed', provider_id=provider_id).limit(5).all()
    
    soap_examples = [
        {
            'subjective': 'Client reports chronic lower back pain, worse in mornings. Pain level 7/10. Sitting at desk 8 hours/day.',
            'objective': 'Moderate tension in lumbar paraspinals, reduced ROM in forward flexion. Trigger points identified in QL bilaterally.',
            'assessment': 'Chronic mechanical low back pain, likely postural. Good response to deep tissue work. Client tolerated pressure well.',
            'plan': 'Continue biweekly sessions. Recommended stretching routine. Consider adding hip flexor work next session.',
            'pain_before': 7,
            'pain_after': 3
        },
        {
            'subjective': 'Client feeling stressed, tight shoulders and neck. Headaches 2-3x/week. Sleep quality poor.',
            'objective': 'Significant tension in upper traps, levator scapulae, and SCM. Limited cervical rotation bilaterally.',
            'assessment': 'Tension headaches, stress-related myofascial pain. Client very responsive to myofascial release techniques.',
            'plan': 'Weekly sessions recommended. Taught self-massage for SCM. Suggested stress management resources.',
            'pain_before': 6,
            'pain_after': 2
        },
        {
            'subjective': 'Runner training for marathon. No acute pain, seeking maintenance and recovery support.',
            'objective': 'Moderate tightness in hamstrings, IT bands, and calves. Good overall muscle tone. No adhesions noted.',
            'assessment': 'Sports massage for maintenance. Preventive care appropriate. Client has good body awareness.',
            'plan': 'Continue every 2 weeks during training. Focus on legs, add hip flexors as needed.',
            'pain_before': 2,
            'pain_after': 1
        }
    ]
    
    for i, apt in enumerate(completed_appointments[:3]):
        if i < len(soap_examples):
            example = soap_examples[i]
            soap_note = SOAPNote(
                client_id=apt.client_id,
                provider_id=provider_id,
                appointment_id=apt.id,
                subjective=example['subjective'],
                objective=example['objective'],
                assessment=example['assessment'],
                plan=example['plan'],
                pain_level_before=example['pain_before'],
                pain_level_after=example['pain_after'],
                session_duration=apt.duration_minutes,
                created_at=apt.appointment_date
            )
            db.session.add(soap_note)
            print(f"  + SOAP note for {apt.client.name} ({apt.appointment_date})")
    
    db.session.commit()
    
    # Create performance metrics
    print("\n--- Creating Performance Metrics ---")
    for i in range(30):
        metric_date = today - timedelta(days=i)
        sessions = 3 + (i % 5)  # 3-7 sessions per day
        revenue = sessions * 100.00  # Average $100 per session
        
        metric = PerformanceMetric(
            provider_id=provider_id,
            metric_date=metric_date,
            sessions_completed=sessions,
            total_revenue=revenue,
            avg_session_duration=65,
            client_satisfaction=4.5 + (i % 5) * 0.1,
            new_clients=1 if i % 7 == 0 else 0,
            returning_clients=sessions - (1 if i % 7 == 0 else 0)
        )
        db.session.add(metric)
    
    print(f"  + Created 30 days of performance metrics")
    db.session.commit()
    
    print("\n" + "="*50)
    print("✓ SAMPLE DATA SEEDING COMPLETE!")
    print("="*50)
    print("\nSummary:")
    print(f"  - Clients: {len(clients)}")
    print(f"  - Treatments: {len(treatments)}")
    print(f"  - Appointments: {len(appointments_data)}")
    print(f"  - SOAP Notes: {min(3, len(completed_appointments))}")
    print(f"  - Medical Alerts: {len(medical_alerts)}")
    print(f"  - Performance Metrics: 30 days")
    print(f"\nYou can now view the populated dashboard at /provider-portal")

def main():
    """Main execution"""
    with app.app_context():
        print("\n" + "="*50)
        print("TOUGH LOVE MASSAGE - DATA SEEDING SCRIPT")
        print("="*50)
        
        # First migrate any existing intakes
        migrate_existing_intakes()
        
        # Then seed sample data
        response = input("\nDo you want to seed sample data? (yes/no): ").lower()
        if response in ['yes', 'y']:
            provider_id = input("Enter provider ID (default: 1): ").strip()
            provider_id = int(provider_id) if provider_id else 1
            seed_sample_data(provider_id)
        else:
            print("Skipping sample data seeding")
        
        print("\n✓ Script complete!")

if __name__ == '__main__':
    main()
