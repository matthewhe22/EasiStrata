from django.db.models import Sum
from django.shortcuts import get_object_or_404

from base.models import Client
from finance.models import FS, COA, GL
from property.models import Property, OCMaster, OcBudget
from scripts.DB.DBClass import MySQLClass
from scripts.utils.date_utils import date_to_str_db
from scripts.utils.str_utils import if_str_null


class FinStat(object):
    def __init__(self, id):
        self.fs_id = id
        self.oc_info = {}
        self.property_info = {}
        self.client_info = {}

    def get_fs_info(self):
        fs = get_object_or_404(FS, pk=self.fs_id)
        self.property_id = fs.property_ref_id
        self.oc_id = fs.oc_ref_id
        self.client_id = fs.client_ref_id
        self.fin_year = fs.fin_year
        self.to_date = fs.to_date
        if fs.from_date:
            self.start_date = fs.from_date
        else:
            oc = get_object_or_404(OCMaster, pk=self.oc_id)
            start_date = oc.billing_start_date
            if start_date.month < self.to_date.month or (
                    start_date.month == self.to_date.month and start_date.day < self.to_date.day):
                start_date = start_date.replace(self.to_date.year)
            else:
                start_date = start_date.replace(self.to_date.year - 1)
            self.start_date = start_date
        self.oc_info ['start_date'] = self.start_date

    def get_oc_info(self):
        oc = get_object_or_404(OCMaster, pk=self.oc_id)
        self.oc_info ['oc_name'] = oc.title
        self.oc_info ['to_date'] = self.to_date
        self.oc_info ['fin_year'] = self.fin_year
        self.oc_info ['oc_beg_bal'] = round(float(oc.beg_bal), 2)
        self.oc_info ['open_bal'] = round(float(oc.beg_bal) + self.get_open_bal(), 2)

    def get_open_bal(self):
        """
        get the opening balance
        """
        sql_stat = "select sum(if(dc='dr',amount,0-amount)) " \
                   "from finance_gl gl left join finance_coa coa on gl.acc_code=coa.acc_code " \
                   "where oc_ref=%s and posting_date<'%s' and coa.account_level2 in ('Assets','Liability')"
        start_date = date_to_str_db(self.start_date)
        sql_stat = sql_stat % (self.oc_id, start_date)
        result = MySQLClass().get_result(sql_stat) [0]
        if result is None or result [0] is None:
            return 0
        else:
            movement = round(float(result [0]), 2)
            return movement

    def get_property_info(self):
        prop = get_object_or_404(Property, pk=self.property_id)
        self.property_info ['plan_num'] = prop.plan_num
        self.property_info [
            'property_address'] = if_str_null(prop.street, '') + '  ' + if_str_null(prop.suburb) + ' ' + if_str_null(
            prop.state) + ' ' + if_str_null(prop.post_code)

    def get_client_info(self):
        client = get_object_or_404(Client, pk=self.client_id)
        self.client_info ['client_name'] = client.client_name

    def get_budget(self):
        budget = {}
        # update 26 Nov 2021 to exclude the IS100001 and IS100002
        sql_stat = "select acc_code,sum(amount) from property_ocbudget where oc_ref_id=%s and fin_year=%s and acc_code<>'IS100001' and acc_code<>'IS100002' group by acc_code"
        sql_stat = sql_stat % (self.oc_id, self.fin_year)
        result = MySQLClass().get_result(sql_stat)
        if len(result) == 0:
            raise Exception('No budget has been set')
        else:
            for item in result:
                budget [item [0]] = float(item [1])
            return budget

    def get_fs_data(self, budget):
        start_date = date_to_str_db(self.start_date)
        end_date = date_to_str_db(self.to_date)
        # update by Apr 29 by adding up 2 parts , part1 is the all accounts in the period and part 2 is the BS account before the from date
        sql_stat = "select coa.account_level2,coa.category,coa.acc_name,coa.acc_code,sum(if(gl.dc='dr',gl.amount,0-gl.amount)) " \
                   "from finance_gl gl left join finance_coa coa on gl.acc_code=coa.acc_code " \
                   "where gl.oc_ref=%s and " \
                   "coa.account_level2 in ('Assets','Liability') and gl.posting_date<='%s' group by coa.account_level2, coa.category, coa.acc_name"
        sql_stat = sql_stat % (self.oc_id, end_date)
        result_bs = MySQLClass().get_result(sql_stat)

        sql_stat = "select coa.account_level2,coa.category,coa.acc_name,coa.acc_code,sum(if(gl.dc='dr',gl.amount,0-gl.amount)) " \
                   "from finance_gl gl left join finance_coa coa on gl.acc_code=coa.acc_code " \
                   "where gl.oc_ref=%s and " \
                   "gl.posting_date>='%s' and gl.posting_date<='%s' and coa.account_level2 not in ('Assets','Liability') and coa.account_level1 <>'Maintenance Plan'" \
                   "group by coa.account_level2, coa.category, coa.acc_name"
        sql_stat = sql_stat % (self.oc_id, start_date, end_date)
        result_period = MySQLClass().get_result(sql_stat)
        result = result_bs + result_period
        fs_data = {}
        fs_data ['Assets'] = {}
        fs_data ['Liability'] = {}
        fs_data ['Equity'] = {}
        fs_data ['Income'] = {}
        fs_data ['Expenditure'] = {}
        fs_data ['surplus_actual'] = 0
        fs_data ['surplus_budget'] = 0
        fs_sum_actual = {'Assets': 0,
                         'Liability': 0,
                         'Equity': 0,
                         'Income': 0,
                         'Expenditure': 0
                         }
        fs_sum_budget = {'Assets': 0,
                         'Liability': 0,
                         'Equity': 0,
                         'Income': 0,
                         'Expenditure': 0
                         }

        if len(result) == 0:
            raise Exception('No gl data selected')
        else:
            for gl_item in result:
                fs_item = gl_item [0]
                category = gl_item [1]
                acc_name = gl_item [2]
                acc_code = gl_item [3]
                amount = float(gl_item [4])
                fs_sum_actual [fs_item] = fs_sum_actual [fs_item] + amount
                if acc_code in budget:
                    budget_amt = round(budget [acc_code], 2) * (-1)
                    budget.pop(acc_code)
                else:
                    budget_amt = 0.00
                fs_sum_budget [fs_item] = fs_sum_budget [fs_item] + budget_amt
                if category in fs_data [fs_item]:
                    fs_data [fs_item] [category].append(FsData(acc_name, amount, budget_amt))
                else:
                    fs_data [fs_item] [category] = []
                    fs_data [fs_item] [category].append(FsData(acc_name, amount, budget_amt))
                fs_data ['surplus_actual'] = round(fs_sum_actual ['Income'] + fs_sum_actual ['Expenditure'], 2) * (-1)
                fs_data ['surplus_budget'] = round(fs_sum_budget ['Income'] + fs_sum_budget ['Expenditure'], 2)
            fs_data ['end_bal'] = round(self.oc_info ['open_bal'] + fs_data ['surplus_actual'], 2)

            equity = FsData('Administrative Fund Reserve', fs_data ['end_bal'], 0)
            # clear the data for pervious sum of equity accounts
            fs_data ['Equity'] = {}
            fs_data ['Equity'] = {'Administrative Fund': [equity, ]}

            for item in fs_data ['Assets'] ['Current Assets']:
                if item.acc_name == 'Cash in Bank':
                    item.actual_amt = item.actual_amt + self.oc_info ['oc_beg_bal']

            fs_sum_actual ['Assets'] = fs_sum_actual ['Assets'] + self.oc_info ['oc_beg_bal']

        return fs_data, fs_sum_actual, fs_sum_budget, budget

    def add_outstanding_budget(self, budget, fs_sum_budget, fs_data):
        if len(budget) > 0:
            for item in budget:
                acc_property = self.get_account_property(item)
                fs_item = acc_property [0]
                category = acc_property [1]
                acc_name = acc_property [2]
                acc_code = acc_property [3]
                budget_amt = round(float(budget [item]), 2) * (-1)
                amount = 0.00
                if category in fs_data [fs_item]:
                    fs_data [fs_item] [category].append(FsData(acc_name, amount, budget_amt))
                else:
                    fs_data [fs_item] [category] = []
                    fs_data [fs_item] [category].append(FsData(acc_name, amount, budget_amt))
                fs_sum_budget [fs_item] = fs_sum_budget [fs_item] + budget_amt
                fs_data ['surplus_budget'] = round(fs_sum_budget ['Income'] + fs_sum_budget ['Expenditure'], 2)
        return fs_sum_budget, fs_data

    def get_account_property(self, account):
        coa = COA.objects.get(acc_code=account)
        fs_item = coa.account_level2
        category = coa.category
        acc_name = coa.acc_name
        acc_code = account
        return [fs_item, category, acc_name, acc_code]

    def generate_fs(self):
        self.get_fs_info()
        self.get_oc_info()
        self.get_property_info()
        self.get_client_info()
        budget = self.get_budget()
        fs = self.get_fs_data(budget)
        fs_budget = self.add_outstanding_budget(fs [3], fs [2], fs [0])
        # feed data for maintain
        maintain_data = FSManagement(self.oc_id, self.start_date, self.to_date, self.fin_year).get_account_list()
        data = {**self.oc_info, **self.property_info, **self.client_info, **maintain_data}

        result = {'fs_data': fs_budget [1],
                  'data': data,
                  'fs_sum_actual': fs [1],
                  'fs_sum_budget': fs_budget [0],

                  }
        return result


class FSManagement():
    """
    procedures for getting budget
    1. get income and exp accounts list from COA
    2. aggregate accounts through GL- actual number
    3. iterate list from step 1, to get actual number and budget numbers
    """

    def __init__(self, oc_id, from_date, to_date, fin_year):
        self.oc_id = oc_id
        self.from_date = from_date
        self.to_date = to_date
        self.fin_year = fin_year
        self._income_accounts = []
        self._exp_accounts = []

    def get_account_list(self):
        # accounts = COA.objects.filter(account_level1='Maintenance Plan').values('acc_code', 'acc_name')
        accounts = COA.objects.filter(account_level1='Maintenance Plan')
        total_income_budget = 0
        total_income_actual = 0
        total_exp_budget = 0
        total_exp_actual = 0

        for item in accounts:

            # get budget amt
            budget_amt = 0
            actual_amt = 0
            budget = OcBudget.objects.filter(fin_year=self.fin_year, oc_ref_id=self.oc_id,
                                             acc_code=item.acc_code).first()
            if budget_amt is not None:
                budget_amt = float(budget.amount)

            actual = GL.objects.filter(posting_date__gte=self.from_date, posting_date__lte=self.to_date,
                                       oc_ref_id=self.oc_id, acc_code=item.acc_code).values('dc').annotate(
                total_amt=Sum('amount'))

            for actual_item in actual:
                if actual_item ['dc'] == 'cr':
                    actual_amt = actual_amt + float(actual_item ['total_amt'])
                if actual_item ['dc'] == 'dr':
                    actual_amt = actual_amt - float(actual_item ['total_amt'])

            if item.account_level2.strip().lower() == 'income':
                self._income_accounts.append(FsData(item.acc_name, actual_amt, budget_amt))
                total_income_budget = total_income_budget + budget_amt
                total_income_actual = total_income_actual + actual_amt

            if item.account_level2.strip().lower() == 'expenditure':
                self._exp_accounts.append(FsData(item.acc_name, actual_amt, budget_amt))
                total_exp_actual = total_exp_actual + actual_amt
                total_exp_budget = total_exp_budget + budget_amt

        return {
            'total_income_budget': total_income_budget,
            'total_income_actual': total_income_actual,
            'total_exp_budget': total_exp_budget,
            'total_exp_actual': total_exp_actual,
            'maintain_income_items': self._income_accounts,
            'maintain_exp_items': self._exp_accounts,
            'maintain_budget_surplus': total_income_budget + total_exp_budget,
            'maintain_actual_surplus': total_income_actual + total_exp_actual,
        }


class FsData:
    def __init__(self, acc_name, actual_amt, budget_amt):
        self.acc_name = acc_name
        self.actual_amt = actual_amt
        self.budget_amt = budget_amt
