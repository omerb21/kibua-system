#!/usr/bin/env python3
"""Standalone CLI script to fill טופס 161ד without Flask.

Run from project root (where 161d.pdf template is located)::

    pip install pdfrw
    python fill_161d_cli.py

It will create ``filled_cli.pdf`` next to the template and print which
fields were updated.
"""
import sys
from pathlib import Path
from datetime import datetime
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfObject, PdfString

# 12 example values – replace as needed
DATA = {
    'Today': datetime.now().strftime('%d/%m/%Y'),
    'ClientFirstName': 'ישראל',
    'ClientLastName': 'ישראלי',
    'ClientID': '123456789',
    'ClientAddress': 'הרצל 1, דירה 2, תל אביב, 12345',
    'ClientBdate': '01/01/1980',
    'Clientphone': '050-1234567',
    'ClientZdate': '01/01/2023',
    'Clientmaanakpatur': '10,000.50',
    'Clientpgiabahon': '5,000.25',
    'clientcapsum': '2,000.00',
    'clientshiryun': '15,000.00',
}


def _clean(raw):
    """Return plain field name string from PdfString/PdfName/etc."""
    if hasattr(raw, 'to_unicode'):
        raw = raw.to_unicode()
    text = str(raw).strip()
    return text.lstrip('(').rstrip(')').strip('\u200e\u200f')


def fill(template: Path, output: Path) -> int:
    """Fill template into *output* file. Return number of updated fields."""
    pdf = PdfReader(str(template))
    updated = 0

    for field in pdf.Root.AcroForm.Fields:
        stack = field.Kids if getattr(field, 'Kids', None) else [field]
        for widget in stack:
            if widget.T:
                name = _clean(widget.T)
                if name in DATA:
                    widget.V = PdfString.from_unicode(DATA[name])
                    widget.AP = PdfDict()  # clear appearance – regenerate
                    updated += 1
                    print(f"✔ Filled {name}")

    pdf.Root.AcroForm.NeedAppearances = PdfObject('true')
    PdfWriter().write(str(output), pdf)
    return updated


def main() -> None:
    tpl = Path('161d.pdf')
    out = Path('filled_cli.pdf')

    if not tpl.exists():
        print(f"Template not found: {tpl.resolve()}")
        sys.exit(1)

    updated = fill(tpl, out)
    print(f"\nUpdated {updated}/{len(DATA)} fields")
    print("Saved:", out.resolve())


if __name__ == '__main__':
    main()
