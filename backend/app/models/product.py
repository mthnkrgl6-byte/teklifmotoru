from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    diameter: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), default="adet")
    price: Mapped[float] = mapped_column(Float, nullable=False)
