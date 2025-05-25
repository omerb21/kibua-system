import sqlite3
import os

def find_database_file():
    """מציאת קובץ מסד הנתונים בתיקייה הנוכחית ובתיקיות משנה"""
    base_dir = os.path.dirname(__file__)
    instance_dir = os.path.join(base_dir, 'instance')
    
    # נחפש ספציפית את rights_fixation.db שמצאנו קודם
    rights_db = os.path.join(instance_dir, 'rights_fixation.db')
    if os.path.exists(rights_db) and os.path.getsize(rights_db) > 0:
        print(f"Found rights_fixation.db: {rights_db}")
        return rights_db
        
    # אם לא מצאנו, נחפש בצורה כללית
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.db') and os.path.getsize(os.path.join(root, file)) > 0:
                db_path = os.path.join(root, file)
                print(f"Found database: {db_path}")
                return db_path
    return None

def check_database_structure(db_path):
    """בדיקת מבנה מסד הנתונים - טבלאות ועמודות"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # קבלת רשימת הטבלאות
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\nDatabase tables ({len(tables)}):")
        for table in tables:
            table_name = table[0]
            print(f"\n- Table: {table_name}")
            
            # קבלת מבנה העמודות של כל טבלה
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"  Columns ({len(columns)}):")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                print(f"    {col_name} ({col_type}){' PRIMARY KEY' if pk else ''}")
                
            # ספירת מספר השורות בטבלה
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            print(f"  Row count: {row_count}")
            
            # אם זו טבלה שנראית כמו טבלת מענקים, נציג כמה רשומות לדוגמה
            if 'grant' in table_name.lower() or 'מענק' in table_name:
                print(f"  Sample data (up to 3 rows):")
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = cursor.fetchall()
                for row in sample_data:
                    print(f"    {row}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error checking database structure: {str(e)}")
        return False

if __name__ == "__main__":
    print("Checking database structure...")
    db_path = find_database_file()
    
    if db_path:
        check_database_structure(db_path)
    else:
        print("No database file found")
