from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product import Product
from app.schemas.quotation import AnalysisResponse
from app.services.detection import detect_products
from app.services.exporters import export_excel, export_pdf
from app.services.extractors import extract_text
from app.services.matching import calculate_summary, match_items

router = APIRouter(prefix="/api", tags=["analysis"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = db.scalars(select(Product)).all()
    return [
        {
            "product_code": p.product_code,
            "product_name": p.product_name,
            "diameter": p.diameter,
            "unit": p.unit,
            "price": p.price,
        }
        for p in products
    ]


def parse_price(value: object) -> float:
    raw = str(value).strip().replace(" ", "").replace(",", ".")
    return float(raw)


@router.post("/products/upload-pricelist")
async def upload_pricelist(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    extension = (file.filename or "").lower().split(".")[-1]
    if extension not in {"xlsx", "csv"}:
        raise HTTPException(status_code=400, detail="Price list must be .xlsx or .csv")

    if extension == "xlsx":
        df = pd.read_excel(BytesIO(content))
    else:
        try:
            df = pd.read_csv(BytesIO(content), sep=None, engine="python")
        except Exception:
            df = pd.read_csv(BytesIO(content))

    required_cols = {"product_code", "product_name", "price"}
    missing = required_cols.difference(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(sorted(missing))}")

    created = 0
    updated = 0

    for row in df.fillna("").to_dict(orient="records"):
        product_code = str(row.get("product_code", "")).strip()
        product_name = str(row.get("product_name", "")).strip()

        if not product_code or not product_name:
            continue

        try:
            price = parse_price(row.get("price", "0"))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Invalid price for product_code={product_code}") from exc

        existing = db.scalar(select(Product).where(Product.product_code == product_code))
        diameter = str(row.get("diameter", "")).strip() or None
        unit = str(row.get("unit", "")).strip() or "adet"

        if existing:
            existing.product_name = product_name
            existing.diameter = diameter
            existing.unit = unit
            existing.price = price
            updated += 1
            continue

        db.add(
            Product(
                product_code=product_code,
                product_name=product_name,
                diameter=diameter,
                unit=unit,
                price=price,
            )
        )
        created += 1

    db.commit()
    return {"created": created, "updated": updated, "total": created + updated}


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_file(
    file: UploadFile | None = File(None),
    raw_text: str | None = Form(None),
    discount: float = Form(0.0),
    vat_rate: float = Form(0.2),
    include_vat: bool = Form(True),
    db: Session = Depends(get_db),
):
    extracted_text = ""

    if file is not None:
        content = await file.read()
        try:
            extracted_text = extract_text(file.filename, content)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    elif raw_text and raw_text.strip():
        extracted_text = raw_text.strip()
    else:
        raise HTTPException(status_code=400, detail="Provide either a file or raw_text")

    detected_items = detect_products(extracted_text)
    quotation_rows = match_items(db, detected_items)
    summary = calculate_summary(
        quotation_rows,
        discount=discount,
        vat_rate=vat_rate if include_vat else 0,
    )

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
