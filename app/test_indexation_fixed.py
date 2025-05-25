"""
בדיקת אלגוריתם ההצמדה המתוקן לאחר יישום ההנחיות הטכניות
"""
import sys
from datetime import date
from indexation import calculate_adjusted_amount, index_grant, ratio_last_32y

def test_indexation_fixes():
    """בודק את כל התיקונים שבוצעו במנגנון ההצמדה"""
    
    print("===== בדיקת מנגנון ההצמדה המתוקן =====")
    
    # בדיקה A: בדיקת calculate_adjusted_amount עם תאריכים נכונים
    amount = 100
    end_work_date = '2010-06-30'
    elig_date = date(2025, 1, 1)
    
    print("\n1. בדיקת הצמדה למדד (כולל טיפול בתאריכים):")
    print(f"   סכום מקורי: {amount} ₪")
    print(f"   תאריך סיום עבודה: {end_work_date}")
    print(f"   תאריך יעד להצמדה: {elig_date}")
    
    # קריאה לפונקציה המתוקנת
    result = calculate_adjusted_amount(amount, end_work_date, elig_date)
    
    print(f"   סכום מוצמד מלא: {result} ₪")
    
    # וידוא שהתוצאה בטווח הצפוי (בין 160 ל-180)
    if result and 160 <= result <= 180:
        print("   ✓ תקין: הסכום המוצמד בטווח הצפוי (160-180 ₪)")
    else:
        print(f"   ✗ שגיאה: הסכום המוצמד ({result}) אינו בטווח הצפוי (160-180 ₪)")
    
    # בדיקה B: יחס 32 שנה מתוקן
    work_start = date(1980, 1, 1)
    work_end = date(2010, 6, 30)
    elig_date = date(2025, 1, 1)
    
    print("\n2. בדיקת חישוב יחס 32 שנה:")
    print(f"   תאריך תחילת עבודה: {work_start}")
    print(f"   תאריך סיום עבודה: {work_end}")
    print(f"   תאריך זכאות: {elig_date}")
    
    ratio = ratio_last_32y(work_start, work_end, elig_date)
    
    print(f"   יחס מחושב: {ratio:.4f}")
    
    # וידוא שהיחס קרוב לערך הצפוי (~0.47)
    if ratio and 0.45 <= ratio <= 0.49:
        print(f"   ✓ תקין: היחס המחושב ({ratio:.4f}) קרוב לערך הצפוי (~0.47)")
    else:
        print(f"   ✗ שגיאה: היחס המחושב ({ratio:.4f}) אינו קרוב לערך הצפוי (~0.47)")
    
    # בדיקה C: שילוב הצמדה ויחס
    print("\n3. בדיקת שילוב הצמדה ויחס (מניעת כפל הצמדה):")
    
    # חישוב ידני לצורך הדגמה (בפועל זה נעשה ב-process_grant)
    indexed_full = result  # מהבדיקה הראשונה
    final_amount = indexed_full * ratio
    
    print(f"   סכום מוצמד מלא: {indexed_full} ₪")
    print(f"   יחס 32 שנה: {ratio:.4f}")
    print(f"   סכום מוצמד סופי (× יחס): {final_amount:.2f} ₪")
    
    # וידוא שהסכום הסופי אינו אפס
    if final_amount > 0:
        print(f"   ✓ תקין: הסכום הסופי ({final_amount:.2f} ₪) גדול מאפס")
    else:
        print(f"   ✗ שגיאה: הסכום הסופי הוא אפס או שלילי")
    
    # סיכום
    print("\n===== סיכום בדיקות =====")
    success = (result and 160 <= result <= 180) and (ratio and 0.45 <= ratio <= 0.49) and (final_amount > 0)
    
    if success:
        print("כל הבדיקות עברו בהצלחה! מנגנון ההצמדה תוקן כנדרש.")
    else:
        print("חלק מהבדיקות נכשלו. יש לבדוק את הקוד שוב.")

if __name__ == "__main__":
    test_indexation_fixes()
