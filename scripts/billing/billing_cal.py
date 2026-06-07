from dateutil.relativedelta import relativedelta
from django.db.models import Sum

from finance.models import Billing
from property.models import OCMaster, OcBudget
from scripts.DB.DBClass import MySQLClass
from datetime import date, datetime
from scripts.utils.cal_utils import generate_id, allocate_levy
from scripts.GL.create_gl import JournalEntry, GLGenerator
from scripts.utils.date_utils import get_today
from scripts.utils.property_utils import get_property_gst_from_oc
from scripts.GL.client_ledger import create_client_ledger
from scripts.error.custom_error import MissingOCBudgetException
from scripts.utils.fin_utils import get_lot_balance


class BillingCal(object):
    def __init__(self, fin_year, client_id, oc_id, from_date, user, account="IS100001", display=True):
        self.fin_year = fin_year
        self.client_id = client_id
        self.oc_id = oc_id
        if type(from_date).__name__ == 'str':
            self.from_date = datetime.strptime(from_date, '%d/%m/%Y')
        else:
            self.from_date = from_date
        self.due_date = get_today() + relativedelta(days=+27)
        self.user = user
        # output of lot distribution amount
        self.lot_amt = {}
        self.account = account
        self.display = display
        self.cal_flag = True

    # since revenue being splitted into 2 accounts got another function to handle
    def build_total_frequency(self):

        if get_property_gst_from_oc(self.oc_id):
            gst_factor = 1.1
        else:
            gst_factor = 1

        self.frequency = OCMaster.objects.get(pk=self.oc_id).frequency
        total_levy = OcBudget.objects.filter(oc_ref_id=self.oc_id, fin_year=self.fin_year,
                                             acc_code__in=('IS100001', 'IS100002')).aggregate(total_levy=Sum('amount'))
        if type(total_levy ['total_levy']).__name__ == "Decimal" and float(total_levy ['total_levy']) != 0:
            self.total_levy = abs(float(total_levy ['total_levy'])) * gst_factor
        else:
            raise MissingOCBudgetException("OC ID" + str(self.oc_id) + "in financial year " + str(
                self.fin_year) + "cant't find")

    # this function will be used for billing generation with 2 account respectively
    def build_account_frequency(self):
        if get_property_gst_from_oc(self.oc_id):
            gst_factor = 1.1
        else:
            gst_factor = 1

        self.frequency = OCMaster.objects.get(pk=self.oc_id).frequency
        total_levy = OcBudget.objects.filter(oc_ref_id=self.oc_id, fin_year=self.fin_year,
                                             acc_code=self.account).aggregate(total_levy=Sum('amount'))
        if type(total_levy ['total_levy']).__name__ == "Decimal" and total_levy ['total_levy'] != 0:
            self.total_levy = abs(float(total_levy ['total_levy'])) * gst_factor
        elif self.account == "IS100001":
            self.cal_flag = False
            raise MissingOCBudgetException("OC ID" + str(self.oc_id) + "in financial year " + str(
                self.fin_year) + "cant't find, billing batch job abort")

        else:
            self.cal_flag = False
        # print (self.total_levy)

    def levy_cal(self):
        # billing date should be 28 days ahead of exact from date
        self.billing_date = self.from_date + relativedelta(days=-28)
        if self.frequency == 'Annual':
            month = 12
            self.to_date = self.from_date + relativedelta(months=+12)
        elif self.frequency == 'Half yearly':
            month = 6
            self.to_date = self.from_date + relativedelta(months=+6)
        elif self.frequency == 'Quarterly':
            month = 3
            self.to_date = self.from_date + relativedelta(months=+3)
        elif self.frequency == 'Mont' \
                               'hly':
            month = 1
            self.to_date = self.from_date + relativedelta(months=+1)
        self.to_date = self.to_date + relativedelta(days=-1)

        period_amount = round(self.total_levy / 12 * month, 2)
        liability_dict = {}

        sql_stat = "select lot_ref_id,liability from property_lotocmap where oc_ref_id=%s"
        sql_stat = sql_stat % self.oc_id
        result = MySQLClass().get_result(sql_stat)

        for item in result:
            liability_dict [int(item [0])] = float(item [1])

        # @0515 remove 原有轧差逻辑，放入直接分摊逻辑，保证相同liability 的levy 相同，但是总数可以有偏差
        self.lot_amt = allocate_levy(liability_dict, period_amount)
        self.annual_lot_amt = allocate_levy(liability_dict, self.total_levy)

    def get_annual_levy(self, lot_id):
        self.build_total_frequency()
        self.levy_cal()
        return self.annual_lot_amt [lot_id]

    def save_billing(self):
        title = ['billing_num', 'lot_ref_id', 'billing_amount', 'billing_from', 'billing_to', 'due_date',
                 'billing_date',
                 'status', 'collected_amount', 'oc_ref', 'client_ref_id', 'mail_status', 'special_flag', 'is_valid',
                 'is_show', 'desc']
        data = []
        for item in self.lot_amt:
            status = 'unpaid'
            balance = get_lot_balance(self.oc_id, item)
            collected_amount = 0
            billing_num = generate_id('BILLING')

            if balance > 0:
                collected_amount = min(balance, self.lot_amt [item])
                net_off_data = {'oc_id': self.oc_id,
                                'client_id': 1,
                                'amount': collected_amount,
                                'inc_exp': "BS300003",
                                'desc': "lot" + str(item) + "revenue " + self.from_date.strftime(
                                    '%d-%m-%Y') + 'prepay net off',
                                'user': self.user,
                                'posting_date': self.from_date
                                }
                je = GLGenerator(net_off_data)
                je.generate_je()

            if collected_amount == self.lot_amt [item]:
                status = 'paid'

            if self.account == "IS100001":
                levy_rev_desc = "Operating Levy fee"
            else:
                levy_rev_desc = "Maintenance Plan fee"
            # update on 20 Aug 2021, from SQL insert to django ORM
            bill = Billing()
            bill.createby = bill.updateby = self.user
            bill.client_ref_id = 1
            bill.collected_amount = collected_amount
            bill.oc_ref_id = self.oc_id
            bill.billing_num = billing_num
            bill.lot_ref_id = item
            bill.billing_amount = self.lot_amt [item]
            bill.billing_from = self.from_date
            bill.billing_to = self.to_date
            bill.due_date = self.due_date
            bill.billing_date = get_today()
            # bill.mail_status = 'prepared'
            bill.status = status
            bill.desc = levy_rev_desc + " from " + self.from_date.strftime(
                "%d %b %Y") + " to" + self.to_date.strftime("%d %b %Y")
            bill.is_show = self.display
            bill.save()

            desc = "lot" + str(item) + levy_rev_desc + self.from_date.strftime('%d-%m-%Y')
            context = {'oc_id': self.oc_id,
                       'client_id': 1,
                       'amount': self.lot_amt [item],
                       'inc_exp': self.account,
                       'desc': desc,
                       'user': self.user,
                       'posting_date': self.from_date
                       }
            create_client_ledger(self.oc_id, item, 0 - self.lot_amt [item], billing_num, self.user, date.today())
            je = GLGenerator(context)
            je.generate_je()

    def generate_bill(self):
        self.build_account_frequency()
        if self.cal_flag:
            self.levy_cal()
            self.save_billing()
