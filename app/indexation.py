import requests
from datetime import datetime
from logging import getLogger

logger = getLogger(__name__)

# CBS Consumer Price Index API endpoint
CBS_CPI_API = 'https://api.cbs.gov.il/index/data/calculator/120010'

def log_change(message):
    """Helper function to log changes and warnings"""
    logger.warning(message)

def calculate_adjusted_amount(amount, end_work_date, to_date=None):
    """
    מחשב את הסכום המוצמד לפי API של הלמ"ס
    
    :param amount: סכום נומינלי להצמדה
    :param end_work_date: תאריך סיום עבודה (YYYY-MM-DD)
    :param to_date: תאריך יעד להצמדה (אם None, ישתמש בתאריך נוכחי)
    :return: סכום מוצמד או None בשגיאה
    """
    try:
        url = 'https://api.cbs.gov.il/index/data/calculator/120010'
        
        # וידוא שהתאריך היעד מועבר כמחרוזת בפורמט YYYY-MM-DD
        if to_date and not isinstance(to_date, str):
            to_date = to_date.isoformat()  # המרה לפורמט YYYY-MM-DD
            
        params = {
            'value': amount, 
            'date': end_work_date,          # חייב להיות str!
            'toDate': to_date if to_date else datetime.today().date().isoformat(), 
            'format': 'json', 
            'download': 'false'
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        answer = data.get('answer')
        if not answer:
            log_change(f'אזהרה: API ללא answer עבור {end_work_date} | תשובה: {data}')
            return None
        to_value = answer.get('to_value')
        if to_value is None:
            log_change(f'אזהרה: אין to_value עבור {end_work_date} | תשובה: {data}')
            return None
        return round(float(to_value), 2)
    except Exception as e:
        log_change(f'שגיאה בהצמדה עבור {end_work_date}: {e}')
        return None

def index_grant(amount: float,
                start_date: str,
                end_work_date: str,
                elig_date: str | None = None) -> float | None:
    """
    פונקציה עוטפת שמשתמשת בפונקציה הנכונה calculate_adjusted_amount
    
    :param amount: סכום נומינלי
    :param start_date: תאריך תחילת עבודה (לא נדרש לחישוב הצמדה)
    :param end_work_date: תאריך סיום עבודה
    :param elig_date: תאריך הזכאות (אם None ישתמש בתאריך נוכחי)
    :return: סכום מוצמד
    """
    # נשתמש בפונקציה המתוקנת
    if elig_date:
        # אם יש תאריך זכאות, נצטרך להמיר את התאריך לאובייקט מתאים
        from datetime import date
        # המרה ממחרוזת YYYY-MM-DD לאובייקט date
        elig_date_obj = date.fromisoformat(elig_date)
        return calculate_adjusted_amount(amount, end_work_date, elig_date_obj)
    else:
        # ללא תאריך זכאות - נשתמש בתאריך נוכחי
        return calculate_adjusted_amount(amount, end_work_date)

def ratio_last_32y(start_date, end_date, eligibility_date):
    """
    Calculate the ratio of the last 32 years
    
    Args:
        start_date: The start date of employment
        end_date: The end date of employment
        eligibility_date: The eligibility date
        
    Returns:
        The ratio of the last 32 years (between 0 and 1)
    """
    # For backward compatibility - delegates to the new function
    return work_ratio_within_last_32y(start_date, end_date, eligibility_date)


def work_ratio_within_last_32y(start_date, end_date, elig_date):
    """
    מחשב את היחס של ימי העבודה בין start_date ל-end_date שנופלים
    בתוך 32 השנים שקדמו ל-elig_date.
    """
    from datetime import datetime, timedelta
    
    try:
        # המרת תאריכים לאובייקטי date אם הם מחרוזות
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        if isinstance(elig_date, str):
            elig_date = datetime.strptime(elig_date, '%Y-%m-%d').date()
            
        today = elig_date  # השתמש תמיד בתאריך הזכאות
        limit_start = today - timedelta(days=int(365.25 * 32))
        
        total_days = (end_date - start_date).days
        overlap_start = max(start_date, limit_start)
        overlap_end = min(end_date, today)
        overlap_days = max((overlap_end - overlap_start).days, 0)
        
        ratio = (overlap_days / total_days) if total_days > 0 else 0
        # גבולות
        ratio = min(max(ratio, 0), 1)
        
        # לוג לפיקוח
        print(f"[יחסי מענק] תאריך ייחוס={today}, התחלה={start_date}, "
              f"סיום={end_date}, חפיפה={overlap_days} ימים, יחס={ratio:.4f}")
        return ratio
    except Exception as e:
        print(f"[שגיאה ביחס מענק] התחלה={start_date}, סיום={end_date}, שגיאה: {str(e)}")
        return 0.0
