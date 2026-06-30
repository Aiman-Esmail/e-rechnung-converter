"""
app.py — واجهة Streamlit لمحول XRechnung (نسخة محسّنة بـ st.form)
"""

import streamlit as st
from datetime import date
from decimal import Decimal
import sys
import os

st.set_page_config(
    page_title="E-Rechnung Converter",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp { background: #F7F8FA; font-family: 'Inter', sans-serif; }
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 2rem; padding-bottom: 2rem; max-width: 900px;}

.card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.hero {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px;
    padding: 36px 40px;
    margin-bottom: 28px;
    color: white;
}

.hero h1 { font-size: 1.8rem; font-weight: 700; margin: 0 0 8px 0; color: white; }
.hero p { font-size: 0.95rem; color: #94A3B8; margin: 0; }

.badge {
    display: inline-block;
    background: rgba(99,179,237,0.15);
    color: #63B3ED;
    border: 1px solid rgba(99,179,237,0.3);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.72rem;
    font-weight: 500;
    margin-bottom: 14px;
    letter-spacing: 0.05em;
}

.section-title {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    color: #6B7280;
    text-transform: uppercase;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid #F3F4F6;
}

.stFormSubmitButton > button {
    background: #1a1a2e !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    height: 52px !important;
    margin-top: 8px !important;
}

.stFormSubmitButton > button:hover {
    background: #0f3460 !important;
    transform: translateY(-1px) !important;
}

.stDownloadButton > button {
    background: #059669 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100% !important;
    height: 48px !important;
}

div[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)

sys.path.insert(0, os.path.dirname(__file__))
try:
    from core.invoice_model import Invoice, Party, InvoiceLine, PaymentInfo
    from core.xml_generator import generate_xrechnung_xml
    CORE_LOADED = True
except ImportError as e:
    CORE_LOADED = False
    IMPORT_ERROR = str(e)

st.markdown("""
<div class="hero">
    <div class="badge">XRechnung · UBL 2.1 · EN 16931</div>
    <h1>🧾 E-Rechnung Converter</h1>
    <p>Füllen Sie das Formular aus und laden Sie Ihre konforme XRechnung-XML-Datei herunter.</p>
</div>
""", unsafe_allow_html=True)

if not CORE_LOADED:
    st.error(f"Fehler beim Laden der Module: {IMPORT_ERROR}")
    st.stop()

def get_vat_rate(label):
    if "19" in label: return Decimal("19.00")
    if "7" in label: return Decimal("7.00")
    return Decimal("0.00")

def get_vat_code(label):
    if "Reverse" in label: return "AE"
    if "0%" in label: return "Z"
    return "S"

vat_options = ["19% MwSt.", "7% MwSt.", "0% (Steuerfrei)", "Reverse Charge"]

# Session state للبنود
if "num_lines" not in st.session_state:
    st.session_state.num_lines = 1

# أزرار إضافة/حذف بنود (خارج الـ form)
col_add, col_del = st.columns([1, 1])
with col_add:
    if st.button("＋ Position hinzufügen"):
        st.session_state.num_lines += 1
        st.rerun()
with col_del:
    if st.button("－ Position entfernen") and st.session_state.num_lines > 1:
        st.session_state.num_lines -= 1
        st.rerun()

# الـ Form الرئيسي
with st.form("invoice_form"):

    # --- Rechnungsdaten ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Rechnungsdaten</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        invoice_number = st.text_input("Rechnungsnummer *", value="RE-2026-001")
    with c2:
        issue_date = st.date_input("Rechnungsdatum *", value=date.today())
    with c3:
        currency = st.selectbox("Währung", ["EUR", "USD", "GBP"])
    c4, c5 = st.columns(2)
    with c4:
        buyer_reference = st.text_input("Leitweg-ID *", placeholder="04011000-1234512345-67")
    with c5:
        invoice_type = st.selectbox("Rechnungsart", ["Rechnung (380)", "Gutschrift (381)"])
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Verkäufer ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Verkäufer (Ihr Unternehmen)</div>', unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    with s1:
        seller_name = st.text_input("Firmenname *", placeholder="Musterfirma GmbH")
        seller_street = st.text_input("Straße & Hausnummer *", placeholder="Musterstraße 1")
        seller_city = st.text_input("Stadt *", placeholder="Hamburg")
        seller_contact = st.text_input("Ansprechpartner", placeholder="Max Mustermann")
    with s2:
        seller_email = st.text_input("E-Mail *", placeholder="info@musterfirma.de")
        seller_vat = st.text_input("USt-IdNr.", placeholder="DE123456789")
        cp, cc = st.columns(2)
        with cp:
            seller_postal = st.text_input("PLZ *", placeholder="20095")
        with cc:
            seller_country = st.text_input("Land *", value="DE", max_chars=2)
        seller_phone = st.text_input("Telefon *", placeholder="+49 40 12345678")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Käufer ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Käufer (Rechnungsempfänger)</div>', unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    with b1:
        buyer_name = st.text_input("Firmenname *", placeholder="Beispiel AG", key="bn")
        buyer_street = st.text_input("Straße & Hausnummer *", placeholder="Kundenweg 5", key="bs")
        buyer_city = st.text_input("Stadt *", placeholder="Berlin", key="bc")
    with b2:
        buyer_email = st.text_input("E-Mail *", placeholder="buchhaltung@beispiel.de", key="be")
        buyer_vat = st.text_input("USt-IdNr.", placeholder="DE987654321", key="bv")
        bp, bco = st.columns(2)
        with bp:
            buyer_postal = st.text_input("PLZ *", placeholder="10115", key="bpl")
        with bco:
            buyer_country = st.text_input("Land *", value="DE", max_chars=2, key="bco")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Zahlung ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Zahlungsinformationen</div>', unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        iban = st.text_input("IBAN", placeholder="DE89370400440532013000")
    with p2:
        bic = st.text_input("BIC", placeholder="COBADEFFXXX")
    payment_terms = st.text_input("Zahlungsbedingungen",
                                   value="Zahlbar innerhalb von 14 Tagen netto")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Rechnungspositionen ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Rechnungspositionen</div>', unsafe_allow_html=True)

    descs, qtys, prices, vats = [], [], [], []
    for i in range(st.session_state.num_lines):
        st.markdown(f"**Position {i+1}**")
        lc1, lc2, lc3, lc4 = st.columns([4, 1.5, 1.8, 2])
        with lc1:
            descs.append(st.text_input("Beschreibung *", placeholder="KI-Beratung", key=f"d{i}"))
        with lc2:
            qtys.append(st.number_input("Menge", value=1.0, min_value=0.01, step=1.0, key=f"q{i}"))
        with lc3:
            prices.append(st.number_input("Preis (€)", value=0.0, min_value=0.0,
                                           step=10.0, format="%.2f", key=f"p{i}"))
        with lc4:
            vats.append(st.selectbox("MwSt.", vat_options, key=f"v{i}"))

    st.markdown('</div>', unsafe_allow_html=True)

    # --- زر التوليد ---
    submitted = st.form_submit_button("🔄 XRechnung XML generieren")

# --- معالجة النتيجة بعد الـ form ---
if submitted:
    errors = []
    if not invoice_number.strip(): errors.append("Rechnungsnummer fehlt")
    if not seller_name.strip(): errors.append("Verkäufer: Firmenname fehlt")
    if not seller_email.strip(): errors.append("Verkäufer: E-Mail fehlt")
    if not seller_street.strip(): errors.append("Verkäufer: Straße fehlt")
    if not seller_city.strip(): errors.append("Verkäufer: Stadt fehlt")
    if not seller_postal.strip(): errors.append("Verkäufer: PLZ fehlt")
    if not seller_phone.strip(): errors.append("Verkäufer: Telefon fehlt (BR-DE-6)")
    if not buyer_name.strip(): errors.append("Käufer: Firmenname fehlt")
    if not buyer_email.strip(): errors.append("Käufer: E-Mail fehlt")
    if not buyer_street.strip(): errors.append("Käufer: Straße fehlt")
    if not buyer_city.strip(): errors.append("Käufer: Stadt fehlt")
    if not buyer_postal.strip(): errors.append("Käufer: PLZ fehlt")
    if not any(d.strip() for d in descs):
        errors.append("Mindestens eine Position mit Beschreibung erforderlich")

    if errors:
        st.error("**Pflichtfelder fehlen:**")
        for e in errors:
            st.error(f"• {e}")
    else:
        try:
            seller = Party(
                name=seller_name.strip(),
                street=seller_street.strip(),
                city=seller_city.strip(),
                postal_code=seller_postal.strip(),
                country_code=seller_country.strip().upper(),
                email=seller_email.strip(),
                vat_id=seller_vat.strip() or None,
                contact_name=seller_contact.strip() or None,
                contact_phone=seller_phone.strip(),
            )
            buyer = Party(
                name=buyer_name.strip(),
                street=buyer_street.strip(),
                city=buyer_city.strip(),
                postal_code=buyer_postal.strip(),
                country_code=buyer_country.strip().upper(),
                email=buyer_email.strip(),
                vat_id=buyer_vat.strip() or None,
            )
            lines_obj = []
            for i in range(st.session_state.num_lines):
                if not descs[i].strip():
                    continue
                lines_obj.append(InvoiceLine(
                    line_id=str(i+1),
                    description=descs[i].strip(),
                    quantity=Decimal(str(qtys[i])),
                    unit_code="C62",
                    unit_price=Decimal(str(prices[i])),
                    vat_category_code=get_vat_code(vats[i]),
                    vat_rate=get_vat_rate(vats[i]),
                ))

            # حساب الإجماليات
            total_net = sum(
                (Decimal(str(qtys[i])) * Decimal(str(prices[i]))).quantize(Decimal("0.01"))
                for i in range(st.session_state.num_lines) if descs[i].strip()
            )
            total_vat = sum(
                ((Decimal(str(qtys[i])) * Decimal(str(prices[i]))) *
                 get_vat_rate(vats[i]) / 100).quantize(Decimal("0.01"))
                for i in range(st.session_state.num_lines) if descs[i].strip()
            )
            total_gross = total_net + total_vat

            payment = PaymentInfo(
                iban=iban.strip() or None,
                bic=bic.strip() or None,
                payment_terms=payment_terms.strip() or None,
            )
            invoice = Invoice(
                invoice_number=invoice_number.strip(),
                issue_date=issue_date,
                currency_code=currency,
                seller=seller,
                buyer=buyer,
                lines=lines_obj,
                invoice_type_code="381" if "381" in invoice_type else "380",
                buyer_reference=buyer_reference.strip() or None,
                payment_info=payment,
            )
            xml_bytes = generate_xrechnung_xml(invoice)
            filename = f"{invoice_number.strip().replace('/', '-')}.xml"

            # عرض الإجماليات
            st.success("✅ XRechnung XML erfolgreich erstellt!")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Nettobetrag", f"{total_net:,.2f} {currency}")
            with m2:
                st.metric("MwSt.", f"{total_vat:,.2f} {currency}")
            with m3:
                st.metric("Gesamtbetrag", f"{total_gross:,.2f} {currency}")

            st.download_button(
                label="⬇️ XML-Datei herunterladen",
                data=xml_bytes,
                file_name=filename,
                mime="application/xml",
            )
            st.info("💡 Validieren Sie die Datei auf: https://erechnungsvalidator.service.bund.de")

        except Exception as e:
            st.error(f"Fehler beim Erstellen: {str(e)}")
