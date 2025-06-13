import os
import tempfile
import pdfkit
import subprocess
import platform
from datetime import datetime, date
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName
from app.models import Client, Grant, Pension, Commutation

# Check if wkhtmltopdf is installed and configure its path
def find_wkhtmltopdf_path():
    """Tries to find the wkhtmltopdf executable path"""
    try:
        # For Windows
        if platform.system() == 'Windows':
            # Common installation locations
            possible_paths = [
                r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
                r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
                # Add more potential paths if needed
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
                    
            # Try to find it in PATH
            try:
                result = subprocess.run(['where', 'wkhtmltopdf'], 
                                      capture_output=True, 
                                      text=True, 
                                      check=True)
                if result.stdout.strip():
                    return result.stdout.strip()
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
        
        # For Linux/Mac
        else:
            try:
                result = subprocess.run(['which', 'wkhtmltopdf'], 
                                      capture_output=True, 
                                      text=True, 
                                      check=True)
                if result.stdout.strip():
                    return result.stdout.strip()
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
                
    except Exception as e:
        print(f"Error finding wkhtmltopdf: {e}")
    
    return None

# Configure pdfkit with wkhtmltopdf path if found
wkhtmltopdf_path = find_wkhtmltopdf_path()
if wkhtmltopdf_path:
    pdfkit_config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    print(f"Found wkhtmltopdf at: {wkhtmltopdf_path}")
else:
    pdfkit_config = None
    print("wkhtmltopdf not found. PDF generation will fallback to HTML files.")


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
    from app.routes import process_grant
    from app.utils import calculate_eligibility_age
    
    client = Client.query.get_or_404(client_id)
    grants = Grant.query.filter_by(client_id=client_id).all()
    
    # חישוב מחדש של המענקים לפני יצירת הנספח
    from app.indexation import index_grant, work_ratio_within_last_32y
    first_pension = Pension.query.filter_by(client_id=client_id).order_by(Pension.start_date).first()
    
    # רשימת המענקים המחושבת מחדש
    recalculated_grants = []
    
    if first_pension:
        # חישוב תאריך זכאות
        eligibility_date = calculate_eligibility_age(client.birth_date, client.gender, first_pension.start_date)
        print(f"תאריך זכאות: {eligibility_date.isoformat()}")
        
        # חישוב מחדש של כל המענקים
        print(f"חישוב מחדש של {len(grants)} מענקים ללקוח {client_id}")
        
        for grant in grants:
            try:
                # בדיקת תקינות נתונים
                if not grant.grant_amount:
                    print(f"מענק {grant.id} חסר סכום - דילוג")
                    continue
                if not grant.work_start_date or not grant.work_end_date:
                    print(f"מענק {grant.id} חסר תאריכים - דילוג")
                    continue
                
                # חישוב מחדש בצורה מדויקת
                indexed_full = index_grant(
                    amount=grant.grant_amount,
                    start_date=grant.work_start_date.isoformat(),
                    end_work_date=grant.work_end_date.isoformat(),
                    elig_date=eligibility_date.isoformat()
                )
                
                # בדיקה שההצמדה הצליחה
                if indexed_full is None:
                    print(f"הצמדה נכשלה עבור מענק {grant.id} – דילוג")
                    continue

                # חישוב יחס העבודה
                try:
                    ratio = work_ratio_within_last_32y(
                        grant.work_start_date,
                        grant.work_end_date,
                        eligibility_date
                    )
                    if ratio is None or ratio <= 0:
                        print(f"יחס עבודה לא תקין עבור מענק {grant.id} - דילוג")
                        continue
                except Exception as ratio_error:
                    print(f"שגיאה בחישוב יחס עבודה עבור מענק {grant.id}: {ratio_error}")
                    continue
                
                # הסכום המוצמד כפול היחס
                indexed_amount = indexed_full * ratio
                impact = indexed_amount * 1.35
                
                # שמירת הנתונים המחושבים מחדש
                recalculated_grant = {
                    'original': grant,
                    'indexed_full': indexed_full,
                    'ratio': ratio,
                    'indexed_amount': indexed_amount,
                    'impact': impact,
                    'relevant_nominal': grant.grant_amount * ratio  # סכום נומינלי רלוונטי
                }
                recalculated_grants.append(recalculated_grant)
                
                print(f"מענק {grant.id}: סכום={grant.grant_amount}, מוצמד מלא={indexed_full}, יחס={ratio}, סכום מוצמד יחסי={indexed_amount}, השפעה={impact}")
            except Exception as e:
                print(f"מענק {grant.id} נכשל ולא נכנס לנספח: {e}")
                continue  # דילוג על מענק בעייתי
    
    # אם אין מענקים, לא ניצור נספח
    if not grants:
        return None
        
    # אם כל המענקים נכשלו בהצמדה, לא ניצור נספח
    if not recalculated_grants:
        print(f"אין מענקים תקינים עבור לקוח {client_id}, הפקת נספח בוטלה.")
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
        
        <table class="grants-table">
            <thead>
                <tr>
                    <th>מעסיק</th>
                    <th>תאריך תחילת עבודה</th>
                    <th>תאריך סיום עבודה</th>
                    <th>סכום נומינלי</th>
                    <th>תאריך קבלה</th>
                    <th>מענק נומינלי רלוונטי לקיבוע זכויות</th>
                    <th>מענק פטור צמוד</th>
                    <th>השפעה על הפטור</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    # הוספת שורות לטבלה מהערכים המחושבים מחדש
    # איפוס משתני סיכום
    total_nominal = 0
    total_indexed = 0
    total_impact = 0
    total_relevant_nominal = 0
    
    # אם יש ערכים מחושבים מחדש, נשתמש בהם
    grants_to_use = recalculated_grants if recalculated_grants else [{'original': g, 'indexed_amount': g.grant_indexed_amount, 'ratio': g.grant_ratio, 'impact': g.impact_on_exemption} for g in grants]
    
    # מיון המענקים לפי תאריך סיום עבודה ועיבוד כל מענק בנפרד
    for grant_data in grants_to_use:
        grant = grant_data['original']
        nominal_amount = grant.grant_amount
        relevant_nominal = grant_data.get('relevant_nominal', nominal_amount) 
        indexed_amount = grant_data.get('indexed_amount', 0)
        impact = grant_data.get('impact', 0)
        
        # הוספת סכומים לסיכום הכולל
        total_nominal += nominal_amount
        total_relevant_nominal += relevant_nominal
        total_indexed += indexed_amount
        total_impact += impact
        
        html_content += f'''
                <tr>
                    <td>{grant.employer_name or ''}</td>
                    <td>{grant.work_start_date.strftime('%d/%m/%Y') if grant.work_start_date else ''}</td>
                    <td>{grant.work_end_date.strftime('%d/%m/%Y') if grant.work_end_date else ''}</td>
                    <td>{format(nominal_amount, ',.2f')} ₪</td>
                    <td>{grant.grant_date.strftime('%d/%m/%Y') if grant.grant_date else ''}</td>
                    <td>{format(relevant_nominal, ',.2f')} ₪</td>
                    <td>{format(indexed_amount, ',.2f')} ₪</td>
                    <td>{format(impact, ',.2f')} ₪</td>
                </tr>
        '''
    
    # כל הסכומים כבר חושבו בלולאה לעיל ומוכנים להצגה
    
    # הוספת שורת סיכום
    html_content += f'''
                <tr class="total-row">
                    <td colspan="3">סה"כ</td>
                    <td>{format(total_nominal, ',.2f')} ₪</td>
                    <td></td>
                    <td>{format(total_relevant_nominal, ',.2f')} ₪</td>
                    <td>{format(total_indexed, ',.2f')} ₪</td>
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
    
    output_path = os.path.join(output_dir, f"grants_appendix_{client_id}.pdf")
    
    # שמירת ה-HTML לקובץ זמני
    html_temp_file = os.path.join(output_dir, f"grants_appendix_{client_id}.html")
    with open(html_temp_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    try:
        # ניסיון ליצור קובץ PDF עם wkhtmltopdf
        if pdfkit_config:
            pdfkit.from_file(html_temp_file, output_path, options={
                'encoding': 'UTF-8',
                'page-size': 'A4',
                'margin-top': '10mm',
                'margin-right': '10mm',
                'margin-bottom': '10mm',
                'margin-left': '10mm',
                'orientation': 'landscape'
            }, configuration=pdfkit_config)
        else:
            # אם wkhtmltopdf לא נמצא, נודיע שמשתמשים בקובץ HTML במקום
            print("Using HTML file instead of PDF due to missing wkhtmltopdf")
            output_path = html_temp_file
    except Exception as e:
        print(f"Error generating PDF with pdfkit: {e}")
        # אם הייתה שגיאה, נחזיר את הקובץ HTML במקום PDF
        output_path = html_temp_file
    
    return output_path


def fill_161d_form(client_id: int) -> str:
    """
    ממלא טופס 161ד עם נתוני הלקוח
    
    Args:
        client_id: מזהה הלקוח
        
    Returns:
        נתיב לקובץ ה-PDF שנוצר
    """
    from pathlib import Path
    from app.utils import calculate_eligibility_age, calculate_summary
    
    client = Client.query.get_or_404(client_id)
    
    # חישוב סיכום מלא עם כל הנתונים הדרושים
    summary = calculate_summary(client_id)
    print("### Summary keys:", list(summary.keys()))
    
    # פונקציית עזר לגישה בטוחה לתכונות
    def safe_value(dict_obj, key, default=0):
        return dict_obj.get(key, default)
    
    # פונקציה לעיצוב מספרים
    def format_number(value, default=''):
        if value in (None, ''):
            return default
        try:
            return f'{float(value):,.2f}'
        except (ValueError, TypeError):
            return default
    
    # הכן את הערכים בדיוק לפי שמות השדות בתבנית (case-sensitive)
    unicode_vals = {
        'Today':             date.today().strftime('%d/%m/%Y'),
        'ClientFirstName':   client.first_name or '',
        'ClientLastName':    client.last_name or '',
        'ClientID':          client.tz or '',           # חייב ID באותיות גדולות!
        'ClientAddress':     client.address or '',
        'Clientphone':       client.phone or '',        # חייב phone באות קטנה!
        'ClientBdate':       client.birth_date.strftime('%d/%m/%Y') if client.birth_date else '',
        'ClientZdate':       summary.get('client_info', {}).get('eligibility_date', '').split('T')[0] if isinstance(summary.get('client_info', {}).get('eligibility_date', ''), str) else '',
        'Clientmaanakpatur': format_number(safe_value(summary, 'grants_nominal')),
        'Clientpgiabahon':   format_number(safe_value(summary, 'grants_impact')),
        'clientcapsum':      format_number(safe_value(summary, 'commutations_total')),
        'clientshiryun':     format_number(safe_value(summary, 'remaining_exemption')),
    }
    
    # טען את התבנית
    template_path = Path('static/templates/161d.pdf')
    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.addpages(reader.pages)
    
    # מלא את השדות
    fields = reader.Root.AcroForm.Fields or []
    updated = 0
    
    # קודם לכל - הדפס את המפתחות הקיימים כדי להשוות
    print("### unicode_vals keys →", sorted(list(unicode_vals.keys())))
    
    # אוסף את כל שמות השדות בטופס
    form_field_names = set()
    for parent in fields:
        for widget in _get_all_widgets(parent):
            if widget.get('T'):
                key = _clean_field_name(widget.T)
                form_field_names.add(key)
    print("### form field names  →", sorted(list(form_field_names)))
    
    # עכשיו מלא את השדות
    for parent in fields:
        for widget in _get_all_widgets(parent):
            if widget.get('T'):
                raw = widget.T
                key = _clean_field_name(raw)
                print("### RAW", repr(raw), "→", repr(key))
                if key in unicode_vals:
                    widget.V = unicode_vals[key]
                    widget.AP = ''  # נקה הופעה ישנה
                    updated += 1
                    print(f"### Updated field '{key}' with value: {unicode_vals[key]}")
                else:
                    print(f"### MISSING key '{key}' not found in unicode_vals!")
    
    print(f"Updated {updated} of {len(unicode_vals)} fields")
    
    # שמירה
    output_dir = Path('static/generated')
    output_dir.mkdir(exist_ok=True)
    output = output_dir/f'161d_client_{client.id}.pdf'
    
    # טיפול בקובץ קיים / בעיות הרשאה
    try:
        if output.exists():
            try:
                output.unlink()
            except PermissionError:
                ts = datetime.now().strftime('%H%M%S')
                output = output.with_stem(f"{output.stem}_{ts}")
                print(f"Permission issue - saving to alternate file: {output}")
        writer.write(str(output), reader)
    except PermissionError:
        ts = datetime.now().strftime('%H%M%S')
        output = output.with_stem(f"{output.stem}_{ts}")
        print(f"Permission issue on write - saving to alternate file: {output}")
        writer.write(str(output), reader)
    
    return str(output)


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
                    <th>משלם ההיוון</th>
                    <th>תיק ניכויים</th>
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
                    <td>{commutation.withholding_file or ''}</td>
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
    
    output_path = os.path.join(output_dir, f"commutations_appendix_{client_id}.pdf")
    
    # שמירת ה-HTML לקובץ זמני
    html_temp_file = os.path.join(output_dir, f"commutations_appendix_{client_id}.html")
    with open(html_temp_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    try:
        # ניסיון ליצור קובץ PDF עם wkhtmltopdf
        if pdfkit_config:
            pdfkit.from_file(html_temp_file, output_path, options={
                'encoding': 'UTF-8',
                'page-size': 'A4',
                'margin-top': '10mm',
                'margin-right': '10mm',
                'margin-bottom': '10mm',
                'margin-left': '10mm'
            }, configuration=pdfkit_config)
        else:
            # אם wkhtmltopdf לא נמצא, נודיע שמשתמשים בקובץ HTML במקום
            print("Using HTML file instead of PDF due to missing wkhtmltopdf")
            output_path = html_temp_file
    except Exception as e:
        print(f"Error generating PDF with pdfkit: {e}")
        # אם הייתה שגיאה, נחזיר את הקובץ HTML במקום PDF
        output_path = html_temp_file
    
    return output_path
