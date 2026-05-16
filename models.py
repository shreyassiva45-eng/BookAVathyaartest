from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False) # 'normal' or 'priest'
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    gotra = db.Column(db.String(50))
    sutra = db.Column(db.String(50))
    veda = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Priest Specific
    functions_rituals = db.Column(db.Text) # comma separated list string for simplicity
    
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    normal_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    priest_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    date = db.Column(db.String(20), nullable=False) # Store as string YYYY-MM-DD for simplicity
    location_address = db.Column(db.String(255), nullable=False)
    ritual = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    status = db.Column(db.String(20), default='awaiting') # 'awaiting', 'confirmed', 'rejected'
    otp = db.Column(db.String(10)) 
    tracking_status = db.Column(db.String(20), default='not_started') # 'not_started', 'started', 'reached', 'verified'
    priest_lat = db.Column(db.Float, nullable=True)
    priest_lng = db.Column(db.Float, nullable=True)
    is_finished = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer, nullable=True) # 1-5 Optional
    review_comment = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    normal_user = db.relationship('User', foreign_keys=[normal_user_id], backref='my_bookings')
    priest = db.relationship('User', foreign_keys=[priest_id], backref='my_gigs')
