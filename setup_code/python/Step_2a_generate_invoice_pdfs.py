"""
ClearPath Safety Solutions — Invoice PDF Generator
Generates 36 realistic highway safety product invoices with line items.
Output: poc_invoices/ directory (one PDF per invoice)
"""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT_DIR = Path("poc_invoices")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── BRAND COLORS ─────────────────────────────────────────────────────────────
ORANGE  = colors.HexColor("#F47920")
NAVY    = colors.HexColor("#1B3A5C")
LGRAY   = colors.HexColor("#F5F5F5")
MGRAY   = colors.HexColor("#D0D5DD")
DKGRAY  = colors.HexColor("#444444")

# ── PRODUCT CATALOG ──────────────────────────────────────────────────────────
# (sku, description, unit_price)
PRODUCTS = [
    ("CPB-TL3-48",  "Type 3 Redirective Barrier — MASH TL-3 Rated (48\" unit)",     285.00),
    ("CPA-100S",    "Compact Crash Attenuator — Single-Sided, NCHRP 350",            1_250.00),
    ("CPD-RPM-Y",   "Raised Pavement Marker — Yellow Reflective (box/100)",          148.00),
    ("CPD-POST-6",  "Delineator Post — 6\" Flexible w/ Base (each)",                 22.50),
    ("CPD-DRUM-28", "Channelizer Drum — 28\" MUTCD Compliant, Orange (each)",         88.00),
    ("CPS-SIGN-48",  "Temporary Work Zone Sign — 48\"×48\" Roll-Up (each)",           195.00),
    ("CPC-CONE-28", "Traffic Cone — 28\" High-Intensity Reflective Sleeve (each)",    14.75),
    ("CPB-PCB-10",  "Temporary Concrete Barrier — 10 ft section (rental/mo)",         95.00),
    ("CPA-TMA-T3",  "Truck-Mounted Attenuator — TL-3 Retrofit Kit",                 4_800.00),
    ("CPL-LED-ARR", "LED Arrow Board — 48\"×96\" Trailer-Mounted (rental/mo)",        375.00),
]

# ── CUSTOMERS ────────────────────────────────────────────────────────────────
# (customer_id, customer_name_doc, bill_to_address, payment_terms, po_required)
CUSTOMERS = [
    ("DOT001", "Texas Department of Transportation",
     "125 E. 11th Street, Austin, TX 78701",             "NET 45", True),
    ("DOT002", "Illinois Department of Transportation",
     "2300 S. Dirksen Pkwy, Springfield, IL 62764",      "NET 45", True),
    ("DOT003", "North Carolina DOT — Division 5",
     "1020 Birch Ridge Dr, Raleigh, NC 27610",           "NET 30", True),
    ("CON001", "Granite Horizon Contractors LLC",
     "4400 Commerce Park Dr, Dallas, TX 75247",          "NET 30", False),
    ("CON002", "Apex Infrastructure Group Inc.",
     "1750 Keystone Ave, Lisle, IL 60532",               "NET 30", False),
    ("CON003", "Summit Roads & Bridges Corp.",
     "890 Capital Blvd, Raleigh, NC 27603",              "NET 21", False),
    ("MUN001", "City of Phoenix — Public Works Dept.",
     "200 W. Washington St, Phoenix, AZ 85003",          "NET 45", True),
    ("CON004", "Meridian Highway Services LLC",
     "3301 N. 7th Ave, Phoenix, AZ 85013",               "NET 30", False),
    ("DOT004", "Colorado DOT — Region 1",
     "2000 S. Holly St, Denver, CO 80222",               "NET 45", True),
    ("CON005", "PeakLine Construction Partners",
     "5280 Industrial Blvd, Denver, CO 80239",           "NET 30", False),
]

# ── INVOICE LINE ITEMS ───────────────────────────────────────────────────────
# Each invoice: (invoice_id, customer_idx, invoice_date, due_date, po_number, line_items)
# line_items: list of (sku_idx, qty, note_or_none)
# ERP amounts intentionally differ on 4 invoices (seeded mismatches)

INVOICES = [
    # ── Texas DOT (3 invoices) ──────────────────────────────────────────────
    ("INV-2001", 0, "2026-01-08", "2026-02-22", "PO-TXDOT-8801",
     [(0, 50, None), (3, 200, None), (4, 30, None)]),
    ("INV-2002", 0, "2026-02-10", "2026-03-27", "PO-TXDOT-8844",
     [(2, 10, None), (5, 15, None), (6, 100, None)]),
    ("INV-2003", 0, "2026-03-05", "2026-04-19", "PO-TXDOT-8902",
     [(0, 40, None), (4, 25, "MISMATCH: doc shows 23 drums"), (7, 8, None)]),  # qty mismatch on invoice

    # ── Illinois DOT (3 invoices) ───────────────────────────────────────────
    ("INV-2004", 1, "2026-01-12", "2026-02-26", "PO-IDOT-2201",
     [(1, 2, None), (5, 20, None), (3, 150, None)]),
    ("INV-2005", 1, "2026-02-14", "2026-03-31", "PO-IDOT-2245",
     [(0, 35, None), (6, 200, None), (2, 5, None)]),
    ("INV-2006", 1, "2026-03-08", "2026-04-22", "PO-IDOT-2289",
     [(4, 40, None), (7, 12, None), (5, 10, None)]),

    # ── NC DOT (3 invoices) ─────────────────────────────────────────────────
    ("INV-2007", 2, "2026-01-15", "2026-02-14", None,
     [(3, 300, None), (6, 150, None), (4, 20, None)]),
    ("INV-2008", 2, "2026-02-18", "2026-03-20", None,
     [(5, 12, None), (0, 28, None), (2, 8, None)]),
    ("INV-2009", 2, "2026-03-10", "2026-04-09", "PO-NCDOT-5512",
     [(1, 1, "MISMATCH: doc unit price $1,275 vs ERP $1,250"), (4, 35, None), (3, 100, None)]),  # price mismatch

    # ── Granite Horizon Contractors (3 invoices) ────────────────────────────
    ("INV-2010", 3, "2026-01-07", "2026-02-06", None,
     [(6, 500, None), (3, 400, None), (2, 15, None)]),
    ("INV-2011", 3, "2026-02-09", "2026-03-11", None,
     [(0, 20, None), (4, 50, None), (5, 8, None)]),
    ("INV-2012", 3, "2026-03-03", "2026-04-02", "PO-GHC-0041",
     [(7, 20, None), (9, 2, None), (6, 80, None)]),

    # ── Apex Infrastructure Group (3 invoices) ──────────────────────────────
    ("INV-2013", 4, "2026-01-10", "2026-02-09", None,
     [(8, 1, None), (5, 18, None), (3, 250, None)]),
    ("INV-2014", 4, "2026-02-12", "2026-03-14", None,
     [(0, 30, None), (4, 45, None), (2, 6, None)]),
    ("INV-2015", 4, "2026-03-06", "2026-04-05", None,
     [(6, 300, None), (7, 10, None), (5, 14, None)]),

    # ── Summit Roads & Bridges (3 invoices) ────────────────────────────────
    ("INV-2016", 5, "2026-01-14", "2026-02-04", None,
     [(3, 180, None), (6, 120, None), (4, 28, None)]),
    ("INV-2017", 5, "2026-02-17", "2026-03-10", None,
     [(5, 10, None), (0, 22, None), (2, 7, None)]),
    ("INV-2018", 5, "2026-03-09", "2026-03-30", None,
     [(4, 38, None), (9, 1, None), (3, 200, None)]),

    # ── City of Phoenix (3 invoices) ────────────────────────────────────────
    ("INV-2019", 6, "2026-01-09", "2026-02-23", "PO-PHX-PW-1101",
     [(6, 400, None), (3, 350, None), (5, 22, None)]),
    ("INV-2020", 6, "2026-02-11", "2026-03-28", "PO-PHX-PW-1134",
     [(0, 45, None), (4, 60, None), (2, 12, None)]),
    ("INV-2021", 6, "2026-03-07", "2026-04-21", "PO-PHX-PW-1178",
     [(7, 15, None), (5, 16, None), (3, 280, None)]),

    # ── Meridian Highway Services (3 invoices) ──────────────────────────────
    ("INV-2022", 7, "2026-01-13", "2026-02-12", None,
     [(4, 55, None), (6, 250, None), (2, 9, None)]),
    # MISMATCH: customer name — ERP has "Meridian Highway Services LLC", doc has "Meridian Hwy Services LLC"
    ("INV-2023", 7, "2026-02-16", "2026-03-18", None,
     [(0, 18, None), (5, 11, "MISMATCH: customer name variant on doc"), (3, 160, None)]),
    ("INV-2024", 7, "2026-03-11", "2026-04-10", None,
     [(9, 2, None), (6, 180, None), (4, 42, None)]),

    # ── Colorado DOT (3 invoices) ────────────────────────────────────────────
    ("INV-2025", 8, "2026-01-11", "2026-02-25", "PO-CDOT-6601",
     [(1, 3, None), (5, 24, None), (3, 220, None)]),
    ("INV-2026", 8, "2026-02-13", "2026-03-30", "PO-CDOT-6644",
     [(0, 55, None), (4, 70, None), (2, 11, None)]),
    ("INV-2027", 8, "2026-03-04", "2026-04-18", "PO-CDOT-6688",
     [(6, 350, None), (7, 18, None), (5, 20, None)]),

    # ── PeakLine Construction (3 invoices) ───────────────────────────────────
    ("INV-2028", 9, "2026-01-16", "2026-02-06", None,
     [(4, 48, None), (3, 300, None), (6, 200, None)]),
    ("INV-2029", 9, "2026-02-19", "2026-03-12", None,
     [(5, 13, None), (0, 25, None), (2, 8, None)]),
    # MISMATCH: payment terms — ERP shows NET 30, doc shows NET 45
    ("INV-2030", 9, "2026-03-12", "2026-04-26", None,
     [(7, 14, None), (9, 1, "MISMATCH: payment terms NET 45 on doc vs NET 30 ERP"), (4, 35, None)]),
]

# ── STYLES ───────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Body10",  parent=styles["BodyText"], fontSize=10, leading=13))
styles.add(ParagraphStyle(name="Body9",   parent=styles["BodyText"], fontSize=9,  leading=12))
styles.add(ParagraphStyle(name="Small8",  parent=styles["BodyText"], fontSize=8,  leading=10))
styles.add(ParagraphStyle(name="Right10", parent=styles["BodyText"], fontSize=10, leading=13, alignment=TA_RIGHT))
styles.add(ParagraphStyle(name="Bold10",  parent=styles["BodyText"], fontSize=10, leading=13, fontName="Helvetica-Bold"))

def money(v: float) -> str:
    return f"${v:,.2f}"

def build_invoice(row):
    invoice_id, cust_idx, inv_date, due_date, po_number, line_items = row
    cust_id, cust_name_doc, bill_to, terms, _ = CUSTOMERS[cust_idx]

    # Resolve mismatch notes and compute line totals
    lines = []
    for sku_idx, qty, note in line_items:
        sku, desc, unit_price = PRODUCTS[sku_idx]
        # For the quantity mismatch (INV-2003): doc shows 23 drums but ERP has 25
        if note and "23 drums" in note:
            doc_qty = 23
        else:
            doc_qty = qty
        # For the price mismatch (INV-2009): doc shows $1,275 unit price
        if note and "1,275" in note:
            doc_unit = 1_275.00
        else:
            doc_unit = unit_price
        line_total = doc_qty * doc_unit
        lines.append((sku, desc, doc_qty, doc_unit, line_total))

    # For customer name mismatch (INV-2023): show variant name on doc
    display_name = cust_name_doc
    if invoice_id == "INV-2023":
        display_name = "Meridian Hwy Services LLC"

    # For payment terms mismatch (INV-2030): doc shows NET 45
    display_terms = terms
    if invoice_id == "INV-2030":
        display_terms = "NET 45"

    subtotal = sum(l[4] for l in lines)
    tax = 0.00
    total_due = subtotal + tax

    path = OUT_DIR / f"{invoice_id}.pdf"
    doc = SimpleDocTemplate(
        str(path), pagesize=LETTER,
        leftMargin=0.65*inch, rightMargin=0.65*inch,
        topMargin=0.55*inch, bottomMargin=0.65*inch,
    )
    story = []

    # ── HEADER ──────────────────────────────────────────────────────────────
    header = Table(
        [[
            # Logo / company block
            Paragraph(
                "<b><font color='#F47920'>ClearPath</font> "
                "<font color='#1B3A5C'>SAFETY SOLUTIONS</font></b><br/>"
                "<font size='8' color='#5B6B82'>Highway &amp; Work Zone Safety Products</font><br/>"
                "<font size='8' color='#5B6B82'>4820 Commerce Pkwy  |  Irving, TX 75063</font><br/>"
                "<font size='8' color='#5B6B82'>ar@clearpathsafety.com  |  (972) 555-0190</font>",
                styles["Body10"]
            ),
            Paragraph(
                f"<b><font size='18' color='#1B3A5C'>INVOICE</font></b><br/><br/>"
                f"<b>Invoice No:</b> {invoice_id}<br/>"
                f"<b>Invoice Date:</b> {inv_date}<br/>"
                f"<b>Due Date:</b> {due_date}",
                styles["Right10"]
            ),
        ]],
        colWidths=[3.9*inch, 2.9*inch],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(header)

    # Orange rule under header
    from reportlab.platypus import HRFlowable
    story.append(HRFlowable(width="100%", thickness=3, color=ORANGE, spaceAfter=8))

    # ── BILL TO / SUMMARY ───────────────────────────────────────────────────
    summary = Table(
        [
            [
                Paragraph("<b>Bill To</b>", styles["Bold10"]),
                Paragraph("<b>Order Summary</b>", styles["Bold10"]),
            ],
            [
                Paragraph(
                    f"<b>{display_name}</b><br/>"
                    f"<font size='9'>{bill_to}</font>",
                    styles["Body10"]
                ),
                Paragraph(
                    f"<b>Customer ID:</b> {cust_id}<br/>"
                    f"<b>Payment Terms:</b> {display_terms}<br/>"
                    f"<b>Currency:</b> USD"
                    + (f"<br/><b>PO Number:</b> {po_number}" if po_number else ""),
                    styles["Body10"]
                ),
            ],
        ],
        colWidths=[3.9*inch, 2.9*inch],
    )
    summary.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), colors.HexColor("#EBF5FF")),
        ("BOX",          (0,0), (-1,-1), 0.6, NAVY),
        ("INNERGRID",    (0,0), (-1,-1), 0.35, colors.HexColor("#C8D8EA")),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
    ]))
    story.append(summary)
    story.append(Spacer(1, 0.18*inch))

    # ── LINE ITEMS TABLE ────────────────────────────────────────────────────
    col_headers = [
        Paragraph("<b>SKU</b>",         styles["Small8"]),
        Paragraph("<b>Description</b>", styles["Small8"]),
        Paragraph("<b>Qty</b>",         styles["Small8"]),
        Paragraph("<b>Unit Price</b>",  styles["Small8"]),
        Paragraph("<b>Line Total</b>",  styles["Small8"]),
    ]
    table_data = [col_headers]
    for sku, desc, qty, unit, total in lines:
        table_data.append([
            Paragraph(sku,          styles["Body9"]),
            Paragraph(desc,         styles["Body9"]),
            Paragraph(str(qty),     styles["Body9"]),
            Paragraph(money(unit),  styles["Body9"]),
            Paragraph(money(total), styles["Body9"]),
        ])

    line_table = Table(
        table_data,
        colWidths=[1.1*inch, 2.85*inch, 0.55*inch, 1.0*inch, 1.05*inch],
    )
    line_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  NAVY),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("BOX",          (0,0), (-1,-1), 0.6, colors.HexColor("#A0A8B8")),
        ("INNERGRID",    (0,0), (-1,-1), 0.35, colors.HexColor("#CDD4DE")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#F5F9FC")]),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",        (2,1), (-1,-1), "CENTER"),
        ("LEFTPADDING",  (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 0.16*inch))

    # ── TOTALS ──────────────────────────────────────────────────────────────
    totals = Table(
        [
            ["Subtotal",        money(subtotal)],
            ["Tax (0%)",        money(tax)],
            ["Total Amount Due", money(total_due)],
        ],
        colWidths=[1.7*inch, 1.4*inch],
    )
    totals.setStyle(TableStyle([
        ("BOX",          (0,0), (-1,-1), 0.6, colors.HexColor("#A0A8B8")),
        ("INNERGRID",    (0,0), (-1,-1), 0.35, colors.HexColor("#D8DEE7")),
        ("BACKGROUND",   (0,2), (-1,2),  colors.HexColor("#FFF3E8")),
        ("FONTNAME",     (0,2), (-1,2),  "Helvetica-Bold"),
        ("TEXTCOLOR",    (0,2), (-1,2),  ORANGE),
        ("ALIGN",        (0,0), (-1,-1), "RIGHT"),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0), (-1,-1), 6),
    ]))

    totals_wrap = Table(
        [[
            Paragraph(
                "Remit payment by the due date shown above. Include the invoice number "
                "and PO number (if applicable) with your payment advice. "
                "Questions: ar@clearpathsafety.com",
                styles["Small8"]
            ),
            totals,
        ]],
        colWidths=[4.4*inch, 2.4*inch],
    )
    totals_wrap.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(totals_wrap)
    story.append(Spacer(1, 0.15*inch))

    # ── FOOTER ──────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=MGRAY, spaceBefore=4))
    story.append(Paragraph(
        "<font size='7' color='#888888'>"
        "ClearPath Safety Solutions  |  TX Vendor ID: 1-75-6003921  |  "
        "DUNS: 08-447-1290  |  Cage Code: 7K8R2  |  "
        "NET terms per Master Supply Agreement. Late payments subject to 1.5%/month finance charge."
        "</font>",
        styles["Small8"]
    ))

    doc.build(story)
    return total_due


if __name__ == "__main__":
    total_revenue = 0.0
    for inv in INVOICES:
        total = build_invoice(inv)
        total_revenue += total
        print(f"  {inv[0]}  →  {CUSTOMERS[inv[1]][1][:35]:<35}  ${total:>12,.2f}")
    print(f"\nCreated {len(INVOICES)} PDFs in {OUT_DIR.resolve()}")
    print(f"Total invoice value: ${total_revenue:,.2f}")
