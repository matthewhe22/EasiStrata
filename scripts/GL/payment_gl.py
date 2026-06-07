from scripts.utils.fin_utils import bill_payment_gl, payment_in_advance
from finance.models import ClientLedger, Billing


class PaymentGL(object):
    def __init__(self, oc_id, lot_id, recpt_no, amount, trans_date, user, balance):
        self.lot_id = lot_id
        self.recpt_no = recpt_no
        self.amount = float(amount)
        self.trans_date = trans_date
        self.oc_id = oc_id
        self.user = user
        self.balance = float(balance)
        self.handle()

    def handle(self):

        # pure advance payment
        if self.balance >= 0 and self.amount > 0:
            self.advance_pay_gl(self.amount)
        # pay for balance and payment is greater than payable
        if self.balance < 0 and self.amount > 0 and abs(self.balance) < abs(self.amount):
            self.advance_pay_gl(self.amount + self.balance)
            self.generate_gl_from_list(abs(self.balance))

        # pay for balance and payment is smaller or equal to payable
        if self.balance < 0 and self.amount > 0 and abs(self.balance) >= abs(self.amount):
            self.generate_gl_from_list(abs(self.amount))

    def advance_pay_gl(self, amount, reverse=False):
        payment_in_advance(self.oc_id, amount, self.user, self.trans_date, self.recpt_no, reverse)

    def generate_gl_from_list(self, amount):
        all_bills = Billing.objects.filter(lot_ref_id=self.lot_id, oc_ref_id=self.oc_id, is_valid=True).order_by('-id')
        bill_list = []
        for item in all_bills:
            if amount > 0:
                if item.billing_amount < amount:
                    bill_amount = float(item.billing_amount)
                    bill_list.append({'bill': item,
                                      'amount': bill_amount})
                    amount = amount - bill_amount
                else:
                    bill_list.append({'bill': item,
                                      'amount': amount})
                    break
        # generate GL based on the bill_list
        for item in bill_list:
            bill_payment_gl(item ['bill'], item ['amount'], self.user, self.recpt_no, self.trans_date)
