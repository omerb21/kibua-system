from app import create_app, db
from app.models import Client, Pension, Grant
from app.utils import calculate_eligibility_age
from app.routes import process_grant

app = create_app()

with app.app_context():
    # מעבר על כל הלקוחות
    clients = Client.query.all()
    print(f"נמצאו {len(clients)} לקוחות")
    
    for client in clients:
        print(f"\nמעבד לקוח {client.id}: {client.first_name} {client.last_name}")
        
        # קבלת קצבה ראשונה לחישוב תאריך זכאות
        first_pension = Pension.query.filter_by(client_id=client.id).order_by(Pension.start_date).first()
        
        if first_pension:
            # חישוב תאריך זכאות
            eligibility_date = calculate_eligibility_age(client.birth_date, client.gender, first_pension.start_date)
            print(f"תאריך זכאות: {eligibility_date}")
            
            # חישוב מחדש של כל המענקים
            grants = Grant.query.filter_by(client_id=client.id).all()
            print(f"מספר מענקים: {len(grants)}")
            
            for grant in grants:
                print(f"\nמענק #{grant.id}:")
                print(f"  לפני: סכום מוצמד={grant.grant_indexed_amount}, יחס={grant.grant_ratio}, השפעה={grant.impact_on_exemption}")
                
                # חישוב מחדש
                process_grant(grant, eligibility_date)
                
                print(f"  אחרי: סכום מוצמד={grant.grant_indexed_amount}, יחס={grant.grant_ratio}, השפעה={grant.impact_on_exemption}")
            
            # שמירת השינויים בבסיס הנתונים
            db.session.commit()
            print(f"עודכנו {len(grants)} מענקים ללקוח {client.id}")
        else:
            print(f"לא נמצאו קצבאות ללקוח {client.id}")

print("\nהחישוב מחדש הסתיים בהצלחה")
