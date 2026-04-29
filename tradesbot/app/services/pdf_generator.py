"""
PDF Generator — creates invoice and quote PDFs using fpdf2.
"""
import tempfile
from datetime import datetime
from fpdf import FPDF
from app.services.media import upload_to_storage
from app.utils.logger import get_logger

log = get_logger("pdf_generator")


class InvoicePDF(FPDF):
    """Custom PDF class for invoices."""

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "TAX INVOICE", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-30)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, "Thank you for your business!", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, f"Generated on {datetime.now().strftime('%d %b %Y %H:%M')}", align="C")


def generate_invoice_pdf(
    invoice_number: str,
    invoice_data: dict,
    business_name: str = "Tradesperson",
    gstin: str = "N/A",
) -> str:
    """
    Generate an invoice PDF and upload to MinIO.
    Returns the URL of the uploaded PDF.
    """
    pdf = InvoicePDF()
    pdf.add_page()

    # Business details
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, business_name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"GSTIN: {gstin}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Invoice info
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 6, f"Invoice #: {invoice_number}", new_x="RIGHT")
    pdf.cell(95, 6, f"Date: {datetime.now().strftime('%d %b %Y')}", align="R", new_x="LMARGIN", new_y="NEXT")

    customer = invoice_data.get("customer_name", "Customer")
    pdf.cell(0, 6, f"Customer: {customer}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # Items table header
    pdf.set_fill_color(40, 40, 40)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(10, 8, "#", fill=True, align="C")
    pdf.cell(75, 8, "Description", fill=True)
    pdf.cell(20, 8, "HSN/SAC", fill=True, align="C")
    pdf.cell(15, 8, "Qty", fill=True, align="C")
    pdf.cell(30, 8, "Rate", fill=True, align="R")
    pdf.cell(30, 8, "Amount", fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

    # Items
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    items = invoice_data.get("items", [])

    for i, item in enumerate(items, 1):
        bg = (245, 245, 245) if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)

        desc = str(item.get("description", ""))[:40]
        hsn = str(item.get("hsn_sac", "9954"))
        qty = str(item.get("quantity", 1))
        rate = float(item.get("unit_price", 0))
        total = float(item.get("total", 0))

        pdf.cell(10, 7, str(i), fill=True, align="C")
        pdf.cell(75, 7, desc, fill=True)
        pdf.cell(20, 7, hsn, fill=True, align="C")
        pdf.cell(15, 7, qty, fill=True, align="C")
        pdf.cell(30, 7, f"Rs.{rate:,.0f}", fill=True, align="R")
        pdf.cell(30, 7, f"Rs.{total:,.0f}", fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # Totals
    subtotal = float(invoice_data.get("subtotal", 0))
    cgst = float(invoice_data.get("cgst_amount", 0))
    sgst = float(invoice_data.get("sgst_amount", 0))
    grand_total = float(invoice_data.get("grand_total", 0))

    x_label = 120
    x_value = 150
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(x_label)
    pdf.cell(30, 7, "Subtotal:", align="R")
    pdf.cell(30, 7, f"Rs.{subtotal:,.0f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(x_label)
    pdf.cell(30, 7, "CGST (9%):", align="R")
    pdf.cell(30, 7, f"Rs.{cgst:,.0f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(x_label)
    pdf.cell(30, 7, "SGST (9%):", align="R")
    pdf.cell(30, 7, f"Rs.{sgst:,.0f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(x_label, pdf.get_y(), x_label + 60, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_x(x_label)
    pdf.cell(30, 8, "TOTAL:", align="R")
    pdf.cell(30, 8, f"Rs.{grand_total:,.0f}", align="R", new_x="LMARGIN", new_y="NEXT")

    # Payment terms
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 9)
    terms = invoice_data.get("payment_terms", "Due within 15 days")
    pdf.cell(0, 6, f"Payment Terms: {terms}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Payment: UPI / Bank Transfer / Cash", new_x="LMARGIN", new_y="NEXT")

    # Save to temp file and upload
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            pdf_bytes = f.read()

    stored_url = upload_to_storage(
        pdf_bytes,
        filename=f"{invoice_number}.pdf",
        content_type="application/pdf",
    )

    log.info("invoice_pdf_generated", invoice=invoice_number, size=len(pdf_bytes))
    return stored_url
