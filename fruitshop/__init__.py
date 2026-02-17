from flask import Flask
from flask_qrcode import QRcode
from fruitshop.config import Config
import os

def create_app():
    app = Flask(__name__)
    
    # Load the config
    app.config.from_object(Config)
    
    # Load also from env vars
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    # Init the database
    from fruitshop.database import db, init_database
    db.init_app(app)

    with app.app_context():
        init_database(db)
    
    # Setup routes
    from fruitshop.shop.routes import bp as shop_bp
    from fruitshop.auth.routes import bp as auth_bp
    from fruitshop.admin.routes import bp as admin_bp
    app.register_blueprint(shop_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    
    # Init the QRcode extension
    QRcode(app)

    return app