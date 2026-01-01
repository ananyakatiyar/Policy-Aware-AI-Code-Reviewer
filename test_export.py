import argparse
import os
import sys
import webbrowser
import requests
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"

def test_export(base_url: str = "http://127.0.0.1:8000", output: str = "test_report.pdf", open_file: bool = False):
    print("Testing PDF Export...")
    
    # Mock data matching ReviewResponse schema
    data = {
        "risk_score": 85,
        "risk_level": "LOW RISK",
        "violations": [
            {
                "id": "123",
                "line": 10,
                "severity": "HIGH",
                "message": "Hardcoded secret detected",
                "rule_id": "no_secrets",
                "status": "OPEN",
                "risk_explanation": "Secrets in code are bad.",
                "exploit_scenario": "Hackers find them.",
                "fix_recommendation": "Use env vars.",
                "secure_code_example": "os.getenv('KEY')"
            }
        ],
        "audit": {
            "timestamp": "Jan 01, 2026",
            "file": "test.py"
        },
        "risk_delta": 5
    }
    
    def generate_pdf(payload: Dict[str, Any], filename: str = "test_report.pdf"):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except Exception as e:
            print("Local PDF generation requires reportlab. Install it and retry.")
            raise

        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        x_margin = 50
        y = height - 50

        c.setFont("Helvetica-Bold", 14)
        c.drawString(x_margin, y, "Audit Report")
        y -= 30

        c.setFont("Helvetica", 11)
        c.drawString(x_margin, y, f"Risk Score: {payload.get('risk_score')}")
        y -= 18
        c.drawString(x_margin, y, f"Risk Level: {payload.get('risk_level')}")
        y -= 22

        violations = payload.get('violations', [])
        if violations:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_margin, y, "Violations:")
            y -= 18
            c.setFont("Helvetica", 10)
            for v in violations:
                # ensure enough space on page
                if y < 80:
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica", 10)

                id_ = v.get('id') or v.get('rule_id')
                c.drawString(x_margin, y, f"- [{v.get('severity', '')}] {v.get('message', '')} (id: {id_})")
                y -= 14
                if v.get('risk_explanation'):
                    c.drawString(x_margin + 12, y, f"Explanation: {v.get('risk_explanation')}" )
                    y -= 12
                if v.get('fix_recommendation'):
                    c.drawString(x_margin + 12, y, f"Fix: {v.get('fix_recommendation')}")
                    y -= 12
                if v.get('secure_code_example'):
                    c.drawString(x_margin + 12, y, f"Example: {v.get('secure_code_example')}")
                    y -= 12
                y -= 6

        audit = payload.get('audit', {}) or {}
        if audit:
            if y < 120:
                c.showPage()
                y = height - 50
            c.setFont("Helvetica-Bold", 12)
            c.drawString(x_margin, y, "Audit Summary:")
            y -= 18
            c.setFont("Helvetica", 10)
            c.drawString(x_margin, y, f"Timestamp: {audit.get('timestamp')}")
            y -= 14
            c.drawString(x_margin, y, f"File: {audit.get('file')}")
            y -= 14

        c.save()
        print(f"SUCCESS: Local PDF generated at {filename}")

    # Try server export first; if not available, fallback to local PDF generation
    try:
        response = requests.post(f"{base_url}/export/pdf", json=data, timeout=5)
        if response.status_code == 200 and response.headers.get('content-type','').lower() == 'application/pdf':
            with open(output, "wb") as f:
                f.write(response.content)
            print(f"SUCCESS: PDF exported to {output} (from server)")
            if open_file:
                _open_file(output)
            return
        else:
            print(f"Server export failed or returned non-PDF (status {response.status_code}). Falling back to local generation.")
    except Exception as e:
        print(f"Server export not available ({e}). Falling back to local generation.")

    # Fallback: generate local PDF
    try:
        generate_pdf(data, output)
        if open_file:
            _open_file(output)
    except Exception as e:
        print(f"Local PDF generation failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export audit report to PDF (server or local fallback).")
    parser.add_argument("--url", default=BASE_URL, help="Base URL for server export (default: http://127.0.0.1:8000)")
    parser.add_argument("--output", default="test_report.pdf", help="Output PDF filename")
    parser.add_argument("--open", dest="open_file", action="store_true", help="Open the PDF after generation (Windows uses os.startfile)")
    args = parser.parse_args()

    def _open_file(path: str):
        try:
            if sys.platform.startswith('win'):
                os.startfile(path)
            else:
                webbrowser.open(f'file://{os.path.abspath(path)}')
        except Exception as e:
            print(f"Could not open file {path}: {e}")

    test_export(base_url=args.url, output=args.output, open_file=args.open_file)
