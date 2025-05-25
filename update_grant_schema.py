import sqlite3
import os
from datetime import datetime

def log_change(message):
    timestamp = datetime.now().isoformat()
    with open('log_schema_updates.txt', 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {message}\n')

def update_grants_schema():
    """
    עדכון סכמת מסד הנתונים של מענקים כדי להוסיף את העמודה החדשה
    limited_indexed_amount - סכום מוגבל ל-32 שנים
    """
    # מציאת מסד הנתונים rights_fixation.db בתיקיית instance
    base_dir = os.path.dirname(__file__)
    db_path = os.path.join(base_dir, 'instance', 'rights_fixation.db')
    
    if not os.path.exists(db_path):
        log_change(f"מסד הנתונים לא נמצא בנתיב: {db_path}")
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # בדיקה האם העמודה כבר קיימת
        cursor.execute("PRAGMA table_info(grant)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'limited_indexed_amount' not in columns:
            # הוספת העמודה החדשה
            cursor.execute('ALTER TABLE grant ADD COLUMN limited_indexed_amount REAL')
            log_change("נוספה עמודה limited_indexed_amount לטבלת grant")
            print("Added limited_indexed_amount column to grant table")
            
            # עדכון ערכים ראשוניים - מעתיק את הערכים הקיימים של grant_indexed_amount
            cursor.execute('UPDATE grant SET limited_indexed_amount = grant_indexed_amount')
            log_change("עודכנו ערכים ראשוניים בעמודה limited_indexed_amount")
            print("Initialized limited_indexed_amount with grant_indexed_amount values")
            
            conn.commit()
            print("Schema updated successfully")
        else:
            print("Column limited_indexed_amount already exists")
        
        conn.close()
        return True
    except Exception as e:
        log_change(f"שגיאה בעדכון סכמת מסד הנתונים: {str(e)}")
        print(f"Error updating schema: {str(e)}")
        return False

if __name__ == "__main__":
    print("Updating grant schema to add limited_indexed_amount column...")
    success = update_grants_schema()
    
    if success:
        print("Schema update completed successfully")
    else:
        print("Schema update failed")
