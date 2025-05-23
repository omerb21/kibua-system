"""
מודול זה מכיל את טבלת התקרות השנתיות לקיבוע זכויות
והפונקציות לחישוב תקרת ההון הפטור
"""

# מיפוי שנה → תקרה חודשית
ANNUAL_CAPS = {  # תקרה חודשית (₪) לפי שנת זכאות
    2025: 9430,
    2024: 9430,
    2023: 9120,
    2022: 8660,
    2021: 8460,
    2020: 8510,
    2019: 8480,
    2018: 8380,
    2017: 8360,
    2016: 8380,
    2015: 8460,
    2014: 8470,
    2013: 8310,
    2012: 8190
}

# קבועים לחישוב תקרת ההון הפטורה
PERCENT_EXEMPT = 0.57  # 57%
MULTIPLIER = 180

def get_monthly_cap(year: int) -> float:
    """החזר תקרה חודשית; ברירת-מחדל: 2025."""
    return ANNUAL_CAPS.get(year, ANNUAL_CAPS[2025])  # ברירת מחדל 2025

def calc_exempt_capital(year: int) -> float:
    """החזר תקרת-הון פטורה: cap × 180 × 57 %."""
    return get_monthly_cap(year) * MULTIPLIER * PERCENT_EXEMPT
    
# שמירת הפונקציות הישנות לאחוריות
def get_exemption_cap_by_year(year: int) -> float:
    """
    מחזיר את התקרה החודשית לפי שנת הזכאות (פונקציה ישנה, השתמש ב-get_monthly_cap)
    """
    return get_monthly_cap(year)

def calculate_exempt_capital(year: int) -> float:
    """
    מחשב את תקרת ההון הפטור לפי השנה (פונקציה ישנה, השתמש ב-calc_exempt_capital)
    """
    return calc_exempt_capital(year)
