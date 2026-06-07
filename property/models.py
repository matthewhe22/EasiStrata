from typing import List, Tuple
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models

from base.models import DateModel


class Property(DateModel):
    name = models.CharField(max_length=200, null=True, blank=True)
    lots_num = models.BigIntegerField()
    total_lot_liability = models.DecimalField(max_digits=20, decimal_places=2)
    total_lot_entitle = models.DecimalField(max_digits=20, decimal_places=2)
    street = models.CharField(max_length=200)
    suburb = models.CharField(max_length=200, null=True, blank=True)
    state = models.CharField(max_length=200, null=True, blank=True)
    post_code = models.CharField(max_length=10)
    country = models.CharField(max_length=200, null=True, blank=True, default="Australia")
    ABN = models.CharField(max_length=200, null=True, blank=True)
    TFN = models.CharField(max_length=200, null=True, blank=True)
    GST_register = models.BooleanField(default=False)
    plan_num = models.CharField(max_length=200, null=True, blank=True)
    plan_type = models.CharField(max_length=50, null=True, blank=True)
    rel_act = models.CharField(max_length=200, null=True, blank=True)
    module_type = models.CharField(max_length=50, null=True, blank=True)
    init_period = models.BooleanField(default=False)

    def __str__(self):
        if self.name is not None:
            return self.name
        else:
            return self.street


class Lot(DateModel):
    """
    owner_firstname
    owner_lastname
    tenant_email
    email-> email1
    tenant_email->email2
    """

    LOT_TYPE = [
        ('residential', 'residential'),
        ('commercial', 'commercial'),

    ]

    MAIL = [
        ('owner', 'owner'),
        # ('tenant','tenant'),
        ('agent', 'agent'),

    ]

    property_ref = models.ForeignKey(Property, on_delete=models.CASCADE)
    # floor = models.CharField(max_length=50, null=True, blank=True)
    lot = models.CharField(max_length=50)
    type_lot = models.CharField(max_length=50, null=True, blank=True)
    module_type = models.CharField(max_length=50, choices=LOT_TYPE, default='residential')
    billing_adr = models.CharField(max_length=200, null=True, blank=True)
    owner_adr = models.CharField(max_length=200, null=True, blank=True)
    owner_name1 = models.CharField(max_length=50, null=True, blank=True)
    owner_name2 = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=100, null=True, blank=True)
    email1 = models.EmailField(null=True, blank=True)
    email2 = models.EmailField(null=True, blank=True)
    agent_contact = models.CharField(max_length=100, null=True, blank=True)
    agent_name = models.CharField(max_length=100, null=True, blank=True)
    agent_email = models.EmailField(null=True, blank=True)
    tenant_email = models.EmailField(null=True, blank=True)
    # important NOTE prefer_mail is the levy correspondence and general mail is the general correpondence
    prefer_mail = models.CharField(choices=MAIL, default='owner', max_length=20)
    general_mail = models.CharField(choices=MAIL, default='owner', max_length=20)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_committee = models.BooleanField(default=False)
    unit_no = models.CharField(null=True, blank=True, max_length=30)

    def __str__(self):
        return self.unit_no

    def get_owner_mail(self):
        mail_list = []
        if self.email1:
            mail_list.append(self.email1)
        if self.email2:
            mail_list.append(self.email2)

        return mail_list

    def get_agent_mail(self):
        mail_list = []
        if self.agent_email:
            mail_list.append(self.agent_email)

        return mail_list

    def get_tenant_mail(self):
        output = []
        if self.tenant_email:
            output.append(self.tenant_email)
        return output

    def get_lot(self):
        return self.lot


class OCMaster(DateModel):
    FREQ: List [Tuple [str, str]] = [('Quarterly', 'quarter'), ('Monthly', 'month'), ('Half yearly', 'half year'),
                                     ('Annual', 'annual')]
    title = models.CharField(max_length=150)
    description = models.CharField(max_length=250, null=True, blank=True)
    start_date = models.DateField()
    expiry_date = models.DateField()
    property_ref = models.ForeignKey(Property, on_delete=models.CASCADE)
    manager_first_name = models.CharField(max_length=100, null=True, blank=True)
    manager_last_name = models.CharField(max_length=100, null=True, blank=True)
    manager_sign = models.ImageField(upload_to='media/', null=True, blank=True)
    seal = models.ImageField(upload_to='media/', null=True, blank=True)
    manager_threshold = models.IntegerField(default=0)
    chairman_threshold = models.IntegerField(default=0)
    BSB = models.CharField(max_length=20, null=True, blank=True)
    Account = models.CharField(max_length=50, null=True, blank=True)
    Account_name = models.CharField(max_length=130, null=True, blank=True)
    beg_bal = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    frequency = models.CharField(max_length=20, choices=FREQ)
    billing_start_date = models.DateField()
    liability = models.IntegerField(default=0)
    bank_fee = models.IntegerField(default=10)
    biller_code = models.CharField(max_length=50, null=True, blank=True)
    oc_rule = models.FileField(blank=True, null=True)
    meeting_mins = models.FileField(blank=True, null=True)

    def __str__(self):
        return self.title

    def get_last_num(self):
        return self.description [-1:]

    def oc_before_start_day(self):
        return self.billing_start_date + timedelta(days=-1)


class LotOCMap(DateModel):
    oc_ref = models.ForeignKey(OCMaster, on_delete=models.CASCADE)
    lot_ref = models.ForeignKey(Lot, on_delete=models.CASCADE)
    entitlement = models.DecimalField(max_digits=20, decimal_places=2)
    liability = models.DecimalField(max_digits=20, decimal_places=2)
    CRN = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        if self.CRN:
            return self.CRN
        else:
            return ""


class OcBudget(DateModel):
    oc_ref = models.ForeignKey(OCMaster, on_delete=models.CASCADE)
    fin_year = models.IntegerField()
    acc_code = models.CharField(max_length=20)
    acc_name = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
