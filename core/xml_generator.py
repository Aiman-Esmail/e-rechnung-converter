"""
xml_generator.py
يحوّل كائن Invoice إلى ملف XRechnung XML بصيغة UBL 2.1
"""

from lxml import etree
from core.invoice_model import Invoice, Party


NSMAP = {
    None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}

CAC = NSMAP["cac"]
CBC = NSMAP["cbc"]


def _sub(parent, tag_ns: str, tag: str, text: str = None, **attrib):
    child = etree.SubElement(parent, f"{{{tag_ns}}}{tag}", **attrib)
    if text is not None:
        child.text = str(text)
    return child


def _build_party(parent_tag: str, party: Party):
    wrapper = etree.Element(f"{{{CAC}}}{parent_tag}")
    party_el = _sub(wrapper, CAC, "Party")

    _sub(party_el, CBC, "EndpointID", text=party.email, schemeID="EM")

    party_name = _sub(party_el, CAC, "PartyName")
    _sub(party_name, CBC, "Name", text=party.name)

    address = _sub(party_el, CAC, "PostalAddress")
    _sub(address, CBC, "StreetName", text=party.street)
    _sub(address, CBC, "CityName", text=party.city)
    _sub(address, CBC, "PostalZone", text=party.postal_code)
    country = _sub(address, CAC, "Country")
    _sub(country, CBC, "IdentificationCode", text=party.country_code)

    if party.vat_id:
        tax_scheme = _sub(party_el, CAC, "PartyTaxScheme")
        _sub(tax_scheme, CBC, "CompanyID", text=party.vat_id)
        scheme = _sub(tax_scheme, CAC, "TaxScheme")
        _sub(scheme, CBC, "ID", text="VAT")

    legal_entity = _sub(party_el, CAC, "PartyLegalEntity")
    _sub(legal_entity, CBC, "RegistrationName", text=party.name)
    if party.legal_registration_id:
        _sub(legal_entity, CBC, "CompanyID", text=party.legal_registration_id)

    if party.contact_name or party.contact_phone:
        contact = _sub(party_el, CAC, "Contact")
        if party.contact_name:
            _sub(contact, CBC, "Name", text=party.contact_name)
        if party.contact_phone:
            _sub(contact, CBC, "Telephone", text=party.contact_phone)
        _sub(contact, CBC, "ElectronicMail", text=party.email)

    return wrapper

def generate_xrechnung_xml(invoice: Invoice, pretty: bool = True) -> bytes:
    root = etree.Element(f"{{{NSMAP[None]}}}Invoice", nsmap=NSMAP)

    _sub(root, CBC, "CustomizationID", text=invoice.specification_id)
    _sub(root, CBC, "ProfileID", text=invoice.business_process_id)
    _sub(root, CBC, "ID", text=invoice.invoice_number)
    _sub(root, CBC, "IssueDate", text=invoice.issue_date.isoformat())
    _sub(root, CBC, "InvoiceTypeCode", text=invoice.invoice_type_code)

    if invoice.notes:
        _sub(root, CBC, "Note", text=invoice.notes)

    _sub(root, CBC, "DocumentCurrencyCode", text=invoice.currency_code)

    if invoice.buyer_reference:
        _sub(root, CBC, "BuyerReference", text=invoice.buyer_reference)

    if invoice.purchase_order_reference:
        order_ref = _sub(root, CAC, "OrderReference")
        _sub(order_ref, CBC, "ID", text=invoice.purchase_order_reference)

    root.append(_build_party("AccountingSupplierParty", invoice.seller))
    root.append(_build_party("AccountingCustomerParty", invoice.buyer))

    if invoice.payment_info:
        pi = invoice.payment_info
        if pi.iban:
            payment_means = _sub(root, CAC, "PaymentMeans")
            _sub(payment_means, CBC, "PaymentMeansCode", text=pi.payment_means_code)
            financial_account = _sub(payment_means, CAC, "PayeeFinancialAccount")
            _sub(financial_account, CBC, "ID", text=pi.iban)
            if pi.bic:
                branch = _sub(financial_account, CAC, "FinancialInstitutionBranch")
                _sub(branch, CBC, "ID", text=pi.bic)

        if pi.payment_terms:
            payment_terms_el = _sub(root, CAC, "PaymentTerms")
            _sub(payment_terms_el, CBC, "Note", text=pi.payment_terms)

    tax_total = _sub(root, CAC, "TaxTotal")
    _sub(tax_total, CBC, "TaxAmount", text=str(invoice.total_vat_amount), currencyID=invoice.currency_code)

    for (vat_code, vat_rate), amounts in invoice.vat_breakdown.items():
        subtotal = _sub(tax_total, CAC, "TaxSubtotal")
        _sub(subtotal, CBC, "TaxableAmount", text=str(amounts["net"]), currencyID=invoice.currency_code)
        _sub(subtotal, CBC, "TaxAmount", text=str(amounts["vat"]), currencyID=invoice.currency_code)
        category = _sub(subtotal, CAC, "TaxCategory")
        _sub(category, CBC, "ID", text=vat_code)
        _sub(category, CBC, "Percent", text=str(vat_rate))
        scheme = _sub(category, CAC, "TaxScheme")
        _sub(scheme, CBC, "ID", text="VAT")

    monetary_total = _sub(root, CAC, "LegalMonetaryTotal")
    _sub(monetary_total, CBC, "LineExtensionAmount",
         text=str(invoice.total_net_amount), currencyID=invoice.currency_code)
    _sub(monetary_total, CBC, "TaxExclusiveAmount",
         text=str(invoice.total_net_amount), currencyID=invoice.currency_code)
    _sub(monetary_total, CBC, "TaxInclusiveAmount",
         text=str(invoice.total_gross_amount), currencyID=invoice.currency_code)
    _sub(monetary_total, CBC, "PayableAmount",
         text=str(invoice.total_gross_amount), currencyID=invoice.currency_code)

    for line in invoice.lines:
        line_el = _sub(root, CAC, "InvoiceLine")
        _sub(line_el, CBC, "ID", text=line.line_id)
        _sub(line_el, CBC, "InvoicedQuantity", text=str(line.quantity), unitCode=line.unit_code)
        _sub(line_el, CBC, "LineExtensionAmount",
             text=str(line.net_amount), currencyID=invoice.currency_code)

        item = _sub(line_el, CAC, "Item")
        _sub(item, CBC, "Name", text=line.description)
        classified_tax = _sub(item, CAC, "ClassifiedTaxCategory")
        _sub(classified_tax, CBC, "ID", text=line.vat_category_code)
        _sub(classified_tax, CBC, "Percent", text=str(line.vat_rate))
        scheme = _sub(classified_tax, CAC, "TaxScheme")
        _sub(scheme, CBC, "ID", text="VAT")

        price = _sub(line_el, CAC, "Price")
        _sub(price, CBC, "PriceAmount", text=str(line.unit_price), currencyID=invoice.currency_code)

    return etree.tostring(
        root,
        pretty_print=pretty,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=False,
    )


def save_xrechnung_xml(invoice: Invoice, output_path: str) -> str:
    xml_bytes = generate_xrechnung_xml(invoice)
    with open(output_path, "wb") as f:
        f.write(xml_bytes)
    return output_path