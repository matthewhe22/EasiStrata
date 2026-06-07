import logging

from finance.models import GL, IncomeExp, COA
import datetime
from scripts.utils.cal_utils import generate_id, distribute_value
from scripts.utils.date_utils import diff_month, get_defer_period_list, date_to_period
from scripts.utils.property_utils import get_property_gst_from_oc

PREPAY_ACCOUNT = 'BS300002'



class JournalEntry:

    def __init__(self, data):
        self.valid_input(data)
        self._build_request_data(data)

    def _build_request_data(self, data):
        self.oc_id = data ['oc_id']
        self.amount = float(data ['amount'])
        self.inc_exp = data ['inc_exp']
        self.user = data ['user']
        self.input_gst_amt = float(data.get('input_gst_amt', 0))
        self.client_id = data ['client_id']
        self.posting_date = data.get('posting_date', datetime.date.today())
        self.desc = data.get('desc', '')
        self.convert_period()
        self.reverse = data.get('reverse', False)
        self.defer_from = data.get('defer_from', False)
        self.defer_periods = data.get('defer_periods', False)
        self.property_gst_flag = get_property_gst_from_oc(data ['oc_id'])
        self.get_gst_account()
        self.get_account()
        self.convert_period()

    def valid_input(self, data):
        COMPULSORY = ['oc_id', 'amount', 'inc_exp', 'client_id']
        for item in COMPULSORY:
            if item not in data:
                raise Exception(f'compulsory {item} is missing for GL generation')

    def get_gst_account(self):
        input = COA.objects.get(is_gst_input=1)
        output = COA.objects.get(is_gst_output=1)
        self.input_gst_acc = input.acc_code
        self.output_gst_acc = output.acc_code

    # get debit and credit account from income expense config
    def get_account(self):

        if self.inc_exp:
            income_expense = IncomeExp.objects.get(income_expense_code=self.inc_exp)
            self.is_defer = income_expense.is_deferred
            self.expense = income_expense.debit_acc
            # if (income_expense.is_deferred):
            #     self.debit_acc = PREPAY_ACCOUNT
            # else:
            self.debit_acc = income_expense.debit_acc
            self.credit_acc = income_expense.credit_acc
            self.gst_flag = income_expense.is_gst_output

    def convert_period(self):
        self.period = date_to_period(self.posting_date)


class GLGenerator:
    def __init__(self, data):
        self.data = data
        self.request_data = JournalEntry(data)
        self._prepare_je()

    def support(self):
        pass

    def _prepare_je(self):
        self.debit = GL()
        self.credit = GL()
        self.gst = GL()
        # TODO put doc_num generate function to generate function to keep continous document number
        doc_num = generate_id('DOC')
        # if self.request_data.is_defer:
        #     self.debit.acc_code = self.request_data.expense
        #     self.credit.acc_code = PREPAY_ACCOUNT
        # else:
        self.debit.acc_code = self.request_data.debit_acc
        self.credit.acc_code = self.request_data.credit_acc

        if not self.request_data.reverse:
            self.debit.dc = 'dr'
            self.credit.dc = 'cr'
            self.gst.dc = 'cr'
        else:
            self.gst.dc = 'dr'
            self.debit.dc = 'cr'
            self.credit.dc = 'dr'

        for item in [self.debit, self.credit, self.gst]:
            item.doc_num = doc_num
            item.createby = self.request_data.user
            item.updateby = self.request_data.user
            item.posting_date = self.request_data.posting_date
            item.document_date = datetime.date.today()
            item.period = self.request_data.period
            if self.request_data.is_defer:
                item.description = self.request_data.desc + '_amortize'
            else:
                item.description = self.request_data.desc
            item.exp_type = self.request_data.inc_exp
            item.oc_ref_id = self.request_data.oc_id
            item.client_ref_id = self.request_data.client_id

    def generate_je(self):
        OutputGenerator(self.data).generate()
        InputGenerator(self.data).generate()
        DrCrGenerator(self.data).generate()
        AmortizeGenerator(self.data).generate()

        """
        1. property gst==True and gst_account=True
        2. property gst==True and input_gst <>0
        3. property gst==False and input_gst<>0
        4. Property gst==False
        :return:
        """


# property gst is true and confirm output gst
class OutputGenerator(GLGenerator):
    def support(self):
        return not self.request_data.is_defer and self.request_data.gst_flag and self.request_data.input_gst_amt == 0 and self.request_data.property_gst_flag

    def generate(self):
        if self.support():
            self.debit.amount = self.request_data.amount
            self.credit.amount = round(self.request_data.amount / 1.1, 2)
            self.gst.amount = self.request_data.amount - self.credit.amount
            self.gst.acc_code = self.request_data.output_gst_acc
            self.debit.save()
            self.credit.save()
            self.gst.save()


class InputGenerator(GLGenerator):
    def support(self):
        return not self.request_data.gst_flag and self.request_data.input_gst_amt > 0 and self.request_data.property_gst_flag

    def generate(self):
        # for input gst amount in request_data is GST exclusive
        if self.support():
            if self.request_data.is_defer:
                self.debit.acc_code = PREPAY_ACCOUNT

            self.credit.amount = self.request_data.amount + self.request_data.input_gst_amt
            self.debit.amount = self.request_data.amount
            # reverse the debit/credit of input gst as the init is only applicable for output gst
            if self.gst.dc == 'dr':
                self.gst.dc = 'cr'
            else:
                self.gst.dc = 'dr'

            self.gst.amount = self.request_data.input_gst_amt
            self.gst.acc_code = self.request_data.input_gst_acc
            self.debit.save()
            self.credit.save()
            self.gst.save()


class DrCrGenerator(GLGenerator):
    def support(self):
        # add support function to support is_defer for insurance premiums but need to replace dr account as prepaid account
        if not self.request_data.property_gst_flag:
            return True
        elif self.request_data.property_gst_flag and not self.request_data.gst_flag and self.request_data.input_gst_amt == 0:
            return True
        else:
            return False

    def generate(self):
        if self.support():
            if self.request_data.is_defer:
                self.debit.acc_code = PREPAY_ACCOUNT

            self.debit.amount = self.request_data.amount + self.request_data.input_gst_amt
            self.credit.amount = self.debit.amount
            self.debit.save()
            self.credit.save()


class AmortizeGenerator(GLGenerator):
    """
    1. this is for insurance premiums only
    2. strategy is that both DrCr and Amortize will be used
    3. step1- for DrCr Dr: Prepaid Expenses  Cr: Account Payable
    4. step2- for everymonth amortization Dr: Insurance Premiums Cr: Prepaid Expenses


    1. get the date list and value list accordingly
    2. generate je and save
    :return:
    """

    def support(self):
        return self.request_data.is_defer and self.request_data.defer_periods and self.request_data.defer_from

    def generate(self):
        if self.support():
            # total_month = diff_month(self.request_data.defer_to, self.request_data.defer_from)
            total_month = self.request_data.defer_periods
            posting_date_list = get_defer_period_list(self.request_data.defer_from, total_month)
            value_list = distribute_value(self.request_data.amount, total_month)

            for index, entry in enumerate(posting_date_list):
                # need to build new debit and credit instance
                debit = GL()
                credit = GL()

                debit.client_ref_id = credit.client_ref_id = self.debit.client_ref_id
                debit.exp_type = credit.exp_type = self.debit.exp_type
                debit.createby = credit.createby = self.debit.createby
                debit.updateby = credit.updateby = self.debit.updateby
                debit.description = credit.description = self.debit.description
                debit.posting_date = credit.posting_date = posting_date_list [index]
                debit.document_date = credit.document_date = datetime.date.today()
                debit.period = credit.period = date_to_period(debit.posting_date)
                debit.amount = credit.amount = value_list [index]
                debit.doc_num = credit.doc_num = generate_id('DOC')
                debit.oc_ref_id = credit.oc_ref_id = self.debit.oc_ref_id
                # specific property
                debit.acc_code = self.debit.acc_code
                debit.dc = self.debit.dc
                credit.acc_code = PREPAY_ACCOUNT
                credit.dc = self.credit.dc

                try:
                    debit.save()
                    credit.save()
                except Exception as e:
                    logging.exception(e)
