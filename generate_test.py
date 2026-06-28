import sys
sys.path.insert(0, '.')

from core.invoice_model import Invoice, Party, InvoiceLine, PaymentInfo, VAT_CATEGORY_CODES
from core.xml_generator import save_xrechnung_xml
from datetime import date
from decimal import Decimal

seller = Party(
    name='Aiman Esmail IT-Dienstleistungen',
    street='Musterstraße 1',
    city='Hamburg',
    postal_code='20095',
    country_code='DE',
    email='kontakt@aiman-it.de',
    vat_id='DE123456789',
    contact_name='Aiman Esmail',
    contact_phone='+49 40 12345678', 
)

buyer = Party(
    name='Beispiel GmbH',
    street='Kundenweg 5',
    city='Berlin',
    postal_code='10115',
    country_code='DE',
    email='buchhaltung@beispiel-gmbh.de',
)

line1 = InvoiceLine(
    line_id='1',
    description='KI-Beratung - Entwicklung Rechnungsmodul',
    quantity=Decimal('10'),
    unit_code='HUR',
    unit_price=Decimal('95.00'),
    vat_category_code=VAT_CATEGORY_CODES['STANDARD'],
    vat_rate=Decimal('19.00'),
)

inv = Invoice(
    invoice_number='RE-2026-001',
    issue_date=date(2026, 6, 19),
    currency_code='EUR',
    seller=seller,
    buyer=buyer,
    lines=[line1],
    buyer_reference='04011000-1234512345-67',
    payment_info=PaymentInfo(iban='DE89370400440532013000', payment_terms='Zahlbar innerhalb 14 Tagen netto'),
)

path = save_xrechnung_xml(inv, 'test_invoice2.xml')
print('Saved to', path)