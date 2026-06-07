from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views as p_view

app_name='property'
urlpatterns=[
path('property/', p_view.PropertyListView.as_view(), name='property_list'),
path('property/create', p_view.PropertyCreateView.as_view(), name='property_create'),
path('property/delete', p_view.property_delete, name='property_delete'),
path('prop/update/<int:pk>', p_view.PropertyUpdateView.as_view(), name='property_update'),
path('lot/', p_view.LotListView.as_view(), name='lot_list'),
    path('lot/create', p_view.LotCreateView.as_view(), name='lot_create'),
    path('lot/delete', p_view.lot_delete, name='lot_delete'),
    path('lot/update/<int:pk>', p_view.LotUpdateView.as_view(), name='lot_update'),
    path('oc/', p_view.OcListView.as_view(), name='oc_list'),
    path('oc/create', p_view.OcCreateView.as_view(), name='oc_create'),
    path('oc/delete', p_view.oc_delete, name='oc_delete'),
    path('oc/update/<int:pk>', p_view.OcUpdateView.as_view(), name='oc_update'),
    path('ocbudget/', p_view.OcBudListView.as_view(), name='oc_budget_list'),
    path('ocbudgetsum/', p_view.property_budget_sum, name='oc_budget_sum'),
    path('ocbudget/copy', p_view.init_new_budget, name='init_new_budget'),
    path('ocbudget/create', p_view.OcBudCreateView.as_view(), name='oc_budget_create'),
    path('ocbudget/delete', p_view.oc_budget_delete, name='oc_budget_delete'),
    path('ocbudget/update/<int:pk>', p_view.OcBudUpdateView.as_view(), name='oc_budget_update'),
    path('lotoc/', p_view.LotOcListView.as_view(), name='lotoc_list'),
    path('lotoc/create', p_view.LotOcCreateView.as_view(), name='lotoc_create'),
    path('lotoc/delete', p_view.lot_oc_delete, name='lotoc_delete'),
    path('lotoc/update/<int:pk>', p_view.LotOcUpdateView.as_view(), name='lotoc_update'),
    path('ajax/getoc', p_view.get_oc, name='get_oc'),
    path('ajax/getlot', p_view.get_lot, name='get_lot'),
    path('ajax/getlotfromoc', p_view.get_lot_from_oc, name='get_lot_from_oc'),
    path('ajax/getproperty', p_view.get_property, name='get_property'),
    path('ajax/getliability', p_view.get_liability, name='get_liability'),
    path('notification/', p_view.notify_list, name='notify_log'),

]
