from sqlalchemy import select
from sqlalchemy.orm import Session
from rapidfuzz import fuzz

from app.models.product import Product
from app.schemas.quotation import DetectedItem, QuotationRow, QuotationSummary


def match_items(db: Session, items: list[DetectedItem]) -> list[QuotationRow]:
    products = db.scalars(select(Product)).all()
    rows: list[QuotationRow] = []

    for item in items:
        best = None
        best_score = 0.0
        for product in products:
            name_score = fuzz.token_sort_ratio(item.product_name.lower(), product.product_name.lower())
            diameter_score = 100 if (not item.diameter or not product.diameter or item.diameter == product.diameter) else 40
            score = (name_score * 0.8) + (diameter_score * 0.2)
            if score > best_score:
                best, best_score = product, score
        if best:
            total = round(item.quantity * best.price, 2)
            rows.append(
                QuotationRow(
                    product_name=best.product_name,
                    product_code=best.product_code,
                    diameter=best.diameter,
                    quantity=item.quantity,
                    unit_price=best.price,
                    total_price=total,
                    confidence=round(best_score, 2),
                )
            )
    return rows


def calculate_summary(rows: list[QuotationRow], discount: float = 0.0, vat_rate: float = 0.2) -> QuotationSummary:
    subtotal = round(sum(r.total_price for r in rows), 2)
    discounted = max(subtotal - discount, 0)
    vat_amount = round(discounted * vat_rate, 2)
    grand_total = round(discounted + vat_amount, 2)
    return QuotationSummary(
        subtotal=subtotal,
        discount=discount,
        vat_rate=vat_rate,
        vat_amount=vat_amount,
        grand_total=grand_total,
    )
