"""
Script to recreate the database with the updated schema
"""
import os
from app import create_app, db
from app.models import Client, Grant, Pension, Commutation

def reset_db():
    app = create_app()
    with app.app_context():
        # Check if database file exists and remove it
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'rights_fixation.db')
        if os.path.exists(db_path):
            print(f"Removing existing database at {db_path}")
            os.remove(db_path)
        
        # Create all tables with the updated schema
        print("Creating new database with updated schema...")
        db.create_all()
        print("Database schema created successfully.")
        
        # Add sample data if needed
        # Here you could add code to recreate any required test data
        
        print("Database reset complete!")

if __name__ == "__main__":
    reset_db()
