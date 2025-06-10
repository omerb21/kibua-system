import requests
from datetime import datetime, date, timedelta
from sqlalchemy import func
from app.models import Grant, Client, Pension, Commutation
from app.exemption_caps import calc_exempt_capital, get_monthly_cap, get_exemption_percentage

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
    
    # חישוב יחס מתוך 32 שנים לפי ההנחיות
    # משתמשים ב-365.25 כדי לקחת בחשבון שנים מעוברות
    max_days_32y = 32 * 365.25
    
    return round(overlap_days / max_days_32y, 4) if overlap_days > 0 else 0.0

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


def calculate_summary(client_id: int, eligibility_date=None) -> dict:
    """
    מחשב את סיכום הפטור המלא ללקוח לפי המבנה החדש
    
    Args:
        client_id: מזהה הלקוח
        eligibility_date: תאריך זכאות ספציפי (אופציונלי)
        
    Returns:
        מילון עם כל פרטי הסיכום כולל הפרדה בין סכום מוצמד מלא וסכום מוגבל ל-32 שנים
    """
    # שלב 1: קבלת נתוני הלקוח
    client = Client.query.get_or_404(client_id)
    
    # קבלת קצבה ראשונה (אם קיימת)
    first_pension = Pension.query.filter_by(client_id=client_id).order_by(Pension.start_date).first()
    
    # שלב 1: קביעת שנת הזכאות
    # אם התקבל תאריך זכאות מבחוץ, השתמש בו
    if eligibility_date:
        # אם התקבל כמחרוזת, המר לתאריך
        if isinstance(eligibility_date, str):
            from datetime import datetime
            eligibility_date = datetime.fromisoformat(eligibility_date).date()
        elig_year = eligibility_date.year
    # אחרת חשב לפי כללי ברירת המחדל
    elif not first_pension:
        current_date = datetime.now().date()
        eligibility_date = calculate_eligibility_age(client.birth_date, client.gender, current_date)
        elig_year = eligibility_date.year
    else:
        eligibility_date = calculate_eligibility_age(client.birth_date, client.gender, first_pension.start_date)
        elig_year = eligibility_date.year
    
    # שלב 2: חישוב תקרת ההון הפטורה
    exempt_cap = calc_exempt_capital(elig_year)
    
    # שלב 3: חישוב סך המענקים
    grants = Grant.query.filter_by(client_id=client_id).all()
    
    # חישוב סכומים נומינליים ומוצמדים
    nominal_total = 0
    indexed_total_full = 0    # סכום מוצמד מלא (ללא הגבלת 32 שנים)
    indexed_total_limited = 0 # סכום מוצמד מוגבל ל-32 שנים
    valid_grants_count = 0
    
    from app.routes import process_grant  # Import here to avoid circular imports
    from app.indexation import index_grant, work_ratio_within_last_32y

    for grant in grants:
        # חישוב סכום מוצמד
        if not grant.grant_amount:
            continue
            
        nominal_total += grant.grant_amount
        
        try:
            # הצמדה מלאה לפי API
            indexed_full = index_grant(
                amount=grant.grant_amount,
                start_date=grant.work_start_date.isoformat(),
                end_work_date=grant.work_end_date.isoformat(),
                elig_date=eligibility_date.isoformat()
            )
            
            if indexed_full is None:
                continue
                
            # חישוב היחס של 32 השנים האחרונות
            ratio = work_ratio_within_last_32y(
                grant.work_start_date, 
                grant.work_end_date, 
                eligibility_date
            )
            
            # חישוב הסכום המוגבל = מוצמד מלא * יחס
            indexed_limited = indexed_full * ratio
            
            # הוספה לסכומים הכוללים
            indexed_total_full += indexed_full
            indexed_total_limited += indexed_limited
            valid_grants_count += 1
            
            # שמירת הנתונים באובייקט המענק לשימוש בנספחים
            grant.grant_indexed_amount = indexed_full
            grant.grant_ratio = ratio
            grant.impact_on_exemption = indexed_limited
            grant.limited_indexed_amount = indexed_limited
            
        except Exception as e:
            print(f"שגיאה בעיבוד מענק {grant.id}: {e}")
            continue
    
    # לוג במקרה שאין מענקים תקינים אך קיימים מענקים ברשומה
    grant_note = None
    if valid_grants_count == 0 and grants:
        grant_note = "לא נמצאו מענקים תקינים. נא לבדוק נתוני תאריכים או סכומים."
        print(f"אזהרה: אין מענקים תקינים שעברו הצמדה עבור לקוח {client_id}")
    
    # שלב 4: חישוב סך ההיוונים
    # שליפת היוונים מכל הקצבאות
    comm_total = 0
    commutations = []
    
    for pension in Pension.query.filter_by(client_id=client_id).all():
        pension_comms = Commutation.query.filter_by(pension_id=pension.id, include_calc=True).all()
        commutations.extend(pension_comms)
        for comm in pension_comms:
            if comm.amount:
                comm_total += comm.amount
    
    # שלב 5: חישוב יתרת תקרה
    # פגיעה בתקרה מחושבת רק על המענקים המוגבלים ל-32 שנים
    grants_impact = indexed_total_limited * 1.35 if indexed_total_limited > 0 else 0
    
    # חישוב הפחתת מענק עתידי
    reserved_impact = 0
    if client.reserved_grant_amount:
        reserved_impact = client.reserved_grant_amount * 1.35
        
    # הפחתת כל הפגיעות מתקרת ההון הפטורה
    remaining_cap = exempt_cap - grants_impact - comm_total - reserved_impact
    
    # שלב 6-8: חישוב קצבה פטורה ואחוז
    monthly_cap = get_monthly_cap(elig_year)
    
    # חישוב קצבה פטורה לפי נוסחה מתוקנת - יתרת תקרה זמינה לחלק ל-180
    if remaining_cap > 0:
        pension_exempt = remaining_cap / 180
    else:
        pension_exempt = 0
    
    # חישוב אחוז הקצבה הפטורה
    pension_rate = round((pension_exempt / monthly_cap) * 100, 2) if monthly_cap > 0 else 0
    
    # הכנת התשובה במבנה החדש
    summary = {
        # נתוני לקוח
        "client_info": {
            "id": client.id,
            "name": f"{client.first_name} {client.last_name}",
            "eligibility_date": eligibility_date.isoformat(),
            "elig_year": elig_year
        },
        # סיכום חישובים לפי הסדר החדש
        "exempt_cap": round(exempt_cap, 2),                  # 1. תקרת ההון הפטורה
        "grants_nominal": round(nominal_total, 2),           # 2. סך מענקים פטורים נומינליים
        "grants_indexed_full": round(indexed_total_full, 2),  # 3A. סך מענקים פטורים מוצמדים ללא הגבלה
        "grants_indexed_limited": round(indexed_total_limited, 2), # 3B. סך מענקים פטורים מוצמדים מוגבלים ל-32 שנים
        "grants_impact": round(grants_impact, 2),            # 4. סך פגיעה בפטור = (3B) × 1.35
        "reserved_grant_nominal": round(client.reserved_grant_amount, 2) if client.reserved_grant_amount else 0,  # 4.1 מענק עתידי משוריין (נומינלי)
        "reserved_grant_impact": round(reserved_impact, 2),   # 4.2 השפעת מענק עתידי (×1.35)
        "commutations_total": round(comm_total, 2),           # 5. סך היוונים
        "remaining_cap": round(remaining_cap, 2),            # 6. הפרש תקרת הון פטורה מול סך מענקים והיוונים
        "monthly_cap": round(monthly_cap, 2),               # 7. תקרת קצבה מזכה
        "pension_exempt": round(pension_exempt, 2),          # 8. קצבה פטורה מחושבת
        "pension_rate": pension_rate,                        # 9. אחוז הקצבה הפטורה
        # נתונים נוספים לנספחים
        "details": {
            "grants_count": len(grants),
            "commutations_count": len(commutations)
        },
        "grant_note": grant_note
    }
    
    # ליותר תאימות לאחור, משאירים את הערך הישן במקום grants_indexed
    summary["grants_indexed"] = summary["grants_indexed_limited"]
    
    return summary
