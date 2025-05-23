from flask import Blueprint, jsonify, request, send_file
import os
from app.models import db, Client, Grant, Pension, Commutation
from app.utils import (
    calculate_eligibility_age, 
    calculate_indexed_grant, 
    calculate_grant_ratio,
    calculate_grant_impact,
    get_exemption_cap_by_year,
    fetch_indexation_factor,
    calculate_total_grant_impact,
    calculate_total_commutation_impact,
    calculate_available_exemption_cap,
    calculate_final_exempt_amount
)
from datetime import date

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
        "address": client.address
    })

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
    
    # Create a temporary Grant object
    grant = Grant(
        grant_amount=data['amount'],
        grant_date=date.fromisoformat(data['grant_date'])
    )
    
    eligibility_date = date.fromisoformat(data['eligibility_date'])
    
    try:
        indexed_amount = calculate_indexed_grant(grant, eligibility_date)
        return jsonify({
            "original_amount": grant.grant_amount,
            "indexed_amount": indexed_amount,
            "indexation_factor": indexed_amount / grant.grant_amount if grant.grant_amount > 0 else 0
        })
    except ValueError as e:
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
    
    # 1. חישוב סכום מוצמד
    indexed_amount = fetch_indexation_factor(grant_date, eligibility_date, grant_amount)
    
    # 2. חישוב חלק יחסי
    ratio = calculate_grant_ratio(grant_start_date, grant_end_date, eligibility_date)
    
    # 3. חישוב פגיעה בתקרה
    impact = calculate_grant_impact(grant_amount, indexed_amount/grant_amount, ratio)
    
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

@main_bp.route('/api/calculate-exemption-summary', methods=['POST'])
def api_calculate_exemption_summary():
    """
    חישוב סיכום פטור כולל לקצבה ללקוח לפי המבנה החדש
    """
    data = request.get_json()
    client_id = data.get('client_id')
    
    try:
        # שימוש בפונקציה החדשה לחישוב הסיכום
        summary = calculate_summary(client_id)
        
        # עדכון בדטאבייס
        db.session.commit()
        
        return jsonify(summary)
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"שגיאה בחישוב הסיכום: {str(e)}"}), 500

from app.pdf_filler import fill_pdf_form, generate_grants_appendix, generate_commutations_appendix
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
@main_bp.route("/api/clients/<int:client_id>/pensions", methods=["POST"])
def add_pension_to_client(client_id):
    data = request.get_json()
    pension = Pension(
        client_id=client_id,
        payer_name=data.get('payer_name'),
        start_date=date.fromisoformat(data.get('start_date')) if data.get('start_date') else None
    )
    db.session.add(pension)
    db.session.commit()
    return jsonify(pension.to_dict()), 201

# קבלת רשימת היוונים לקצבה
@main_bp.route("/api/pensions/<int:pension_id>/commutations", methods=["GET"])
def get_pension_commutations(pension_id):
    pension = Pension.query.get_or_404(pension_id)
    return jsonify([c.to_dict() for c in pension.commutations])

# הוספת היוון לקצבה
@main_bp.route("/api/pensions/<int:pension_id>/commutations", methods=["POST"])
def add_commutation_to_pension(pension_id):
    data = request.get_json()
    commutation = Commutation(
        pension_id=pension_id,
        amount=data.get('amount'),
        date=date.fromisoformat(data.get('date')) if data.get('date') else None,
        full_or_partial=data.get('full_or_partial', 'partial')
    )
    db.session.add(commutation)
    db.session.commit()
    return jsonify(commutation.to_dict()), 201

@main_bp.route("/api/fill-161d-pdf", methods=["POST"])
def api_fill_161d_pdf():
    """
    מקבל מזהה לקוח, מחשב את סיכום הפטור לקצבה, וממלא טופס 161ד
    """
    try:
        data = request.get_json()
        client_id = data["client_id"]
    
        # שליפת נתוני הלקוח
        client = Client.query.get_or_404(client_id)
        
        # חישוב הסיכום עם הפונקציה החדשה
        summary = calculate_summary(client_id)
        
        # קבלת תאריכים נדרשים
        elig_date = datetime.fromisoformat(summary["client_info"]["eligibility_date"])
    
        # הכנת נתונים למילוי הטופס לפי המבנה החדש
        form_data = {
            # פרטי לקוח
            "full_name": f"{client.first_name} {client.last_name}",
            "tz": client.tz,
            "birth_date": client.birth_date.strftime("%d/%m/%Y"),
            "eligibility_date": elig_date.strftime("%d/%m/%Y"),
            
            # סיכום חישובים לפי הסדר החדש
            "cap_exempt": str(summary["exempt_cap"]),                 # 1. תקרת ההון הפטורה
            "grants_nominal": str(summary["grants_nominal"]),         # 2. סך מענקים פטורים נומינליים
            "grants_indexed": str(summary["grants_indexed"]),         # 3. סך מענקים פטורים מוצמדים
            "grants_impact": str(summary["grants_impact"]),           # 4. סך פגיעה בפטור
            "comm_total": str(summary["commutations_total"]),         # 5. סך היוונים
            "remaining_cap": str(summary["remaining_cap"]),           # 6. הפרש תקרת הון פטורה
            "monthly_cap": str(summary["monthly_cap"]),               # 7. תקרת קצבה מזכה
            "pension_exempt": str(summary["pension_exempt"]),         # 8. קצבה פטורה מחושבת
            "pension_rate": f'{summary["pension_rate"]}%',            # 9. אחוז הקצבה הפטורה
        }
    
        # נתיבים לקבצי PDF
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        input_pdf = os.path.join(base_dir, "static", "templates", "161ד.pdf")
        output_dir = os.path.join(base_dir, "static", "generated")
        
        # וידוא שהתיקייה קיימת
        os.makedirs(output_dir, exist_ok=True)
        
        output_pdf = os.path.join(output_dir, f"161ד_מלא_{client_id}.pdf")
    
        # מילוי הטופס
        fill_pdf_form(input_pdf, output_pdf, form_data)
        
        # יצירת נספחים
        grants_appendix_path = generate_grants_appendix(client_id)
        commutations_appendix_path = generate_commutations_appendix(client_id)
        
        # הכנת נתיבים יחסיים
        response = {
            "message": "PDF נוצר בהצלחה", 
            "main_pdf": {
                "path": f"static/generated/161ד_מלא_{client_id}.pdf",
                "download_url": f"/download-pdf/161d/{client_id}"
            }
        }
        
        # הוספת נתיבי הנספחים אם נוצרו
        if grants_appendix_path:
            response["grants_appendix"] = {
                "path": f"static/generated/נספח_מענקים_{client_id}.pdf",
                "download_url": f"/download-pdf/grants/{client_id}"
            }
            
        if commutations_appendix_path:
            response["commutations_appendix"] = {
                "path": f"static/generated/נספח_היוונים_{client_id}.pdf",
                "download_url": f"/download-pdf/commutations/{client_id}"
            }
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"שגיאה ביצירת ה-PDF: {str(e)}"}), 500


@main_bp.route("/download-pdf/<string:doc_type>/<int:client_id>", methods=["GET"])
def download_pdf(doc_type, client_id):
    """
    מאפשר הורדת קבצי PDF שונים ללקוח (טופס ראשי, נספח מענקים, נספח היוונים)
    """
    client = Client.query.get_or_404(client_id)
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    # הגדרת הנתיבים ושמות הקבצים לפי סוג המסמך
    if doc_type == "161d":
        pdf_path = os.path.join(base_dir, "static", "generated", f"161ד_מלא_{client_id}.pdf")
        download_name = f"161ד_{client.first_name}_{client.last_name}_{client.tz}.pdf"
    elif doc_type == "grants":
        pdf_path = os.path.join(base_dir, "static", "generated", f"נספח_מענקים_{client_id}.pdf")
        download_name = f"נספח_מענקים_{client.first_name}_{client.last_name}.pdf"
    elif doc_type == "commutations":
        pdf_path = os.path.join(base_dir, "static", "generated", f"נספח_היוונים_{client_id}.pdf")
        download_name = f"נספח_היוונים_{client.first_name}_{client.last_name}.pdf"
    else:
        return jsonify({"error": "סוג מסמך לא תקין"}), 400
    
    if not os.path.exists(pdf_path):
        return jsonify({"error": "קובץ PDF לא נמצא"}), 404
    
    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=download_name
    )
    
# שמירת נתיב ישן לתאימות לאחור
@main_bp.route("/download-pdf/<int:client_id>", methods=["GET"])
def legacy_download_pdf(client_id):
    """נתיב קודם להורדת קובץ (לתאימות אחורה)"""
    return download_pdf("161d", client_id)


@main_bp.route("/api/calculate-exemption-summary", methods=["POST"])
def calculate_exemption_summary():
    data = request.get_json()
    client_id = data["client_id"]
    client = Client.query.get_or_404(client_id)
    pension = client.pensions[0]
    eligibility_date = calculate_eligibility_age(client.birth_date, client.gender, pension.start_date)
    grants = client.grants
    commutations = [c for p in client.pensions for c in p.commutations]

    summary = {
        "grant_total": calculate_total_grant_impact(grants),
        "commutation_total": calculate_total_commutation_impact(commutations),
        "exemption_cap": get_exemption_cap_by_year(eligibility_date.year),
    }
    summary["final_exemption"] = calculate_final_exempt_amount(
        summary["exemption_cap"] - summary["grant_total"],
        summary["commutation_total"]
    )

    return jsonify(summary)


@main_bp.route("/api/fill-161d-pdf", methods=["POST"])
def fill_161d_pdf():
    data = request.get_json()
    client_id = data["client_id"]
    client = Client.query.get_or_404(client_id)
    pension = client.pensions[0]
    eligibility_date = calculate_eligibility_age(client.birth_date, client.gender, pension.start_date)
    grants = client.grants
    commutations = [c for p in client.pensions for c in p.commutations]

    summary = {
        "grant_total": calculate_total_grant_impact(grants),
        "commutation_total": calculate_total_commutation_impact(commutations),
        "exemption_cap": get_exemption_cap_by_year(eligibility_date.year),
    }
    summary["final_exemption"] = calculate_final_exempt_amount(
        summary["exemption_cap"] - summary["grant_total"],
        summary["commutation_total"]
    )

    form_data = {
        "full_name": f"{client.first_name} {client.last_name}",
        "tz": client.tz,
        "birth_date": client.birth_date.strftime("%d/%m/%Y"),
        "eligibility_date": eligibility_date.strftime("%d/%m/%Y"),
        "grant_total": summary["grant_total"],
        "commutation_total": summary["commutation_total"],
        "exemption_cap": summary["exemption_cap"],
        "final_exemption": summary["final_exemption"],
    }

    input_pdf = "static/templates/161ד.pdf"
    output_pdf = f"static/generated/161ד_מלא_{client_id}.pdf"

    fill_pdf_form(input_pdf, output_pdf, form_data)

    return jsonify({"path": output_pdf})
