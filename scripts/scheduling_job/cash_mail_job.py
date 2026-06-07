import logging

from django.db.models import Q

from finance.models import CashReceipt

from scripts.PDF_service.pdf import cash_receipt_pdf_to_file
from scripts.mail.send_mail import msg_service
from . import cash_mail_template as template
from .billing_mail_job import update_sending, get_sign
from time import sleep


def cash_batch_service():
    """
    filter mail status of prepared or fail
    change status to sending
    generate pdf
    send mail
    :return: none
    """
    cashes = CashReceipt.objects.filter(Q(is_valid=True), Q(mail_status='prepared') | Q(mail_status='fail'))
    for item in cashes:
        try:
            if CashReceipt.objects.get(pk=item.pk).mail_status in ('prepared', 'fail'):
                update_sending(item)
                info = get_subject(item)

                subject = info [0] + template.TITLE

                lot = item.get_lot_instance()

                if lot.prefer_mail == "owner":
                    # add sub if to check if mail1 and mail2 exist
                    if lot.email1:
                        send_pdf_mail(item.pk, subject, lot.email1)
                    if lot.email2:
                        send_pdf_mail(item.pk, subject, lot.email2)
                # check if agent mail exists
                elif lot.prefer_mail == 'agent' and lot.agent_email:
                    send_pdf_mail(item.pk, subject, lot.agent_email)

                if not bool(item.attachment):
                    item.attachment = item.recpt_no + ".pdf"

                item.mail_status = 'sent'
                item.save()
                # sleep(40)


        except Exception as e:
            logging.exception(e)
            item.mail_status = 'fail'
            item.save()


def get_subject(cash_receipt):
    """
    this function is used to get subject of a normal billing
    :param bill:
    :return: first para is subject string, second is oc manager's name
    """

    lot = cash_receipt.get_lot_instance()

    oc = cash_receipt.get_oc()

    property = cash_receipt.get_property()
    sub = property.plan_num + '- Unit' + lot.unit_no + "  " + property.street + ' ' + property.suburb + ' ' + property.state + ' ' + property.post_code
    return sub, oc.manager_first_name + ' ' + oc.manager_last_name


def send_pdf_mail(id, subject, to):
    file_path = cash_receipt_pdf_to_file(id)
    sign = get_sign(1)
    body = template.BODY + '\n\n' + sign

    msg_service(subject, to, body, file_path)
