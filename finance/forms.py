from django.urls import reverse
from property.models import Property

from .models import *
from django import forms
from base.cust_widgets import FengyuanChenDatePickerInput, FileInputCustom
import datetime
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Button, HTML

ATTACH_LIST = [('oc_rule', 'copy of the Rules of the Owners Corporation'), ('statement',
                                                                            'statement in the prescribed form providing advice and information to prospective purchasers and lot owners.'),
               ('last_agm', 'copy of the Minutes of the last Annual General Meeting '),
               ('fs', 'a copy of the annual financial report as of date'),
               ('currency', 'copy of Certificate of Currency')]


class COACreateForm(forms.ModelForm):
    class Meta:
        model = COA
        fields = (
            'acc_code', 'acc_name', 'category', 'account_level1', 'account_level2', 'is_gst_output', 'is_gst_input')

        labels = {
            'acc_code': 'Account Code',
            'acc_name': 'Account Name',
            'account_level1': 'Account Level 1',
            'account_level2': 'Account Level 2',
            'is_gst_output': 'GST Output Flag',
            'is_gst_input': 'GST Input Flag'

        }


class IncCreateForm(forms.ModelForm):
    class Meta:
        model = IncomeExp
        fields = (
            'name', 'income_expense_code', 'category', 'debit_acc', 'credit_acc', 'is_gst_output', 'is_deferred')

        labels = {
            'name': 'Income Expense Name',
            'income_expense_code': 'Income Expense Code',
            'debit_acc': 'Debit Account Code',
            'credit_acc': 'Credit Account Code',
            'is_deferred': 'Deferral Expense Flag',
            'is_gst_output': 'GST Output Applicable',

        }


class SupplierCreateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-3 mb-0'),
                Column('address', css_class='form-group col-md-3 mb-0'),
                Column('exp_ref', css_class='form-group col-md-3 mb-0'),
                Column('type_supply', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            'description',
            Row(
                Column('suburb', css_class='form-group col-md-4 mb-0'),
                Column('post_code', css_class='form-group col-md-4 mb-0'),
                Column('description', css_class='form-group col-md-4 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('contact_person', css_class='form-group col-md-3 mb-0'),
                Column('contact_num', css_class='form-group col-md-3 mb-0'),
                Column('contact_email', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ), Row(
                Column('ABN', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),

            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-secondary',
                   onclick="window.location.href = '{}';".format(reverse('finance:supply_list')))
        )

    class Meta:
        model = Supplier
        fields = (
            'name', 'address', 'suburb', 'post_code', 'type_supply', 'ABN', 'description', 'exp_ref', 'contact_person'
            , 'contact_num', 'contact_email')

        labels = {
            'type_supply': 'Supplier Type',
            'exp_ref': 'Expense Type',
            'contact_person': 'Contact Person',
            'contact_num': 'Contact Number',
            'contact_email': 'Contact Email',
            'payment_acc': 'Payment Account',

        }


class InvoiceCreateForm(forms.ModelForm):
    property = forms.ModelChoiceField(queryset=Property.objects.all())
    inv_date = forms.DateField(widget=FengyuanChenDatePickerInput(), label='Invoice Date')
    defer_from = forms.DateField(widget=FengyuanChenDatePickerInput(), label='Defer from',
                                 required=False)
    defer_to = forms.DateField(widget=FengyuanChenDatePickerInput(), label='Defer to',
                               required=False)
    attachment = forms.FileField(widget=FileInputCustom, required=False, help_text="PDF or Excel")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('property', css_class='form-group col-md-4 mb-0'),
                Column('oc_ref', css_class='form-group col-md-4 mb-0'),
                Column('supplier_ref', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'ref',

            Row(
                Column('inv_num', css_class='form-group col-md-3 mb-0'),
                Column('inv_date', css_class='form-group col-md-3 mb-0'),
                Column('exp_ref', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('amount', css_class='form-group col-md-3 mb-0'),
                Column('input_gst', css_class='form-group col-md-3 mb-0'),
                Column('attachment', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('defer_from', css_class='form-group col-md-3 mb-0'),
                Column('defer_periods', css_class='form-group col-md-3 mb-0'),

                css_class='form-row'
            ),

            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-primary',
                   onclick="window.location.href = '{}';".format(reverse('finance:invoice_list')))
        )

    class Meta:
        model = Invoice
        fields = (
            'inv_date', 'inv_num', 'ref', 'supplier_ref', 'due_date', 'amount', 'input_gst',
            'exp_ref', 'oc_ref', 'defer_from', 'defer_to', 'attachment', 'defer_periods')

        labels = {
            'inv_num': 'Invoice Number',
            'ref': 'Description',
            'exp_ref': 'Expense Type',
            'oc_ref': 'OC',
            'supplier_ref': 'Supplier',
            'due_date': 'Due Date',
            'amount': 'Amount(GST exclusive)',
            'input_gst': 'Input GST',
            'defer_periods': 'Amortization Period'

        }


class BillingCreateForm(forms.ModelForm):
    property = forms.ModelChoiceField(queryset=Property.objects.all())
    billing_from = forms.DateField(widget=FengyuanChenDatePickerInput)
    billing_to = forms.DateField(widget=FengyuanChenDatePickerInput)
    due_date = forms.DateField(widget=FengyuanChenDatePickerInput, required=False)
    billing_date = forms.DateField(widget=FengyuanChenDatePickerInput)
    income_ref = forms.ModelChoiceField(queryset=IncomeExp.objects.filter(income_expense_code__startswith="IS1"),
                                        label="Income Type")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            # Row(
            #     Column('billing_num', css_class='form-group col-md-12 mb-0'),
            #
            #     css_class='form-row'
            # ),
            Row(
                Column('property', css_class='form-group col-md-4 mb-0'),
                Column('oc_ref', css_class='form-group col-md-4 mb-0'),
                Column('lot_ref', css_class='form-group col-md-4 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('billing_amount', css_class='form-group col-md-5 mb-0'),
                Column('collected_amount', css_class='form-group col-md-5 mb-0'),

                css_class='form-row'
            ),
            'desc',
            Row(
                Column('income_ref', css_class='form-group col-md-3 mb-0'),
                Column('billing_from', css_class='form-group col-md-3 mb-0'),
                Column('billing_to', css_class='form-group col-md-3 mb-0'),
                Column('billing_date', css_class="form-group col-md-3 mb-0"),

                css_class='form-row'
            ),
            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-primary',
                   onclick="window.location.href = '{}';".format(reverse('finance:billing_list')))
        )

    class Meta:
        model = Billing
        fields = (
            # 'billing_num',
            'lot_ref', 'billing_amount', 'collected_amount', 'billing_from', 'billing_to',
            'desc',
            'billing_date', 'oc_ref')

        labels = {
            'billing_num': 'Billing No.',
            'lot_ref': 'Lot No.',
            'oc_ref': 'OC',
            'desc': 'Description'

        }


class OcCreateForm(forms.ModelForm):
    property = forms.ModelChoiceField(queryset=Property.objects.all())
    special_fee = forms.CharField(required=False, initial='Nil',
                                  widget=forms.TextInput(
                                      attrs={'placeholder': 'No special fees or levies have been struck except:'}))
    additional_charge = forms.CharField(required=False, initial='Nil', widget=forms.TextInput(attrs={
        'placeholder': 'The Owners Corporation has not performed and is not about to perform any repairs, or other work which may incur additional charges to those set out above except the following:'}))
    issue_date = forms.DateField(widget=FengyuanChenDatePickerInput)
    additional_liability = forms.CharField(required=False, initial='Nil', widget=forms.TextInput(attrs={
        'placeholder': 'The Owners Corporation has no liabilities in addition to any liabilities shown above except the following'}))
    affect_common_property = forms.CharField(required=False, initial='Nil',
                                             widget=forms.TextInput(attrs={
                                                 'placeholder': 'The Owners Corporation has no current contracts, leases, licenses or agreements affecting the common'}))
    cur_agreement = forms.CharField(required=False, initial='Nil', widget=forms.TextInput(
        attrs={'placeholder': 'The Owners Corporation has no current agreements to provide services to lot owners'}))
    non_statisfy_order = forms.CharField(required=False, initial='Nil', widget=forms.TextInput(
        attrs={
            'placeholder': 'There have been no notices or orders served on the Owners Corporation in the last 12 months that have not been satisfied '}))
    legal_proceeding = forms.CharField(required=False, initial='Nil', widget=forms.TextInput(
        attrs={
            'placeholder': 'The Owners Corporation is not a party to any legal proceedings or aware of any circumstances'}))

    attachment_list = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=ATTACH_LIST,

    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('property', css_class='form-group col-md-5 mb-0'),
                Column('oc_ref', css_class='form-group col-md-5 mb-0'),

                css_class='form-row'),
            Row(
                Column('lot_ref', css_class='form-group col-md-4 mb-0'),
                Column('issue_date', css_class="form-group col-md-4 mb-0"),
                Column('applicant', css_class="form-group col-md-4 mb-0"),

                css_class='form-row'),
            'special_fee',
            'additional_charge',
            'additional_liability',
            'affect_common_property',
            'cur_agreement',
            'non_statisfy_order',
            'legal_proceeding',
            Row(
                Column('attachment_list', css_class='form-group col-md-4 mb-0'),

                css_class='form-row'),
            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-primary',
                   onclick="window.location.href = '{}';".format(reverse('finance:oc_cert_list')))
        )

    class Meta:
        model = Occertificate
        fields = (
            'oc_ref', 'lot_ref', 'special_fee', 'additional_charge', 'additional_liability',
            'affect_common_property', 'cur_agreement', 'applicant')

        labels = {
            'oc_ref': 'OC',
            'lot_ref': 'Lot No.',
            # 'issue_date': 'Issue Date',
            'special_fee': 'Special fees or levies',
            'additional_charge': 'Additional Charge',
            'additional_liability': "OC's additional liability",
            'affect_common_property': 'Current agreements affecting common property',
            'cur_agreement': 'Current services agreements',
            'applicant': 'Applicant',
        }


class GLForm(forms.Form):
    property = forms.ModelChoiceField(queryset=Property.objects.all())
    oc_ref = forms.ModelChoiceField(queryset=OCMaster.objects.all(), label='OC')
    amount = forms.DecimalField(max_digits=20, decimal_places=2, initial=0.00)
    input_gst_amt = forms.DecimalField(max_digits=20, decimal_places=2, initial=0.00, required=False)
    inc_exp = forms.ModelChoiceField(queryset=IncomeExp.objects.all(), label="Income Expense Type")
    desc = forms.CharField(max_length=100, label="Description")
    posting_date = forms.DateField(initial=datetime.date.today(),
                                   widget=FengyuanChenDatePickerInput)

    def clean(self):
        cleaned_data = super(GLForm, self).clean()
        oc = cleaned_data.get('oc_ref')
        if not oc:
            raise forms.ValidationError('oc could not be none')


class InvoiceForm(forms.Form):
    invoice_id = forms.IntegerField(widget=forms.HiddenInput(), disabled=True)
    invoice = forms.CharField(max_length=100, label="Invoice Number", disabled=True)
    bal_amount = forms.DecimalField(max_digits=20, decimal_places=2, disabled=True)
    payment_amount = forms.DecimalField(max_digits=20, decimal_places=2, initial=0.00)


class FsForm(forms.ModelForm):
    from_date = forms.DateField(widget=FengyuanChenDatePickerInput, label="Start Date",
                                required=False)
    to_date = forms.DateField(widget=FengyuanChenDatePickerInput, label="End Date")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('property_ref', css_class='form-group col-md-5 mb-0'),
                Column('oc_ref', css_class='form-group col-md-5 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('fin_year', css_class='form-group col-md-4 mb-0'),
                Column('from_date', css_class='form-group col-md-4 mb-0'),
                Column('to_date', css_class='form-group col-md-4 mb-0'),

                css_class='form-row'
            ),

            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-secondary',
                   onclick="window.location.href = '{}';".format(reverse('finance:fs_list')))
        )

    class Meta:
        model = FS
        fields = (
            'property_ref', 'oc_ref', 'fin_year', 'to_date', 'from_date')

        labels = {
            'property_ref': 'Property',
            'oc_ref': 'OC',
            'fin_year': 'Financial year',

        }


class specialLevyForm(forms.Form):
    LEVY_TYPE = (('operating', 'operating'), ('special', 'special'), ('maintenance', 'maintenance'))

    property_ref = forms.ModelChoiceField(queryset=Property.objects.all(), label="Property")
    oc_ref = forms.ModelChoiceField(queryset=OCMaster.objects.all(), label="OC")
    # financial_year = forms.IntegerField(label="Financial year")
    total_budget = forms.DecimalField(max_digits=10, decimal_places=2)
    rev_type = forms.ChoiceField(choices=LEVY_TYPE, label="Billing Type")
    desc = forms.CharField(max_length=200, label="Description",
                           widget=forms.Textarea(attrs={'rows': '4', 'columns': '5'})
                           )
    billing_date = forms.DateField(widget=FengyuanChenDatePickerInput, label="Billing Date")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row('property_ref', css_class="form-group col-md-4 mb-0"),
            Row('oc_ref', css_class="form-group col-md-4 mb-0"),

            Row('rev_type', css_class="form-group col-md-3 mb-0"),
            Row('total_budget', css_class="form-group col-md-3 mb-0"),
            Row('billing_date', css_class="form-group col-md-3 mb-0"),
            Row('desc', css_class="form-group col-md-8 mb-0"),
            # 'desc',
            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-secondary',
                   onclick="window.location.href = '{}';".format(reverse('base:base_index'))))
