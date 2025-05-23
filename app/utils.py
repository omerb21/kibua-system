from datetime import date
import requests
from app.models import Grant
from app.exemption_caps import get_exemption_cap_by_year, calculate_exempt_capital

def calculate_eligibility_age(birth_date: date, gender: str, pension_start: date) -> date:
    """
    Calculate eligibility age based on gender and pension start date
    
    Args:
        birth_date: The client's birth date
        gender: The client's gender ('male' or 'female')
        pension_start: The pension start date
        
    Returns:
        The eligibility date (max of legal retirement age and pension start date)
    """
    # גיל פרישה לפי מגדר
    legal_retirement_age = date(birth_date.year + (67 if gender == "male" else 62), birth_date.month, birth_date.day)
    return max(legal_retirement_age, pension_start)

def fetch_indexation_factor(from_date: date, to_date: date, amount: float) -> float:
    """
    Fetch indexation factor from CBS (Central Bureau of Statistics)
    
    Args:
        from_date: The start date for indexation
        to_date: The end date for indexation
        amount: The amount to be indexed
        
    Returns:
        The indexed amount
    """
    # זמנית, מחזיר מדד קבוע 1.65 עד שיהיה מימוש עם ה-API של הלמ"ס
    # TODO: לממש קריאה אמיתית ל-API של הלמ"ס
    return amount * 1.65

    # מימוש עתידי עם API
    url = "https://www.cbs.gov.il/he/Pages/calculator.aspx"
    # הדוגמה היא עקרונית – בפועל יש להשתמש ב־API הפנימי של הלמ"ס או לחשב ממדדים קיימים

    payload = {
        "amount": amount,
        "from_date": from_date.strftime("%m/%Y"),
        "to_date": to_date.strftime("%m/%Y"),
    }

    # דוגמה תיאורטית – בפועל המימוש יתבסס על קריאה מקומית / קובץ
    response = requests.post(url, json=payload)

    if response.ok:
        return response.json()["linked_amount"]
    else:
        raise ValueError("מדד לא נשלף בהצלחה")

def calculate_indexed_grant(grant: Grant, eligibility_date: date) -> float:
    """
    Calculate indexed grant amount
    
    Args:
        grant: The grant object
        eligibility_date: The eligibility date for indexation
        
    Returns:
        The indexed grant amount
    """
    return fetch_indexation_factor(grant.grant_date, eligibility_date, grant.grant_amount)

def calculate_grant_ratio(grant_start: date, grant_end: date, eligibility_date: date) -> float:
    """
    מחשב את שיעור החפיפה של תקופת העבודה של מענק עם 32 השנים שלפני גיל הזכאות
    
    Args:
        grant_start: תאריך תחילת עבודה
        grant_end: תאריך סיום עבודה
        eligibility_date: תאריך זכאות
        
    Returns:
        שיעור החפיפה בין 0 ל-1
    """
    window_start = date(eligibility_date.year - 32, eligibility_date.month, eligibility_date.day)
    overlap_start = max(grant_start, window_start)
    overlap_end = min(grant_end, eligibility_date)

    if overlap_end < overlap_start:
        return 0.0

    overlap_days = (overlap_end - overlap_start).days
    grant_days = (grant_end - grant_start).days

    return round(overlap_days / grant_days, 4) if grant_days > 0 else 0.0

def calculate_grant_impact(grant_amount: float, indexation_factor: float, ratio: float) -> float:
    """
    מחשב את הסכום הפוגע מתוך תקרת ההון הפתורה – כולל הצמדה ומקדם חלקי
    
    Args:
        grant_amount: סכום המענק הנומינלי
        indexation_factor: מקדם ההצמדה
        ratio: החלק היחסי
        
    Returns:
        הסכום הפוגע בתקרה
    """
    return round(grant_amount * indexation_factor * ratio, 2)

# get_exemption_cap_by_year מיובא כעת מ־exemption_caps.py

def calculate_total_grant_impact(grants: list) -> float:
    """
    מחשבת את סך הפגיעות בתקרת ההון מתוך כל המענקים
    
    Args:
        grants: רשימת מענקים
        
    Returns:
        סך הפגיעה בתקרה
    """
    return round(sum(g.impact_on_exemption or 0 for g in grants), 2)

def calculate_total_commutation_impact(commutations: list) -> float:
    """
    מחשבת את סך ההיוון הפטור שפוגע בקצבה המזכה
    
    Args:
        commutations: רשימת היוונים
        
    Returns:
        סך הפגיעה מהיוונים
    """
    return round(sum(c.amount or 0 for c in commutations), 2)

def calculate_available_exemption_cap(eligibility_year: int, grant_impact: float) -> float:
    """
    מחשב את יתרת תקרת ההון הזמינה לאחר קיזוז מענקים
    
    Args:
        eligibility_year: שנת הזכאות
        grant_impact: סך הפגיעה ממענקים
        
    Returns:
        יתרת תקרת הון זמינה
    """
    cap = calculate_exempt_capital(eligibility_year)  # שימוש בפונקציה החדשה עם חישוב מלא
    return round(cap - grant_impact, 2)

def calculate_final_exempt_amount(exemption_cap_remaining: float, commutation_impact: float) -> float:
    """
    מחשב את סכום הפטור לקצבה (כפוף לפגיעות מהיוונים)
    
    Args:
        exemption_cap_remaining: יתרת תקרת הון לאחר מענקים
        commutation_impact: סך הפגיעה מהיוונים
        
    Returns:
        סכום הפטור הסופי לקצבה
    """
    return round(max(exemption_cap_remaining - commutation_impact, 0), 2)
