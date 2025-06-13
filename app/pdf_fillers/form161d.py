#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal 161d PDF filler usable both as a library and from CLI.

The function :func:`fill_161d` is imported by *routes.py* and returns the
absolute path of the generated PDF.  Internally we keep the implementation
identical to the proven CLI script; we simply build the *DATA* dictionary
from the database when a *client_id* is provided.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Dict

from pdfrw import PdfReader, PdfWriter, PdfDict, PdfObject, PdfString

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
TEMPLATE_PATH = STATIC_DIR / "templates" / "161d.pdf"
GENERATED_DIR = STATIC_DIR / "generated"


def _pdf_str(val):
    """Return PdfString that displays Hebrew correctly without manual encoding.

    pdfrw (>=0.4) automatically selects UTF-16-BE with BOM when the text
    contains non-PDFDocEncoding characters, so we only need to convert to
    string and pass it to ``PdfString.from_unicode``.
    """
    return PdfString.from_unicode(str(val))


def _update_widget(widget, value: str) -> None:
    widget.V = _pdf_str(value)
    widget.AP = PdfDict()  # clear appearance so Acrobat redraws


def _fill_pdf(data: Dict[str, str], output_path: Path) -> int:
    """Fill *TEMPLATE_PATH* with *data* and save to *output_path*.

    Returns number of updated fields.
    """
    reader = PdfReader(str(TEMPLATE_PATH))
    if "/AcroForm" not in reader.Root:
        raise RuntimeError("Template missing AcroForm – is it the right file?")

    reader.Root.AcroForm.NeedAppearances = PdfObject("true")

    updated = 0
    for parent in reader.Root.AcroForm.Fields:
        # parent itself
        name = parent.T[1:-1] if parent.T else None
        if name in data:
            _update_widget(parent, data[name])
            updated += 1

        # iterate kids
        for kid in parent.Kids or []:
            kname = kid.T[1:-1] if kid.T else None
            if kname in data:
                _update_widget(kid, data[kname])
                updated += 1

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    PdfWriter().write(str(output_path), reader)
    return updated


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def fill_161d(client_id: int) -> str:
    """Fill טופס 161ד for *client_id* and return absolute output path.

    The function fetches the client and summary information from the DB and
    maps them into the 12 required fields.  Any missing values are replaced
    with empty strings so the PDF still renders.
    """
    # Local imports to avoid heavy dependencies at module import time
    from app.models import Client
    from app.utils import calculate_summary

    client: Client = Client.query.get_or_404(client_id)
    summary = calculate_summary(client_id)

    def safe(key: str) -> str:
        return str(summary.get(key, "")) if summary and key in summary else ""

    data = {
        "Today": date.today().strftime("%d/%m/%Y"),
        "ClientFirstName": client.first_name or "",
        "ClientLastName": client.last_name or "",
        "ClientID": client.tz or "",
        "ClientAddress": client.address or "",
        "ClientBdate": client.birth_date.strftime("%d/%m/%Y") if client.birth_date else "",
        "Clientphone": client.phone or "",
        "ClientZdate": summary.get("client_info", {}).get("eligibility_date", "")[:10]
        if isinstance(summary.get("client_info", {}).get("eligibility_date", ""), str)
        else "",
        "Clientmaanakpatur": safe("grants_nominal"),
        "Clientpgiabahon": safe("grants_impact"),
        "clientcapsum": safe("commutations_total"),
        "clientshiryun": safe("remaining_exemption"),
    }

    output = GENERATED_DIR / f"161d_{client_id}.pdf"
    count = _fill_pdf(data, output)
    print(f"Updated {count}/12 fields → {output}")
    return str(output)


# ---------------------------------------------------------------------------
# CLI helper for quick testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    import sys

    cid = int(sys.argv[1]) if len(sys.argv) == 2 else 0
    if not TEMPLATE_PATH.exists():
        print("Template 161d.pdf not found in static/templates – abort")
        sys.exit(1)

    path = fill_161d(cid)
    print("Saved to", path)
