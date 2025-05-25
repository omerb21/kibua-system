from datetime import date
import requests
from sqlalchemy import func
from app.models import Grant, Client, Pension, Commutation
from app.exemption_caps import calc_exempt_capital, get_monthly_cap, PERCENT_EXEMPT

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


def calculate_summary(client_id: int) -> dict:
    """
    מחשב את סיכום הפטור המלא ללקוח לפי המבנה החדש
    
    Args:
        client_id: מזהה הלקוח
        
    Returns:
        מילון עם כל פרטי הסיכום
    """
    # שלב 1: קבלת נתוני הלקוח
    client = Client.query.get_or_404(client_id)
    
    # קבלת קצבה ראשונה (אם קיימת)
    first_pension = Pension.query.filter_by(client_id=client_id).order_by(Pension.start_date).first()
    
    # שלב 1: קביעת שנת הזכאות
    # אם אין קצבה, נשתמש בתאריך ברירת מחדל - גיל הפרישה הרגיל לפי המגדר
    if not first_pension:
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
    indexed_total = 0
    
    from app.routes import process_grant  # Import here to avoid circular imports

    for grant in grants:
        # חישוב סכום מוצמד
        if not grant.grant_amount:
            continue
            
        nominal_total += grant.grant_amount
        
        # עיבוד המענק עם הפונקציה החדשה (הצמדה אמיתית לפי API)
        process_grant(grant, eligibility_date)
        
        # חישוב הסכומים המוצמדים לפי תוצאות העיבוד
        if grant.grant_indexed_amount and grant.grant_ratio:
            indexed_total += grant.grant_indexed_amount
    
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
    grants_impact = indexed_total * 1.35
    remaining_cap = exempt_cap - grants_impact - comm_total
    
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
        "grants_indexed": round(indexed_total, 2),           # 3. סך מענקים פטורים מוצמדים
        "grants_impact": round(grants_impact, 2),            # 4. סך פגיעה בפטור = (3) × 1.35
        "commutations_total": round(comm_total, 2),           # 5. סך היוונים
        "remaining_cap": round(remaining_cap, 2),            # 6. הפרש תקרת הון פטורה מול סך מענקים והיוונים
        "monthly_cap": round(monthly_cap, 2),               # 7. תקרת קצבה מזכה
        "pension_exempt": round(pension_exempt, 2),          # 8. קצבה פטורה מחושבת
        "pension_rate": pension_rate,                        # 9. אחוז הקצבה הפטורה
        # נתונים נוספים לנספחים
        "details": {
            "grants_count": len(grants),
            "commutations_count": len(commutations)
        }
    }
    
    return summary
