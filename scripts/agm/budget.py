from property.models import OcBudget, OCMaster
from django.db.models import Q
from scripts.utils.cal_utils import allocate_levy, build_liability_dict, transform_lotid_to_lot
from scripts.utils.fin_utils import get_account_category


class AgmOCBudget():
    def __init__(self, oc_id, fyear):

        self.oc_id = oc_id
        self.fyear = int(fyear)
        self._output_context = {}
        #        self._output_contex is a nested dictionary
        self.total_amt = 0

    def _generate_fin_year(self):
        self._output_context ['fyear'] = str(self.fyear) + '-' + str(self.fyear + 1)

    def _get_oc_expense(self):
        # update logic to exclude IS100001 and IS100002 , due to change of main revenue source
        exp_item_list = OcBudget.objects.filter(Q(oc_ref_id=self.oc_id), Q(fin_year=(self.fyear + 1)),
                                                (~Q(acc_code="IS100001")), (~Q(acc_code="IS100002")))
        exp_item_dict = {}
        for item in exp_item_list:
            if get_account_category(item) not in exp_item_dict:
                exp_item_dict [get_account_category(item)] = {item.acc_name: item.amount}
            else:
                exp_item_dict [get_account_category(item)] [item.acc_name] = item.amount

            self.total_amt = self.total_amt + item.amount

        self._output_context ['exp_items'] = exp_item_dict
        self._output_context ['budget_total'] = self.total_amt

    def _get_property(self):
        oc = OCMaster.objects.get(pk=self.oc_id)
        property = oc.property_ref

        self._output_context ['oc'] = oc
        self._output_context ['property'] = property

    def _generate_lot_budget(self):
        total_liability = 0

        lot_liability_dict = build_liability_dict(self.oc_id)
        lot_liability_dict = transform_lotid_to_lot(lot_liability_dict)
        lot_budget_dict = {}
        if lot_liability_dict:
            lot_budget_dict = allocate_levy(lot_liability_dict, self.total_amt)

        for item in lot_budget_dict:
            lot_budget_dict [item] = LiabilityItem(lot_liability_dict [item], lot_budget_dict [item])
            total_liability = total_liability + lot_liability_dict [item]
        # # convert lot id in lot_budget_dict to lot name
        # output_lot_dict={}
        # for item in lot_budget_dict:
        #     output_lot_dict[Lot.objects.get(id=item).lot]=lot_budget_dict[item]

        self._output_context ['budget_items'] = lot_budget_dict
        self._output_context ['total_liability'] = total_liability

    def get_context(self):
        self._generate_fin_year()
        self._get_oc_expense()
        self._get_property()
        self._generate_lot_budget()
        return self._output_context


class LiabilityItem():
    # to show income table in the table with liabilities and fees for each lot
    def __init__(self, liability, fee):
        self.liability = liability
        self.fee = float(fee)
