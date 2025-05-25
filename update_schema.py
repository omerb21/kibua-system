"""
Script to update the SQLite database schema by adding new columns 
to the commutation table without deleting existing data
"""
import sqlite3
import os

def update_schema():
    # Path to the database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'rights_fixation.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    print(f"Updating database schema at {db_path}...")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get current columns in commutation table
    cursor.execute("PRAGMA table_info(commutation)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add payer_name column if it doesn't exist
    if 'payer_name' not in columns:
        print("Adding payer_name column to commutation table...")
        cursor.execute("ALTER TABLE commutation ADD COLUMN payer_name TEXT")
    else:
        print("payer_name column already exists")
    
    # Add include_calc column if it doesn't exist
    if 'include_calc' not in columns:
        print("Adding include_calc column to commutation table...")
        cursor.execute("ALTER TABLE commutation ADD COLUMN include_calc BOOLEAN DEFAULT 1")
    else:
        print("include_calc column already exists")
    
    # Rename date column to comm_date if needed
    if 'date' in columns and 'comm_date' not in columns:
        print("Renaming date column to comm_date...")
        
        # In SQLite, renaming a column requires creating a new table
        # First, create a temporary table with the new schema
        cursor.execute("""
        CREATE TABLE commutation_new (
            id INTEGER PRIMARY KEY,
            pension_id INTEGER,
            payer_name TEXT,
            amount FLOAT,
            comm_date DATE,
            full_or_partial TEXT,
            include_calc BOOLEAN DEFAULT 1,
            FOREIGN KEY (pension_id) REFERENCES pension (id)
        )
        """)
        
        # Copy data from old table to new table
        cursor.execute("""
        INSERT INTO commutation_new (id, pension_id, payer_name, amount, comm_date, full_or_partial, include_calc)
        SELECT id, pension_id, payer_name, amount, date, full_or_partial, include_calc FROM commutation
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE commutation")
        
        # Rename new table to the original name
        cursor.execute("ALTER TABLE commutation_new RENAME TO commutation")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database schema update completed successfully!")

if __name__ == "__main__":
    update_schema()
