"""
invoice_model.py
نموذج بيانات الفاتورة وفق متطلبات EN 16931 / XRechnung 3.0.x
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional, List


# BT-24: تم تصحيحها لتطابق الإصدار الرسمي الحالي (xeinkauf.de/kosit)
XRECHNUNG_SPECIFICATION_ID = "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0"

DEFAULT_BUSINESS_PROCESS_ID = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"

INVOICE_TYPE_CODES = {
    "INVOICE": "380",
    "CREDIT_NOTE": "381",
    "CORRECTED_INVOICE": "384",
    "SELF_BILLED": "389",
}

VAT_CATEGORY_CODES = {
    "STANDARD": "S",
    "ZERO": "Z",
    "EXEMPT": "E",
    "REVERSE_CHARGE": "AE",
    "INTRA_COMMUNITY": "K",
    "EXPORT": "G",
    "OUTSIDE_SCOPE": "O",
}

PAYMENT_MEANS_CODES = {
    "CREDIT_TRANSFER": "30",
    "DIRECT_DEBIT": "49",
    "SEPA_CREDIT_TRANSFER": "58",
}


@dataclass
class Party:
    name: str
    street: str
    city: str
    postal_code: str
    country_code: str
    email: str
    vat_id: Optional[str] = None
    tax_registration_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    legal_registration_id: Optional[str] = None


@dataclass
class PaymentInfo:
    payment_means_code: str = PAYMENT_MEANS_CODES["SEPA_CREDIT_TRANSFER"]
    iban: Optional[str] = None
    bic: Optional[str] = None
    payment_terms: Optional[str] = None
    due_date: Optional[date] = None


@dataclass
class InvoiceLine:
    line_id: str
    description: str
    quantity: Decimal
    unit_code: str
    unit_price: Decimal
    vat_category_code: str
    vat_rate: Decimal

    @property
    def net_amount(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))


@dataclass
class Invoice:
    invoice_number: str
    issue_date: date
    currency_code: str
    seller: Party
    buyer: Party
    lines: List[InvoiceLine] = field(default_factory=list)
    invoice_type_code: str = INVOICE_TYPE_CODES["INVOICE"]
    specification_id: str = XRECHNUNG_SPECIFICATION_ID
    business_process_id: str = DEFAULT_BUSINESS_PROCESS_ID
    buyer_reference: Optional[str] = None
    purchase_order_reference: Optional[str] = None
    payment_info: Optional[PaymentInfo] = None
    notes: Optional[str] = None

    @property
    def total_net_amount(self) -> Decimal:
        return sum((line.net_amount for line in self.lines), Decimal("0.00"))

    @property
    def total_vat_amount(self) -> Decimal:
        total = Decimal("0.00")
        for line in self.lines:
            vat = (line.net_amount * line.vat_rate / Decimal("100")).quantize(Decimal("0.01"))
            total += vat
        return total

    @property
    def total_gross_amount(self) -> Decimal:
        return self.total_net_amount + self.total_vat_amount

    @property
    def vat_breakdown(self) -> dict:
        breakdown = {}
        for line in self.lines:
            key = (line.vat_category_code, line.vat_rate)
            vat_amount = (line.net_amount * line.vat_rate / Decimal("100")).quantize(Decimal("0.01"))
            if key not in breakdown:
                breakdown[key] = {"net": Decimal("0.00"), "vat": Decimal("0.00")}
            breakdown[key]["net"] += line.net_amount
            breakdown[key]["vat"] += vat_amount
        return breakdown