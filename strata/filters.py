import django_filters
from django.db.models import Q

from .models import *

from base.cust_widgets import FengyuanChenDatePickerInput


class InsureFilter(django_filters.FilterSet):
    due_date = django_filters.DateFilter(field_name='date_to', lookup_expr='lte', label="Due Date(Before)",
                                         widget=FengyuanChenDatePickerInput)

    class Meta:
        model = Insurance
        fields = ['policy_num', 'property_ref', 'company_name']


class AgmFilter(django_filters.FilterSet):
    fyear = django_filters.NumberFilter(field_name='fyear', label='Financial Year End')

    class Meta:
        model = AGM
        fields = ['property_ref', 'oc_ref', 'fyear']
