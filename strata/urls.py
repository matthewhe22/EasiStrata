from django.urls import path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views as s_view

app_name = 'strata'

# path('property/create', p_view.PropertyCreateView.as_view(), name='property_create'),
urlpatterns = [
    path('insurance/new', s_view.InsuranceCreateView.as_view(), name='insurance_new'),
    path('insurance/', s_view.InsuranceListView.as_view(), name='insurance_list'),
    path('insurance/update/<int:pk>', s_view.InsuranceUpdateView.as_view(), name='insurance_update'),
    path('insurance/delete', s_view.insurance_delete, name='insurance_del'),
    path('agm/new', s_view.AgmCreateView.as_view(), name='agm_new'),
    path('agm/', s_view.AGMListView.as_view(), name='agm_list'),
    path('agm/update/<int:pk>', s_view.AgmUpdateView.as_view(), name='agm_update'),
    path('agm/pdf/<int:pk>', s_view.Agm2Pdf.as_view(), name='agm_pdf'),
    path('agm/pdfraw/<int:pk>', s_view.GetAgmData.as_view(), name='agm_pdf_raw'),
    path('agm/budgetraw/<int:pk>', s_view.AgmBudget2Pdf.as_view(), name='agm_budget'),
    path('agm/ajax/create', s_view.create_agm_ajax, name='agm_create_ajax'),
    path('agm/ajax/invite', s_view.create_agm_invite_ajax, name='agm_invite_ajax'),
    path('agm/ajax/minutes', s_view.meeting_minutes_upload, name='minutes_upload_ajax'),
    path('agm/ajax/sendinvite', s_view.send_agm_notfication, name='send_agm'),
    path('agm/ajax/del', s_view.agm_delete, name='agm_del'),
    path('agm/agenda', s_view.render_agendas, name='agenda'),
    path('agm/agenda/del', s_view.agenda_del_priority, name='agenda_del'),
    path('agm/agenda/detail', s_view.get_agenda_detail, name='agenda_detail'),
    path('agm/agenda/manage', s_view.agenda_detail_maintain, name='agenda_maintain'),
    path('owner/request/', s_view.OwnerRequestListView.as_view(), name='owner_request'),
    path('owner/request/new', s_view.new_request, name='request_new'),

]
