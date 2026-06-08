import logging

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from my_project.weasy_compat import WeasyTemplateResponseMixin
from my_project import settings
from scripts.agm.budget import AgmOCBudget
from scripts.agm.agm_notice import AGMItem
from scripts.agm.agm_master import generate_agm_pdf
# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from scripts.notification.Notify import Notify
from .filters import *
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView, DetailView, TemplateView
from base.models import Client
from .forms import InsureCreateForm, AgmCreateForm, OwnerRequestForm
from .models import *
from django_filters.views import FilterView
from my_project.agm_config import EMAIL_BODY


class InsuranceCreateView(LoginRequiredMixin, CreateView):
    model = Insurance
    template_name = 'strata/new_insurance.html'
    form_class = InsureCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        return super(InsuranceCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('strata:insurance_list')


class InsuranceUpdateView(LoginRequiredMixin, UpdateView):
    model = Insurance
    template_name = 'strata/new_insurance.html'
    form_class = InsureCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        return super(InsuranceUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('strata:insurance_list')


class InsuranceListView(LoginRequiredMixin, FilterView):
    fields = ('policy_num', 'date_from', 'date_to', 'property_ref', 'company_name', 'premium_amt', 'est_commission',
              'currency_cert')
    template_name = 'strata/insurance_list.html'
    filterset_class = InsureFilter
    paginate_by = 30
    queryset = Insurance.objects.select_related('property_ref')


class AgmCreateView(LoginRequiredMixin, CreateView):
    model = AGM
    template_name = 'strata/new_agm.html'
    form_class = AgmCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref_id = 1

        return super(AgmCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('strata:agm_list')


class AgmUpdateView(LoginRequiredMixin, UpdateView):
    model = AGM
    template_name = 'strata/new_agm.html'
    form_class = AgmCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        return super(AgmUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('strata:agm_list')


class AGMListView(LoginRequiredMixin, FilterView):
    fields = ('property_ref', 'oc_ref', 'meeting_datetime', 'fyear', 'meeting_minutes', 'meeting_invite', 'is_sent')
    template_name = 'strata/agm_list.html'
    filterset_class = AgmFilter
    paginate_by = 30
    queryset = AGM.objects.select_related('property_ref', 'oc_ref')


@csrf_exempt
def create_agm_ajax(request):
    if request.method == "POST":
        try:

            agm_item = AGMItem()
            # agm_item.set_instance_from_request(request)
            result, msg = agm_item.handle(request)
            if agm_item.agm:

                return JsonResponse(
                    data={'result': result, 'msg': msg, 'id': agm_item.id})
            else:
                return JsonResponse(
                    data={'result': result, 'msg': msg})

        except Exception as e:
            logging.exception(e)
            msg = 'save failed due to ' + str(e)
            return JsonResponse(data={'result': 'fail', "msg": msg})


@csrf_exempt
def create_agm_invite_ajax(request):
    if request.method == "POST":
        try:
            id = request.POST.get('agm_id')
            agm_item = AGMItem()
            agm_item.set_instance_from_agm(id, request.user.username)
            result = agm_item.result
            msg = agm_item.msg
            if agm_item.result == "success":
                invite_path = generate_agm_pdf(agm_item)
                agm_item.update_invite_path(invite_path)

            return JsonResponse(
                data={'result': result, 'msg': msg})

        except Exception as e:
            logging.exception(e)
            msg = 'save failed due to ' + str(e)
            return JsonResponse(data={'result': 'fail', "msg": msg})


@csrf_exempt
def send_agm_notfication(request):
    if request.method == "POST":
        try:
            id = request.POST.get('agm_id')
            agm_item = AGMItem()
            agm_item.set_instance_from_agm(id)
            if agm_item.agm.meeting_invite.name:
                title = agm_item.generate_title()

                data = {'property_id': agm_item.property_id,
                        'oc_id': agm_item.oc_id,
                        'title': title,
                        'body': EMAIL_BODY,
                        'note_type': 'agm_owner',
                        'client_id': 1,
                        'user': request.user.username,
                        'purpose': 'owner',
                        'attachment': agm_item.agm.meeting_invite
                        }

                note = Notify()
                note.init_strategy()
                note.notify(data)
                agm_item.agm.is_agm_sent = True
                agm_item.updateby = request.user.username
                agm_item.agm.save()

                return JsonResponse(
                    data={'result': 'success', 'msg': 'notification sent'})

            else:
                return JsonResponse(
                    data={'result': 'failed', 'msg': 'no meeting invite identified'})

        except Exception as e:
            logging.exception(e)
            msg = 'notification sent failed to ' + str(e)
            return JsonResponse(data={'result': 'fail', "msg": msg})


@require_POST
def insurance_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')

        for item in id_list:
            del_item = get_object_or_404(Insurance, pk=int(item))
            del_item.delete()
    return HttpResponseRedirect('/strata/insurance/')


class GetAgmData(TemplateView):
    template_name = settings.AGM_TEMPLATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:

            pk = int(self.kwargs ['pk'])
            agm = AGM.objects.get(id=pk)
            gen_date = agm.createtime
            context = agm.render_agm_context()
            context ['agm'] = agm
            insurance = Insurance.objects.filter(date_from__lte=gen_date, date_to__gte=gen_date,
                                                 property_ref=agm.property_ref).first()
            context ['insurance'] = insurance
            return context
        except Exception as e:
            messages.warning(self.request, e)
            return {}


class Agm2Pdf(GetAgmData, WeasyTemplateResponseMixin):
    pdf_stylesheets = [
        settings.STATIC_DIR + '/css/agm.css',
    ]
    # show pdf in-line (default: True, show download dialog)
    pdf_attachment = False
    # suggested filename (is required for attachment!)
    pdf_filename = 'agm.pdf'


class GetAgmBudgetData(TemplateView):
    template_name = settings.AGM_BUDGET_TEMPLATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:

            pk = int(self.kwargs ['pk'])
            agm = AGM.objects.get(id=pk)
            amg_budget = AgmOCBudget(agm.oc_ref_id, agm.fyear)
            context = amg_budget.get_context()

            return context
        except Exception as e:
            logging.exception(e)
            messages.warning(self.request, e)
            return {}


class AgmBudget2Pdf(GetAgmBudgetData, WeasyTemplateResponseMixin):
    pdf_stylesheets = [
        settings.STATIC_DIR + '/css/agm.css',
    ]
    # show pdf in-line (default: True, show download dialog)
    pdf_attachment = False
    # suggested filename (is required for attachment!)
    pdf_filename = 'agm_budget.pdf'


def render_agendas(request):
    agendas = None
    if request.method == "GET":
        agm_id = int(request.GET.get('agm_id'))
        agendas = AgmDetail.objects.filter(agm_ref_id=agm_id).order_by('seq_no')

    return render(request, 'strata/clause.html', {'agendas': agendas})


@csrf_exempt
def agenda_del_priority(request):
    if request.method == "POST":
        result = 'success'
        msg = 'no action performed'
        try:
            id = int(request.POST.get('agenda_id'))
            request_type = request.POST.get('type')
            agm_detail = AgmDetail.objects.get(id=id)
            delta = 0

            if request_type == "del":
                to_move_records = AgmDetail.objects.filter(agm_ref=agm_detail.agm_ref,
                                                           seq_no__gt=agm_detail.seq_no).order_by('seq_no')
                for item in to_move_records:
                    item.seq_no = item.seq_no - 1
                    item.updateby = request.user.username
                    item.save()
                agm_detail.delete()

                msg = "delete successful"
            if request_type == 'up':
                delta = -1
            if request_type == 'down':
                delta = 1
            if request_type in ('up', 'down'):
                cur_seq = agm_detail.seq_no
                swap_agm_detail = AgmDetail.objects.get(agm_ref=agm_detail.agm_ref, seq_no=cur_seq + delta)
                agm_detail.seq_no = cur_seq + delta
                agm_detail.save()

                swap_agm_detail.seq_no = cur_seq
                swap_agm_detail.save()
                msg = 'priority adjusted'

            return JsonResponse(
                data={'result': result, 'msg': msg, 'agm_id': agm_detail.agm_ref_id})

        except Exception as e:
            logging.exception(e)
            msg = 'save failed due to ' + str(e)
            return JsonResponse(data={'result': 'fail', "msg": msg})


def get_agenda_detail(request):
    if request.method == "GET":
        agenda_id = int(request.GET.get('id'))
        agenda_detail = AgmDetail.objects.get(id=agenda_id)
        return JsonResponse({
            'seq_no': agenda_detail.seq_no,
            'title': agenda_detail.title,
            'content': agenda_detail.content
        })


@csrf_exempt
def agenda_detail_maintain(request):
    result = "success"
    msg = ""
    try:
        if request.method == "POST":
            mode = request.POST.get('mode')
            if request.POST.get('agendaId'):
                agenda_id = int(request.POST.get('agendaId'))
            content = request.POST.get('content')
            title = request.POST.get('title')
            seq = int(request.POST.get('seq'))
            agm_id = int(request.POST.get('agmId'))

            # agenda detail update
            if mode == "update":
                agenda_detail = AgmDetail.objects.get(id=agenda_id)
                agenda_detail.title = title
                agenda_detail.content = content
                agenda_detail.updateby = request.user.username
                agenda_detail.save()
                msg = "Agenda updated"
                return JsonResponse({
                    'result': result,
                    'msg': msg,
                })
            # new agenda created
            if mode == "new":
                agm_item = AGM.objects.get(id=agm_id)
                if seq >= 1 and seq <= (agm_item.get_max_seq_no() + 1):
                    # increase original records seq no
                    to_move_items = AgmDetail.objects.filter(agm_ref_id=agm_id, seq_no__gte=seq)
                    for item in to_move_items:
                        item.seq_no = item.seq_no + 1
                        item.save()

                    agm_item = AgmDetail()
                    agm_item.client_ref_id = 1
                    agm_item.createby = agm_item.updateby = request.user.username
                    agm_item.agm_ref_id = agm_id
                    agm_item.seq_no = seq
                    agm_item.title = title
                    agm_item.content = content
                    if 'insurnace' in title or 'insurance' in content:
                        agm_item.is_insurance = True
                    agm_item.save()
                    msg = "new agenda created"
                    return JsonResponse({
                        'result': result,
                        'msg': msg,
                    })

    except Exception as e:
        logging.exception(e)
        msg = 'save failed due to ' + str(e)
        return JsonResponse(data={'result': 'fail', "msg": msg})


@csrf_exempt
def agm_delete(request):
    if request.method == "POST":
        try:
            id = int(request.POST.get('agm_id'))
            agm_item = AGM.objects.get(id=id)
            agm_item.delete()
            return JsonResponse({
                'result': "success",
                'msg': "delete successfully",
            })

        except Exception as e:
            return JsonResponse(data={'result': 'fail', "msg": "delete failed due to " + str(e)})


@csrf_exempt
def meeting_minutes_upload(request):
    if request.method == "POST":
        try:
            agm_id = request.POST.get('agmID')
            item = AGM.objects.get(pk=int(agm_id))
            if 'meeting_minutes' in request.FILES:
                attachment = request.FILES ['meeting_minutes']
                fs = FileSystemStorage()
                filename = fs.save(attachment.name, attachment)
                item.meeting_minutes = filename
                item.save()
                return JsonResponse(data={'result': 'success', 'msg': 'upload successfully'})

        except Exception as e:
            return JsonResponse(data={'result': 'fail', 'msg': 'upload fail due to ' + str(e)})


class OwnerRequestListView(LoginRequiredMixin, TemplateView):
    template_name = 'strata/owner_request.html'

    def get_context_data(self, **kwargs):
        form = OwnerRequestForm()
        lot = Lot.objects.filter(user_id=self.request.user.id).first()
        if lot:
            owner_request = OwnerRequest.objects.filter(lot_ref_id=lot.id)
        else:
            owner_request = None
        return {'requests': owner_request,
                'form': form}


@csrf_exempt
def new_request(request):
    if request.method == "POST":
        try:

            instance = OwnerRequestForm(request.POST)
            if instance.is_valid():
                item = OwnerRequest()
                item.createby = item.updateby = request.user.username
                item.msg_body = instance.cleaned_data ['msg_body']
                item.msg_subject = instance.cleaned_data ['msg_subject']
                item.category = instance.cleaned_data ['category']

                lot = Lot.objects.filter(user_id=request.user.id).first()
                item.lot_ref_id = lot.id
                item.client_ref_id = 1

                item.save()
            return JsonResponse(data={'result': 'success', 'msg': 'request submitted'})

        except Exception as e:
            return JsonResponse(data={'result': 'fail', 'msg': 'fail due to ' + str(e)})
