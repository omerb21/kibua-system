import os
import tempfile
import pdfkit
from datetime import datetime
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName
from app.models import Client, Grant, Pension, Commutation

def fill_pdf_form(input_path: str, output_path: str, data: dict):
    """
    ממלא טופס PDF מבוסס AcroForm עם נתונים
    
    Args:
        input_path: נתיב לקובץ PDF המקורי
        output_path: נתיב לשמירת קובץ PDF מלא
        data: מילון של שדות ונתונים למילוי
    """
    template_pdf = PdfReader(input_path)
    for page in template_pdf.pages:
        annotations = page['/Annots']
        if annotations:
            for annotation in annotations:
                if annotation['/Subtype'] == '/Widget' and annotation.get('/T'):
                    field_name = annotation['/T'][1:-1]  # Strip parentheses
                    if field_name in data:
                        annotation.update(
                            PdfDict(V=str(data[field_name]), Ff=1)
                        )

    PdfWriter().write(output_path, template_pdf)


def generate_grants_appendix(client_id: int) -> str:
    """
    יוצר נספח PDF עם טבלת המענקים של הלקוח
    
    Args:
        client_id: מזהה הלקוח
        
    Returns:
        נתיב לקובץ ה-PDF שנוצר
    """
    client = Client.query.get_or_404(client_id)
    grants = Grant.query.filter_by(client_id=client_id).all()
    
    # אם אין מענקים, לא ניצור נספח
    if not grants:
        return None
    
    # יצירת HTML טבלה
    html_content = f'''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>נספח מענקים - {client.first_name} {client.last_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; direction: rtl; }}
            h1 {{ text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
            th {{ background-color: #f2f2f2; }}
            .sum-row {{ font-weight: bold; background-color: #e6e6e6; }}
        </style>
    </head>
    <body>
        <h1>נספח מענקים - {client.first_name} {client.last_name}</h1>
        <h3>מספר זהות: {client.tz}</h3>
        <p>תאריך הפקה: {datetime.now().strftime('%d/%m/%Y')}</p>
        
        <table>
            <thead>
                <tr>
                    <th>מעסיק</th>
                    <th>תאריך תחילת עבודה</th>
                    <th>תאריך סיום עבודה</th>
                    <th>סכום נומינלי</th>
                    <th>תאריך קבלה</th>
                    <th>סכום מוצמד</th>
                    <th>יחס</th>
                    <th>השפעה על הפטור</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    # הוספת שורות לטבלה
    total_nominal = 0
    total_indexed = 0
    total_impact = 0
    
    for grant in grants:
        nominal = grant.grant_amount or 0
        indexed = grant.grant_indexed_amount or 0
        ratio = grant.grant_ratio or 0
        impact = grant.impact_on_exemption or 0
        
        total_nominal += nominal
        total_indexed += indexed * ratio
        total_impact += impact
        
        html_content += f'''
                <tr>
                    <td>{grant.employer_name or ''}</td>
                    <td>{grant.work_start_date.strftime('%d/%m/%Y') if grant.work_start_date else ''}</td>
                    <td>{grant.work_end_date.strftime('%d/%m/%Y') if grant.work_end_date else ''}</td>
                    <td>{format(nominal, ',.2f')} ₪</td>
                    <td>{grant.grant_date.strftime('%d/%m/%Y') if grant.grant_date else ''}</td>
                    <td>{format(indexed, ',.2f')} ₪</td>
                    <td>{ratio:.2%}</td>
                    <td>{format(impact, ',.2f')} ₪</td>
                </tr>
        '''
    
    # הוספת שורת סיכום
    html_content += f'''
                <tr class="sum-row">
                    <td colspan="3">סה"כ</td>
                    <td>{format(total_nominal, ',.2f')} ₪</td>
                    <td></td>
                    <td>{format(total_indexed, ',.2f')} ₪</td>
                    <td></td>
                    <td>{format(total_impact, ',.2f')} ₪</td>
                </tr>
            </tbody>
        </table>
        
        <p><strong>הערה:</strong> השפעה על הפטור מחושבת לפי סכום מוצמד × יחס × 1.35</p>
    </body>
    </html>
    '''
    
    # יצירת קובץ PDF מ-HTML
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    output_dir = os.path.join(base_dir, "static", "generated")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"נספח_מענקים_{client_id}.pdf")
    
    # יצירת הקובץ בעזרת pdfkit
    pdfkit.from_string(html_content, output_path, options={
        'encoding': 'UTF-8',
        'page-size': 'A4',
        'margin-top': '10mm',
        'margin-right': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'orientation': 'landscape'
    })
    
    return output_path


def generate_commutations_appendix(client_id: int) -> str:
    """
    יוצר נספח PDF עם טבלת ההיוונים של הלקוח
    
    Args:
        client_id: מזהה הלקוח
        
    Returns:
        נתיב לקובץ ה-PDF שנוצר
    """
    client = Client.query.get_or_404(client_id)
    pensions = Pension.query.filter_by(client_id=client_id).all()
    
    # אוסף את כל ההיוונים מכל הקצבאות
    all_commutations = []
    for pension in pensions:
        commutations = Commutation.query.filter_by(pension_id=pension.id).all()
        for comm in commutations:
            all_commutations.append((pension.payer_name, comm))
    
    # אם אין היוונים, לא ניצור נספח
    if not all_commutations:
        return None
    
    # יצירת HTML טבלה
    html_content = f'''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>נספח היוונים - {client.first_name} {client.last_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; direction: rtl; }}
            h1 {{ text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
            th {{ background-color: #f2f2f2; }}
            .sum-row {{ font-weight: bold; background-color: #e6e6e6; }}
            .not-included {{ color: #999; text-decoration: line-through; }}
        </style>
    </head>
    <body>
        <h1>נספח היוונים - {client.first_name} {client.last_name}</h1>
        <h3>מספר זהות: {client.tz}</h3>
        <p>תאריך הפקה: {datetime.now().strftime('%d/%m/%Y')}</p>
        
        <table>
            <thead>
                <tr>
                    <th>משלם הקצבה</th>
                    <th>משלם ההיוון</th>
                    <th>תאריך היוון</th>
                    <th>סכום</th>
                    <th>סוג היוון</th>
                    <th>נכלל בחישוב</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    # הוספת שורות לטבלה
    total_amount = 0
    total_included = 0
    
    for pension_name, commutation in all_commutations:
        amount = commutation.amount or 0
        included = commutation.include_calc
        
        if included:
            total_included += amount
        total_amount += amount
        
        row_class = "" if included else "not-included"
        
        html_content += f'''
                <tr class="{row_class}">
                    <td>{pension_name or ''}</td>
                    <td>{commutation.payer_name or ''}</td>
                    <td>{commutation.date.strftime('%d/%m/%Y') if commutation.date else ''}</td>
                    <td>{format(amount, ',.2f')} ₪</td>
                    <td>{"מלא" if commutation.full_or_partial == "full" else "חלקי"}</td>
                    <td>{"כן" if included else "לא"}</td>
                </tr>
        '''
    
    # הוספת שורת סיכום
    html_content += f'''
                <tr class="sum-row">
                    <td colspan="3">סה"כ</td>
                    <td>{format(total_amount, ',.2f')} ₪</td>
                    <td colspan="2">סה"כ נכלל בחישוב: {format(total_included, ',.2f')} ₪</td>
                </tr>
            </tbody>
        </table>
        
        <p><strong>הערה:</strong> רק היוונים המסומנים כ"נכלל בחישוב" נלקחים בחשבון בחישוב הפטור הסופי.</p>
    </body>
    </html>
    '''
    
    # יצירת קובץ PDF מ-HTML
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    output_dir = os.path.join(base_dir, "static", "generated")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"נספח_היוונים_{client_id}.pdf")
    
    # יצירת הקובץ בעזרת pdfkit
    pdfkit.from_string(html_content, output_path, options={
        'encoding': 'UTF-8',
        'page-size': 'A4',
        'margin-top': '10mm',
        'margin-right': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm'
    })
    
    return output_path
