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
    חישוב סיכום פטור כולל לקצבה ללקוח:
    1. איסוף כל המענקים הפטורים וההיוונים
    2. חישוב סך הפגיעות בתקרת ההון
    3. חישוב יתרת תקרה וסכום פטור סופי
    """
    data = request.get_json()
    client_id = data.get('client_id')
    
    # בדיקה שהלקוח קיים
    client = Client.query.get_or_404(client_id)
    
    # קבלת קצבה ראשונה (אם קיימת)
    first_pension = Pension.query.filter_by(client_id=client_id).order_by(Pension.start_date).first()
    if not first_pension:
        return jsonify({"error": "לא נמצאה קצבה ללקוח"}), 404
    
    # שליפת כל המענקים של הלקוח
    grants = Grant.query.filter_by(client_id=client_id).all()
    
    # שליפת היוונים מכל הקצבאות
    all_commutations = []
    pensions = Pension.query.filter_by(client_id=client_id).all()
    for pension in pensions:
        commutations = Commutation.query.filter_by(pension_id=pension.id).all()
        all_commutations.extend(commutations)
    
    # קביעת תאריך הזכאות
    eligibility_date = calculate_eligibility_age(client.birth_date, client.gender, first_pension.start_date)
    eligibility_year = eligibility_date.year
    
    # עדכון וחישוב השפעת המענקים
    for grant in grants:
        # חישוב סכום מוצמד
        indexed_amount = fetch_indexation_factor(grant.grant_date, eligibility_date, grant.grant_amount)
        grant.grant_indexed_amount = indexed_amount
        
        # חישוב חלק יחסי
        ratio = calculate_grant_ratio(grant.work_start_date, grant.work_end_date, eligibility_date)
        grant.grant_ratio = ratio
        
        # חישוב פגיעה בתקרה
        impact = calculate_grant_impact(grant.grant_amount, indexed_amount/grant.grant_amount, ratio)
        grant.impact_on_exemption = impact
    
    # סיכום כל הפגיעות
    total_grant_impact = calculate_total_grant_impact(grants)
    total_commutation_impact = calculate_total_commutation_impact(all_commutations)
    
    # חישוב יתרת תקרה זמינה
    exemption_cap = get_exemption_cap_by_year(eligibility_year)
    available_cap = calculate_available_exemption_cap(eligibility_year, total_grant_impact)
    
    # חישוב סכום פטור סופי
    final_exempt = calculate_final_exempt_amount(available_cap, total_commutation_impact)
    
    # עדכון בדטאבייס
    db.session.commit()
    
    # הכנת תשובה
    result = {
        "client_info": {
            "id": client.id,
            "name": f"{client.first_name} {client.last_name}",
            "eligibility_date": eligibility_date.isoformat()
        },
        "exemption_summary": {
            "total_grant_impact": total_grant_impact,
            "total_commutation_impact": total_commutation_impact,
            "exemption_cap_for_year": exemption_cap,
            "available_exemption_cap": available_cap,
            "final_exempt_amount": final_exempt
        },
        "details": {
            "grants_count": len(grants),
            "commutations_count": len(all_commutations)
        }
    }
    
    return jsonify(result)


from app.pdf_filler import fill_pdf_form

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
    data = request.get_json()
    client_id = data["client_id"]

    # שליפת נתוני הלקוח
    client = Client.query.get_or_404(client_id)
    
    # בדיקה שיש לפחות קצבה אחת
    if not client.pensions:
        return jsonify({"error": "ללקוח אין קצבאות"}), 404
    
    pension = client.pensions[0]
    eligibility_date = calculate_eligibility_age(client.birth_date, client.gender, pension.start_date)

    # שליפת מענקים והיוונים
    grants = client.grants
    commutations = [c for p in client.pensions for c in p.commutations]

    # חישוב סיכום הפטור
    summary = {
        "grant_total": calculate_total_grant_impact(grants),
        "commutation_total": calculate_total_commutation_impact(commutations),
        "exemption_cap": get_exemption_cap_by_year(eligibility_date.year),
    }
    summary["final_exemption"] = calculate_final_exempt_amount(
        summary["exemption_cap"] - summary["grant_total"],
        summary["commutation_total"]
    )

    # הכנת נתונים למילוי הטופס
    form_data = {
        "full_name": f"{client.first_name} {client.last_name}",
        "tz": client.tz,
        "birth_date": client.birth_date.strftime("%d/%m/%Y"),
        "eligibility_date": eligibility_date.strftime("%d/%m/%Y"),
        "grant_total": str(summary["grant_total"]),
        "commutation_total": str(summary["commutation_total"]),
        "exemption_cap": str(summary["exemption_cap"]),
        "final_exemption": str(summary["final_exemption"]),
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

    # חזרת נתיב יחסי למערכת
    relative_path = f"static/generated/161ד_מלא_{client_id}.pdf"
    download_url = f"/download-pdf/{client_id}"
    
    return jsonify({"message": "PDF נוצר בהצלחה", "path": relative_path, "download_url": download_url})


@main_bp.route("/download-pdf/<int:client_id>", methods=["GET"])
def download_pdf(client_id):
    """
    הורדת טופס 161ד מלא עבור לקוח מסויים
    """
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    pdf_path = os.path.join(base_dir, "static", "generated", f"161ד_מלא_{client_id}.pdf")
    
    if not os.path.exists(pdf_path):
        return jsonify({"error": "הקובץ לא נמצא"}), 404
        
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"161ד_מלא_{client_id}.pdf",
        mimetype="application/pdf"
    )


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
