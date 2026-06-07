import logging
from concurrent.futures import ThreadPoolExecutor

from django.db.models import Q

from base.models import Client
from finance.models import Billing
from property.models import Lot, OCMaster, Property as Pro
from scripts.PDF_service.pdf import billing_pdf_file
from scripts.mail.send_mail import msg_service
from . import mail_template as template
from time import sleep


def billing_batch_service():
    """
    filter mail status of prepared or fail
    change status to sending
    generate pdf
    send mail
    :return: none
    """
    bill = Billing.objects.filter(Q(is_valid=True, is_show=True), Q(mail_status='prepared') | Q(mail_status='fail'))
    for item in bill:
        try:
            if Billing.objects.get(pk=item.pk).mail_status in ('prepared', 'fail'):
                update_sending(item)
                info = get_subject(item)

                subject = info [0] + template.TITLE
                lot_id = item.lot_ref_id
                lot = Lot.objects.get(pk=lot_id)

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
                    item.attachment = item.billing_num + ".pdf"

                item.mail_status = 'sent'
                item.save()
                # sleep(40)


        except Exception as e:
            logging.exception(e)
            item.mail_status = 'fail'
            item.save()


def update_sending(bill):
    # bill = Billing.objects.get(pk=id)
    bill.mail_status = 'sending'
    bill.save()


def send_pdf_mail(id, subject, to):
    file_path = billing_pdf_file(id)
    sign = get_sign(1)
    body = template.BODY + '\n\n' + sign

    msg_service(subject, to, body, file_path)


def get_subject(bill):
    """
    this function is used to get subject of a normal billing
    :param bill:
    :return: first para is subject string, second is oc manager's name
    """
    oc_id = bill.oc_ref_id
    lot_id = bill.lot_ref_id
    lot = Lot.objects.get(pk=lot_id)

    oc = OCMaster.objects.get(pk=oc_id)

    property_id = oc.property_ref_id
    property = Pro.objects.get(pk=property_id)
    sub = property.plan_num + '- Unit' + lot.unit_no + "  " + property.street + ' ' + property.suburb + ' ' + property.state + ' ' + property.post_code + '-' + oc.description
    return sub, oc.manager_first_name + ' ' + oc.manager_last_name


def get_sign(client_id):
    client = Client.objects.get(pk=client_id)
    sign = '\n' + client.client_name + '\n' + 'M:' + client.telephone + '\n' + "Email:" + client.email + '\n' + "A:" + client.Address + '\n' + "P:" + client.post_adr

    return sign
