from pydantic import BaseModel


class DetectedItem(BaseModel):
    product_name: str
    diameter: str | None = None
    quantity: float = 1
    source_text: str | None = None


class QuotationRow(BaseModel):
    product_name: str
    product_code: str
    diameter: str | None = None
    quantity: float
    unit_price: float
    total_price: float
    confidence: float


class QuotationSummary(BaseModel):
    subtotal: float
    discount: float
    vat_rate: float
    vat_amount: float
    grand_total: float


class AnalysisResponse(BaseModel):
    extracted_text: str
    detected_items: list[DetectedItem]
    quotation_rows: list[QuotationRow]
    summary: QuotationSummary
