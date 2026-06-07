import logging
from base.models import Notification
from django.db.models import Q
from concurrent.futures import ThreadPoolExecutor
from scripts.utils.str_utils import check_valid_email
from scripts.mail.send_mail import msg_service

from strata.models import OwnerRequest

executor = ThreadPoolExecutor(max_workers=50)


def notification_batch_service():
    """
    filter mail status of prepared or fail
    change status to sending
    generate pdf
    send mail
    :return: none


    logic change on 20 Aug 2020, notification service changed and then mail sending servcie should only filter
    category with email and  also send email in username

    """
    note = Notification.objects.filter(Q(mail_status='prepared') | Q(mail_status='fail'), category__contains='email')
    for item in note:
        try:
            # executor.submit(update_sending, (item.pk))
            if Notification.objects.get(pk=item.pk).mail_status in ('prepared', 'fail'):
                item.mail_status = 'sending'
                item.save()
                subject = item.msg_subject
                if bool(item.attachment):
                    file_path = item.attachment.path
                else:
                    file_path = None

                if check_valid_email(item.user_name):
                    msg_service(subject, item.user_name, item.msg_body, file_path, cc=item.cc)

                item.mail_status = 'sent'
                item.save()
                # sleep(40)
        except Exception as e:
            logging.exception(e)
            item.mail_status = 'fail'
            item.save()


def owner_request_batch_service():
    """
    filter mail status of prepared or fail
    change status to sending
    generate pdf
    send mail
    :return: none


    logic change on 20 Aug 2020, notification service changed and then mail sending servcie should only filter
    category with email and  also send email in username

    """
    note = OwnerRequest.objects.filter(mail_status='prepared')
    for item in note:
        try:
            # executor.submit(update_sending, (item.pk))
            if OwnerRequest.objects.get(pk=item.pk).mail_status in ('prepared', 'fail'):
                item.mail_status = 'sending'
                item.save()

                if bool(item.attachment):
                    file_path = item.attachment.path
                else:
                    file_path = None

                if check_valid_email(item.lot_ref.email1):
                    # print(item.lot_ref.email1)
                    msg_service(item.msg_subject, 'info@topocs.com.au', item.msg_body, file_path,
                                reply_to=item.lot_ref.email1)

                item.mail_status = 'sent'
                item.save()
                # sleep(40)
        except Exception as e:
            logging.exception(e)
            item.mail_status = 'fail'
            item.save()
