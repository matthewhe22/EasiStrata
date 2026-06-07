from django.db import models
from django.db.models import Max

from base.models import DateModel
from property.models import Lot
from scripts.utils.date_utils import agm_date_to_str, datetime_to_str
import calendar


# Create your models here.

class Insurance(DateModel):
    policy_num = models.CharField(max_length=100)
    date_from = models.DateField()
    date_to = models.DateField()
    property_ref = models.ForeignKey('property.Property', on_delete=models.CASCADE)
    broker = models.CharField(max_length=100, null=True, blank=True)
    company_name = models.CharField(max_length=100, null=True, blank=True)
    premium_amt = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    premium_due_date = models.DateField(null=True, blank=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, default=0.0000)
    base_premium = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, default=0.00)
    est_commission = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, default=0.00)
    actual_commission = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, default=0.00)
    common_contents = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, default=0.00)
    policy_kind = models.CharField(max_length=50, default='Residential Strata')
    building_amt = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    public_amt = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    building_covered = models.CharField(max_length=50, default='see more details in the Certificate of Currency')
    terrorism_covered = models.CharField(max_length=50, null=True, blank=True)
    loss_rent = models.CharField(max_length=50, null=True, blank=True)
    liability = models.CharField(max_length=50, null=True, blank=True)
    voluntary_worker = models.CharField(max_length=50, null=True, blank=True)
    fidelity_guarantee = models.CharField(max_length=50, null=True, blank=True)
    office_bearers = models.CharField(max_length=50, null=True, blank=True)
    gov_audit_cost = models.CharField(max_length=50, null=True, blank=True)
    appeal_exp = models.CharField(max_length=50, null=True, blank=True)
    legal_def = models.CharField(max_length=50, null=True, blank=True)
    fixture_improve = models.CharField(max_length=50, null=True, blank=True)
    currency_cert = models.FileField(null=True, blank=True)
    excess = models.IntegerField(default=0)


class AGM(DateModel):
    property_ref = models.ForeignKey('property.Property', on_delete=models.CASCADE)
    oc_ref = models.ForeignKey('property.OCMaster', on_delete=models.CASCADE)
    meeting_datetime = models.DateTimeField()
    location = models.CharField(max_length=200)
    fyear = models.IntegerField()
    meeting_minutes = models.FileField(null=True, blank=True)
    meeting_invite = models.FileField(null=True, blank=True)
    is_agm_sent = models.BooleanField(default=False)
    is_minutes_sent = models.BooleanField(default=False)
    is_init = models.BooleanField(default=False)

    def render_agm_context(self):
        agendas = AgmDetail.objects.filter(agm_ref_id=self.id).order_by('seq_no')

        return {'property': self.property_ref,
                'oc': self.oc_ref,
                'client': self.client_ref,
                'agendas': agendas
                }

    def get_date(self):
        return calendar.day_name [self.meeting_datetime.weekday()] + ' ' + agm_date_to_str(self.meeting_datetime)

    def get_time(self):
        return datetime_to_str(self.meeting_datetime)

    def get_notice_date(self):
        return agm_date_to_str(self.createtime)

    def get_max_seq_no(self):
        max_seq = AgmDetail.objects.filter(agm_ref_id=self.id).aggregate(Max('seq_no'))
        return max_seq ['seq_no__max']


class AgmDetail(DateModel):
    agm_ref = models.ForeignKey('strata.AGM', on_delete=models.CASCADE)
    seq_no = models.IntegerField(default=1)
    title = models.CharField(max_length=150)
    content = models.CharField(max_length=1500, null=True, blank=True)
    is_insurance = models.BooleanField(default=False)

    def is_first(self):
        if self.seq_no == 1:
            return True
        else:
            return False

    def is_last(self):
        max_seq = AgmDetail.objects.filter(agm_ref=self.agm_ref).aggregate(Max('seq_no'))
        if self.seq_no == max_seq ['seq_no__max']:
            return True
        else:
            return False

    class Meta:
        ordering = ['seq_no']


class OwnerRequest(DateModel):
    MAIL = [('prepared', 'prepared'), ('sending', 'sending'), ('sent', 'sent'), ('fail', 'fail'), ('na', 'na')]
    MTD = [('certificate', 'OC certificate request'), ('key', 'Key and Fob request'), ('issue', 'Issue report '),
           ('other', 'Other')]

    msg_subject = models.CharField(max_length=100)
    msg_body = models.CharField(max_length=2000)
    attachment = models.FileField(null=True, blank=True)
    mail_status = models.CharField(choices=MAIL, default='prepared', max_length=20)
    category = models.CharField(choices=MTD, default='certificate', max_length=20)
    lot_ref = models.ForeignKey(Lot, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-id']
