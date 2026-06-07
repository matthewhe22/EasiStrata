import logging

from django.db.models import Sum, Q

from property.models import OCMaster, Lot, Property
from base.models import Client
import calendar
import datetime
from finance.models import Occertificate, COA, GL
from strata.models import Insurance
from django.shortcuts import get_object_or_404
from scripts.DB.DBClass import MySQLClass
from .billing_cal import BillingCal
from scripts.utils.fin_utils import get_paid_to_date
from scripts.utils.date_utils import day_offset

FREQ_CONVERT = {'Annual': (12, 1),
                'Half yearly': (6, 2),
                'Quarterly': (3, 4),
                'Monthly': (1, 12)
                }


# refactor on Apr 16th by returning dict of different object
class Certificate(object):

    def __init__(self, pk):
        self.certificate_id = pk
        self.cert = get_object_or_404(Occertificate, pk=self.certificate_id)
        self.oc_id = self.cert.oc_ref_id
        self.lot_id = self.cert.lot_ref_id
        self.client_id = self.cert.client_ref_id
        self.before_oc_flag = False

    def set_instance(self):
        self.lot = Lot.objects.get(pk=self.lot_id)
        self.oc = OCMaster.objects.get(pk=self.oc_id)
        self.property_id = self.oc.property_ref_id
        self.client = Client.objects.get(pk=self.client_id)
        self.property = Property.objects.get(pk=self.property_id)
        self._check_before_oc()
        # add new flag on whether oc certificate is used before oc start

    def _check_before_oc(self):
        if self.cert.issue_date < self.oc.billing_start_date:
            self.before_oc_flag = True

    def get_insurance(self):
        if self.before_oc_flag:
            issue_date = self.oc.billing_start_date
        else:
            issue_date = self.cert.issue_date
        if Insurance.objects.filter(property_ref_id=self.property_id, date_from__lte=issue_date,
                                    date_to__gte=issue_date).count() != 1:
            raise Exception('Insurance config error for the property {self.property.title}')
        else:
            self.insurance = Insurance.objects.get(property_ref_id=self.property_id, date_from__lte=issue_date,
                                                   date_to__gte=issue_date)

    def convert_fyear(self):
        # convert the financial year based on the logic and financial year will be used to get correct budget
        start_date = self.oc.billing_start_date
        issue_date = self.cert.issue_date
        if start_date.month == 1 and start_date.day == 1:
            fyear = issue_date.year
        elif (start_date.month == issue_date.month and issue_date.month < start_date.month) or (
                issue_date.month < start_date.month):
            fyear = issue_date.year
        else:
            fyear = issue_date.year + 1
        return fyear

    def get_billing_period(self):
        """
        generate start billing month and subsequent billing months for oc in a whole billing period
        """
        start_date = self.oc.billing_start_date
        start_day = self.oc.billing_start_date.day
        datee = datetime.datetime.strptime(str(start_date), "%Y-%m-%d")
        start_billing_month = calendar.month_name [datee.month]
        billing_month = self.generate_month(datee.month, self.oc.frequency)
        # take the previous day of cert issuance date as the end date of fs
        finance_date = day_offset(self.cert.issue_date, -1)

        return {'start_date': start_date,
                'start_day': start_day,
                'start_billing_month': start_billing_month,
                'billing_month': billing_month,
                'finance_date': finance_date

                }

    def generate_month(self, billing_month, frequency):

        output = []
        interval = FREQ_CONVERT [frequency] [0]
        total = FREQ_CONVERT [frequency] [1] - 1
        if frequency == 'Annual':
            return " "
        else:
            for x in range(0, total):
                billing_month = billing_month + interval
                if billing_month <= 12:
                    output.append(calendar.month_name [billing_month])
                else:
                    output.append(calendar.month_name [billing_month - 12])
            month_str = 'then '
            for item in output:
                month_str = month_str + item + ", "
            month_str = month_str [:-2]
        return month_str

    def get_billing_info(self, fyear):
        start_date = self.oc.billing_start_date
        sql_stat = 'select ifnull(sum(billing_amount-collected_amount),0) from finance_billing where ' \
                   'lot_ref_id=%s and oc_ref=%s and status="unpaid"'
        sql_stat = sql_stat % (self.lot_id, self.oc_id)
        result = MySQLClass().get_result(sql_stat) [0]
        unpaid = float(result [0])

        paid_until = get_paid_to_date(self.oc_id, self.lot_id)

        if paid_until is None or self.before_oc_flag:
            paid_until = self.oc.oc_before_start_day()

        levy_cal = BillingCal(fyear, self.client_id, self.oc_id, start_date, ' ')
        levy = levy_cal.get_annual_levy(self.lot_id)

        return {'unpaid': unpaid,
                'paid_until': paid_until,
                'levy': levy}

    def cal_equity(self):
        # 1 is a mock data which is compulsory for class Financial Statement
        if self.before_oc_flag:
            return {'equity': 'nil'}

        try:
            cash_code = COA.objects.get(acc_name='Cash in Bank').acc_code
            # code_list = []
            # code_result = COA.objects.filter(
            #     Q(acc_code__istartswith='BS3') | Q(acc_code__istartswith='BS4')).values_list('acc_code')
            # Nov 17 change cash code to all balance sheet account codes 1 June change back to previous logic
            # for item in code_result:
            #     code_list.append(item [0])

            beg_bal = OCMaster.objects.get(id=self.oc_id).beg_bal
            amt_dr = GL.objects.filter(acc_code=cash_code, oc_ref_id=self.oc_id, dc='dr',
                                       posting_date__lte=self.cert.issue_date).aggregate(Sum('amount'))
            amt_cr = GL.objects.filter(acc_code=cash_code, oc_ref_id=self.oc_id, dc='cr',
                                       posting_date__lte=self.cert.issue_date).aggregate(Sum('amount'))
            amt = float(amt_dr ['amount__sum'] or 0.00) - float(amt_cr ['amount__sum'] or 0.00) + float(beg_bal or 0.00)
        except Exception as e:
            logging.exception(e)
            amt = 0
        finally:
            return {'equity': amt}

    def generate_feed_data(self):
        billing = {}
        try:
            self.set_instance()
            self.get_insurance()
            billing_period = self.get_billing_period()

            if self.before_oc_flag:
                fyear = self.oc.billing_start_date.year + 1
            else:
                fyear = self.convert_fyear()
            billing_info = self.get_billing_info(fyear)

            equity = self.cal_equity()
            billing = {**billing_period, **billing_info, **equity}

        except Exception as e:
            logging.exception(e)
        finally:
            data = {'cert': self.cert,
                    'oc': self.oc,
                    'property': self.property,
                    'client': self.client,
                    'lot': self.lot,
                    'billing': billing,
                    'insurance': self.insurance,
                    'before_oc_flag': self.before_oc_flag}
            return data
