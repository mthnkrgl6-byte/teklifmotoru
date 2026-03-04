from io import BytesIO

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.schemas.quotation import QuotationRow, QuotationSummary


def export_excel(rows: list[QuotationRow], summary: QuotationSummary) -> bytes:
    df = pd.DataFrame([r.model_dump() for r in rows])
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Quotation")
        s = pd.DataFrame([summary.model_dump()])
        s.to_excel(writer, index=False, sheet_name="Summary")
    return output.getvalue()


def export_pdf(rows: list[QuotationRow], summary: QuotationSummary) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    y = 800
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "AI Plumbing Quotation")
    y -= 30
    c.setFont("Helvetica", 10)
    for row in rows:
        c.drawString(50, y, f"{row.product_code} | {row.product_name} | Qty: {row.quantity} | Total: {row.total_price}")
        y -= 18
        if y < 120:
            c.showPage()
            y = 800
    y -= 10
    c.drawString(50, y, f"Subtotal: {summary.subtotal}")
    c.drawString(50, y - 18, f"Discount: {summary.discount}")
    c.drawString(50, y - 36, f"VAT ({int(summary.vat_rate*100)}%): {summary.vat_amount}")
    c.drawString(50, y - 54, f"Grand Total: {summary.grand_total}")
    c.save()
    buffer.seek(0)
    return buffer.read()
