import os
import math
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Booking
import random
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'purohit_super_secret_key_123!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///purohit.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth_portal'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def calculate_distance(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]:
        return float('inf')
    R = 6371  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'normal':
            return redirect(url_for('normal_dashboard'))
        else:
            return redirect(url_for('priest_dashboard'))
    return redirect(url_for('auth_portal'))

@app.route('/auth', methods=['GET', 'POST'])
def auth_portal():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'login':
            email = request.form.get('email')
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                if user.role == 'normal':
                    return redirect(url_for('normal_dashboard'))
                else:
                    return redirect(url_for('priest_dashboard'))
            flash('Invalid email or password', 'error')
        elif action == 'signup':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role') # 'normal' or 'priest'
            gotra = request.form.get('gotra_brahmin') or request.form.get('gotra_non_brahmin')
            sutra = request.form.get('sutra')
            veda = request.form.get('veda')
            gender = request.form.get('gender')
            
            user = User.query.filter_by(email=email).first()
            if user:
                flash('Email address already exists', 'error')
                return redirect(url_for('auth_portal'))
                
            new_user = User(
                email=email, name=name, password_hash=generate_password_hash(password, method='scrypt'),
                role=role, gotra=gotra, sutra=sutra, veda=veda, gender=gender,
                latitude=request.form.get('lat', type=float),
                longitude=request.form.get('lng', type=float)
            )
            if role == 'priest':
                new_user.functions_rituals = request.form.get('functions')
                
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            if role == 'normal':
                return redirect(url_for('normal_dashboard'))
            else:
                return redirect(url_for('priest_dashboard'))
                
    return render_template('auth.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth_portal'))

# --- NORMAL USER ROUTES ---
@app.route('/dashboard')
@login_required
def normal_dashboard():
    if current_user.role != 'normal': return redirect(url_for('index'))
    
    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)
    
    priests = User.query.filter_by(role='priest').all()
    
    if user_lat is not None and user_lng is not None:
        for p in priests:
            p.distance = calculate_distance(user_lat, user_lng, p.latitude, p.longitude)
        priests.sort(key=lambda x: x.distance)
    
    return render_template('normal_dashboard.html', priests=priests, user_lat=user_lat, user_lng=user_lng)

@app.route('/book_priest/<int:priest_id>', methods=['POST'])
@login_required
def book_priest(priest_id):
    if current_user.role != 'normal': return redirect(url_for('index'))
    date_str = request.form.get('date')
    ritual = request.form.get('ritual')
    address = request.form.get('address')
    amount = float(request.form.get('amount', '1000')) # Mock amount
    
    # Validate date is not in the past
    try:
        if 'T' in date_str:
            booking_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
            if booking_date < datetime.now():
                flash('Cannot book for past dates or times.', 'error')
                return redirect(url_for('normal_dashboard'))
        else:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d')
            if booking_date.date() < datetime.now().date():
                flash('Cannot book for past dates.', 'error')
                return redirect(url_for('normal_dashboard'))
    except (ValueError, TypeError):
        flash('Invalid date format.', 'error')
        return redirect(url_for('normal_dashboard'))
    
    booking = Booking(
        normal_user_id=current_user.id,
        priest_id=priest_id,
        date=date_str,
        location_address=address,
        ritual=ritual,
        amount=amount,
        status='awaiting'
    )
    db.session.add(booking)
    db.session.commit()
    flash('Booking request sent successfully!', 'success')
    return redirect(url_for('my_bookings'))

@app.route('/my_bookings')
@login_required
def my_bookings():
    if current_user.role != 'normal': return redirect(url_for('index'))
    bookings = Booking.query.filter_by(normal_user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('normal_bookings.html', bookings=bookings)

@app.route('/booking/<int:booking_id>/finish', methods=['POST'])
@login_required
def finish_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.normal_user_id == current_user.id:
        booking.is_finished = True
        booking.rating = request.form.get('rating')
        booking.review_comment = request.form.get('review')
        db.session.commit()
    return redirect(url_for('my_bookings'))

# --- PRIEST USER ROUTES ---
@app.route('/priest_dashboard')
@login_required
def priest_dashboard():
    if current_user.role != 'priest': return redirect(url_for('index'))
    bookings = Booking.query.filter_by(priest_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('priest_dashboard.html', bookings=bookings)

@app.route('/booking/<int:booking_id>/update_status', methods=['POST'])
@login_required
def update_booking_status(booking_id):
    if current_user.role != 'priest': return redirect(url_for('index'))
    booking = Booking.query.get_or_404(booking_id)
    if booking.priest_id == current_user.id:
        action = request.form.get('action') # 'accept', 'reject'
        if action == 'accept':
            booking.status = 'confirmed'
            # Generate OTP
            booking.otp = str(random.randint(1000, 9999))
        elif action == 'reject':
            booking.status = 'rejected'
            # Trigger refund logic in reality here
        db.session.commit()
    return redirect(url_for('priest_dashboard'))

@app.route('/booking/<int:booking_id>/track', methods=['POST'])
@login_required
def track_booking(booking_id):
    if current_user.role != 'priest': return redirect(url_for('index'))
    booking = Booking.query.get_or_404(booking_id)
    if booking.priest_id == current_user.id:
        tracking_action = request.form.get('tracking_action') # 'start', 'reached', 'verify_otp'
        if tracking_action == 'start':
            booking.tracking_status = 'started'
        elif tracking_action == 'reached':
            booking.tracking_status = 'reached'
        elif tracking_action == 'verify_otp':
            submitted_otp = request.form.get('otp')
            if submitted_otp == booking.otp:
                booking.tracking_status = 'verified'
                flash('Function Started!', 'success')
            else:
                flash('Invalid OTP', 'error')
        db.session.commit()
    return redirect(url_for('priest_dashboard'))

@app.route('/booking/<int:booking_id>/update_location', methods=['POST'])
@login_required
def update_location(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.priest_id == current_user.id:
        data = request.get_json()
        booking.priest_lat = data.get('lat')
        booking.priest_lng = data.get('lng')
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 403

@app.route('/booking/<int:booking_id>/get_location')
@login_required
def get_location(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    # Check if the current user is the one who made the booking
    if booking.normal_user_id == current_user.id:
        return jsonify({
            'lat': booking.priest_lat,
            'lng': booking.priest_lng,
            'status': booking.tracking_status
        })
    return jsonify({'status': 'error'}), 403

def setup_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    setup_db()
    app.run(debug=True, port=5000)
