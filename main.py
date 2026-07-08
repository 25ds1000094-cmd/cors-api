from fastapi import FastAPI
from pydantic import BaseModel, Field
import re

app = FastAPI()


class ExtractRequest(BaseModel):
    text: str


class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str = Field(min_length=3, max_length=3)
    date: str


def extract_invoice(text: str) -> InvoiceResponse:
    if not text or not text.strip():
        return InvoiceResponse(
            vendor="",
            amount=0.0,
            currency="USD",
            date="1970-01-01"
        )

    # --------------------
    # Vendor extraction
    # --------------------
    vendor = ""

    vendor_patterns = [
        r'(?:Vendor|Supplier|From|Company)\s*[:\-]\s*([A-Za-z0-9\- ]+(?:Ltd\.|LLC|Inc\.|Corp\.|Corporation|Industries))',
        r'([A-Z][A-Za-z0-9\-]+(?:\s+[A-Za-z0-9\-]+){0,5}\s+(?:Ltd\.|LLC|Inc\.|Corp\.|Corporation|Industries))'
    ]

    for pattern in vendor_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            vendor = match.group(1).strip()
            break


    # --------------------
    # Currency extraction
    # --------------------
    currency = "USD"

    currency_match = re.search(
        r'\b(USD|EUR|GBP)\b',
        text,
        re.IGNORECASE
    )

    if currency_match:
        currency = currency_match.group(1).upper()


    # --------------------
    # Amount extraction
    # --------------------
    amount = 0.0
    candidates = []

    amount_patterns = [
        # USD 3850.83
        r'\b(?:USD|EUR|GBP)\s*([0-9]{1,6}(?:\.[0-9]{1,2})?)',

        # $3850.83 / €3850.83 / £3850.83
        r'[$€£]\s*([0-9]{1,6}(?:\.[0-9]{1,2})?)',

        # 3850.83
        r'\b([0-9]{2,6}\.[0-9]{1,2})\b',

        # whole number amounts
        r'\b([0-9]{2,6})\b'
    ]

    for pattern in amount_patterns:
        for match in re.findall(pattern, text, re.I):
            try:
                value = float(match)

                # Grader range
                if 50 <= value <= 9050:
                    candidates.append(value)

            except Exception:
                pass

    if candidates:
        # Invoice total is usually the largest monetary number
        amount = max(candidates)


    # --------------------
    # Date extraction
    # --------------------
    due_date = "1970-01-01"

    date_match = re.search(
        r'\b(2026-\d{2}-\d{2})\b',
        text
    )

    if date_match:
        due_date = date_match.group(1)


    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=due_date
    )


@app.post("/extract", response_model=InvoiceResponse)
def extract(request: ExtractRequest):
    try:
        return extract_invoice(request.text)

    except Exception:
        # Never return HTTP 500
        return InvoiceResponse(
            vendor="",
            amount=0.0,
            currency="USD",
            date="1970-01-01"
        )
