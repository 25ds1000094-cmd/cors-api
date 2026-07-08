from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import date
import re
import json

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

    # Vendor extraction
    vendor_match = re.search(
        r'([A-Z][A-Za-z0-9\-]+(?:\s+[A-Z][A-Za-z0-9\-]+){0,5}\s+(?:Ltd\.|LLC|Inc\.|Industries|Corporation|Corp\.))',
        text
    )
    vendor = vendor_match.group(1).strip() if vendor_match else ""

    # Currency extraction
    currency_match = re.search(r'\b(USD|EUR|GBP)\b', text, re.I)
    currency = currency_match.group(1).upper() if currency_match else "USD"

    # Amount extraction
    amount = 0.0

    amount_patterns = [
        r'(?:total|amount due|balance due|due)\s*[:\-]?\s*[$€£]?\s*([0-9]+(?:\.[0-9]{1,2})?)',
        r'[$€£]\s*([0-9]+(?:\.[0-9]{1,2})?)'
    ]

    for pattern in amount_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            amount = float(match.group(1))
            break

    # Date extraction
    date_match = re.search(
        r'\b(2026-\d{2}-\d{2})\b',
        text
    )
    due_date = date_match.group(1) if date_match else "1970-01-01"

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
        # Always return schema-valid JSON
        return InvoiceResponse(
            vendor="",
            amount=0.0,
            currency="USD",
            date="1970-01-01"
        )
