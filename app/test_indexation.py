"""
בדיקת אלגוריתם ההצמדה החדש
"""
import sys
from datetime import date
from indexation import calculate_adjusted_amount, index_grant

def test_indexation():
    """בודק את פונקציית ההצמדה עם הנתונים מהדרישות"""
    # בדיקה כפי שהוגדרה בדרישות: סכום 100 ₪, תאריך '2015-06-30', toDate='2025-01-01'
    amount = 100
    work_end_date = '2015-06-30'
    target_date = date(2025, 1, 1)
    
    # קריאה לפונקציה הנכונה
    result = calculate_adjusted_amount(amount, work_end_date, target_date)
    
    print(f"סכום מקורי: {amount} ₪")
    print(f"תאריך סיום עבודה: {work_end_date}")
    print(f"תאריך יעד להצמדה: {target_date}")
    print(f"סכום מוצמד: {result} ₪")
    
    # וידוא שהסכום המוצמד גדול מהסכום המקורי
    if result is not None:
        assert result > amount, "הסכום המוצמד אמור להיות גדול מהסכום המקורי"
        print("✓ בדיקה הצליחה: הסכום המוצמד גדול מהסכום המקורי")
    else:
        print("✗ בדיקה נכשלה: לא התקבל סכום מוצמד")

if __name__ == "__main__":
    test_indexation()
