"""
Migration script to add the reserved_grant_amount field to the Client model.
Run this script after updating the models.py file.
"""

import os
import sys
import sqlite3

# Add the current directory to the path so we can import the app module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def run_migration():
    """Add reserved_grant_amount column to client table if it doesn't exist."""
    # Get the database file path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'instance', 'rights_fixation.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return
    
    print(f"Using database at: {db_path}")
    
    # Connect to the database directly
    try:
        # Check if the column already exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the columns in the client table
        cursor.execute("PRAGMA table_info(client)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'reserved_grant_amount' not in column_names:
            print("Adding reserved_grant_amount column to client table...")
            cursor.execute("ALTER TABLE client ADD COLUMN reserved_grant_amount FLOAT DEFAULT 0.0")
            conn.commit()
            print("Migration successful!")
        else:
            print("Column already exists. No migration needed.")
        
        conn.close()
    except Exception as e:
        print(f"Database error: {str(e)}")

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)
