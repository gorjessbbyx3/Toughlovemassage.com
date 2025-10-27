
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, time

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Intake(db.Model):
    __tablename__ = 'intakes'
    
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    medical_history = db.Column(db.Text)
    pregnancy_stage = db.Column(db.String(100))
    booking_id = db.Column(db.String(100))
    confirmed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    provider_notes = db.Column(db.Text)
    assigned_provider_id = db.Column(db.Integer, db.ForeignKey('providers.id'))
    
    assigned_provider = db.relationship('Provider', back_populates='intakes')
    
    def __repr__(self):
        return f'<Intake {self.client_name}>'

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
    client_notes = db.relationship('ClientNote', back_populates='provider', cascade='all, delete-orphan')
    
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
    client_email = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    provider = db.relationship('Provider', back_populates='client_notes')
    
    def __repr__(self):
        return f'<ClientNote {self.client_email}>'

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
