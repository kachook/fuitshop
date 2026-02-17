from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_database(db: SQLAlchemy):
    from fruitshop.shop.models import Fruit, Order, OrderItem, Promotion, OrderReview
    from fruitshop.auth.models import User
    
    db.create_all()
    
    # Create fruits
    if db.session.query(Fruit).count() == 0:
        fruits = [
            Fruit(name='Apple', price=1.99),
            Fruit(name='Orange', price=2.99),
            Fruit(name='Peach', price=1.49),
            Fruit(name='Blueberry', price=0.99),
            Fruit(name='Strawberry', price=1.49),
            Fruit(name='Kiwi', price=1.99),
            Fruit(name='Lemon', price=0.99),
            Fruit(name='Lime', price=0.99),
            Fruit(name='Watermelon', price=4.99),
        ]
        db.session.bulk_save_objects(fruits)
    
    # Create admin user
    if db.session.query(User).count() == 0:
        from fruitshop.auth.models import User
        from fruitshop.auth.utils import hash_password
        user = User(username='admin', password_hash=hash_password('admin'), otp_secret='', role='admin')
        db.session.add(user)
    
    # Create promotion
    if db.session.query(Promotion).count() == 0:
        promo = Promotion(code='10OFF', discount=10, uses_left=99999999)
        db.session.add(promo)
    
    db.session.commit()