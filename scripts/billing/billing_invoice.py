import decimal
import logging

from base.models import Client
from finance.models import Billing
from property.models import Property, Lot, OCMaster, LotOCMap
from scripts.utils.fin_utils import get_invoice_lot_balance, get_lot_balance, get_latest_lot_balance, \
    generate_billing_info


# Apr 15 , ORM refactor, also put date as filter unpaid amount etc.
class BillingInv(object):
    def __init__(self, pk, hist_flag=True):
        self.hist_flag = hist_flag
        self.bill = Billing.objects.get(id=pk)
        self.lot_id = self.bill.lot_ref_id
        self.oc_id = self.bill.oc_ref_id
        self.client_id = self.bill.client_ref_id
        self.property_id = OCMaster.objects.get(pk=self.oc_id).property_ref_id

    def set_instance(self):
        # set instance of property, lot , oc and client
        self.lot = Lot.objects.get(pk=self.lot_id)
        self.oc = OCMaster.objects.get(pk=self.oc_id)
        self.client = Client.objects.get(pk=self.client_id)
        self.property = Property.objects.get(pk=self.property_id)

        if LotOCMap.objects.filter(lot_ref_id=self.lot_id, oc_ref_id=self.oc_id).exists():
            self.CRN = LotOCMap.objects.get(lot_ref_id=self.lot_id, oc_ref_id=self.oc_id).CRN
        else:
            self.CRN = ''

    def get_billing_info(self):
        # July 3rd logic change to get owner_name no matter is agent or direct billing
        # billing_name2 = ''
        # billing_name1 = self.lot.owner_name1
        # if self.lot.owner_name2 is not None:
        #     billing_name2 = self.lot.owner_name2
        #
        # if self.lot.billing_adr is not None:
        #     billing_address = self.lot.billing_adr
        # else:
        #     billing_address = 'Unit ' + self.lot.unit_no + ', ' + self.property.street + ' ' + self.property.state + ' ' + self.property.post_code
        # return {'billing_name1': billing_name1,
        #         'billing_name2': billing_name2,
        #         'billing_address': billing_address}
        return generate_billing_info(self.lot, self.property)

    def get_unpaid_record(self):
        # get current balance of generating the bill and the balance before generating the bill
        """
        depends on self.hist_flag, if it is true then get historical data of the invoice
        else get the latest invoice

        :return:
        """
        if self.hist_flag:
            balances = get_invoice_lot_balance(self.lot_id, self.bill.billing_num)
        else:
            balances = get_latest_lot_balance(self.oc_id, self.lot_id)
        unpaid_records = []
        total_billing_amt = decimal.Decimal(0.00)
        if balances ['last_bal'] >= 0:
            total_broughtforward = balances ['last_bal']
            total_billing_amt = self.bill.billing_amount
            self.bill.payable_amount = abs(min(0, balances ['cur_bal']))
            unpaid_records.append(self.bill)

        else:
            total_broughtforward = decimal.Decimal(0.00)
            if self.hist_flag:
                billing_records = Billing.objects.filter(id__lte=self.bill.id, oc_ref_id=self.oc_id,
                                                         lot_ref_id=self.lot_id, is_valid=True).order_by('-id')
            else:
                billing_records = Billing.objects.filter(oc_ref_id=self.oc_id,
                                                         lot_ref_id=self.lot_id, is_valid=True).order_by('-id')
            unpaid_amt = abs(balances ['cur_bal'])
            for item in billing_records:
                if unpaid_amt > 0 and item.billing_amount > 0:
                    if unpaid_amt >= item.billing_amount:
                        item.payable_amount = item.billing_amount
                        # unpaid_records.append(item)
                        unpaid_amt = unpaid_amt - item.billing_amount

                    else:
                        item.collected_amount = item.billing_amount - unpaid_amt
                        item.payable_amount = unpaid_amt
                        # unpaid_records.append(item)
                        unpaid_amt = 0
                    unpaid_records.append(item)

                    total_billing_amt = total_billing_amt + item.billing_amount
                else:
                    break

        return {'unpaid': unpaid_records,
                'total_billing': total_billing_amt,
                'payable': min(balances ['cur_bal'], decimal.Decimal(0.00)),
                'broughtforward_amt': total_broughtforward,
                }

    def generate_feed_data(self):

        self.set_instance()
        billing_info = self.get_billing_info()
        unpaid_record = self.get_unpaid_record()
        data = {'bill': self.bill,
                'oc': self.oc,
                'property': self.property,
                'client': self.client,
                'lot': self.lot,
                'CRN': self.CRN,
                'billing_info': billing_info,
                'unpaid_record': unpaid_record,
                'hist': self.hist_flag
                }

        return data
