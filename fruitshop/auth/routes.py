from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import pyotp
import datetime

from fruitshop.database import db
from fruitshop.auth.models import User
from fruitshop.auth.utils import hash_password, check_password

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # Get username and password
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Please enter a username and password.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get the user from the database
    user = User.query.filter_by(username=username).first()

    # Check if the user exists or if the password is correct
    if not user or not check_password(password, user.password_hash):
        flash('Incorrect username or password.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get valid 2fa codes
    otp = pyotp.TOTP(user.otp_secret)
    now = datetime.datetime.now()
    otp_codes = [otp.at(now, i) for i in range(-2, 3)]

    # Set the login user ID for 2fa login
    session.clear()
    session['login_user_id'] = user.id
    session['login_otp_codes'] = otp_codes

    return redirect(url_for('auth.login_2fa'))

@bp.route('/login/2fa', methods=['GET', 'POST'])
def login_2fa():
    # Get the login user ID from the session
    user_id = session.get('login_user_id')
    otp_codes = session.get('login_otp_codes')
    if not user_id or not otp_codes:
        return redirect(url_for('auth.login'))

    # Get the user from the database
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))

    if request.method == 'GET':
        return render_template('login_2fa.html')

    otp_code = request.form.get('otp')
    
    if not otp_code:
        flash('Please enter an OTP code.', 'danger')
        return redirect(url_for('auth.login_2fa'))

    # Check if the OTP code is valid
    if otp_code not in otp_codes:
        flash('Invalid OTP code.', 'danger')
        return redirect(url_for('auth.login_2fa'))

    # Set the session variables
    session.clear()
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    session['balance'] = user.balance
    
    # Flash a success message
    flash(f"Logged in as: {session['username']}", 'success')
    
    if user.role == 'admin':
        return redirect(url_for('admin.index'))
    
    return redirect(url_for('shop.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    # Get username and password
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('Please enter a username and password.', 'danger')
        return redirect(url_for('auth.register'))

    # Check if the username is already taken
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Username is already taken.', 'danger')
        return redirect(url_for('auth.register'))

    # Hash the password
    password_hash = hash_password(password)

    # Generate a random OTP secret
    otp_secret = pyotp.random_base32()
    
    # Get valid 2fa codes
    otp = pyotp.TOTP(otp_secret)
    now = datetime.datetime.now()
    otp_codes = [otp.at(now, i) for i in range(-2, 3)]

    # Save the registration details to the session
    session.clear()
    session['register_username'] = username
    session['register_password_hash'] = password_hash
    session['register_otp_secret'] = otp_secret
    session['register_otp_codes'] = otp_codes
    
    return redirect(url_for('auth.register_2fa'))

@bp.route('/register/2fa', methods=['GET', 'POST'])
def register_2fa():
    # Get the registration details from the session
    username = session.get('register_username')
    password_hash = session.get('register_password_hash')
    otp_secret = session.get('register_otp_secret')
    otp_codes = session.get('register_otp_codes')
    
    if not username or not password_hash or not otp_secret or not otp_codes:
        return redirect(url_for('auth.register'))
    
    if request.method == 'GET':
        # Generate QR code
        otp = pyotp.TOTP(otp_secret)
        otp_url = otp.provisioning_uri(username, issuer_name="Fruit Shop")
        
        return render_template('register_2fa.html', otp_url=otp_url, otp_secret=otp_secret)
    
    otp_code = request.form.get('otp')
    
    if not otp_code:
        flash('Please enter an OTP code.', 'danger')
        return redirect(url_for('auth.register_2fa'))
    
    # Check if the OTP code is valid
    if otp_code not in otp_codes:
        flash('Invalid OTP code.', 'danger')
        return redirect(url_for('auth.register_2fa'))
    
    # Create a new user
    new_user = User(
        username=username,
        password_hash=password_hash,
        otp_secret=otp_secret,
        role='user',
        balance=5.0
    )

    # Save to database
    db.session.add(new_user)
    db.session.commit()
    
    # Clear the session
    session.clear()

    # Flash a success message
    flash(f"You have successfully registered, {username}. A complimentary $5 has been credited to your account.", 'success')

    # Redirect to the login page
    return redirect(url_for('auth.login'))

@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear session
    session.clear()
    
    flash('Logged out.', 'success')
    return redirect(url_for('auth.login'))