from app import create_app, db
import os

def update_database():
    # Create the Flask application
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        print("Dropping all tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating all tables...")
        db.create_all()
        
        print("Database update completed successfully!")

if __name__ == "__main__":
    update_database()
