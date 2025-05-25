"""
בדיקת התיקון בחישוב יחס מענקים בתוך חלון 32 שנה
"""
from datetime import date
from indexation import work_ratio_within_last_32y

def test_work_ratio():
    """
    בדיקת היחס המתוקן של ימי עבודה בתוך חלון 32 שנה
    """
    print("===== בדיקת חישוב יחס מתוקן =====")
    
    # מקרה בדיקה 1: לפי הדוגמה בהנחיות
    start1 = date(1985, 1, 1)
    end1 = date(1999, 12, 31)
    elig1 = date(2025, 4, 1)
    
    ratio1 = work_ratio_within_last_32y(start1, end1, elig1)
    print(f"מקרה 1: תקופת עבודה 1985-01-01 עד 1999-12-31, תאריך זכאות 2025-04-01")
    print(f"יחס מחושב: {ratio1:.6f}")
    print(f"יחס צפוי: ~0.466")
    print(f"תקין: {'כן' if 0.46 <= ratio1 <= 0.47 else 'לא'}")
    print()
    
    # מקרה בדיקה 2: כל העבודה בתוך חלון 32 שנה
    start2 = date(2000, 1, 1)
    end2 = date(2020, 12, 31)
    elig2 = date(2025, 4, 1)
    
    ratio2 = work_ratio_within_last_32y(start2, end2, elig2)
    print(f"מקרה 2: כל העבודה בתוך 32 שנה - 2000-01-01 עד 2020-12-31, זכאות 2025-04-01")
    print(f"יחס מחושב: {ratio2:.6f}")
    print(f"יחס צפוי: 1.0")
    print(f"תקין: {'כן' if ratio2 == 1.0 else 'לא'}")
    print()
    
    # מקרה בדיקה 3: כל העבודה לפני החלון
    start3 = date(1980, 1, 1)
    end3 = date(1990, 12, 31)
    elig3 = date(2025, 4, 1)
    window_start = date(1993, 4, 1)  # 32 שנה לפני תאריך הזכאות
    
    ratio3 = work_ratio_within_last_32y(start3, end3, elig3)
    print(f"מקרה 3: כל העבודה לפני החלון - 1980-01-01 עד 1990-12-31, זכאות 2025-04-01")
    print(f"תחילת חלון 32 שנה: {window_start}")
    print(f"יחס מחושב: {ratio3:.6f}")
    print(f"יחס צפוי: 0.0")
    print(f"תקין: {'כן' if ratio3 == 0.0 else 'לא'}")
    print()
    
    # מקרה בדיקה 4: מענק 100,000 ₪ משנות עבודה 1985-1999
    # נבדוק את תוצאת היחס כפול הסכום המוצמד
    grant_amount = 100000
    indexation_factor = 0.72562  # הגורם שהוזכר בהנחיות - 72,562 ₪ מתוך 100,000 ₪
    expected_ratio = 0.466  # היחס הצפוי במקרה 1
    
    print(f"מקרה 4: מענק 100,000 ₪ משנות עבודה 1985-1999")
    print(f"סכום מוצמד: {grant_amount * indexation_factor:.2f} ₪")
    print(f"יחס מחושב: {ratio1:.6f}")
    print(f"סכום מוצמד יחסי: {grant_amount * indexation_factor * ratio1:.2f} ₪")
    print(f"השפעה על הפטור (× 1.35): {grant_amount * indexation_factor * ratio1 * 1.35:.2f} ₪")
    print()
    
    print("===== סיכום =====")
    all_passed = (0.46 <= ratio1 <= 0.47) and (ratio2 == 1.0) and (ratio3 == 0.0)
    print(f"כל הבדיקות עברו בהצלחה: {'כן' if all_passed else 'לא'}")
    
    if all_passed:
        print("\nהיחס המתוקן פותר את הבעיה ומחשב את היחס הנכון של 46.6% במקום 21.5%")
        print("כעת המענק המוצמד היחסי יחושב נכון (72,562 ₪ × 0.466 = 33,794 ₪) במקום הערך השגוי הקודם")
    

if __name__ == "__main__":
    test_work_ratio()
