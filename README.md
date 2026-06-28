# E-Rechnung Converter 🇩🇪

أداة تحويل الفواتير إلى صيغة XRechnung (UBL 2.1) المتوافقة مع المعيار الألماني EN 16931.

## المتطلبات

- Python 3.10+
- Java 11+ (لتشغيل KoSIT validator)

## التثبيت

pip install -r requirements.txt

## إعداد KoSIT Validator (مرة وحدة)

راجع ملف `kosit/SETUP.md` لتعليمات تحميل أدوات التحقق الرسمية.

## الاستخدام

from core.invoice_model import Invoice, Party, InvoiceLine, PaymentInfo
from core.xml_generator import save_xrechnung_xml

## البنية

- core/invoice_model.py  — نموذج بيانات الفاتورة (EN 16931)
- core/xml_generator.py  — مولّد XRechnung XML (UBL 2.1)
- core/validator.py      — تكامل مع KoSIT validator

## الحالة

✅ فاتورة اختبار اجتازت KoSIT Validator 1.6.0 بنجاح (Validation successful)
🔄 قيد التطوير: واجهة Streamlit + استخراج PDF