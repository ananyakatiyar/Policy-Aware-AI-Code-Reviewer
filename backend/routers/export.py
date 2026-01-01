from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.models.schemas import ReviewResponse
from fpdf import FPDF
import io

router = APIRouter(prefix="/export", tags=["Export"])

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Code Security Audit Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

@router.post("/pdf")
async def export_pdf(report_data: ReviewResponse):
    try:
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Summary
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Risk Score: {report_data.risk_score} ({report_data.risk_level})", 0, 1)
        pdf.cell(0, 10, f"Timestamp: {report_data.audit.timestamp}", 0, 1)
        
        if hasattr(report_data, 'risk_delta') and report_data.risk_delta != 0:
            delta_str = f"+{report_data.risk_delta}" if report_data.risk_delta > 0 else str(report_data.risk_delta)
            pdf.cell(0, 10, f"Risk Delta: {delta_str}", 0, 1)
            
        pdf.ln(10)
        
        # Violations
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Violations Found:", 0, 1)
        pdf.set_font("Arial", size=11)
        
        if not report_data.violations:
             pdf.cell(0, 10, "No violations found.", 0, 1)
        
        for v in report_data.violations:
            # Title
            pdf.set_font("Arial", 'B', 11)
            severity_text = f"[{v.severity}]"
            pdf.cell(0, 8, f"{severity_text} Line {v.line}: {v.message}", 0, 1)
            
            # Details
            pdf.set_font("Arial", size=10)
            
            if v.status == "FALSE_POSITIVE":
                pdf.set_text_color(128, 128, 128)
                pdf.cell(0, 6, "(Marked as False Positive)", 0, 1)
                pdf.set_text_color(0, 0, 0)
            
            # Use multi_cell for long text
            if v.risk_explanation:
                pdf.multi_cell(0, 6, f"Risk: {v.risk_explanation}")
            if v.exploit_scenario:
                pdf.multi_cell(0, 6, f"Exploit: {v.exploit_scenario}")
            if v.fix_recommendation:
                pdf.multi_cell(0, 6, f"Fix: {v.fix_recommendation}")
                
            pdf.ln(4)
            
        # Output
        # FPDF output to string (dest='S') returns a string (latin-1 encoded bytes effectively in Py3)
        # We need to encode it to bytes
        pdf_output = pdf.output(dest='S').encode('latin-1')
        buffer = io.BytesIO(pdf_output)
        
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=audit_report.pdf"}
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
