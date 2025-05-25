from app import create_app
from app.models import Client, Pension, Grant
from app.utils import calculate_eligibility_age
from app.indexation import index_grant, work_ratio_within_last_32y
from datetime import date
import json

app = create_app()

def calculate_total_expected(client_id):
    """
    חישוב מדויק של הסכום המוצמד הכולל והשפעתו לפי נתוני הלקוח
    """
    with app.app_context():
        # שליפת נתוני הלקוח
        client = Client.query.get(client_id)
        if not client:
            print(f"לקוח עם ID {client_id} לא נמצא")
            return
        
        # שליפת קצבה ראשונה לחישוב תאריך זכאות
        first_pension = Pension.query.filter_by(client_id=client_id).order_by(Pension.start_date).first()
        if not first_pension:
            print(f"לא נמצאו קצבאות ללקוח {client_id}")
            return
        
        # חישוב תאריך זכאות
        eligibility_date = calculate_eligibility_age(client.birth_date, client.gender, first_pension.start_date)
        print(f"תאריך זכאות: {eligibility_date.isoformat()}")
        
        # שליפת המענקים
        grants = Grant.query.filter_by(client_id=client_id).all()
        print(f"נמצאו {len(grants)} מענקים")
        
        # חישוב מדויק לכל מענק
        total_nominal = 0
        total_indexed_old = 0  # הערך הישן כפי שמופיע בבסיס הנתונים
        total_indexed_new = 0  # הערך החדש המחושב מחדש
        total_impact_old = 0
        total_impact_new = 0
        
        grant_details = []
        
        for grant in grants:
            # חישוב מחדש של הסכום המוצמד
            indexed_full = index_grant(
                amount=grant.grant_amount,
                start_date=grant.work_start_date.isoformat(),
                end_work_date=grant.work_end_date.isoformat(),
                elig_date=eligibility_date.isoformat()
            )
            
            # חישוב מחדש של היחס
            ratio = work_ratio_within_last_32y(
                grant.work_start_date,
                grant.work_end_date,
                eligibility_date
            )
            
            # חישוב הסכום המוצמד והשפעתו
            indexed_amount_new = indexed_full * ratio
            impact_new = indexed_amount_new * 1.35
            
            # הערכים הישנים מבסיס הנתונים
            indexed_amount_old = grant.grant_indexed_amount or 0
            ratio_old = grant.grant_ratio or 0
            impact_old = grant.impact_on_exemption or 0
            
            # הוספה לסך הכל
            total_nominal += grant.grant_amount or 0
            total_indexed_old += indexed_amount_old
            total_indexed_new += indexed_amount_new
            total_impact_old += impact_old
            total_impact_new += impact_new
            
            # שמירת פרטי החישוב למענק זה
            grant_info = {
                "id": grant.id,
                "employer": grant.employer_name,
                "amount": grant.grant_amount,
                "work_start": grant.work_start_date.isoformat(),
                "work_end": grant.work_end_date.isoformat(),
                "grant_date": grant.grant_date.isoformat() if grant.grant_date else None,
                "old": {
                    "indexed": indexed_amount_old,
                    "ratio": ratio_old,
                    "impact": impact_old
                },
                "new": {
                    "indexed_full": indexed_full,
                    "ratio": ratio,
                    "indexed": indexed_amount_new,
                    "impact": impact_new
                },
                "diff": {
                    "indexed": indexed_amount_new - indexed_amount_old,
                    "impact": impact_new - impact_old
                }
            }
            grant_details.append(grant_info)
            
            # הדפסת פרטי החישוב לכל מענק
            print(f"\nמענק #{grant.id}: {grant.employer_name}")
            print(f"  תקופה: {grant.work_start_date.isoformat()} - {grant.work_end_date.isoformat()}")
            print(f"  סכום: {grant.grant_amount}")
            print(f"  ישן: סכום מוצמד={indexed_amount_old}, יחס={ratio_old}, השפעה={impact_old}")
            print(f"  חדש: סכום מוצמד מלא={indexed_full}, יחס={ratio}, סכום מוצמד={indexed_amount_new}, השפעה={impact_new}")
            print(f"  פער: סכום מוצמד={indexed_amount_new - indexed_amount_old}, השפעה={impact_new - impact_old}")
        
        # סיכום
        print("\n--- סיכום ---")
        print(f"סך נומינלי: {total_nominal}")
        print(f"סך מוצמד (ישן): {total_indexed_old}")
        print(f"סך מוצמד (חדש): {total_indexed_new}")
        print(f"פער בסכום המוצמד: {total_indexed_new - total_indexed_old}")
        print(f"סך השפעה (ישן): {total_impact_old}")
        print(f"סך השפעה (חדש): {total_impact_new}")
        print(f"פער בהשפעה: {total_impact_new - total_impact_old}")
        
        # שמירת התוצאות לקובץ
        results = {
            "client_id": client_id,
            "client_name": f"{client.first_name} {client.last_name}",
            "eligibility_date": eligibility_date.isoformat(),
            "totals": {
                "nominal": total_nominal,
                "indexed_old": total_indexed_old,
                "indexed_new": total_indexed_new,
                "indexed_diff": total_indexed_new - total_indexed_old,
                "impact_old": total_impact_old,
                "impact_new": total_impact_new,
                "impact_diff": total_impact_new - total_impact_old
            },
            "grants": grant_details
        }
        
        with open(f"exact_calculation_{client_id}.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\nתוצאות מפורטות נשמרו לקובץ exact_calculation_{client_id}.json")
        
        return results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("שימוש: python calculate_exact.py [client_id]")
        sys.exit(1)
    
    try:
        client_id = int(sys.argv[1])
        calculate_total_expected(client_id)
    except ValueError:
        print("מזהה לקוח חייב להיות מספר")
        sys.exit(1)
