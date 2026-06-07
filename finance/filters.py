import django_filters
from django.db.models import Q

from .models import *
from property.models import Property, OCMaster, LotOCMap
from base.cust_widgets import FengyuanChenDatePickerInput


class GLFilter(django_filters.FilterSet):
    posting_gt = django_filters.DateFilter(field_name='posting_date', lookup_expr='gte', label="Posting Date(from)",
                                           widget=FengyuanChenDatePickerInput)
    posting_lt = django_filters.DateFilter(field_name='posting_date', lookup_expr='lte', label="Posting Date(to)",
                                           widget=FengyuanChenDatePickerInput)

    class Meta:
        model = GL
        fields = ['oc_ref', 'unpresent_flag', 'doc_num']


class GLReconFilter(django_filters.FilterSet):
    posting_gt = django_filters.DateFilter(field_name='posting_date', lookup_expr='gte', label="Posting Date(from)",
                                           widget=FengyuanChenDatePickerInput)
    posting_lt = django_filters.DateFilter(field_name='posting_date', lookup_expr='lte', label="Posting Date(to)",
                                           widget=FengyuanChenDatePickerInput)

    class Meta:
        model = GL
        fields = ['oc_ref', 'unpresent_flag', 'doc_num']

    @property
    def qs(self):
        parent = super(GLReconFilter, self).qs
        # author = getattr(self.request, 'user', None)

        return parent.filter(acc_code="BS300000")


class OcCertFilter(django_filters.FilterSet):
    date_gt = django_filters.DateFilter(field_name='issue_date', lookup_expr='gte', label="Date(from)",
                                        widget=FengyuanChenDatePickerInput)
    date_lt = django_filters.DateFilter(field_name='issue_date', lookup_expr='lte', label="Date(to)",
                                        widget=FengyuanChenDatePickerInput)

    property = django_filters.ModelChoiceFilter(queryset=Property.objects.all(), label="Property",
                                                method="property_oc_filter")

    def property_oc_filter(self, queryset, name, value):
        # value is a object

        oc_list = OCMaster.objects.filter(property_ref_id=value.id).values('id')
        oc_id = []
        for item in oc_list:
            oc_id.append(item ['id'])
        return queryset.filter(Q(oc_ref_id__in=oc_id))

    class Meta:
        model = Occertificate
        fields = ['oc_ref']


class VendorFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", label='Name', lookup_expr="icontains")
    type_supply = django_filters.CharFilter(field_name="type_supply", label='Type of supplier', lookup_expr="icontains")

    class Meta:
        model = Supplier
        fields = ['type_supply']


class FsFilter(django_filters.FilterSet):
    class Meta:
        model = FS
        fields = "__all__"


class InvFilter(django_filters.FilterSet):
    PAY_SAT = [('paid', 'paid'), ('unpaid', 'unpaid')]
    date_gt = django_filters.DateFilter(field_name='inv_date', lookup_expr='gte', label="Invoice date(from)",
                                        widget=FengyuanChenDatePickerInput)
    date_lt = django_filters.DateFilter(field_name='inv_date', lookup_expr='lte', label="Invoice date(to)",
                                        widget=FengyuanChenDatePickerInput)
    property = django_filters.ModelChoiceFilter(queryset=Property.objects.all(), label="Property",
                                                method="property_oc_filter")
    inv_num = django_filters.CharFilter(field_name="inv_num", label="Invoice No.", lookup_expr='icontains')
    payment_status = django_filters.ChoiceFilter(field_name="payment_status", label="Payment Status", initial="unpaid",
                                                 choices=PAY_SAT)

    def property_oc_filter(self, queryset, name, value):
        # value is a object

        oc_list = OCMaster.objects.filter(property_ref_id=value.id).values('id')
        oc_id = []
        for item in oc_list:
            oc_id.append(item ['id'])
        return queryset.filter(Q(oc_ref_id__in=oc_id)).order_by('-inv_date')

    class Meta:
        model = Invoice
        fields = {
            'supplier_ref': ['exact', ],
            'payment_status': ['exact', ],

        }


class CashFilter(django_filters.FilterSet):
    date_gt = django_filters.DateFilter(field_name='recpt_date', lookup_expr='gte', label="Receipt date(from)",
                                        widget=FengyuanChenDatePickerInput)
    date_lt = django_filters.DateFilter(field_name='recpt_date', lookup_expr='lte', label="Receipt date(to)",
                                        widget=FengyuanChenDatePickerInput)
    property_ref = django_filters.ModelChoiceFilter(queryset=Property.objects.all(), label="Property",
                                                    method="property_lot_filter")
    lot_ref = django_filters.ModelChoiceFilter(queryset=Lot.objects.all(), label="Lot")
    recpt_num = django_filters.CharFilter(field_name="recpt_no", label="Receipt No.", lookup_expr='icontains')

    def property_lot_filter(self, queryset, name, value):
        return queryset.filter(Q(lot_ref__property_ref_id=value.id)).order_by('-recpt_no')

    class Meta:
        model = CashReceipt
        fields = ['reference', 'description']


class BankFilter(django_filters.FilterSet):
    date_gt = django_filters.DateFilter(field_name='trans_date', lookup_expr='gte', label="Transaction date(from)",
                                        widget=FengyuanChenDatePickerInput)
    date_lt = django_filters.DateFilter(field_name='trans_date', lookup_expr='lte', label="Transaction date(to)",
                                        widget=FengyuanChenDatePickerInput)
    property_ref = django_filters.ModelChoiceFilter(queryset=Property.objects.all(), label="Property",
                                                    method="property_oc_filter")
    oc_ref = django_filters.ModelChoiceFilter(queryset=OCMaster.objects.all(), label="OC",
                                              method="oc_filter")
    # oc_ref=django_filters.ChoiceFilter(field_name='oc_ref',label='OC')
    narrative = django_filters.CharFilter(field_name="narrative", label="Narrative", lookup_expr='icontains')
    acc_num = django_filters.CharFilter(field_name="acc_num", label="Account No", lookup_expr='icontains')

    def property_oc_filter(self, queryset, name, value):
        return queryset.filter(Q(oc_ref__property_ref_id=value.id))

    def oc_filter(self, queryset, name, value):
        return queryset.filter(Q(oc_ref_id=value.id))

    @property
    def qs(self):
        parent = super().qs
        return parent.filter(amount__gt=0).order_by('-trans_date')

    class Meta:
        model = BankTrans
        fields = ['narrative', 'acc_num']


class ClientLedgerFilter(django_filters.FilterSet):
    date_gt = django_filters.DateFilter(field_name='trans_date', lookup_expr='gte', label="Trans Date(from)",
                                        widget=FengyuanChenDatePickerInput)
    date_lt = django_filters.DateFilter(field_name='trans_date', lookup_expr='lte', label="Trans Date(to)",
                                        widget=FengyuanChenDatePickerInput)
    property_ref = django_filters.ModelChoiceFilter(queryset=Property.objects.all(), label="Property",
                                                    method="property_lot_filter")
    oc_ref = django_filters.ModelChoiceFilter(queryset=OCMaster.objects.all(), label="OC", method="oc_filter")
    lot_ref = django_filters.ModelChoiceFilter(queryset=Lot.objects.all(), label="Lot", method="lot_filter")

    reference = django_filters.CharFilter(field_name="reference", label="Reference", lookup_expr='icontains')
    description = django_filters.CharFilter(field_name="description", label="Description", lookup_expr='icontains')

    def property_lot_filter(self, queryset, name, value):
        # value is a object
        lot_list = LotOCMap.objects.filter(oc_ref__property_ref_id=value.id).values('lot_ref_id')
        lot_ids = []
        for item in lot_list:
            lot_ids.append(item ['lot_ref_id'])
        return queryset.filter(Q(lot_ref_id__in=lot_ids)).order_by('-trans_date')

    def oc_filter(self, queryset, name, value):
        # value is a object

         return queryset.filter(oc_ref_id=value.id).order_by('-trans_date')

    def lot_filter(self, queryset, name, value):
        # value is a object

        return queryset.filter(Q(lot_ref_id=value.id)).order_by('-trans_date')

    class Meta:
        model = ClientLedger
        fields = ['reference', 'description']


class BillFilter(django_filters.FilterSet):
    property = django_filters.ModelChoiceFilter(queryset=Property.objects.all(), label="Property",
                                                method="property_oc_filter")

    date_gt = django_filters.DateFilter(field_name='billing_date', lookup_expr='gte', label="Billing date(from)",
                                        widget=FengyuanChenDatePickerInput)
    date_lt = django_filters.DateFilter(field_name='billing_date', lookup_expr='lte', label="Billing date(to)",
                                        widget=FengyuanChenDatePickerInput)
    oc_ref = django_filters.ModelChoiceFilter(field_name="oc_ref", label="OC", queryset=OCMaster.objects.all())
    billing_num = django_filters.CharFilter(field_name="billing_num", label="Billing No.", lookup_expr='icontains')
    agent = django_filters.CharFilter(label="Agent", method="agent_filter")
    unit = django_filters.CharFilter(label="Unit", method="unit_filter")
    special = django_filters.BooleanFilter(field_name="special_flag", label="Special Levy")

    def property_oc_filter(self, queryset, name, value):
        # value is a object

        oc_list = OCMaster.objects.filter(property_ref_id=value.id).values('id')
        oc_id = []
        for item in oc_list:
            oc_id.append(item ['id'])
        return queryset.filter(Q(oc_ref_id__in=oc_id)).order_by('-billing_num')

    def agent_filter(self, queryset, name, value):
        lot_list = Lot.objects.filter(agent_contact__contains=value).values('id')
        lot_id = []
        for item in lot_list:
            lot_id.append(item ['id'])
        return queryset.filter(Q(lot_ref_id__in=lot_id)).order_by('-billing_num')

    def unit_filter(self, queryset, name, value):
        lot_list = Lot.objects.filter(unit_no__contains=value).values('id')
        lot_id = []
        for item in lot_list:
            lot_id.append(item ['id'])
        return queryset.filter(Q(lot_ref_id__in=lot_id)).order_by('-billing_num')

    class Meta:
        model = Billing
        fields = {'oc_ref': ['exact', ],
                  'status': ['exact', ], }
