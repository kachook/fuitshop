from fruitshop.database import db
from datetime import datetime

class Fruit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    order_items = db.relationship('OrderItem', backref='fruit', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    promo = db.Column(db.String(100))
    subtotal = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)
    review = db.relationship('OrderReview', backref='order', lazy=True) # one-to-one
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    fruit_id = db.Column(db.Integer, db.ForeignKey('fruit.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Promotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), nullable=False)
    discount = db.Column(db.Float, nullable=False)
    uses_left = db.Column(db.Integer, nullable=False)

class OrderReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    comments = db.Column(db.String(1000), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    db.UniqueConstraint('order_id', name='unique_order_id')
