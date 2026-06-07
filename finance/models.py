from datetime import datetime

from django.db import models
from base.models import DateModel, DateModelNonClient
from property.models import OCMaster, Property, Lot
from scripts.utils.date_utils import date_to_str
from scripts.utils.property_utils import get_oc_name, get_property_name

MAIL = [('prepared', 'prepared'), ('sending', 'sending'), ('sent', 'sent'), ('fail', 'fail'), ("draft", "draft")]


# Create your models here.
class COA(DateModelNonClient):
    LEVEL1 = [('Income', 'Income'), ('Expenditure', 'Expenditure'), ]
    CAT = [
        ('Administration', 'Administration'),
        ('Professional Services', 'Professional Services'),
        ('Management', 'Management'),
        ('Repairs & Maintenance', 'Repairs & Maintenance'),
        ('Renewals & Replacements', 'Renewals & Replacements'),
        ('Miscellaneous', 'Miscellaneous'),
        ('Other Revenue', 'Other Revenue'),
        ('Levy Revenue', 'Levy Revenue'),
        ('Utilities', 'Utilities'),
        ('Personal Property', 'Personal Property'),
        ('Other Accounts', 'Other Accounts'),
        ('Holding Accounts', 'Holding Accounts'),
        ('Insurance', 'Insurance'),
        ('Shared Costs', 'Shared Costs'),
        ('Strata Setup', 'Strata Setup'),

    ]

    acc_code = models.CharField(max_length=100)
    acc_name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    account_level1 = models.CharField(max_length=20, choices=LEVEL1)
    account_level2 = models.CharField(max_length=100)
    is_gst_output = models.BooleanField(default=False)
    is_gst_input = models.BooleanField(default=False)


class IncomeExp(DateModel):
    CAT = [('income', 'income'), ('expense', 'expense'), ('AR', 'AR'), ('AP', 'AP'), ('prepay', 'prepay'),
           ('refund', 'refund')]
    name = models.CharField(max_length=100)
    income_expense_code = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    debit_acc = models.CharField(max_length=50)
    credit_acc = models.CharField(max_length=50)
    is_gst_output = models.BooleanField(default=False)
    is_deferred = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Supplier(DateModel):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    suburb = models.CharField(max_length=20)
    post_code = models.CharField(max_length=20)
    type_supply = models.CharField(max_length=30, blank=True, null=True)
    type_contract = models.CharField(max_length=30, blank=True, null=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    exp_ref = models.ForeignKey(IncomeExp, on_delete=models.CASCADE)
    ABN = models.CharField(max_length=50, null=True, blank=True)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    contact_num = models.CharField(max_length=100, null=True, blank=True)
    contact_email = models.EmailField(max_length=100, null=True, blank=True)
    payment_acc = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name


class Invoice(DateModel):
    SAT = [('00', 'cancel'), ('01', 'prepared'), ('02', 'pending for oc manager'), ('03', 'oc manager approved'),
           ('04', 'pending for chairman'), ('05', 'chairman approved'),
           ('06', 'rejected by oc manager'), ('07', 'rejected by chairman'), ('08', 'approved')]

    PAY_SAT = [('paid', 'paid'), ('unpaid', 'unpaid')]
    inv_date = models.DateField()
    inv_num = models.CharField(max_length=100)
    ref = models.CharField(max_length=500, null=True, blank=True)
    supplier_ref = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    due_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    input_gst = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    exp_type = models.CharField(max_length=10)
    status = models.CharField(max_length=10, default='01', choices=SAT, null=True, blank=True)
    payment_status = models.CharField(max_length=10, default='unpaid', choices=PAY_SAT, null=True, blank=True)
    last_approved = models.CharField(max_length=20, blank=True, null=True)
    exp_ref = models.ForeignKey(IncomeExp, on_delete=models.CASCADE)
    oc_ref = models.ForeignKey('property.OCMaster', on_delete=models.CASCADE, db_column='oc_ref')
    defer_from = models.DateField(null=True, blank=True)
    defer_to = models.DateField(null=True, blank=True)
    defer_periods = models.IntegerField(default=12)
    attachment = models.FileField(null=True, blank=True)

    def get_property_name(self):
        prop_id = OCMaster.objects.get(pk=self.oc_ref_id).property_ref_id
        property_name = Property.objects.get(pk=prop_id).name
        return property_name

    def get_total(self):
        return self.amount + self.input_gst

    class Meta:
        ordering = ['-inv_date']


class Billing(DateModel):
    STAT = [('unpaid', 'unpaid'), ('paid', 'paid')]

    billing_num = models.CharField(max_length=30)
    lot_ref = models.ForeignKey('property.Lot', on_delete=models.CASCADE)
    billing_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    collected_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    billing_from = models.DateField()
    billing_to = models.DateField()
    due_date = models.DateField()
    billing_date = models.DateField()
    status = models.CharField(max_length=10, default='unpaid', choices=STAT)
    oc_ref = models.ForeignKey('property.OCMaster', on_delete=models.CASCADE, db_column='oc_ref')
    mail_status = models.CharField(max_length=10, default='prepared', choices=MAIL)
    desc = models.CharField(max_length=200, blank=True, null=True)
    attachment = models.FileField(null=True, blank=True)
    special_flag = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=True)
    is_show = models.BooleanField(default=True)

    def get_property_name(self):
        prop_id = OCMaster.objects.get(pk=self.oc_ref_id).property_ref_id
        property_name = Property.objects.get(pk=prop_id).name
        return property_name

    def get_property_id(self):
        return OCMaster.objects.get(pk=self.oc_ref_id).property_ref_id

    def get_unit(self):
        return Lot.objects.get(pk=self.lot_ref_id).unit_no

    def get_agent(self):
        return Lot.objects.get(pk=self.lot_ref_id).agent_name

    def get_payable(self):
        return self.billing_amount - self.collected_amount

    class Meta:
        ordering = ['-billing_num']


class GL(DateModel):
    acc_code = models.CharField(max_length=100)
    posting_date = models.DateField()
    document_date = models.DateField()
    dc = models.CharField(max_length=10)
    period = models.CharField(max_length=10)
    description = models.CharField(max_length=240, null=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    exp_type = models.CharField(max_length=50, null=True)
    oc_ref = models.ForeignKey('property.OCMaster', on_delete=models.CASCADE, db_column='oc_ref')
    doc_num = models.CharField(max_length=30)
    recon_amt = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    unpresent_flag = models.BooleanField(default=False)

    def get_oc_name(self):
        return get_oc_name(self.oc_ref_id)

    def get_property_name(self):
        prop_id = OCMaster.objects.get(pk=self.oc_ref_id).property_ref_id
        property_name = Property.objects.get(pk=prop_id).name
        return property_name


class Occertificate(DateModel):
    oc_ref = models.ForeignKey('property.OCMaster', on_delete=models.CASCADE, db_column='oc_ref')
    lot_ref = models.ForeignKey('property.Lot', on_delete=models.CASCADE)
    issue_date = models.DateField()
    special_fee = models.CharField(max_length=500, default='Nil')
    additional_charge = models.CharField(max_length=500, default='Nil')
    additional_liability = models.CharField(max_length=500, default='Nil')
    affect_common_property = models.CharField(max_length=500, default='Nil')
    cur_agreement = models.CharField(max_length=500, default='Nil')
    non_statisfy_order = models.CharField(max_length=500, default='Nil')
    legal_proceeding = models.CharField(max_length=500, default='Nil')
    applicant = models.CharField(max_length=100, blank=True, null=True)
    attachment = models.FileField(null=True, blank=True, upload_to='certificate/')

    class Meta:
        ordering = ['-id']


class FS(DateModel):
    property_ref = models.ForeignKey(Property, on_delete=models.CASCADE)
    oc_ref = models.ForeignKey('property.OCMaster', on_delete=models.CASCADE, db_column='oc_ref')
    fin_year = models.IntegerField(default=2020)
    to_date = models.DateField()
    from_date = models.DateField(blank=True, null=True)


class BankTrans(DateModel):
    acc_num = models.CharField(max_length=100)
    acc_name = models.CharField(max_length=100)
    trans_date = models.DateField()
    narrative = models.CharField(max_length=240, blank=True, null=True)
    ref_num = models.CharField(max_length=240, blank=True, null=True)
    amount = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    balance = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    category = models.CharField(max_length=240, blank=True, null=True)
    # field for system bpay processing result
    process_result = models.CharField(max_length=240, blank=True, null=True)
    oc_ref = models.ForeignKey('property.OCMaster', on_delete=models.CASCADE, db_column='oc_ref', null=True, blank=True)
    recon_amt = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    # recpt_amt is the amount being created as cash receipt
    recpt_amt = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    unpresent_flag = models.BooleanField(default=False)

    def get_oc_name(self):
        return get_oc_name(self.oc_ref_id)

    def get_property_name(self):
        prop_id = OCMaster.objects.get(pk=self.oc_ref_id).property_ref_id
        property_name = Property.objects.get(pk=prop_id).name
        return property_name


class CashReceipt(DateModel):
    recpt_no = models.CharField(max_length=20)
    recpt_date = models.DateField()
    lot_ref = models.ForeignKey('property.Lot', on_delete=models.CASCADE, db_column='lot_ref', blank=True, null=True)
    amount = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    reference = models.CharField(max_length=240, blank=True, null=True)
    description = models.CharField(max_length=240, blank=True, null=True)
    bank_ref = models.ForeignKey('BankTrans', on_delete=models.CASCADE, db_column='bank_ref')
    is_valid = models.BooleanField(default=True)
    mail_status = models.CharField(max_length=10, default='prepared', choices=MAIL)
    attachment = models.FileField(null=True, blank=True)

    def get_lot(self):
        return Lot.objects.get(pk=self.lot_ref_id).lot

    def get_lot_instance(self):
        return self.lot_ref

    def get_oc_id(self):
        pass

    def get_oc(self):
        return self.bank_ref.oc_ref

    def get_property(self):
        return self.lot_ref.property_ref

    def get_bank_desc(self):
        return self.bank_ref.narrative


class ClientLedger(DateModel):
    trans_date = models.DateField()
    debit_amt = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    credit_amt = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    balance = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    reference = models.CharField(max_length=240, blank=True, null=True)
    description = models.CharField(max_length=240, blank=True, null=True)
    lot_ref = models.ForeignKey('property.Lot', on_delete=models.CASCADE, db_column='lot_ref')
    oc_ref = models.ForeignKey('property.OCMaster', on_delete=models.CASCADE, db_column='oc_ref', null=True, blank=True)

    def get_desc(self):
        if self.description is None and self.reference [:3] == "INV":
            bill = Billing.objects.filter(billing_num=self.reference).first()
            if bill:
                return self.oc_ref.frequency + ' Fee from ' + date_to_str(bill.billing_from) + " to " + date_to_str(
                    bill.billing_to)

            return self.description
        else:
            return self.description

    class Meta:
        ordering = ['-trans_date', '-id']


class InvoicePay(DateModel):
    invoice_ref = models.ForeignKey('Invoice', on_delete=models.CASCADE)
    payment_amount = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    bal_amount = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    posting_date = models.DateField(null=True, blank=True)
    gl_status = models.CharField(max_length=10, default='prepared')
    desc = models.CharField(max_length=100, null=True, blank=True)
    attachment = models.FileField(null=True, blank=True)


class ReconDetail(DateModel):
    SAT = [('00', 'valid'), ('01', 'invalid')]
    recon_id = models.CharField(max_length=20, null=True, blank=True)
    bank_id = models.IntegerField()
    bank_ref = models.CharField(max_length=50, null=True, blank=True)
    bank_amt = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    gl_id = models.IntegerField()
    gl_ref = models.CharField(max_length=50, null=True, blank=True)
    gl_amt = models.DecimalField(default=0.00, max_digits=20, decimal_places=2)
    desc = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, default='00', choices=SAT)


class ReconList(DateModel):
    SAT = [('00', 'prepared'), ('01', 'complete'), ('02', 'cancel')]

    recon_id = models.CharField(max_length=20, null=True, blank=True)
    oc_ref = models.ForeignKey('property.OCMaster', on_delete=models.CASCADE, db_column='oc_ref')
    bank_balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    recon_date = models.DateField()
    status = models.CharField(max_length=10, default='00', choices=SAT)
    note = models.CharField(max_length=200, null=True, blank=True)
