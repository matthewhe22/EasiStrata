from django.template.loader import get_template, render_to_string

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    # WeasyPrint needs native Cairo/Pango libraries that are unavailable on
    # some platforms (e.g. serverless). Defer the failure to call time so the
    # rest of the app can still boot and run.
    HTML = CSS = None
    WEASYPRINT_AVAILABLE = False


def _require_weasyprint():
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "PDF generation is unavailable: WeasyPrint and its native "
            "dependencies (Cairo/Pango) are not installed in this environment."
        )

from base.models import Client
from finance.models import Billing, CashReceipt
from my_project import settings
from scripts.billing.billing_invoice import BillingInv

# module for billing reder pdf file
from scripts.utils.fin_utils import generate_billing_info


def billing_pdf_file(pk):
    _require_weasyprint()
    template_name = settings.INVOICE_TEMPLATE
    billing = BillingInv(pk)
    obj_bill = Billing.objects.get(id=pk)
    if bool(obj_bill.attachment):
        # if billing pdf already generated
        filename = "/" + obj_bill.attachment.name
        save_location = settings.MEDIA_ROOT + filename

    else:
        # if there is no billing pdf
        bill_num = obj_bill.billing_num
        context = billing.generate_feed_data()
        html_string = render_to_string(template_name, context)
        obj_bill.attachment = bill_num + ".pdf"
        filename = "/" + bill_num + ".pdf"
        html = HTML(string=html_string)
        save_location = settings.MEDIA_ROOT + filename
        html.write_pdf(target=save_location, stylesheets=[CSS(settings.STATIC_DIR + '/css/invoice.css')])
        obj_bill.save()

    return save_location


def agm_pdf_to_file(template_name, context, filename, css_path):
    _require_weasyprint()
    # css_path example '/css/agm.css'
    filename = '/temp_agm/' + filename
    html_string = render_to_string(template_name, context)
    html = HTML(string=html_string)
    save_location = settings.MEDIA_ROOT + filename
    html.write_pdf(target=save_location, stylesheets=[CSS(settings.STATIC_DIR + css_path)])

    return save_location


def cash_receipt_pdf_to_file(cash_id):
    _require_weasyprint()
    template_name = settings.RECEIPT_TEMPLATE
    # billing = BillingInv(pk)
    cash = CashReceipt.objects.get(id=cash_id)
    if bool(cash.attachment):
        # if billing pdf already generated
        filename = "/" + cash.attachment.name
        save_location = settings.MEDIA_ROOT + filename

    else:
        # if there is no billing pdf

        property = cash.get_property()
        oc = cash.get_oc()
        lot = cash.get_lot_instance()
        billing_info = generate_billing_info(lot, property)
        context = {
            'item': cash,
            'property': property,
            'oc': oc,
            'lot': lot,
            'billing_info': billing_info,
            'client': Client.objects.get(id=1)
        }

        html_string = render_to_string(template_name, context)
        cash.attachment = cash.recpt_no + ".pdf"
        filename = "/" + cash.recpt_no + ".pdf"
        html = HTML(string=html_string)
        save_location = settings.MEDIA_ROOT + filename
        html.write_pdf(target=save_location, stylesheets=[CSS(settings.STATIC_DIR + '/css/invoice.css')])
        cash.save()

    return save_location
