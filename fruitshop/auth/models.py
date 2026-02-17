from fruitshop.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    otp_secret = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')
    balance = db.Column(db.Float, default=0.0)
    orders = db.relationship('Order', backref='user', lazy=True)