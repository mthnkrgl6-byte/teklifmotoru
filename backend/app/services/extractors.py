from io import BytesIO
from pathlib import Path

import pandas as pd
import pytesseract
from PIL import Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes

from app.core.config import settings

if settings.tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def extract_text_from_excel(content: bytes) -> str:
    workbook = pd.read_excel(BytesIO(content), sheet_name=None)
    lines: list[str] = []
    for sheet_name, df in workbook.items():
        lines.append(f"[Sheet: {sheet_name}]")
        lines.extend(df.fillna("").astype(str).apply(" ".join, axis=1).tolist())
    return "\n".join(filter(None, lines))


def extract_text_from_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    pages = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(pages).strip()
    if text:
        return text
    images = convert_from_bytes(content)
    return "\n".join(pytesseract.image_to_string(img, lang="tur+eng") for img in images)


def extract_text_from_image(content: bytes) -> str:
    image = Image.open(BytesIO(content))
    return pytesseract.image_to_string(image, lang="tur+eng")


def extract_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension == ".xlsx":
        return extract_text_from_excel(content)
    if extension == ".pdf":
        return extract_text_from_pdf(content)
    if extension in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        return extract_text_from_image(content)
    raise ValueError(f"Unsupported file type: {extension}")
