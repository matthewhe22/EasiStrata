from string import Template

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Button
from django import forms
from django.forms.widgets import EmailInput
from base.cust_widgets import FengyuanChenDatePickerInput, FileInputCustom
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import *


class PropertyCreateForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = (
            'street', 'name', 'lots_num', 'total_lot_liability', 'total_lot_entitle', 'post_code', 'plan_num', 'rel_act'
            , 'suburb', 'state', 'ABN', 'GST_register')

        labels = {
            'street': 'Property Address',
            'name': 'Building Name',
            'lots_num': 'Lots No.',
            'total_lot_entitle': 'Total Entitlement',
            'total_lot_liability': 'Total Liability',
            'plan_num': 'Plan No.',
            'rel_act': 'Rel Act',
            'GST_register': 'GST Flag'
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.layout = Layout(
                Row(
                    Column('street', css_class='form-group col-md-3 mb-0'),
                    Column('name', css_class='form-group col-md-3 mb-0'),
                    Column('lots_num', css_class='form-group col-md-3 mb-0'),

                    css_class='form-row'

                ),
                Row(
                    Column('suburb', css_class='form-group col-md-3 mb-0'),
                    Column('state', css_class='form-group col-md-3 mb-0'),
                    Column('post_code', css_class='form-group col-md-3 mb-0'),
                    Column('ABN', css_class='form-group col-md-3` mb-0'),

                    css_class='form-row'
                ),
                'rel_act',
                'GST_register',

                Row(
                    Column('total_lot_liability', css_class='form-group col-md-4 mb-0'),
                    Column('total_lot_entitle', css_class='form-group col-md-4 mb-0'),

                    css_class='form-row'
                ),

                Submit('submit', 'Submit'),
                Button('cancel', 'Cancel', css_class='btn-primary',
                       onclick="window.location.href = '{}';".format(reverse('property:property_list')))

            )


class LotCreateForm(forms.ModelForm):
    email1 = forms.EmailField(widget=EmailInput, required=False)
    email2 = forms.EmailField(widget=EmailInput, required=False)
    agent_email = forms.EmailField(widget=EmailInput, required=False)
    unit_no = forms.CharField(required=False, label="Unit No.")
    billing_adr = forms.CharField(required=False, label='Levy Address', widget=forms.Textarea(attrs={'rows': '4'}))
    owner_adr = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': '4'}), label='Postal Address')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('property_ref', css_class='form-group col-md-3 mb-0'),
                Column('lot', css_class='form-group col-md-3 mb-0'),
                Column('unit_no', css_class='form-group col-md-3 mb-0'),
                Column('module_type', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('billing_adr', css_class='form-group col-md-5 mb-0'),
                Column('owner_adr', css_class='form-group col-md-5 mb-0'),

            )

            ,
            Row(
                Column('owner_name1', css_class='form-group col-md-3 mb-0'),
                Column('owner_name2', css_class='form-group col-md-3 mb-0'),
                Column('prefer_mail', css_class='form-group col-md-3 mb-0'),
                Column('general_mail', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('phone', css_class="form-group col-md-3 mb-0"),
                Column('email1', css_class='form-group col-md-3 mb-0'),
                Column('email2', css_class='form-group col-md-3 mb-0'),
                # Column('is_committee', css_class='form-group col-md-2 mb-0'),

                css_class='form-row'
            ), Row(
                Column('agent_name', css_class='form-group col-md-3 mb-0'),
                Column('agent_contact', css_class='form-group col-md-3 mb-0'),
                Column('agent_email', css_class='form-group col-md-3 mb-0'),
                Column('tenant_email', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            'is_committee',
            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-primary',
                   onclick="window.location.href = '{}';".format(reverse('property:lot_list')))

        )

    class Meta:
        model = Lot
        fields = (
            'property_ref', 'lot', 'type_lot', 'module_type', 'billing_adr', 'email1',
            'email2', 'owner_name1', 'owner_name2',
            'phone', 'agent_email', 'agent_contact', 'agent_name', 'prefer_mail', 'unit_no', 'general_mail',
            'owner_adr', 'tenant_email', 'is_committee')

        labels = {
            'property_ref': 'Property Name',
            'type_lot': 'Lot Type',
            'module_type': 'Module Type',
            'is_committee': 'Is committee member',
            # 'owner_adr': 'Owner Address',
            'owner_name1': 'Name (Owner1)',
            'owner_name2': 'Name (Owner2)',
            'agent_contact': 'Agent Contacts',
            'agent_name': 'Agent Name',
            'agent_email': 'Agent Email',
            'lot': 'Lot No.',
            'prefer_mail': 'Levy Recipient',
            'general_mail': 'General Correspondence',

        }


class PictureWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None, **kwargs):
        value = value.url
        html = Template("""<img src="$link"/>""")
        return mark_safe(html.substitute(link=value))


class OcUpdateForm(forms.ModelForm):
    start_date = forms.DateField(widget=FengyuanChenDatePickerInput())
    expiry_date = forms.DateField(widget=FengyuanChenDatePickerInput())
    billing_start_date = forms.DateField(widget=FengyuanChenDatePickerInput())
    seal = forms.FileField(widget=FileInputCustom, required=False)
    manager_sign = forms.FileField(widget=FileInputCustom, required=False)
    oc_rule = forms.FileField(widget=FileInputCustom, required=False, label="OC Rule")
    meeting_mins = forms.FileField(widget=FileInputCustom, required=False, label="Annual General Meeting Minutes")

    class Meta:
        model = OCMaster
        fields = (
            'title', 'description', 'beg_bal', 'start_date', 'expiry_date', 'property_ref', 'manager_first_name',
            'manager_last_name', 'manager_sign', 'seal', 'manager_threshold', 'chairman_threshold', 'BSB',
            'Account',
            'frequency', 'billing_start_date', 'Account_name', 'liability', 'bank_fee', 'biller_code', 'oc_rule',
            'meeting_mins')

        labels = {
            'title': 'Owner Corporation Name',
            'property_ref': 'Property',
            'manager_first_name': 'First Name(Manager)',
            'manager_last_name': 'Last Name(Manager)',
            'billing_start_date': 'Start Date(Billing)',
            'Account': 'Account Code',
            'Account_name': 'Account Name',
            'manager_sign': 'Manager Signature',
            'seal': 'Company Seal',
            'beg_bal': 'Beginning Balance',
            'liability': 'OC Liability',
            'bank_fee': 'Bank Plan Fee'

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-md-3 mb-0'),
                Column('description', css_class='form-group col-md-3 mb-0'),
                Column('property_ref', css_class='form-group col-md-3 mb-0'),
                Column('frequency', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('start_date', css_class='form-group col-md-3 mb-0'),
                Column('expiry_date', css_class='form-group col-md-3 mb-0'),
                Column('billing_start_date', css_class='form-group col-md-3 mb-0'),
                Column('biller_code', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('manager_first_name', css_class='form-group col-md-2 mb-0'),
                Column('manager_last_name', css_class='form-group col-md-2 mb-0'),
                Column('manager_sign', css_class="form-group col-md-2 mb-0 form-control-file"),
                Column('oc_rule', css_class="form-group col-md-2 mb-0 form-control-file"),
                Column('meeting_mins', css_class="form-group col-md-2 mb-0 form-control-file"),

                css_class='form-row'
            ),
            Row(
                Column('Account_name', css_class='form-group col-md-3 mb-0'),
                Column('Account', css_class='form-group col-md-3 mb-0'),
                Column('BSB', css_class='form-group col-md-3 mb-0'),
                Column('seal', css_class='form-group col-md-3 mb-0 '),

                css_class='form-row'
            ),
            Row(
                Column('manager_threshold', css_class='form-group col-md-3 mb-0'),
                Column('chairman_threshold', css_class='form-group col-md-3 mb-0'),
                Column('beg_bal', css_class='form-group col-md-2 mb-0'),
                Column('liability', css_class='form-group col-md-2 mb-0'),
                Column('bank_fee', css_class='form-group col-md-2 mb-0'),

                css_class='form-row'
            ),
            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-primary',
                   onclick="window.location.href = '{}';".format(reverse('property:oc_list')))
        )


class OcCreateForm(forms.ModelForm):
    start_date = forms.DateField(widget=FengyuanChenDatePickerInput())
    expiry_date = forms.DateField(widget=FengyuanChenDatePickerInput())
    billing_start_date = forms.DateField(widget=FengyuanChenDatePickerInput())
    seal = forms.FileField(widget=FileInputCustom, required=False)
    manager_sign = forms.FileField(widget=FileInputCustom, required=False)
    oc_rule = forms.FileField(widget=FileInputCustom, required=False, label="OC Rule")
    meeting_mins = forms.FileField(widget=FileInputCustom, required=False, label="Annual General Meeting Minutes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-md-3 mb-0'),
                Column('description', css_class='form-group col-md-3 mb-0'),
                Column('property_ref', css_class='form-group col-md-3 mb-0'),
                Column('frequency', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('start_date', css_class='form-group col-md-3 mb-0'),
                Column('expiry_date', css_class='form-group col-md-3 mb-0'),
                Column('billing_start_date', css_class='form-group col-md-3 mb-0'),
                Column('biller_code', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('manager_first_name', css_class='form-group col-md-2 mb-0'),
                Column('manager_last_name', css_class='form-group col-md-2 mb-0'),
                Column('manager_sign', css_class="form-group col-md-2 mb-0 form-control-file"),
                Column('oc_rule', css_class="form-group col-md-2 mb-0 form-control-file"),
                Column('meeting_mins', css_class="form-group col-md-2 mb-0 form-control-file"),

                css_class='form-row'
            ),
            Row(
                Column('Account_name', css_class='form-group col-md-3 mb-0'),
                Column('Account', css_class='form-group col-md-3 mb-0'),
                Column('BSB', css_class='form-group col-md-3 mb-0'),
                Column('seal', css_class='form-group col-md-3 mb-0 '),

                css_class='form-row'
            ),
            Row(
                Column('manager_threshold', css_class='form-group col-md-3 mb-0'),
                Column('chairman_threshold', css_class='form-group col-md-3 mb-0'),
                Column('beg_bal', css_class='form-group col-md-2 mb-0'),
                Column('liability', css_class='form-group col-md-2 mb-0'),
                Column('bank_fee', css_class='form-group col-md-2 mb-0'),

                css_class='form-row'
            ),
            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-primary',
                   onclick="window.location.href = '{}';".format(reverse('property:oc_list')))

        )

    class Meta:
        model = OCMaster
        fields = (
            'title', 'description', 'beg_bal', 'start_date', 'expiry_date', 'property_ref', 'manager_first_name',
            'manager_last_name', 'manager_sign', 'seal', 'manager_threshold', 'chairman_threshold', 'BSB', 'Account',
            'frequency', 'billing_start_date', 'Account_name', 'liability', 'bank_fee', 'biller_code')

        labels = {
            'title': 'Owner Corporation Name',
            'property_ref': 'Property',
            'manager_first_name': 'First Name(Manager)',
            'manager_last_name': 'Last Name(Manager)',
            'billing_start_date': 'Start Date(Billing)',
            'Account': 'Account Code',
            'Account_name': 'Account Name',
            'manager_sign': 'Manager Signature',
            'seal': 'Company Seal',
            'beg_bal': 'Beginning Balance',
            'liability': 'OC Liability',
            'bank_fee': 'Bank Plan Fee',
            # 'oc_rule': 'OC Rules',
            # 'meeting_mins': 'Annual General Meeting Minutes'

        }


class LotOcCreateForm(forms.ModelForm):
    property = forms.ModelChoiceField(queryset=Property.objects.all())
    total_liability = forms.DecimalField(initial=0, disabled=True, label='Total Liability', required=False)
    entitlement = forms.IntegerField(initial=0, required=True)
    liability = forms.IntegerField(initial=0, required=True)

    class Meta:
        model = LotOCMap
        fields = ('oc_ref', 'lot_ref', 'entitlement', 'liability', 'CRN')

        labels = {
            'oc_ref': 'OC Name',
            'lot_ref': 'Lot Name',
            'CRN': 'Client Reference No.(BPAY)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('property', css_class='form-group col-md-4 mb-0'),
                Column('oc_ref', css_class='form-group col-md-4 mb-0'),
                Column('lot_ref', css_class='form-group col-md-4 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('total_liability', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),

            Row(
                Column('entitlement', css_class='form-group col-md-3 mb-0'),
                Column('liability', css_class='form-group col-md-3 mb-0'),
                Column('CRN', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),

            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-primary',
                   onclick="window.location.href = '{}';".format(reverse('property:lotoc_list')))
        )


class OcBudCreateForm(forms.ModelForm):
    property = forms.ModelChoiceField(queryset=Property.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('property', css_class='form-group col-md-4 mb-0'),
                Column('oc_ref', css_class='form-group col-md-4 mb-0'),
                Column('fin_year', css_class='form-group col-md-4 mb-0'),

                css_class='form-row'
            ),
            'ref',

            Row(
                Column('acc_code', css_class='form-group col-md-3 mb-0'),
                Column('acc_name', css_class='form-group col-md-3 mb-0'),
                Column('amount', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),

            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-primary',
                   onclick="window.location.href = '{}';".format(reverse('property:oc_budget_list')))
        )

    class Meta:
        model = OcBudget
        fields = ('oc_ref', 'fin_year', 'acc_code', 'acc_name', 'amount')

        labels = {
            'oc_ref': 'OC Name',
            'fin_year': 'Finance Year',
            'acc_code': 'Account Code',
            'acc_name': 'Account Name',
            'amount': 'Amount',

        }
