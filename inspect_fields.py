#!/usr/bin/env python3
# inspect_fields.py

from pdfrw import PdfReader

def clean(t):
    if hasattr(t, 'to_unicode'):
        return t.to_unicode()
    return str(t)

def main():
    tpl = "161d.pdf"
    pdf = PdfReader(tpl)
    fields = pdf.Root.AcroForm.Fields
    print(f"Found {len(fields)} top-level fields:\n")
    for i, f in enumerate(fields, 1):
        raw = f.T
        name = clean(raw)
        kids = getattr(f, 'Kids', None)
        if kids:
            print(f"{i}. PARENT: {repr(raw)} → {name}, has {len(kids)} Kids")
            for j, k in enumerate(kids, 1):
                kr = k.T
                print(f"    {i}.{j}. CHILD: {repr(kr)} → {clean(kr)}")
        else:
            print(f"{i}. FIELD: {repr(raw)} → {name}")
    print("\n*** End of list ***")

if __name__ == "__main__":
    main()
