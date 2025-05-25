from datetime import datetime, timedelta
import requests
import json

def calculate_relative_amount(start_date, end_date, amount):
    """
    חישוב סכום יחסי לפי יחס ימי העבודה בחלון 32 שנה
    זהו החישוב ל"מענק פטור צמוד (32 שנים)"
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
        
        print(f'[חישוב יחסי] סכום={amount}, התחלה={start}, סיום={end}, חפיפה={overlap_days} ימים, יחס={ratio:.4f}, תוצאה={result}')
        return result
    except Exception as e:
        print(f'[שגיאה בחישוב יחסי] התחלה={start_date}, סיום={end_date}, שגיאה: {str(e)}')
        return 0

def calculate_adjusted_amount(amount, end_work_date):
    """
    חישוב סכום מוצמד לפי API של הלמ"ס
    זהו הבסיס לחישוב "מענק פטור צמוד"
    """
    try:
        if isinstance(end_work_date, datetime):
            end_work_date = end_work_date.date()
            
        if isinstance(end_work_date, str):
            pass  # כבר מחרוזת
        else:
            end_work_date = end_work_date.isoformat()
            
        url = 'https://api.cbs.gov.il/index/data/calculator/120010'
        params = {
            'value': amount, 
            'date': end_work_date, 
            'toDate': datetime.today().date().isoformat(), 
            'format': 'json', 
            'download': 'false'
        }
        
        print(f"[חישוב הצמדה] מבצע קריאה ל-API עם הפרמטרים: {params}")
        
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        answer = data.get('answer')
        if not answer:
            print(f'אזהרה: API ללא answer עבור {end_work_date} | תשובה: {data}')
            return None
            
        to_value = answer.get('to_value')
        if to_value is None:
            print(f'אזהרה: אין to_value עבור {end_work_date} | תשובה: {data}')
            return None
            
        return round(float(to_value), 2)
    except Exception as e:
        print(f'שגיאה בהצמדה עבור {end_work_date}: {e}')
        return None

def calculate_complete_grant(nominal_amount, start_date, end_date):
    """
    חישוב מלא של מענק עם שתי העמודות:
    1. מענק פטור צמוד (32 שנים) - חישוב יחסי
    2. מענק פטור צמוד - חישוב מוצמד מלא (נראה שהוא מוצמד ללא תלות ביחס)
    """
    # חישוב הסכום המוצמד המלא
    adjusted_amount = calculate_adjusted_amount(nominal_amount, end_date)
    
    if adjusted_amount is None:
        print(f"שגיאה בחישוב הסכום המוצמד עבור {nominal_amount} מתאריך {end_date}")
        return None, None
    
    # חישוב הסכום היחסי (32 שנה)
    relative_amount = calculate_relative_amount(start_date, end_date, adjusted_amount)
    
    print(f"סכום נומינלי: {nominal_amount}")
    print(f"סכום מוצמד מלא: {adjusted_amount}")
    print(f"סכום יחסי (32 שנים): {relative_amount}")
    
    return relative_amount, adjusted_amount

# חישוב עבור המענקים שבדוגמה
if __name__ == "__main__":
    print("===== חישוב מענקים לפי הנספח =====")
    
    # מענק ראשון
    start1 = datetime(1985, 1, 1).date()
    end1 = datetime(1999, 12, 31).date()
    amount1 = 100000.0
    
    # מענק שני
    start2 = datetime(2000, 1, 1).date()
    end2 = datetime(2011, 10, 1).date()
    amount2 = 80000.0
    
    # מענק שלישי
    start3 = datetime(2012, 1, 1).date()
    end3 = datetime(2022, 12, 31).date()
    amount3 = 90000.0
    
    print("\n===== מענק ראשון =====")
    rel1, adj1 = calculate_complete_grant(amount1, start1, end1)
    
    print("\n===== מענק שני =====")
    rel2, adj2 = calculate_complete_grant(amount2, start2, end2)
    
    print("\n===== מענק שלישי =====")
    rel3, adj3 = calculate_complete_grant(amount3, start3, end3)
    
    print("\n===== סיכום =====")
    total_rel = rel1 + rel2 + rel3
    total_adj = adj1 + adj2 + adj3
    
    print(f"סה\"כ מענק פטור צמוד (32 שנים): {total_rel}")
    print(f"סה\"כ מענק פטור צמוד: {total_adj}")
    
    results = {
        "grants": [
            {
                "employer": "מעסיק ראשון",
                "period": f"{start1.isoformat()} - {end1.isoformat()}",
                "nominal": amount1,
                "relative_32y": rel1,
                "adjusted_full": adj1
            },
            {
                "employer": "מעסיק שני",
                "period": f"{start2.isoformat()} - {end2.isoformat()}",
                "nominal": amount2,
                "relative_32y": rel2,
                "adjusted_full": adj2
            },
            {
                "employer": "מעסיק שלישי",
                "period": f"{start3.isoformat()} - {end3.isoformat()}",
                "nominal": amount3,
                "relative_32y": rel3,
                "adjusted_full": adj3
            }
        ],
        "totals": {
            "nominal": amount1 + amount2 + amount3,
            "relative_32y": total_rel,
            "adjusted_full": total_adj
        }
    }
    
    # שמירת התוצאות לקובץ JSON
    with open("grant_calculations.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\nהתוצאות נשמרו לקובץ grant_calculations.json")
