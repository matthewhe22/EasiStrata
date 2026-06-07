from django.contrib.auth.models import User
from django import forms
from django.urls import reverse
from finance.models import Supplier
from .models import Client, DataSource
from property.models import Property, OCMaster
from datetime import date
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Button, HTML
from base.cust_widgets import FileInputCustom


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta():
        model = User
        fields = ('password', 'username', 'first_name', 'last_name', 'email', 'is_active', 'is_superuser', 'is_staff')
        template = 'base/new_user.html'


class UserUpdateForm(forms.ModelForm):
    # ONLY list the field subject to read only
    username = forms.CharField(disabled=True)

    class Meta():
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active', 'is_superuser', 'is_staff')

        model = User


# test for fileupload
class UploadFileForm(forms.Form):
    client_code = forms.ModelChoiceField(queryset=Client.objects.all())
    data_source = forms.ModelChoiceField(queryset=DataSource.objects.all())
    property = forms.ModelChoiceField(queryset=Property.objects.all())
    oc_ref = forms.ModelChoiceField(label="Owners Corporation", queryset=OCMaster.objects.all())
    fin_year = forms.IntegerField(initial=date.today().year, required=False, label="Financial year")
    docfile = forms.FileField(label="File", help_text='Excel file only', widget=FileInputCustom)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('client_code', css_class='form-group col-md-5 mb-0'),
                Column('data_source', css_class='form-group col-md-4 mb-0'),

                css_class='form-row'
            ),
            Row(
                Column('property', css_class='form-group col-md-4 mb-0'),
                Column('oc_ref', css_class='form-group col-md-4 mb-0'),
                Column('fin_year', css_class='form-group col-md-4 mb-0'),

                css_class='form-row'
            ), Row(
                Column('docfile', css_class='form-group col-md-4 mb-0'),

                css_class='form-row'
            ),

            Submit('submit', 'Upload')
        )


class DsCreateForm(forms.ModelForm):
    class Meta:
        model = DataSource
        fields = ('data_src', 'filetype', 'sheet_mode', 'sheet_name', 'db_table')
        labels = {'data_src': 'Data source',
                  'filetype': 'File Type',
                  'sheet_mode': 'Sheet Mode',
                  'sheet_name': 'Sheet Name',
                  'db_table': 'Backend Table'

                  }


class OwnerNotiForm(forms.Form):
    PURPOSE_CHOICES = [
        ('general', 'General Correspondence'),
        ('owner', 'Owner Notice'),
        ('levy', 'Levy Notice'),

    ]

    property = forms.ModelChoiceField(queryset=Property.objects.all(), label="Property")
    purpose = forms.CharField(widget=forms.Select(choices=PURPOSE_CHOICES))
    title = forms.CharField(max_length=100, label="Notification title",
                            widget=forms.TextInput(attrs={'placeholder': 'Input title here'}))
    body = forms.CharField(label="Notification body",
                           widget=forms.Textarea(attrs={'placeholder': 'Input body here'}))
    cc = forms.CharField(max_length=50, label="Copy to", required=False,
                         widget=forms.TextInput(attrs={'placeholder': 'separate multiple email addresses by comma'}))
    docfile = forms.FileField(label="Attachment", widget=FileInputCustom, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row('property', css_class="form-group col-md-4 mb-0"),
            Row('purpose', css_class="form-group col-md-4 mb-0"),
            'cc',
            'title',
            'body',
            Row('docfile', css_class="form-group col-md-4 mb-0"),
            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-secondary',
                   onclick="window.location.href = '{}';".format(reverse('base:base_index'))))


class VendorNotiForm(forms.Form):
    vendor = forms.ModelChoiceField(queryset=Supplier.objects.all(), label="Vendor")
    title = forms.CharField(max_length=100, label="Notification title",
                            widget=forms.TextInput(attrs={'placeholder': 'Input title here'}))
    body = forms.CharField(max_length=500, label="Notification body",
                           widget=forms.Textarea(attrs={'placeholder': 'Input body here'}))
    docfile = forms.FileField(label="Attachment", widget=FileInputCustom, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row('vendor', css_class="form-group col-md-4 mb-0"),
            'title',
            'body',
            Row('docfile', css_class="form-group col-md-4 mb-0"),
            Submit('submit', 'Submit'),
            Button('cancel', 'Cancel', css_class='btn-secondary',
                   onclick="window.location.href = '{}';".format(reverse('base:base_index')))
        )
