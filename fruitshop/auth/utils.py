import bcrypt
from functools import wraps
from flask import session, redirect, url_for, g

from fruitshop.auth.models import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the user ID from the session
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Get the user from the database
        user = User.query.get(user_id)
        if not user:
            return redirect(url_for('auth.login'))
        
        # Set user
        g.user = user

        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the user ID from the session
        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('auth.login'))
        
        # Get the user from the database
        user = User.query.get(user_id)
        if not user:
            return redirect(url_for('auth.login'))
        
        # Check if the user is an admin
        if user.role != 'admin':
            return redirect(url_for('shop.index'))
        
        # Set user
        g.user = user

        return f(*args, **kwargs)
    return decorated_function

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))