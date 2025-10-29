
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, time

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    
    preferred_pressure = db.Column(db.String(50))
    focus_areas = db.Column(db.Text)
    allergies = db.Column(db.Text)
    music_preference = db.Column(db.String(100))
    temperature_preference = db.Column(db.String(50))
    aromatherapy_preference = db.Column(db.String(100))
    
    first_visit = db.Column(db.Date)
    last_visit = db.Column(db.Date)
    visit_count = db.Column(db.Integer, default=0)
    lifetime_value = db.Column(db.Float, default=0.0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    intakes = db.relationship('Intake', back_populates='client', cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', back_populates='client', cascade='all, delete-orphan')
    soap_notes = db.relationship('SOAPNote', back_populates='client', cascade='all, delete-orphan')
    medical_alerts = db.relationship('MedicalAlert', back_populates='client', cascade='all, delete-orphan')
    notes = db.relationship('ClientNote', back_populates='client', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Client {self.name}>'

class Intake(db.Model):
    __tablename__ = 'intakes'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    medical_history = db.Column(db.Text)
    pregnancy_stage = db.Column(db.String(100))
    booking_id = db.Column(db.String(100))
    confirmed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    provider_notes = db.Column(db.Text)
    assigned_provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
    
    client = db.relationship('Client', back_populates='intakes')
    assigned_provider = db.relationship('Provider', back_populates='intakes')
    
    def __repr__(self):
        return f'<Intake for Client {self.client_id}>'

class Provider(db.Model):
    __tablename__ = 'providers'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Booking preferences
    buffer_time_minutes = db.Column(db.Integer, default=15)  # Time between appointments
    
    location = db.relationship('Location', back_populates='providers')
    treatments = db.relationship('ProviderTreatment', back_populates='provider', cascade='all, delete-orphan')
    availabilities = db.relationship('ProviderAvailability', back_populates='provider', cascade='all, delete-orphan')
    daily_limits = db.relationship('ProviderDailyLimit', back_populates='provider', cascade='all, delete-orphan')
    intakes = db.relationship('Intake', back_populates='assigned_provider')
    client_notes = db.relationship('ClientNote', foreign_keys='ClientNote.provider_id', back_populates='provider', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Provider {self.username}>'

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500))
    phone = db.Column(db.String(20))
    hours = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    
    providers = db.relationship('Provider', back_populates='location')
    
    def __repr__(self):
        return f'<Location {self.name}>'

class Treatment(db.Model):
    __tablename__ = 'treatments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, default=60)
    price = db.Column(db.Float)
    active = db.Column(db.Boolean, default=True)
    
    providers = db.relationship('ProviderTreatment', back_populates='treatment')
    
    def __repr__(self):
        return f'<Treatment {self.name}>'

class ProviderTreatment(db.Model):
    __tablename__ = 'provider_treatments'
    
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    treatment_id = db.Column(db.Integer, db.ForeignKey('treatments.id'), nullable=False)
    
    provider = db.relationship('Provider', back_populates='treatments')
    treatment = db.relationship('Treatment', back_populates='providers')
    
    def __repr__(self):
        return f'<ProviderTreatment P{self.provider_id} T{self.treatment_id}>'

class ProviderAvailability(db.Model):
    __tablename__ = 'provider_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    active = db.Column(db.Boolean, default=True)
    
    provider = db.relationship('Provider', back_populates='availabilities')
    
    def __repr__(self):
        return f'<Availability P{self.provider_id} Day{self.day_of_week}>'

class ProviderDailyLimit(db.Model):
    __tablename__ = 'provider_daily_limits'
    
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    treatment_id = db.Column(db.Integer, db.ForeignKey('treatments.id'), nullable=False)
    max_per_day = db.Column(db.Integer, nullable=False)
    
    provider = db.relationship('Provider', back_populates='daily_limits')
    treatment = db.relationship('Treatment')
    
    def __repr__(self):
        return f'<DailyLimit P{self.provider_id} T{self.treatment_id}>'

class ClientNote(db.Model):
    __tablename__ = 'client_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
    
    provider = db.relationship('Provider', foreign_keys=[provider_id], back_populates='client_notes')
    client = db.relationship('Client', back_populates='notes')
    created_by = db.relationship('Provider', foreign_keys=[created_by_provider_id])
    updated_by = db.relationship('Provider', foreign_keys=[updated_by_provider_id])
    
    def __repr__(self):
        return f'<ClientNote for Client {self.client_id}>'

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    experience = db.Column(db.Text)
    resume_url = db.Column(db.String(500))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Application {self.name}>'

class Appointment(db.Model):
    __tablename__ = 'appointments'
    __table_args__ = (
        db.UniqueConstraint('provider_id', 'appointment_date', 'start_time', name='_provider_datetime_uc'),
        db.Index('idx_appointment_date_status', 'appointment_date', 'status'),
        db.Index('idx_appointment_provider_date', 'provider_id', 'appointment_date'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    treatment_id = db.Column(db.Integer, db.ForeignKey('treatments.id'))
    appointment_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    status = db.Column(db.String(50), default='scheduled')
    notes = db.Column(db.Text)
    fullslate_booking_id = db.Column(db.String(100), unique=True)
    confirmed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
    
    provider = db.relationship('Provider', foreign_keys=[provider_id], backref='appointments')
    client = db.relationship('Client', back_populates='appointments')
    treatment = db.relationship('Treatment')
    soap_note = db.relationship('SOAPNote', back_populates='appointment', uselist=False, cascade='all, delete-orphan')
    created_by = db.relationship('Provider', foreign_keys=[created_by_provider_id])
    updated_by = db.relationship('Provider', foreign_keys=[updated_by_provider_id])
    
    def __repr__(self):
        return f'<Appointment for Client {self.client_id} on {self.appointment_date}>'

class SOAPNote(db.Model):
    __tablename__ = 'soap_notes'
    __table_args__ = (
        db.UniqueConstraint('appointment_id', name='_one_soap_per_appointment'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, unique=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    subjective = db.Column(db.Text)
    objective = db.Column(db.Text)
    assessment = db.Column(db.Text)
    plan = db.Column(db.Text)
    
    pain_level_before = db.Column(db.Integer)
    pain_level_after = db.Column(db.Integer)
    areas_worked = db.Column(db.Text)
    techniques_used = db.Column(db.Text)
    pressure_preference = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
    is_locked = db.Column(db.Boolean, default=False)
    
    appointment = db.relationship('Appointment', back_populates='soap_note')
    provider = db.relationship('Provider', foreign_keys=[provider_id], backref='soap_notes')
    client = db.relationship('Client', back_populates='soap_notes')
    created_by = db.relationship('Provider', foreign_keys=[created_by_provider_id])
    updated_by = db.relationship('Provider', foreign_keys=[updated_by_provider_id])
    
    def __repr__(self):
        return f'<SOAPNote for Client {self.client_id}>'

class MedicalAlert(db.Model):
    __tablename__ = 'medical_alerts'
    __table_args__ = (
        db.Index('idx_alert_client_active', 'client_id', 'is_active'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default='medium')
    description = db.Column(db.Text, nullable=False)
    contraindications = db.Column(db.Text)
    special_instructions = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
    
    client = db.relationship('Client', back_populates='medical_alerts')
    created_by = db.relationship('Provider', foreign_keys=[created_by_provider_id], backref='created_alerts')
    updated_by = db.relationship('Provider', foreign_keys=[updated_by_provider_id])
    
    def __repr__(self):
        return f'<MedicalAlert {self.alert_type} for Client {self.client_id}>'

class PerformanceMetric(db.Model):
    __tablename__ = 'performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'), nullable=False)
    metric_date = db.Column(db.Date, nullable=False)
    
    sessions_completed = db.Column(db.Integer, default=0)
    sessions_cancelled = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Float, default=0.0)
    
    new_clients = db.Column(db.Integer, default=0)
    returning_clients = db.Column(db.Integer, default=0)
    
    average_rating = db.Column(db.Float)
    total_hours_worked = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    provider = db.relationship('Provider', backref='metrics')
    
    def __repr__(self):
        return f'<Metrics P{self.provider_id} on {self.metric_date}>'

