import os
from flask import Flask
from config import Config
from app.models import db

def create_app(config_class=Config):
    # Initialize Flask app
    app = Flask(__name__, 
               static_folder='static',
               static_url_path='/static')
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not Found'}, 404
        
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal Server Error'}, 500
    
    return app
