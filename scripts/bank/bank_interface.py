"""
summary steps of bank transaction
1. generate bank transaction
2. map oc
3. map lot
4. if 2 and 3 ok, then automatically create cash receipt （generate GL）
5. else pending for manual allocation
"""
from finance.models import BankTrans
from scripts.utils.date_utils import str_to_date
from property.models import OCMaster, LotOCMap
from finance.models import CashReceipt, Billing, ClientLedger
from scripts.GL.client_ledger import create_client_ledger
from scripts.utils.cal_utils import generate_id
from scripts.GL.payment_gl import PaymentGL
from scripts.utils.fin_utils import get_lot_balance
from scripts.billing.payment_interface import handle_payment


class Bank:
    def __init__(self, trans_detail, user):
        # trans_detail is a list
        self.user = user
        self.trans_detail = trans_detail
        self._has_oc = False
        self._has_lot = False

    def _init_trans_instance(self):
        if type(self.trans_detail).__name__ == 'list':
            transaction = BankTrans()
            transaction.createby = self.user
            transaction.updateby = self.user
            transaction.client_ref_id = 1
            transaction.acc_num = self.trans_detail [0]
            transaction.trans_date = str_to_date(self.trans_detail [1])
            transaction.narrative = self.trans_detail [2]
            transaction.client_ref_id = 1
            if self.trans_detail [3]:
                transaction.amount = float(self.trans_detail [3]) * (-1)
            else:
                transaction.amount = float(self.trans_detail [4])
            transaction.balance = self.trans_detail [5]
            transaction.category = self.trans_detail [6]
            self.transaction = transaction
        else:
            raise Exception('The input format is not correct')

    def _match_oc(self):
        _bsb = self.transaction.acc_num [:6]
        _account = self.transaction.acc_num [6:]

        try:
            oc = OCMaster.objects.get(Account__icontains=_account, BSB__contains=_bsb)
            self._has_oc = True
            self.transaction.oc_ref_id = oc.id
        except OCMaster.DoesNotExist:
            self.transaction.process_result = "Error no OC bank account could be matched"
            self.transaction.save()

    def _match_lot(self):
        if "BPAY" in self.transaction.narrative:
            bpay_list = self.transaction.narrative.split(" ")
            bpay_index = bpay_list.index("BPAY") + 1
            bpay_number = bpay_list [bpay_index]
            lot_oc = LotOCMap.objects.filter(CRN__icontains=bpay_number, oc_ref_id=self.transaction.oc_ref_id).first()
            if lot_oc:
                balance = get_lot_balance(self.transaction.oc_ref_id, lot_oc.lot_ref_id)
                self.transaction.recpt_amt = self.transaction.amount
                self.transaction.process_result = "cash receipt created"
                self.transaction.save()
                # create cash receipt
                recpt_no = self._create_cash_receipt(lot_oc.lot_ref_id)
                # increase collected amount for billings
                handle_payment(self.transaction.oc_ref_id, lot_oc.lot_ref_id, self.transaction.amount, self.user)
                PaymentGL(self.transaction.oc_ref_id, lot_oc.lot_ref_id, recpt_no, self.transaction.amount,
                          self.transaction.trans_date, 'batch_import', balance)
            else:
                self.transaction.process_result = "No lot matched. Please manually create cash receipt"
                self.transaction.save()
        elif "INV" in self.transaction.narrative:
            inv_index = self.transaction.narrative.find("INV")
            invoice_id = self.transaction.narrative [inv_index:inv_index + 10]
            bill = Billing.objects.filter(billing_num=invoice_id, is_valid=True).first()
            if bill:
                balance = get_lot_balance(self.transaction.oc_ref_id, bill.lot_ref_id)
                self.transaction.recpt_amt = self.transaction.amount
                self.transaction.process_result = "cash receipt created"
                self.transaction.save()
                recpt_no = self._create_cash_receipt(bill.lot_ref_id)
                PaymentGL(self.transaction.oc_ref_id, bill.lot_ref_id, recpt_no, self.transaction.amount,
                          self.transaction.trans_date, 'batch_import', balance)
                handle_payment(self.transaction.oc_ref_id, bill.lot_ref_id, self.transaction.amount, self.user)

            else:
                # no need to generate bill since it doesn't hit the client ledger
                self.transaction.process_result = "No lot matched. Please manually create cash receipt"
                self.transaction.save()
        else:
            # no need to generate bill since it doesn't hit the client ledger
            self.transaction.process_result = "No lot matched. Please manually create cash receipt"
            self.transaction.save()

    def _create_cash_receipt(self, lot_id):
        receipt = CashReceipt()
        receipt.createby = receipt.updateby = self.user
        receipt.recpt_date = self.transaction.trans_date
        receipt.lot_ref_id = lot_id
        receipt.amount = self.transaction.amount
        receipt.reference = "automatic generation from bank transaction"
        receipt.bank_ref_id = self.transaction.id
        receipt.recpt_no = generate_id('RCP')
        receipt.client_ref_id = 1
        receipt.save()
        self._update_client_ledger(lot_id, receipt.recpt_no)

        return receipt.recpt_no

    def _update_client_ledger(self, lot_id, reference):
        amount = self.transaction.amount
        create_client_ledger(self.transaction.oc_ref_id, lot_id, amount, reference, self.user,
                             self.transaction.trans_date)

    def handle(self):
        self._init_trans_instance()
        self._match_oc()
        if self._has_oc:
            self._match_lot()
