from django.urls import reverse

from .models import *
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Button
from base.cust_widgets import FengyuanChenDatePickerInput, FileInputCustom, DateTimePicker


class InsureCreateForm(forms.ModelForm):
    date_from = forms.DateField(
        widget=FengyuanChenDatePickerInput
    )

    date_to = forms.DateField(
        widget=FengyuanChenDatePickerInput
    )

    premium_due_date = forms.DateField(
        required=False,
        widget=FengyuanChenDatePickerInput
    )
    excess = forms.IntegerField(
        required=True, label="Excess"
    )
    policy_kind = forms.CharField(initial='Residential Strata')
    building_covered = forms.CharField(initial='see more details in the Certificate of Currency')
    company_name = forms.CharField(required=True)
    currency_cert = forms.FileField(widget=FileInputCustom, required=False, label='Currency of Certificate')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('policy_num', css_class='form-group col-md-6 mb-0'),
                Column('property_ref', css_class='form-group col-md-6 mb-0'),

                css_class='form-row'
            ),

            Row(
                Column('company_name', css_class='form-group col-md-6 mb-0'),

                css_class='form-row'
            ),

            Row(
                Column('broker', css_class='form-group col-md-4 mb-0'),
                Column('date_from', css_class='form-group col-md-4 mb-0'),
                Column('date_to', css_class='form-group col-md-4 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('premium_amt', css_class='form-group col-md-3 mb-0'),
                Column('premium_due_date', css_class='form-group col-md-3 mb-0'),
                Column('commission_rate', css_class='form-group col-md-3 mb-0'),
                Column('base_premium', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('est_commission', css_class='form-group col-md-4 mb-0'),
                Column('actual_commission', css_class='form-group col-md-4 mb-0'),
                Column('excess', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('policy_kind', css_class='form-group col-md-5 mb-0'),
                Column('building_covered', css_class='form-group col-md-5 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('building_amt', css_class='form-group col-md-3 mb-0'),
                Column('public_amt', css_class='form-group col-md-3 mb-0'),
                Column('common_contents', css_class='form-group col-md-3 mb-0'),
                Column('currency_cert', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-primary',
                   onclick="window.location.href = '{}';".format(reverse('strata:insurance_list')))

        )

    class Meta:
        model = Insurance
        fields = (
            'policy_num', 'date_from', 'date_to', 'property_ref', 'broker', 'company_name', 'premium_amt',
            'premium_due_date'
            , 'commission_rate', 'base_premium', 'est_commission', 'actual_commission',
            'policy_kind', 'building_amt', 'public_amt', 'building_covered', 'common_contents', 'currency_cert',
            'excess'
        )

        labels = dict(policy_num='Policy No.', date_from='Date From', date_to='Date To', property_ref='Property',
                      company_name='Company', premium_amt='Premium Amount', premium_due_date='Premium Due Date',
                      commission_rate='Commission Rate', base_premium='Base Premium',
                      est_commission='Estimate Commission', actual_commission='Actual Commission'
                      )


class AgmCreateForm(forms.ModelForm):
    meeting_datetime = forms.DateTimeField(widget=DateTimePicker,
                                           required=True, label="Meeting Date")

    location = forms.CharField(initial='ZOOM', widget=forms.Textarea(attrs={'rows': 2, 'cols': 4}))
    fyear = forms.IntegerField(required=True, label="Financial Year End")
    meeting_minutes = forms.FileField(widget=FileInputCustom, required=False, label='Meeting Minutes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('property_ref', css_class='form-group col-md-3 mb-0'),
                Column('oc_ref', css_class='form-group col-md-3 mb-0'),
                Column('meeting_datetime', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ), Row(
                Column('fyear', css_class='form-group col-md-2 mb-0'),

                css_class='form-row'
            ),

            Row(
                Column('location', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('meeting_minutes', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('is_init', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),

            Submit('submit', 'Save AGM Master'),
            Button('cancel', 'Cancel', css_class='btn-primary',
                   onclick="window.location.href = '{}';".format(reverse('strata:agm_list'))),
            Button('gen', 'Generate AGM Invite', css_class='btn-info')

        )

    class Meta:
        model = AGM
        fields = (
            'property_ref', 'oc_ref', 'meeting_datetime', 'location', 'fyear', 'meeting_minutes', 'is_init'
        )

        labels = dict(property_ref='Property',
                      oc_ref='OC')


class OwnerRequestForm(forms.ModelForm):
    msg_body = forms.CharField(widget=forms.Textarea(attrs={'rows': '4', 'columns': '5'}),
                               max_length=500, label="Body")
    msg_subject = forms.CharField(label="Title")

    class Meta:
        model = OwnerRequest
        fields = ('category', 'msg_subject', 'msg_body')
