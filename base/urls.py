from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views as base_view

    
app_name='base'

urlpatterns=[
    path('',base_view.IndexView.as_view(),name='base_index'),
    path('user_login/',base_view.user_login,name='login'),
    path('user_logout/',base_view.user_logout,name='logout'),
    path('owner_notify/',base_view.owner_notify,name='owner_notify'),
    path('vendor_notify/',base_view.vendor_notify,name='vendor_notify'),
    path('user/',base_view.UserListView.as_view(),name='user_list'),
    path('user/create',base_view.user_create,name='user_create'),
    path('user/update/<int:pk>',base_view.UserUpdateView.as_view(),name='user_update'),
    path('client/',base_view.ClientListView.as_view(),name='client_list'),
    path('client/create',base_view.ClientCreateView.as_view(),name='client_create'),
    path('client/update/<int:pk>',base_view.ClientUpdateView.as_view(),name='client_update'),    
    path('ds/',base_view.DsListView.as_view(),name='ds_list'),
    path('ds/create', base_view.DsCreateView.as_view(), name='ds_create'),
    path('ds/update/<int:pk>', base_view.DsUpdateView.as_view(), name='ds_update'),
    path('import/', base_view.run_import, name='import'),
    path('ds_rule/', base_view.DsRuleListView.as_view(), name='ds_rule'),
    path('ds_rule/create', base_view.DsRuleCreateView.as_view(), name='ds_rule_create'),
    path('ds_rule/delete', base_view.ds_rule_delete, name='ds_rule_delete'),
    path('ds_rule/update/<int:pk>', base_view.DsRuleUpdateView.as_view(), name='ds_rule_update'),
    path('job/', base_view.JobListView.as_view(), name='job_list'),
    path('job/delete', base_view.job_delete, name='job_delete'),
    path('alert/', base_view.AltertListView.as_view(), name='alert_list'),
    path('owner/', base_view.OwnerView.as_view(), name='owner_info'),

    # ajax request
    path('ajax/get_ds', base_view.ajax_get_ds_list, name='ajax_get_ds'),
    path('ajax/get_pie', base_view.get_lotnum_pie, name='ajax_get_pie'),
    path('ajax/get_rev', base_view.get_revenue, name='ajax_get_rev'),
    path('ajax/notify', base_view.get_user_notification, name='ajax_notify'),
    path('ajax/read_alert', base_view.read_alert, name='read_alert'),
    path('ajax/oc_sched_init', base_view.oc_billing_init, name='oc_billing_init'),


    
]
