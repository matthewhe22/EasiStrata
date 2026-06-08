import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import CreateView, ListView, UpdateView

from base.models import Client, Notification
from scripts.DB.DBClass import MySQLClass
from scripts.scheduling_job.scheduling import new_oc_billing_schedule, oc_job_remove

from .forms import *
from .filters import *
from django_filters.views import FilterView


# Create your views here.
# section for Property Management
class PropertyCreateView(LoginRequiredMixin, CreateView):
    model = Property
    template_name = 'property/new_property.html'
    form_class = PropertyCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        return super(PropertyCreateView, self).form_valid(form)
        # return HttpResponseRedirect('/property/property/')

    def get_success_url(self):
        return reverse('property:property_list')


class PropertyUpdateView(LoginRequiredMixin, UpdateView):
    model = Property
    template_name = 'property/new_property.html'
    form_class = PropertyCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)

        # obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref_id = 1
        obj.save()
        return HttpResponseRedirect('/property/property/')

    def get_success_url(self):
        return reverse('property:property_list')


class PropertyListView(LoginRequiredMixin, FilterView):
    fields = ('name', 'lots_num', 'total_lot_liability', 'total_lot_entitle', 'plan_num', 'plan_type', 'init_period')
    template_name = 'property/property_list.html'
    paginate_by = 30
    filterset_class = PropertyFilter


# sample delete view
@require_POST
def property_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')

        for item in id_list:
            # del_item = get_object_or_404(Property, pk=int(item))
            del_item = Property.objects.get(pk=int(item))
            del_item.delete()

    return HttpResponseRedirect('/property/property/')


# section for lot management
class LotCreateView(LoginRequiredMixin, CreateView):
    model = Lot
    template_name = 'property/new_lot.html'
    form_class = LotCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        self.property_id = str(obj.property_ref_id)

        return super(LotCreateView, self).form_valid(form)

    def get_success_url(self):
        url = "/property/lot/?property_id=" + self.property_id
        return url


class LotUpdateView(LoginRequiredMixin, UpdateView):
    model = Lot
    template_name = 'property/new_lot.html'
    form_class = LotCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        property_id = str(obj.property_ref_id)
        url = "/property/lot/?property_id=" + property_id

        obj.updateby = self.request.user.username
        obj.client_ref_id = 1
        obj.save()

        return HttpResponseRedirect(url)


class LotListView(LoginRequiredMixin, ListView):

    def get_initial(self, request):
        # print(f'init print{request.GET}')
        return {
            'property_id': self.request.GET.get('property_id')}

    def get_queryset(self):
        result = super(LotListView, self).get_queryset()

        q_property = self.request.GET.get('property_id')
        # print(q_property)

        if q_property:
            result = result.filter(Q(property_ref_id=q_property))

        return result.select_related('property_ref')

    def get_context_data(self, *args, **kwargs):
        context = super(LotListView, self).get_context_data(*args, **kwargs)
        print(f"context print {self.request.GET.get('property_id')}")
        context ['property'] = Property.objects.all()
        if self.request.GET.get('property_id') is not None:
            context ['property_id'] = int(self.request.GET.get('property_id'))
        return context

    model = Lot
    fields = (
        'property_ref', 'floor', 'lot', 'type_lot', 'module_type', 'billing_adr', 'owner_name1', 'owner_name2',
        'email1')
    context_object_name = 'lot'
    template_name = 'property/lot_list.html'
    paginate_by = 30


# sample delete view
@require_POST
def lot_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')

        for item in id_list:
            del_item = get_object_or_404(Lot, pk=int(item))
            del_item.delete()

    return HttpResponseRedirect('/property/lot/')


# section for OC Master
class OcCreateView(LoginRequiredMixin, CreateView):
    model = OCMaster
    template_name = 'property/new_oc.html'
    form_class = OcCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)

        try:
            obj.save()
            new_oc_billing_schedule(obj.pk)
        except Exception as e:
            logging.exception(e)
        return super(OcCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('property:oc_list')


class OcUpdateView(LoginRequiredMixin, UpdateView):
    model = OCMaster
    template_name = 'property/update_oc.html'
    form_class = OcUpdateForm

    def get_context_data(self, **kwargs):
        context = super(OcUpdateView, self).get_context_data(**kwargs)

        if self.object.seal:
            context ['seal_pic'] = self.object.seal.url
        if self.object.manager_sign:
            context ['manager_pic'] = self.object.manager_sign.url
        context ['obj'] = self.object
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        original_date = OCMaster.objects.get(pk=obj.id).billing_start_date
        new_date = obj.billing_start_date

        try:
            obj.save()
            # logic to delete old scheding job and add a new one here
            if original_date != new_date:
                oc_job_remove(obj.pk)
                new_oc_billing_schedule(obj.pk)
        except Exception as e:
            logging.exception(e)
        return super(OcUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('property:oc_list')


class OcListView(LoginRequiredMixin, ListView):

    def get_queryset(self):
        result = super(OcListView, self).get_queryset()

        q_property = self.request.GET.get('property_id')

        if q_property:
            result = result.filter(Q(property_ref_id=q_property))

        return result.select_related('property_ref')

    def get_context_data(self, *args, **kwargs):
        context = super(OcListView, self).get_context_data(*args, **kwargs)
        context ['property'] = Property.objects.all()
        if self.request.GET.get('property_id') is not None:
            context ['property_id'] = int(self.request.GET.get('property_id'))
        return context

    model = OCMaster
    fields = ('title', 'description', 'start_date', 'expiry_date', 'property_ref', 'manager_first_name',
              'manager_last_name', 'manager_sign', 'seal', 'manager_threshold', 'chairman_threshold', 'BSB', 'Account',
              'frequency', 'billing_start_date')
    context_object_name = 'oc'
    template_name = 'property/oc_list.html'
    paginate_by = 30


# sample delete view
@require_POST
def oc_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')

        for item in id_list:
            del_item = get_object_or_404(OCMaster, pk=int(item))
            del_item.delete()

    return HttpResponseRedirect('/property/oc/')


# section for lot oc map
class LotOcCreateView(LoginRequiredMixin, CreateView):
    model = LotOCMap
    template_name = 'property/new_lotoc.html'
    form_class = LotOcCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        oc_id = obj.oc_ref_id
        property_id = str(OCMaster.objects.get(pk=oc_id).property_ref_id)
        url = "/property/lotoc/?property_id=" + property_id
        obj.save()
        return HttpResponseRedirect(url)


class LotOcUpdateView(LoginRequiredMixin, UpdateView):
    model = LotOCMap
    template_name = 'property/new_lotoc.html'
    form_class = LotOcCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        oc_id = obj.oc_ref_id
        property_id = str(OCMaster.objects.get(pk=oc_id).property_ref_id)
        url = "/property/lotoc/?property_id=" + property_id

        obj.updateby = self.request.user.username
        obj.client_ref_id = 1
        obj.save()
        return HttpResponseRedirect(url)


class LotOcListView(LoginRequiredMixin, ListView):
    model = LotOCMap
    fields = ('oc_ref', 'lot_ref', 'entitlement', 'liability')
    context_object_name = 'lotoc'
    template_name = 'property/lotoc_list.html'
    paginate_by = 30

    def get_queryset(self):
        result = super(LotOcListView, self).get_queryset()

        q_property = self.request.GET.get('property_id')
        q_crn = self.request.GET.get('crn')

        if q_property and q_property != '0':
            lot_list = Lot.objects.filter(property_ref_id=q_property).values_list('id', flat=True)
            result = result.filter(lot_ref_id__in=lot_list)

        if q_crn:
            result = result.filter(CRN__icontains=q_crn)

        return result.select_related('oc_ref', 'lot_ref')

    def get_context_data(self, *args, **kwargs):
        context = super(LotOcListView, self).get_context_data(*args, **kwargs)
        context ['property'] = Property.objects.all()
        if self.request.GET.get('property_id') is not None:
            context ['property_id'] = int(self.request.GET.get('property_id'))

        context ['crn'] = self.request.GET.get('crn')
        return context


# sample delete view
@require_POST
def lot_oc_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')

        for item in id_list:
            del_item = get_object_or_404(LotOCMap, pk=int(item))
            del_item.delete()

    return HttpResponseRedirect('/property/lotoc/')


# OC budget
# section for lot oc map
class OcBudCreateView(LoginRequiredMixin, CreateView):
    model = OcBudget
    template_name = 'property/new_ocbudget.html'
    form_class = OcBudCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        fin_year = obj.fin_year
        oc_id = obj.oc_ref_id
        property_id = str(OCMaster.objects.get(pk=oc_id).property_ref_id)
        url = "/property/ocbudget/?property_id=" + property_id + "&fin_year=" + str(fin_year)
        obj.save()
        return HttpResponseRedirect(url)


class OcBudUpdateView(LoginRequiredMixin, UpdateView):
    model = OcBudget
    template_name = 'property/new_ocbudget.html'
    form_class = OcBudCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        fin_year = obj.fin_year
        oc_id = obj.oc_ref_id
        property_id = str(OCMaster.objects.get(pk=oc_id).property_ref_id)
        url = "/property/ocbudget/?property_id=" + property_id + "&fin_year=" + str(fin_year)
        obj.save()
        return HttpResponseRedirect(url)


class OcBudListView(LoginRequiredMixin, ListView):

    def get_queryset(self):
        result = super(OcBudListView, self).get_queryset()

        q_property = self.request.GET.get('property_id')
        q_finyear = self.request.GET.get('fin_year')

        oc_list = OCMaster.objects.filter(property_ref_id=q_property).values_list('id', flat=True)

        if q_property != '0' and q_finyear and q_property:
            result = result.filter(Q(oc_ref_id__in=oc_list), Q(fin_year=q_finyear))
        elif q_property != '0' and q_property:
            result = result.filter(Q(oc_ref_id__in=oc_list))
        elif q_finyear:
            result = result.filter(Q(fin_year=q_finyear))

        return result.select_related('oc_ref')

    def get_context_data(self, *args, **kwargs):
        context = super(OcBudListView, self).get_context_data(*args, **kwargs)
        context ['property'] = Property.objects.all()
        if self.request.GET.get('property_id') is not None:
            context ['property_id'] = int(self.request.GET.get('property_id'))
        return context

    model = OcBudget
    fields = ('oc_ref', 'fin_year', 'acc_code', 'acc_name', 'amount')
    context_object_name = 'ocbudget'
    template_name = 'property/ocbudget_list.html'
    paginate_by = 30


# sample delete view
@require_POST
def oc_budget_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')

        for item in id_list:
            del_item = get_object_or_404(OcBudget, pk=int(item))
            del_item.delete()

    return HttpResponseRedirect('/property/ocbudget/')


@require_GET
def property_budget_sum(request):
    q_property = request.GET.get('property_id')
    q_finyear = request.GET.get('fin_year')
    property = Property.objects.all()

    if q_property != '0' and q_finyear and q_property:
        sql_stat = "select street,name,property_ref_id,oc_ref_id,fin_year,sum(amount) from property_ocbudget " \
                   "left join property_ocmaster po on property_ocbudget.oc_ref_id = po.id left join property_property pp " \
                   "on po.property_ref_id = pp.id " \
                   "where property_ref_id=%s and fin_year=%s and (property_ocbudget.acc_code='IS100001' or property_ocbudget.acc_code='IS100002')" \
                   "group by street,name,property_ref_id,oc_ref_id,fin_year order by fin_year desc"
        sql_stat = sql_stat % (q_property, q_finyear)
    elif q_property != '0' and q_property:
        sql_stat = "select street,name,property_ref_id,oc_ref_id,fin_year,sum(amount) " \
                   "from property_ocbudget left join property_ocmaster po on property_ocbudget.oc_ref_id = po.id " \
                   "left join property_property pp on po.property_ref_id = pp.id " \
                   "where property_ref_id=%s and (property_ocbudget.acc_code='IS100001' or property_ocbudget.acc_code='IS100002') " \
                   "group by street,name,property_ref_id,oc_ref_id,fin_year order by fin_year desc"
        sql_stat = sql_stat % (q_property)
    elif q_finyear:
        sql_stat = "select street,name,property_ref_id,oc_ref_id,fin_year,sum(amount) " \
                   "from property_ocbudget left join property_ocmaster po on " \
                   "property_ocbudget.oc_ref_id = po.id left join property_property pp on po.property_ref_id = pp.id " \
                   "where fin_year=%s and (property_ocbudget.acc_code='IS100001' or property_ocbudget.acc_code='IS100002') " \
                   "group by street,name,property_ref_id,oc_ref_id,fin_year order by fin_year desc"
        sql_stat = sql_stat % (q_finyear)
    else:
        sql_stat = "select street,name,property_ref_id,oc_ref_id,fin_year,sum(amount) " \
                   "from property_ocbudget left join property_ocmaster po " \
                   "on property_ocbudget.oc_ref_id = po.id left join property_property pp " \
                   "on po.property_ref_id = pp.id where (property_ocbudget.acc_code='IS100001' or property_ocbudget.acc_code='IS100002') " \
                   "group by street,name,property_ref_id,oc_ref_id,fin_year order by fin_year desc"
    result = MySQLClass().get_result(sql_stat)
    sum_list = []
    for item in result:
        budget_sum = BudgetSum()
        budget_sum.street = item [0]
        budget_sum.title = item [1]
        budget_sum.property_ref_id = item [2]
        budget_sum.oc_ref_id = item [3]
        budget_sum.fin_year = int(item [4])
        budget_sum.sum_amt = float(item [5])
        sum_list.append(budget_sum)

    if q_property is None:
        q_property = 0
    context = {'sum_list': sum_list,
               'property': property,
               'q_property': int(q_property)}

    return render(request, 'property/ocbudgetsum_list.html', context)


class BudgetSum:
    def __init__(self):
        self.street = ''
        self.title = ''
        self.property_ref_id = 1
        self.oc_ref_id = 1
        self.fin_year = 2020
        self.sum_amt = 0.00


# ajax view
def get_oc(request):
    if request.method == 'GET':
        property_id = request.GET.get('propertyId')
        oc = OCMaster.objects.filter(property_ref_id=property_id)
        return render(request, 'property/oc_dropdown_list_options.html', {'oc': oc})


def get_lot(request):
    if request.method == 'GET':
        property_id = request.GET.get('propertyId')
        lot = Lot.objects.filter(property_ref_id=property_id)
        return render(request, 'property/lot_dropdown_list_options.html', {'lots': lot})


def get_lot_from_oc(request):
    """
    scenario 1
    this function is used for lotoc update screen, while lot id is pre-defined in the page
    sceaario 2
    this function i used for no lot id is selected to get a full list under certain oc
    :param request:
    :return:
    """
    try:
        oc_id = request.GET.get('ocId')
        if request.method == 'GET' and oc_id != '':

            lot_list = LotOCMap.objects.filter(oc_ref_id=oc_id).values('lot_ref_id')
            lot_id = []
            for item in lot_list:
                lot_id.append(item ['lot_ref_id'])
            lot = Lot.objects.filter(id__in=lot_id)
            if request.GET.get('lotId') is not None:

                lot_id = request.GET.get('lotId')
                # property_id = OCMaster.objects.get(pk=oc_id).property_ref_id
                # lot = Lot.objects.filter(property_ref_id=property_id).exclude(pk=lot_id)
                select_lot = Lot.objects.get(pk=lot_id)
                return render(request, 'property/lot_dropdown_list_select.html',
                              {'lots': lot, 'select_lot': select_lot})

            else:
                return render(request, 'property/lot_dropdown_list_select.html', {'lots': lot})
        else:
            return render(request, 'property/lot_dropdown_list_select.html', {})

    except Exception as e:
        logging.exception(e)
        return render(request, 'property/lot_dropdown_list_select.html', {})


def get_property(request):
    try:
        oc_id = request.GET.get('ocId')
        if request.method == 'GET' and oc_id != '':
            oc = OCMaster.objects.get(pk=oc_id)
            data = {'property': oc.property_ref_id,
                    'liability': oc.liability}
            return JsonResponse(data)

        else:
            return JsonResponse({})
    except Exception as e:
        logging.exception(e)
        data = {}
        return JsonResponse(data)


def get_liability(request):
    oc_id = request.GET.get('oc_id')

    if request.method == 'GET' and oc_id != '':
        liability = OCMaster.objects.get(pk=oc_id).liability

        data = {'liability': liability}
        return JsonResponse(data)


@csrf_exempt
def init_new_budget(request):
    oc_id = int(request.POST ['oc_id'])
    oc_name = OCMaster.objects.get(pk=oc_id).title
    fin_year = int(request.POST ['fin_year'])
    user = request.user.username
    # clear financial year data
    OcBudget.objects.filter(oc_ref_id=oc_id, fin_year=fin_year).delete()
    template_year = fin_year - 1
    template_items = OcBudget.objects.filter(oc_ref_id=oc_id, fin_year=template_year)
    if template_items:
        for item in template_items:
            new_oc_budget = OcBudget(createby=user, updateby=user, oc_ref_id=oc_id, fin_year=fin_year,
                                     acc_code=item.acc_code, acc_name=item.acc_name, amount=item.amount,
                                     client_ref_id=1)
            new_oc_budget.save()

        message = oc_name + ' year ' + str(fin_year) + ' budget successfully initiated'
        return JsonResponse({'result': 'success',
                             'message': message})
    else:
        # PY budget doesn't exist should return error
        message = 'cannot find the year ' + str(template_year) + 'budget for oc ' + oc_name + ' budget creation failed '
        return JsonResponse({'result': 'fail',
                             'message': message})


@require_GET
def notify_list(request):
    """


    :param request: return a list view
    :return:
    property, subject,date , sent by
    """

    template_name = 'base/notify_log_list.html'
    log_list = list(Notification.objects.filter(category="email-note").values("property_id", "msg_subject", "createby",
                                                                              "createtime").distinct().order_by(
        '-createtime'))

    # Batch-load all referenced properties in a single query to avoid an N+1 lookup per row
    property_ids = {item ['property_id'] for item in log_list if type(item ['property_id']).__name__ == 'int'}
    properties = {p.id: p for p in Property.objects.filter(pk__in=property_ids)}
    for item in log_list:
        item ['name'] = properties.get(item ['property_id'], '')

    context = {'notify_list': log_list}

    return render(request, template_name, context)
