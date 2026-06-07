import logging
import random

from apscheduler.schedulers.background import BackgroundScheduler
from django.db.models import Q
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJob

from property.models import OCMaster
from scripts.billing.billing_cal import BillingCal
from scripts.notification.Notify import Notify
from scripts.utils.cal_utils import generate_id
from scripts.utils.date_utils import day_offset, get_today, get_fin_year, pick_billing_from
from .billing_mail_job import billing_batch_service
from .cash_mail_job import cash_batch_service
from .owner_mail_job import notification_batch_service, owner_request_batch_service
from ..GL.create_gl import GLGenerator
from ..utils.user_utils import init_lot_user

FREQ_CONVERT = {'Annual': '12',
                'Half yearly': '6',
                'Quarterly': '3',
                'Monthly': '1'
                }


def init_schedule():
    try:
        global sched
        sched = BackgroundScheduler()
        sched.add_jobstore(DjangoJobStore(), "default")

        sched.print_jobs('default')
        sched.start()
        # one time job
        sched.add_job(billing_batch_service, 'cron', minute="1,11,21,31,41,51", second="0",
                      id="billing_batch_service",
                      )
        sched.add_job(cash_batch_service, 'cron', minute="5,15,25,35,45,55", second="0",
                      id="cash_batch_service",
                      )
        sched.add_job(notification_batch_service, 'cron', minute="8,18,28,38,48,58", second="0",
                      id="notification_batch_service",
                      )
        sched.add_job(owner_request_batch_service, 'cron', minute="3,13,23,33,43,53", second="0",
                      id="owner_request_batch_service",
                      )
        sched.add_job(bank_fee_job, 'cron', day="1", hour="11", minute="0", second="0",
                      id="bank_fee_service",
                      )
        sched.add_job(init_lot_user, 'cron', hour="2", minute="30", second="0",
                      id="init_lot_user_service",
                      )

    except Exception as e:
        logging.exception(e)


# init_lot_user


def new_oc_billing_schedule(oc_id):
    start_min = random.randint(0, 59)

    context = {}
    context ['oc_id'] = oc_id
    oc = OCMaster.objects.get(pk=int(oc_id))
    # bill_send_date is the date when scheduling job will generate billing , usually 28 days ahead of billing from
    bill_send_date = day_offset(oc.billing_start_date, -28)
    if bill_send_date.day <= 28:
        job_start_day = str(bill_send_date.day)
    else:
        job_start_day = 28
    frequency = FREQ_CONVERT [oc.frequency]
    job_id = oc.title + '_' + generate_id('JOB')
    try:

        if frequency != "12":
            job_start_month = get_month_interval(bill_send_date.month, int(frequency))

        else:
            job_start_month = bill_send_date.month

        sched.add_job(oc_job, 'cron', kwargs=context, day=job_start_day, month=job_start_month,
                      hour="21", minute=start_min,
                      id=job_id,
                      start_date=bill_send_date)
    except Exception as e:
        logging.exception(e)


def oc_job(**kwargs):
    """
    used for every oc run scheduling job
    :param kwargs:
    {oc_id:{oc_id}}
    :return:
    """
    from_date = day_offset(get_today(), 28)
    user = 'scheduling_job'
    oc_id = int(kwargs ['oc_id'])
    from_date = pick_billing_from(oc_id, from_date)
    fin_year = get_fin_year(oc_id, from_date)
    # calibration of from_date since the 28 days add back will have difference
    property_id = OCMaster.objects.get(pk=oc_id).property_ref_id
    # build data for manager group notification
    log_msg = "OC with id" + str(oc_id) + "with from date" + str(from_date) + " and financial year" + str(fin_year)
    logging.info(log_msg)

    data = {'note_type': 'billing_manager',
            'oc_id': oc_id,
            'property_id': property_id,
            'user': user,
            'client_id': 1,
            'date_from': str(from_date)
            }

    try:
        bill = BillingCal(fin_year, 1, oc_id, from_date, user, 'IS100002', False)
        bill.generate_bill()
        bill = BillingCal(fin_year, 1, oc_id, from_date, user, 'IS100001', True)
        bill.generate_bill()
        # sending message to internal users
        note = Notify()
        note.init_strategy()
        note.notify(data)


    except Exception as e:
        logging.exception(e)


def bank_fee_job():
    """
    step1, get valid oc list, bank fee !=0 and date is greater than start date
    step2, iterate the list to get the bank fee , post journal entry accordingly
    :return:
    there is no return
    """
    today = get_today()
    oc_list = OCMaster.objects.filter(Q(start_date__lte=today) | Q(bank_fee__gt=0)).values('id')
    for item in oc_list:

        oc = OCMaster.objects.get(id=item ['id'])
        desc = oc.title + str(today.year) + '-' + str(today.month) + '  bank fee'
        try:
            data = {'oc_id': item ['id'],
                    'client_id': 1,
                    'amount': oc.bank_fee,
                    'inc_exp': 'IS200460',
                    'desc': desc,
                    'user': 'scheduling_job',
                    }

            je = GLGenerator(data)
            je.generate_je()

            data = {'oc_id': item ['id'],
                    'client_id': 1,
                    'amount': oc.bank_fee,
                    'inc_exp': 'BS400002',
                    'desc': desc + 'payment',
                    'user': 'scheduling_job',
                    }

            je = GLGenerator(data)
            je.generate_je()

            # BS400002



        except Exception as e:
            logging.exception(e)


def job_remove(job_id):
    sched.remove_job(job_id)


def oc_job_remove(oc_id):
    try:
        oc_title = OCMaster.objects.get(pk=oc_id).title
        job = DjangoJob.objects.get(name__contains=oc_title)
        if job:
            job.delete()

    except Exception as e:
        logging.exception(e)


def get_month_interval(start_month, frequency):
    month_array = []
    interval_str = ""
    month_array.append(start_month)
    cycle = 12 / frequency
    while cycle > 1:
        start_month = start_month + frequency
        if start_month <= 12:
            month_array.append(start_month)
        else:
            month_array.append(start_month - 12)
        cycle -= 1

    if len(month_array) > 0:
        for month in month_array:
            interval_str = interval_str + str(month) + ","

    return interval_str [:-1]
