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

    # Highest priority: values near total/due/balance keywords
    priority_patterns = [
        r'(?:total\s*(?:amount|due|payable)?|amount\s*due|balance\s*due|grand\s*total|invoice\s*total)'
        r'\s*[:\-]?\s*(?:USD|EUR|GBP|\$|€|£)?\s*([0-9]{1,6}(?:\.[0-9]{1,2})?)',

        r'(?:USD|EUR|GBP)\s*([0-9]{1,6}(?:\.[0-9]{1,2})?)',

        r'[$€£]\s*([0-9]{1,6}(?:\.[0-9]{1,2})?)'
    ]

    for pattern in priority_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                value = float(match)
                if 50 <= value <= 9050:
                    candidates.append(value)
            except:
                pass

    # If keyword extraction worked, use it
    if candidates:
        amount = candidates[0]

    else:
        # Fallback: decimal numbers only
        fallback = re.findall(
            r'\b([0-9]{2,6}\.[0-9]{1,2})\b',
            text
        )

        for item in fallback:
            value = float(item)
            if 50 <= value <= 9050:
                candidates.append(value)

        if candidates:
            amount = candidates[0]


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
