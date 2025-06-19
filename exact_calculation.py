from datetime import datetime, timedelta
import sqlite3
from flask import g

def calculate_relative_amount_with_logging(start_date, end_date, amount):
    """
    העתק מדויק של הפונקציה המקורית כפי שהוצגה
    """
    try:
        today = datetime.today().date()
        limit_start = today - timedelta(days=365.25 * 32)
        if isinstance(start_date, str):
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start = start_date
        if isinstance(end_date, str):
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            end = end_date
            
        total_days = (end - start).days
        overlap_start = max(start, limit_start)
        overlap_end = min(end, today)
        overlap_days = (overlap_end - overlap_start).days
        ratio = max(0, min(overlap_days / total_days, 1)) if total_days > 0 else 0
        result = round(amount * ratio, 2)
        
        print(f'[DEBUG יחסי מענק] סכום={amount}, התחלה={start}, סיום={end}, חפיפה={overlap_days} ימים, יחס={ratio:.4f}, תוצאה={result}')
        return result
    except Exception as e:
        print(f'[DEBUG שגיאה ביחס מענק] התחלה={start_date}, סיום={end_date}, שגיאה: {str(e)}')
        return 0

# בדיקה של הפונקציה על המענקים של הלקוח
if __name__ == "__main__":
    # מענק ראשון
    amount1 = 152275.8  # הסכום המוצמד המלא
    start1 = datetime(1985, 1, 1).date()
    end1 = datetime(1999, 12, 31).date()
    
    # מענק שני
    amount2 = 94750.61
    start2 = datetime(2000, 1, 1).date()
    end2 = datetime(2011, 10, 1).date()
    
    # מענק שלישי
    amount3 = 95929.47
    start3 = datetime(2012, 1, 1).date()
    end3 = datetime(2022, 12, 31).date()
    
    # חישוב
    result1 = calculate_relative_amount_with_logging(start1, end1, amount1)
    result2 = calculate_relative_amount_with_logging(start2, end2, amount2)
    result3 = calculate_relative_amount_with_logging(start3, end3, amount3)
    
    total = result1 + result2 + result3
    print(f"\nסכום כולל: {total}")
    
    # חישוב ההשפעה על הפטור
    impact1 = round(result1 * 1.35, 2)
    impact2 = round(result2 * 1.35, 2)
    impact3 = round(result3 * 1.35, 2)
    total_impact = impact1 + impact2 + impact3
    
    print(f"השפעה על הפטור: {total_impact}")
