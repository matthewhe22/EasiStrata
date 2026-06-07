from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User


class Client(models.Model):
    createby = models.CharField(max_length=50, default=" ")
    createtime = models.DateField(auto_now_add=True)
    updateby = models.CharField(max_length=50, default=" ")
    updatetime = models.DateField(auto_now=True)
    client_name = models.CharField(max_length=255, verbose_name='client name')
    ABN = models.CharField(max_length=100, blank=True)
    TFN = models.CharField(max_length=50, blank=True)
    Address = models.CharField(max_length=500, blank=True)
    telephone = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=100)
    IsDeleted = models.BooleanField(default=False)
    post_adr = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.client_name


# DateModel is the public class should be inherited by every model under tax auto proejct
class DateModel(models.Model):
    createby = models.CharField(max_length=50, default=" ")
    createtime = models.DateField(auto_now_add=True)
    updateby = models.CharField(max_length=50, default=" ")
    updatetime = models.DateField(auto_now=True)
    client_ref = models.ForeignKey(Client, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class DateModelNonClient(models.Model):
    createby = models.CharField(max_length=50, default=" ")
    createtime = models.DateField(auto_now_add=True)
    updateby = models.CharField(max_length=50, default=" ")
    updatetime = models.DateField(auto_now=True)

    class Meta:
        abstract = True


class DataSource(DateModel):
    SHEET_MODE_CHOICES = [
        ('ALL', 'ALL'),
        ('MATCH', 'MATCH'),
        ('SINGLE', 'SINGLE'),

    ]

    FILE_TYPE_CHOICES = [('EXCEL', 'EXCEL')]
    data_src = models.CharField(max_length=100, unique=True, verbose_name='Name')
    filetype = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='EXCEL')
    sheet_mode = models.CharField(max_length=20, choices=SHEET_MODE_CHOICES, default='ALL')
    sheet_name = models.CharField(max_length=100, blank=True)
    db_table = models.CharField(max_length=100)
    client_ref = models.ForeignKey(Client, on_delete=models.CASCADE, db_column='client_ref')

    def __str__(self):
        return self.data_src


class DataSourceRule(DateModel):
    FIELD_TYPE_CHOICES = [('string', 'string'), ('number', 'number'), ('cal', 'calculation'), ('date', 'date')]
    YES_NO_CHOICES = [(True, 'Yes'), (False, 'No')]
    src_ref = models.ForeignKey('DataSource', on_delete=models.CASCADE, db_column='src_ref')
    src_header = models.CharField(max_length=200)
    ftype = models.CharField(max_length=10, choices=FIELD_TYPE_CHOICES, default='string')
    cal_exp = models.CharField(max_length=100, blank=True)
    map_field = models.CharField(max_length=100, blank=True)
    is_trans = models.BooleanField(choices=YES_NO_CHOICES, default=False)
    reg_exp = models.CharField(max_length=255, blank=True)


class ImportLog(DateModel):
    STATUS_CHOICES = [
        ('01', 'Success'),
        ('02', 'Fail'),
        ('03', 'In progress')

    ]

    # createby definition, user imoprt then should be username, interface import should be interface name
    # company code and taxpayerid subject to be setup as foreignkey later
    doc = models.FileField(upload_to='uploads', null=True, blank=True)
    src_ref = models.ForeignKey('DataSource', on_delete=models.CASCADE, db_column='src_ref')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_code = models.CharField(max_length=50, blank=True)
    error_message = models.CharField(max_length=500, blank=True)


class TB(DateModel):
    acc_code = models.CharField(max_length=100)
    acc_name = models.CharField(max_length=100, null=True, blank=True)
    beg_bal = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    end_bal = models.DecimalField(max_digits=20, decimal_places=2, default=0.00, null=True, blank=True)
    period = models.CharField(max_length=20, null=True)
    client_ref = models.ForeignKey('Client', on_delete=models.CASCADE, db_column='client_ref')


class ErrorConfig(DateModel):
    ERROR_TYPE = [
        ('error', 'error'),
        ('warning', 'warning'),
        ('info', 'info')

    ]

    error_code = models.CharField(max_length=50)
    error_type = models.CharField(max_length=50, choices=ERROR_TYPE)
    error_message = models.CharField(max_length=300, null=True, blank=True)
    note = models.CharField(max_length=200, null=True, blank=True)


class Sequence(DateModel):
    seq_prefix = models.CharField(max_length=100, null=True, blank=True)
    seq_code = models.CharField(max_length=100, unique=True)
    seq_num = models.BigIntegerField(default=0)
    seq_category = models.CharField(max_length=100, null=True, blank=True)
    seq_char_width = models.IntegerField()
    version = models.BigIntegerField(default=0)


class Notification(DateModel):
    MAIL = [('prepared', 'prepared'), ('sending', 'sending'), ('sent', 'sent'), ('fail', 'fail'), ('na', 'na')]
    READ = [('read', 'read'), ('unread', 'unread'), ('na', 'na')]
    MTD = [('email', 'email'), ('note', 'note'), ('email-note', 'email-note'), ('working-order', 'working-order')]

    user_name = models.CharField(max_length=100, null=True, blank=True)
    cc = models.CharField(max_length=100, null=True, blank=True)
    msg_subject = models.CharField(max_length=100)
    msg_body = models.CharField(max_length=2000)
    attachment = models.FileField(null=True, blank=True)
    read_status = models.CharField(default='unread', max_length=20)
    mail_status = models.CharField(choices=MAIL, default='prepared', max_length=20)
    category = models.CharField(choices=MTD, default='note', max_length=20)
    property_id = models.IntegerField(default=0)
    oc_id = models.IntegerField(default=0)
    lot = models.CharField(max_length=50, null=True, blank=True)


# class User(AbstractUser):
#
#     ROLE_CHOICES = (
#         ('staff', 'Staff'),
#         ('owner', 'Owner'),
#         ('manager', 'Manager'),
#     )
#     role = models.CharField(max_length=10,choices=ROLE_CHOICES, blank=True, null=True)


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('staff', 'Staff'),
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('committee', 'Committee Member'))

    user = models.OneToOneField(User, related_name="profile", on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)
