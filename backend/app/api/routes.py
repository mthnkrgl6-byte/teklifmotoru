from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.quotation import AnalysisResponse
from app.services.detection import detect_products
from app.services.exporters import export_excel, export_pdf
from app.services.extractors import extract_text
from app.services.matching import calculate_summary, match_items

router = APIRouter(prefix="/api", tags=["analysis"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_file(
    file: UploadFile = File(...),
    discount: float = Form(0.0),
    db: Session = Depends(get_db),
):
    content = await file.read()
    try:
        extracted_text = extract_text(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    detected_items = detect_products(extracted_text)
    quotation_rows = match_items(db, detected_items)
    summary = calculate_summary(quotation_rows, discount=discount)

    return AnalysisResponse(
        extracted_text=extracted_text,
        detected_items=detected_items,
        quotation_rows=quotation_rows,
        summary=summary,
    )


@router.post("/export/{format}")
def export_quotation(format: str, payload: AnalysisResponse):
    if format not in {"xlsx", "pdf"}:
        raise HTTPException(status_code=400, detail="Unsupported export format")
    data = export_excel(payload.quotation_rows, payload.summary) if format == "xlsx" else export_pdf(payload.quotation_rows, payload.summary)
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "application/pdf"
    filename = f"quotation.{format}"
    return StreamingResponse(BytesIO(data), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})
