import django_filters
# from property.models import
from property.models import Property


class PropertyFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", label='Property Name', lookup_expr="icontains")
    suburb = django_filters.CharFilter(field_name="suburb", label='Suburb', lookup_expr="icontains")
    state = django_filters.CharFilter(field_name="state", label='State', lookup_expr="icontains")
    post_code = django_filters.CharFilter(field_name="post_code", label='Post code', lookup_expr="icontains")

    class Meta:
        model = Property
        fields = ['name']
