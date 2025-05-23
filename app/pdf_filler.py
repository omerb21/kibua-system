from pdfrw import PdfReader, PdfWriter, PdfDict

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
