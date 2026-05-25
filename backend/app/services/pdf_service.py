"""
PDF Processing Service - Extract text from tax documents.
Uses PyMuPDF for PDF extraction, Tesseract OCR for scanned docs.
"""
import os
import asyncio
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import fitz  # PyMuPDF
import structlog
from app.utils.helpers import current_financial_year

logger = structlog.get_logger()


class PDFProcessor:
    """
    Processes uploaded PDF documents to extract text and structured data.
    Handles both searchable PDFs and scanned documents with OCR.
    """

    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def extract_text(self, file_path: str) -> Tuple[str, bool]:
        """
        Extract text from PDF file.
        Returns (extracted_text, is_ocr_used).
        """
        def _extract():
            doc = fitz.open(file_path)
            full_text = ""
            needs_ocr = False

            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                if text.strip():
                    full_text += f"\n--- Page {page_num + 1} ---\n{text}"
                else:
                    needs_ocr = True
                    # Try OCR via PyMuPDF's built-in Tesseract integration
                    try:
                        tp = page.get_textpage_ocr(flags=0, language="eng")
                        ocr_text = page.get_text(textpage=tp)
                        if ocr_text.strip():
                            full_text += f"\n--- Page {page_num + 1} (OCR) ---\n{ocr_text}"
                    except Exception:
                        # OCR not available, skip page
                        pass

            doc.close()
            return full_text.strip(), needs_ocr

        try:
            text, is_ocr = await asyncio.to_thread(_extract)
            logger.info("PDF text extracted", file=file_path, length=len(text), ocr=is_ocr)
            return text, is_ocr
        except Exception as e:
            logger.error("PDF extraction failed", file=file_path, error=str(e))
            return "", False

    def detect_document_type(self, text: str, filename: str) -> str:
        """
        Detect the type of tax document based on content and filename.
        """
        text_lower = text.lower()
        filename_lower = filename.lower()

        # Form 16 detection
        if any(kw in text_lower for kw in ["form 16", "form no. 16", "certificate of tax deducted", "tds certificate"]):
            return "form_16"
        if "form16" in filename_lower or "form_16" in filename_lower:
            return "form_16"

        # Salary slip detection
        if any(kw in text_lower for kw in ["pay slip", "payslip", "salary slip", "pay stub", "earnings statement"]):
            return "salary_slip"
        if "salary" in filename_lower or "payslip" in filename_lower:
            return "salary_slip"

        # ITR detection
        if any(kw in text_lower for kw in ["income tax return", "itr-1", "itr-2", "itr-3", "acknowledgement number"]):
            return "itr"
        if "itr" in filename_lower:
            return "itr"

        # Investment proof
        if any(kw in text_lower for kw in ["investment proof", "ppf", "elss", "provident fund statement"]):
            return "investment_proof"

        return "other"

    def extract_financial_year(self, text: str) -> Optional[str]:
        """Extract financial year from document text."""
        import re
        patterns = [
            r"financial year[:\s]+(\d{4}-\d{2,4})",
            r"f\.?y\.?[:\s]+(\d{4}-\d{2,4})",
            r"assessment year[:\s]+(\d{4}-\d{2,4})",
            r"(\d{4}-\d{2})\s*(?:tax year|financial year)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1)
        return None

    async def save_upload(self, file_content: bytes, filename: str, user_id: str) -> str:
        """Save uploaded file to disk with unique name."""
        import uuid
        safe_name = f"{user_id}_{uuid.uuid4().hex}_{filename}"
        file_path = self.upload_dir / safe_name
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)
        return str(file_path)

    async def process_document(
        self, file_path: str, filename: str
    ) -> Dict[str, Any]:
        """
        Full document processing pipeline:
        1. Extract text
        2. Detect document type
        3. Extract financial year
        4. Return structured result
        """
        text, ocr_used = await self.extract_text(file_path)
        doc_type = self.detect_document_type(text, filename)
        financial_year = self.extract_financial_year(text)

        return {
            "extracted_text": text,
            "document_type": doc_type,
            "financial_year": financial_year,
            "ocr_used": ocr_used,
            "text_length": len(text),
            "pages_extracted": text.count("--- Page"),
        }

    def generate_tax_report_pdf(
        self, report_data: Dict[str, Any], output_path: str
    ) -> bool:
        """Generate a formatted tax analysis PDF report."""
        try:
            from fpdf import FPDF

            class TaxReportPDF(FPDF):
                def header(self):
                    self.set_fill_color(15, 20, 40)
                    self.rect(0, 0, 210, 30, "F")
                    self.set_text_color(255, 255, 255)
                    self.set_font("Helvetica", "B", 18)
                    self.set_xy(10, 8)
                    self.cell(0, 15, "Maffa TaxAI - Tax Analysis Report", align="L")
                    self.set_text_color(0, 0, 0)
                    self.ln(25)

                def footer(self):
                    self.set_y(-15)
                    self.set_font("Helvetica", "I", 8)
                    self.set_text_color(128, 128, 128)
                    self.cell(0, 10, f"Page {self.page_no()} | Generated by Maffa TaxAI | For reference only", align="C")

            pdf = TaxReportPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Title section
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 10, f"Tax Analysis - FY {report_data.get('financial_year', current_financial_year())}", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, f"Prepared for: {report_data.get('user_name', 'User')}", ln=True)
            pdf.ln(5)

            # Old vs New Regime comparison
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 8, "Regime Comparison", ln=True)
            pdf.ln(2)

            old = report_data.get("old_regime", {})
            new = report_data.get("new_regime", {})

            # Table header
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(80, 8, "Parameter", border=1, fill=True)
            pdf.cell(55, 8, "Old Regime", border=1, fill=True, align="C")
            pdf.cell(55, 8, "New Regime", border=1, fill=True, align="C")
            pdf.ln()

            pdf.set_font("Helvetica", "", 10)
            rows = [
                ("Gross Income", old.get("gross_income", 0), new.get("gross_income", 0)),
                ("Total Deductions", old.get("total_deductions", 0), new.get("total_deductions", 0)),
                ("Taxable Income", old.get("taxable_income", 0), new.get("taxable_income", 0)),
                ("Total Tax", old.get("total_tax", 0), new.get("total_tax", 0)),
                ("Effective Rate (%)", old.get("effective_rate", 0), new.get("effective_rate", 0)),
                ("Monthly Take-home", old.get("take_home_monthly", 0), new.get("take_home_monthly", 0)),
            ]

            for i, (label, old_val, new_val) in enumerate(rows):
                fill = i % 2 == 0
                pdf.set_fill_color(248, 248, 248 if fill else 255, 255)
                pdf.cell(80, 7, label, border=1, fill=fill)
                pdf.cell(55, 7, f"₹{old_val:,.0f}", border=1, fill=fill, align="R")
                pdf.cell(55, 7, f"₹{new_val:,.0f}", border=1, fill=fill, align="R")
                pdf.ln()

            pdf.ln(5)

            # Recommendation
            recommended = report_data.get("recommended_regime", "new")
            tax_saved = report_data.get("tax_saved", 0)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Recommendation", ln=True)
            pdf.set_fill_color(220, 255, 220)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 7, f"✓ Go with the {recommended.upper()} regime and save ₹{tax_saved:,.0f} this financial year!", fill=True)
            pdf.ln(5)

            # Key recommendations
            recommendations = report_data.get("key_recommendations", [])
            if recommendations:
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 8, "Tax Saving Recommendations", ln=True)
                pdf.set_font("Helvetica", "", 10)
                for rec in recommendations[:8]:
                    pdf.multi_cell(0, 6, f"• {rec}")
                    pdf.ln(1)

            pdf.output(output_path)
            return True
        except Exception as e:
            logger.error("PDF report generation failed", error=str(e))
            return False


# Singleton
pdf_processor = PDFProcessor()
