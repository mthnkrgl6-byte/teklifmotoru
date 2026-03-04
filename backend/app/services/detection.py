import json
import re
from typing import Any

from openai import OpenAI
from rapidfuzz import fuzz, process

from app.core.config import settings
from app.schemas.quotation import DetectedItem

ALIASES = {
    "pvh": "pvc",
    "pvr": "pvc",
    "ppr": "pprc",
    "kuresel": "küresel",
}
KNOWN_PRODUCTS = ["pvc dirsek", "pprc boru", "küresel vana", "çekvalf", "manşon", "tees"]


def normalize_text(text: str) -> str:
    tokens = []
    for token in text.lower().split():
        token = re.sub(r"[^\wçğıöşü]", "", token)
        tokens.append(ALIASES.get(token, token))
    return " ".join(tokens)


def heuristic_detection(text: str) -> list[DetectedItem]:
    items: list[DetectedItem] = []
    for line in text.splitlines():
        clean = normalize_text(line)
        if not clean:
            continue
        numbers = re.findall(r"\b\d+(?:[.,]\d+)?\b", clean)
        quantity = 1.0
        diameter = None
        if numbers:
            if any(k in clean for k in ["vana", "adet", "pcs"]):
                quantity = float(numbers[0].replace(",", "."))
            else:
                diameter = numbers[0]
                if len(numbers) > 1:
                    quantity = float(numbers[1].replace(",", "."))
        candidate, score, _ = process.extractOne(clean, KNOWN_PRODUCTS, scorer=fuzz.token_sort_ratio) or (clean, 0, 0)
        if score < 45:
            candidate = clean
        items.append(DetectedItem(product_name=candidate.title(), diameter=diameter, quantity=quantity, source_text=line))
    return items


def openai_detection(text: str) -> list[DetectedItem]:
    client = OpenAI(api_key=settings.openai_api_key)
    prompt = (
        "Extract plumbing product lines from the following text. Correct typos and return JSON array "
        "with keys: product_name, diameter (null if absent), quantity.\nText:\n" + text
    )
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or '{"items": []}'
    payload: dict[str, Any] = json.loads(content)
    return [DetectedItem(**item) for item in payload.get("items", [])]


def detect_products(text: str) -> list[DetectedItem]:
    if settings.openai_api_key:
        try:
            items = openai_detection(text)
            if items:
                return items
        except Exception:
            pass
    return heuristic_detection(text)
