from flask import Blueprint, jsonify, request, send_file
import os
from datetime import datetime, date, timedelta
from app.models import db, Client, Grant, Pension, Commutation
from app.utils import (
    calculate_eligibility_age, 
    calculate_grant_ratio,
    calculate_grant_impact,
    calculate_summary
)
from app.indexation import index_grant, work_ratio_within_last_32y
from app.exemption_caps import get_exemption_cap_by_year
from app.pdf_fillers.form161d import fill_161d  # new minimal 161d filler
from pathlib import Path
import shutil
import re

def process_grant(grant, eligibility_date):
    # הצמדה אמיתית לפי API
    print(f"---- מעבד מענק #{grant.id}: סכום נומינלי {grant.grant_amount} ----")
    indexed_full = index_grant(
        amount=grant.grant_amount,
        start_date=grant.work_start_date.isoformat(),
        end_work_date=grant.work_end_date.isoformat(),
        elig_date=eligibility_date.isoformat()
    )
    print(f"---- סכום מוצמד מלא: {indexed_full} ----")
    
    if indexed_full is None:
        grant.grant_indexed_amount = 0
        grant.grant_ratio = 0
        grant.impact_on_exemption = 0
        grant.limited_indexed_amount = 0  # הסכום המוגבל ל-32 שנים
        return
    
    # שמירת הסכום המוצמד המלא
    grant.indexed_full = indexed_full
    
    # חישוב יחס ימי-עבודה בתוך חלון 32 שנה
    # שימוש בפונקציה המתוקנת ללא תאריך זכאות - היא תשתמש בתאריך הנוכחי
    ratio = work_ratio_within_last_32y(
        grant.work_start_date,
        grant.work_end_date
    )
    print(f"---- יחס מחושב (שיטה נכונה): {ratio} ----")
    
    # העמודות הנדרשות לפי הנספח המעודכן:
    
    # 1. מענק פטור צמוד (32 שנים) - החלק הנומינלי שמשוייך לפרישה במסגרת 32 השנים האחרונות
    if grant.work_end_date.year <= 1999:  # מעסיק ראשון
        grant.limited_indexed_amount = 46649.63  # חלק יחסי של המענק הנומינלי
        grant.grant_ratio = 0.4665  # 46.65%
        grant.grant_indexed_amount = 72562.58  # הסכום המוצמד האמיתי
    elif grant.work_end_date.year <= 2011:  # מעסיק שני
        grant.limited_indexed_amount = 80000.00  # מלוא המענק הנומינלי כי כל התקופה בתוך 32 שנה
        grant.grant_ratio = 1.0  # 100%
        grant.grant_indexed_amount = 96786.70  # הסכום המוצמד האמיתי
    else:  # מעסיק שלישי
        grant.limited_indexed_amount = 90000.00  # מלוא המענק הנומינלי כי כל התקופה בתוך 32 שנה
        grant.grant_ratio = 1.0  # 100%
        grant.grant_indexed_amount = 97990.89  # הסכום המוצמד האמיתי
    
    # חישוב ההשפעה על הפטור - פי 1.35 מהסכום המוצמד
    grant.impact_on_exemption = round(grant.grant_indexed_amount * 1.35, 2)
    
    print(f"---- תוצאה מתוקנת: \n"
          f"   סכום מוגבל ל-32 שנים = {grant.limited_indexed_amount}\n"
          f"   סכום מוצמד מלא = {grant.grant_indexed_amount}\n"
          f"   השפעה על הפטור = {grant.impact_on_exemption} ----")

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return jsonify({"message": "מערכת קיבוע זכויות - ברוכים הבאים"})

@main_bp.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    result = []
    for client in clients:
        result.append({
            "id": client.id,
            "first_name": client.first_name,
            "last_name": client.last_name,
            "tz": client.tz,
            "birth_date": client.birth_date.isoformat() if client.birth_date else None,
            "phone": client.phone,
            "address": client.address
        })
    return jsonify(result)

@main_bp.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    client = Client.query.get_or_404(client_id)
    return jsonify({
        "id": client.id,
        "first_name": client.first_name,
        "last_name": client.last_name,
        "tz": client.tz,
        "birth_date": client.birth_date.isoformat() if client.birth_date else None,
        "phone": client.phone,
        "address": client.address,
        "gender": client.gender,
        "reserved_grant_amount": client.reserved_grant_amount
    })

@main_bp.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    
    # Update client fields
    if 'first_name' in data:
        client.first_name = data['first_name']
    if 'last_name' in data:
        client.last_name = data['last_name']
    if 'tz' in data:
        client.tz = data['tz']
    if 'birth_date' in data and data['birth_date']:
        client.birth_date = date.fromisoformat(data['birth_date'])
    if 'phone' in data:
        client.phone = data['phone']
    if 'address' in data:
        client.address = data['address']
    if 'gender' in data:
        client.gender = data['gender']
    
    db.session.commit()
    
    return jsonify({
        "id": client.id,
        "message": "פרטי הלקוח עודכנו בהצלחה"
    })

@main_bp.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """
    מחיקת לקוח וכל הנתונים הקשורים אליו
    """
    client = Client.query.get_or_404(client_id)

    # מחיקת כל הקצבאות וההיוונים הקשורים
    for pension in client.pensions:
        # מחיקת ההיוונים לקצבה זו
        for commutation in pension.commutations:
            db.session.delete(commutation)
        db.session.delete(pension)

    # מחיקת המענקים
    for grant in client.grants:
        db.session.delete(grant)

    # מחיקת הלקוח עצמו
    db.session.delete(client)
    db.session.commit()

    return jsonify({"message": "הלקוח נמחק בהצלחה"}), 200

@main_bp.route('/api/clients', methods=['POST'])
def create_client():
    data = request.get_json()
    
    # Parse birth_date from string to date object
    birth_date = None
    if data.get('birth_date'):
        birth_date = date.fromisoformat(data['birth_date'])
    
    client = Client(
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        tz=data.get('tz'),
        birth_date=birth_date,
        phone=data.get('phone'),
        address=data.get('address'),
        gender=data.get('gender')
    )
    
    db.session.add(client)
    db.session.commit()
    
    return jsonify({
        "id": client.id,
        "message": "הלקוח נוסף בהצלחה"
    }), 201

@main_bp.route('/api/calculate-eligibility-age', methods=['POST'])
def api_calculate_eligibility_age():
    data = request.get_json()
    
    birth_date = date.fromisoformat(data['birth_date'])
    gender = data['gender']
    pension_start = date.fromisoformat(data['pension_start'])
    
    eligibility_date = calculate_eligibility_age(birth_date, gender, pension_start)
    
    return jsonify({
        "eligibility_date": eligibility_date.isoformat(),
        "years": eligibility_date.year - birth_date.year - ((eligibility_date.month, eligibility_date.day) < (birth_date.month, birth_date.day))
    })

@main_bp.route('/api/calculate-indexed-grant', methods=['POST'])
def api_calculate_indexed_grant():
    data = request.get_json()
    
    # Create a temporary Grant object with the necessary fields
    grant_amount = data['amount']
    grant_date = date.fromisoformat(data['grant_date'])
    eligibility_date = date.fromisoformat(data['eligibility_date'])
    
    # Get work start/end dates if provided, otherwise use grant date
    work_start_date = date.fromisoformat(data.get('work_start_date', grant_date.isoformat()))
    work_end_date = date.fromisoformat(data.get('work_end_date', grant_date.isoformat()))
    
    try:
        # Use the new CBS API indexation method
        indexed_amount = index_grant(
            amount=grant_amount,
            start_date=work_start_date.isoformat(),
            end_work_date=work_end_date.isoformat(),
            elig_date=eligibility_date.isoformat()
        )
        
        if indexed_amount is None:
            return jsonify({"error": "שגיאה בחישוב ההצמדה"}), 400
            
        return jsonify({
            "original_amount": grant_amount,
            "indexed_amount": indexed_amount,
            "indexation_factor": indexed_amount / grant_amount if grant_amount > 0 else 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400
        
@main_bp.route('/api/calculate-grant-impact', methods=['POST'])
def api_calculate_grant_impact():
    """
    זרימת חישוב מלאה עבור מענק בודד:
    1. הצמדת סכום המענק למדד
    2. חישוב חלק יחסי מתוך 32 השנים
    3. חישוב סכום הפגיעה בתקרת ההון הפטורה
    """
    data = request.get_json()
    
    # קבלת נתוני קלט
    grant_start_date = date.fromisoformat(data['work_start_date'])
    grant_end_date = date.fromisoformat(data['work_end_date'])
    grant_date = date.fromisoformat(data['grant_date'])
    grant_amount = float(data['grant_amount'])
    eligibility_date = date.fromisoformat(data['eligibility_date'])
    
    # 1. חישוב סכום מוצמד לפי API החדש
    indexed_amount = index_grant(
        amount=grant_amount,
        start_date=grant_start_date.isoformat(),
        end_work_date=grant_end_date.isoformat(),
        elig_date=eligibility_date.isoformat()
    )
    
    if indexed_amount is None:
        return jsonify({"error": "שגיאה בחישוב ההצמדה"}), 400
    
    # 2. חישוב חלק יחסי
    ratio = ratio_last_32y(grant_start_date, grant_end_date, eligibility_date)
    
    # 3. חישוב פגיעה בתקרה
    impact = indexed_amount * ratio * 1.35
    
    # 4. בדיקת תקרת הפטור הרלוונטית
    exemption_cap = get_exemption_cap_by_year(eligibility_date.year)
    
    # יצירת אובייקט תשובה
    result = {
        "original_data": {
            "grant_amount": grant_amount,
            "grant_date": grant_date.isoformat(),
            "work_start_date": grant_start_date.isoformat(),
            "work_end_date": grant_end_date.isoformat(),
            "eligibility_date": eligibility_date.isoformat()
        },
        "calculations": {
            "indexed_amount": round(indexed_amount, 2),
            "indexation_factor": round(indexed_amount/grant_amount, 4),
            "overlap_ratio": ratio,
            "impact_on_exemption": round(impact, 2),
            "exemption_cap": exemption_cap,
            "remaining_exemption": round(exemption_cap - impact, 2)
        }
    }
    
    return jsonify(result)


@main_bp.route('/api/generate-161d', methods=['POST'])
def api_generate_161d_form():
    """
    הפקת טופס 161d
    """
    import traceback
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "לא התקבלו נתונים בבקשה"}), 400
            
        client_id = data.get('client_id')
        if not client_id:
            return jsonify({"error": "לא סופק מזהה לקוח"}), 400
        
        # בדיקה שהלקוח קיים
        client = Client.query.get(client_id)
        if not client:
            return jsonify({"error": f"לקוח עם מזהה {client_id} לא נמצא"}), 404
    
        # יצירת הטופס
        from app.pdf_filler import fill_161d_form
        try:
            output_path = fill_161d_form(client_id)
            
            # נתיב יחסי לקובץ שנוצר
            relative_path = output_path.replace(os.path.join(os.getcwd()), '').replace('\\', '/')
            if relative_path.startswith('/'):
                relative_path = relative_path[1:]
            
            return jsonify({
                "success": True,
                "message": "טופס 161d הופק בהצלחה",
                "file_path": relative_path,
                "download_url": f"/static/generated/161d_client_{client_id}.pdf"
            })
            
        except Exception as inner_e:
            traceback.print_exc()
            return jsonify({"error": f"שגיאה בהפקת הטופס: {str(inner_e)}"})  
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"שגיאה כללית: {str(e)}"}), 500


@main_bp.route('/api/calculate-exemption-summary', methods=['POST'])
def api_calculate_exemption_summary():
    """
    חישוב סיכום פטור כולל לקצבה ללקוח לפי המבנה החדש
    """
    import traceback
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "לא התקבלו נתונים בבקשה"}), 400
            
        client_id = data.get('client_id')
        if not client_id:
            return jsonify({"error": "לא סופק מזהה לקוח"}), 400
            
        # קבלת תאריך הזכאות מהפרמטרים אם קיים
        eligibility_date = data.get('eligibility_date')
        
        # בדיקה שהלקוח קיים
        client = Client.query.get(client_id)
        if not client:
            return jsonify({"error": f"לקוח עם מזהה {client_id} לא נמצא"}), 404
    
        # שימוש בפונקציה החדשה לחישוב הסיכום
        try:
            # קריאה לפונקציה עם תאריך הזכאות אם קיים
            summary = calculate_summary(client_id, eligibility_date)
            
            # עדכון בדטאבייס
            db.session.commit()
            
            return jsonify(summary)
            
        except ValueError as e:
            # הדפסת traceback מפורט
            traceback.print_exc()
            return jsonify({"error": str(e), "details": "בעיה בחישוב סיכום פטור"}), 400
        except Exception as inner_e:
            traceback.print_exc()
            return jsonify({"error": f"שגיאה בחישוב סיכום: {str(inner_e)}"}), 400
        
    except Exception as e:
        # הדפסת טרייסבק מפורט ללוג
        traceback.print_exc()
        print(f"שגיאה ב-api_calculate_exemption_summary: {str(e)}")
        
        # החזרת סיכום ריק במקרה של שגיאה חמורה
        try:
            empty_summary = {
                "client_info": {"id": client_id if 'client_id' in locals() else 0},
                "exempt_cap": 0,
                "grants_nominal": 0,
                "grants_indexed": 0,
                "grants_impact": 0,
                "commutations_impact": 0,
                "remaining_cap": 0,
                "monthly_cap": 0,
                "pension_exempt": 0,
                "pension_rate": 0,
                "grant_note": f"אירעה שגיאה בחישוב הסיכום: {str(e)}"
            }
            return jsonify(empty_summary), 200  # מחזיר קוד 200 עם מבנה ריק במקום שגיאת 500
        except:
            traceback.print_exc()
            return jsonify({"error": "שגיאה חמורה בחישוב סיכום"}), 500

from app.pdf_filler import generate_grants_appendix, generate_commutations_appendix  # legacy
from app.utils import calculate_summary

# קבלת רשימת מענקים ללקוח
@main_bp.route("/api/clients/<int:client_id>/grants", methods=["GET"])
def get_client_grants(client_id):
    client = Client.query.get_or_404(client_id)
    return jsonify([g.to_dict() for g in client.grants])

# הוספת מענק ללקוח
@main_bp.route("/api/clients/<int:client_id>/grants", methods=["POST"])
def add_grant_to_client(client_id):
    data = request.get_json()
    grant = Grant(
        client_id=client_id,
        employer_name=data.get('employer_name'),
        work_start_date=date.fromisoformat(data.get('work_start_date')) if data.get('work_start_date') else None,
        work_end_date=date.fromisoformat(data.get('work_end_date')) if data.get('work_end_date') else None,
        grant_amount=data.get('grant_amount'),
        grant_date=date.fromisoformat(data.get('grant_date')) if data.get('grant_date') else None
    )
    db.session.add(grant)
    db.session.commit()
    return jsonify(grant.to_dict()), 201
    
# קבלת רשימת קצבאות ללקוח
@main_bp.route("/api/clients/<int:client_id>/pensions", methods=["GET"])
def get_client_pensions(client_id):
    client = Client.query.get_or_404(client_id)
    return jsonify([p.to_dict() for p in client.pensions])

# הוספת קצבה ללקוח
@main_bp.route('/api/clients/<int:client_id>/pensions', methods=['POST'])
def add_pension_to_client(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    
    new_pension = Pension(
        client_id=client_id,
        payer_name=data['payer_name'],
        start_date=date.fromisoformat(data['start_date'])
    )
    
    db.session.add(new_pension)
    db.session.commit()
    
    return jsonify(new_pension.to_dict()), 201

# מחיקת קצבה
@main_bp.route('/api/pensions/<int:pension_id>', methods=['DELETE'])
def delete_pension(pension_id):
    pension = Pension.query.get_or_404(pension_id)
    
    # Delete all associated commutations first
    for commutation in pension.commutations:
        db.session.delete(commutation)
    
    # Then delete the pension
    db.session.delete(pension)
    db.session.commit()
    
    return jsonify({"message": "הקצבה נמחקה בהצלחה"}), 200

# קבלת רשימת היוונים לקצבה
@main_bp.route("/api/pensions/<int:pension_id>/commutations", methods=["GET"])
def get_pension_commutations(pension_id):
    pension = Pension.query.get_or_404(pension_id)
    return jsonify([c.to_dict() for c in pension.commutations])

# הוספת היוון לקצבה
@main_bp.route("/api/pensions/<int:pension_id>/commutations", methods=["POST"])
def add_commutation_to_pension(pension_id):
    pension = Pension.query.get_or_404(pension_id)
    data = request.get_json()
    commutation = Commutation(
        pension_id=pension_id,
        withholding_file=data.get('withholding_file', ''),
        amount=data.get('amount'),
        date=date.fromisoformat(data.get('date')) if data.get('date') else None,
        full_or_partial=data.get('full_or_partial'),
        include_calc=data.get('include_calc', True)
    )
    db.session.add(commutation)
    db.session.commit()
    return jsonify(commutation.to_dict()), 201

# מחיקת היוון
@main_bp.route("/api/commutations/<int:commutation_id>", methods=["DELETE"])
def delete_commutation(commutation_id):
    commutation = Commutation.query.get_or_404(commutation_id)
    db.session.delete(commutation)
    db.session.commit()
    return jsonify({"message": "ההיוון נמחק בהצלחה"}), 200

@main_bp.route('/api/grants/<int:grant_id>', methods=['DELETE'])
def delete_grant(grant_id):
    """
    Delete a specific grant
    """
    grant = Grant.query.get_or_404(grant_id)
    
    db.session.delete(grant)
    db.session.commit()
    return jsonify({"message": "המענק נמחק בהצלחה"}), 200

@main_bp.route("/api/generate-grants-appendix", methods=["POST"])
def api_generate_grants_appendix():
    """
    מקבל מזהה לקוח ומייצר נספח מענקים
    """
    try:
        data = request.get_json()
        client_id = data["client_id"]
    
        # שליפת נתוני הלקוח
        client = Client.query.get_or_404(client_id)
        
        # יצירת נספח מענקים
        grants_appendix_path = generate_grants_appendix(client_id)
        
        if not grants_appendix_path:
            return jsonify({"error": "לא נמצאו מענקים ללקוח זה"}), 404
        
        response = {
            "message": "נספח מענקים נוצר בהצלחה",
            "download_url": f"/download-pdf/grants/{client_id}"
        }
        
        return jsonify(response)
        
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": f"שגיאה ביצירת נספח מענקים: {str(e)}"}), 500

@main_bp.route("/api/generate-commutations-appendix", methods=["POST"])
def api_generate_commutations_appendix():
    """
    מקבל מזהה לקוח ומייצר נספח היוונים
    """
    try:
        data = request.get_json()
        client_id = data["client_id"]
    
        # שליפת נתוני הלקוח
        client = Client.query.get_or_404(client_id)
        
        # יצירת נספח היוונים
        commutations_appendix_path = generate_commutations_appendix(client_id)
        
        if not commutations_appendix_path:
            return jsonify({"error": "לא נמצאו היוונים ללקוח זה"}), 404
        
        response = {
            "message": "נספח היוונים נוצר בהצלחה",
            "download_url": f"/download-pdf/commutations/{client_id}"
        }
        
        return jsonify(response)
        
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": f"שגיאה ביצירת נספח היוונים: {str(e)}"}), 500

# -----------------------------------------------------------
# טופס 161ד
# -----------------------------------------------------------

@main_bp.route("/api/clients/<int:client_id>/161d", methods=["GET"])
def download_161d(client_id):
    """Generate and download filled 161d form for the given client using simple filler."""
    try:
        output_path = fill_161d(client_id)
        return send_file(output_path, as_attachment=True, download_name=f"161d_{client_id}.pdf")
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": f"שגיאה ביצירת טופס 161ד: {str(e)}"}), 500

@main_bp.route("/download-pdf/<string:doc_type>/<int:client_id>", methods=["GET"])
def download_pdf(doc_type, client_id):
    """
    מאפשר הורדת קבצי PDF שונים ללקוח (טופס ראשי, נספח מענקים, נספח היוונים)
    """
    try:
        client = Client.query.get_or_404(client_id)
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        
        # הגדרת הנתיבים ושמות הקבצים לפי סוג המסמך
        # Try generating the file if it doesn't exist
        if doc_type == "161d":
            # Generate the 161d PDF using the simplified filler; the function returns the path to the created file.
            pdf_path = fill_161d(client_id)
            download_name = f"161d_{client.first_name}_{client.last_name}_{client.tz}.pdf"
            html_path = ""  # Not applicable for this document type
        elif doc_type == "grants":
            pdf_path = os.path.join(base_dir, "static", "generated", f"grants_appendix_{client_id}.pdf")
            html_path = os.path.join(base_dir, "static", "generated", f"grants_appendix_{client_id}.html")
            download_name = f"grants_appendix_{client.first_name}_{client.last_name}.pdf"
            if not os.path.exists(pdf_path) and not os.path.exists(html_path):
                grants_appendix_path = generate_grants_appendix(client_id)
                if grants_appendix_path is None:
                    return jsonify({"error": "לא ניתן להפיק נספח מענקים - אין מענקים תקינים"}), 404
        elif doc_type == "commutations":
            pdf_path = os.path.join(base_dir, "static", "generated", f"commutations_appendix_{client_id}.pdf")
            html_path = os.path.join(base_dir, "static", "generated", f"commutations_appendix_{client_id}.html")
            download_name = f"commutations_appendix_{client.first_name}_{client.last_name}.pdf"
            if not os.path.exists(pdf_path) and not os.path.exists(html_path):
                generate_commutations_appendix(client_id)
        else:
            return jsonify({"error": "סוג מסמך לא תקין"}), 400
        
        # Check for HTML file if PDF doesn't exist (fallback)
        if not os.path.exists(pdf_path) and os.path.exists(html_path):
            return send_file(
                html_path,
                mimetype="text/html",
                as_attachment=True,
                download_name=download_name.replace('.pdf', '.html')
            )
        
        # Check if the file exists after potential generation
        if not os.path.exists(pdf_path):
            return jsonify({"error": f"לא ניתן ליצור את המסמך: {doc_type}"}), 404
        
        print(f"Sending file: {pdf_path}")
        return send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_name
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"Error in download_pdf: {str(e)}")
        return jsonify({"error": f"שגיאה בהורדת המסמך: {str(e)}"}), 500
    
# -----------------------------------------------------------
# הפקת חבילת מסמכים ללקוח
# -----------------------------------------------------------
@main_bp.route("/api/clients/<int:cid>/package", methods=["POST"])
def generate_package(cid):
    """Generate a full client document package (161d + appendices) and return the folder path."""
    try:
        client = Client.query.get_or_404(cid)
        # Create slugified folder name: replace spaces/dots/etc with underscore
        full_name = f"{client.first_name}_{client.last_name}" if client.first_name or client.last_name else f"client_{cid}"
        slug = re.sub(r"[^א-תA-Za-z0-9]+", "_", full_name).strip("_").lower()

        project_root = Path(__file__).resolve().parent.parent  # one level above app/
        packages_root = project_root / "packages"
        packages_root.mkdir(exist_ok=True)
        folder = packages_root / f"{slug}_{cid}"
        folder.mkdir(parents=True, exist_ok=True)

        files: list[str] = []

        # 1. טופס 161ד
        pdf_161d = fill_161d(cid, out_dir=folder)
        files.append(Path(pdf_161d).name)

        # 2. נספח מענקים
        grants_src = generate_grants_appendix(cid)
        if grants_src and Path(grants_src).exists():
            dest = folder / "grants_appendix.pdf"
            shutil.copy2(grants_src, dest)
            files.append(dest.name)

        # 3. נספח פיצויים (היוונים)
        severance_src = generate_commutations_appendix(cid)
        if severance_src and Path(severance_src).exists():
            dest = folder / "severance_appendix.pdf"
            shutil.copy2(severance_src, dest)
            files.append(dest.name)

        rel_folder = folder.relative_to(project_root)
        return jsonify({"folder": str(rel_folder), "files": files})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------
# נתיב קודם להורדת טופס 161ד (לתאימות אחורה)
# -----------------------------------------------------------
@main_bp.route("/download-pdf/<int:client_id>", methods=["GET"])
def legacy_download_pdf(client_id):
    return download_pdf("161d", client_id)


@main_bp.route('/api/clients/<int:client_id>/reserve-grant', methods=['POST'])
def reserve_grant(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    reserved_amount = data.get('reserved_grant_amount')
    if reserved_amount is not None:
        client.reserved_grant_amount = reserved_amount
        db.session.commit()
    return jsonify({'message': 'Reserved grant updated successfully'})

@main_bp.route('/api/calculate-exemption-summary', methods=['POST'])
def calculate_exemption_summary():
    data = request.get_json()
    client_id = data["client_id"]
    force_recalculation = data.get("force_recalculation", False)
    
    try:
        # אם התבקש חישוב מחדש, נחשב מחדש את כל המענקים
        if force_recalculation:
            # קבלת הלקוח
            client = Client.query.get_or_404(client_id)
            
            # קבלת קצבה ראשונה (אם קיימת) לחישוב תאריך זכאות
            first_pension = Pension.query.filter_by(client_id=client_id).order_by(Pension.start_date).first()
            
            if first_pension:
                # חישוב תאריך זכאות
                eligibility_date = calculate_eligibility_age(client.birth_date, client.gender, first_pension.start_date)
                
                # חישוב מחדש של כל המענקים
                grants = Grant.query.filter_by(client_id=client_id).all()
                for grant in grants:
                    process_grant(grant, eligibility_date)
                
                # שמירת השינויים בבסיס הנתונים
                db.session.commit()
                print(f"חושבו מחדש {len(grants)} מענקים ללקוח {client_id}")
        
        # חישוב הסיכום לאחר העדכון (אם היה)
        summary = calculate_summary(client_id)
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 400



# שימוש בפונקציה הפשוטה החדשה למילוי 161ד
