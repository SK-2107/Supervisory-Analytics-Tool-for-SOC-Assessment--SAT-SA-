"""
Report Generation REST Endpoints for SAT-SA.
"""

from fastapi import APIRouter, HTTPException, Response
from src.db.connection import get_db_connection
from src.reporting.pdf_generator import generate_supervisory_pdf_report

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get("/pdf")
def download_pdf_report():
    """
    Generates and returns an executive PDF audit report.
    """
    conn = get_db_connection()
    try:
        pdf_bytes = generate_supervisory_pdf_report(conn)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=SAT-SA_Supervisory_Report.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
    finally:
        conn.close()
