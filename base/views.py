# IMPORT
# IMPORT
import os
from threading import Thread

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q, Max, Count
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView, CreateView, UpdateView, ListView
from django.views.generic.edit import FormMixin
from django_apscheduler.models import *

from finance.models import GL, Billing, ClientLedger, Invoice, FS
from property.models import Lot
from scripts.DB.DBClass import MySQLClass
from scripts.DB.TAFunctions import *
from scripts.FileImport.init_log import *
from scripts.notification.Notify import Notify
from scripts.scheduling_job.billing_mail_job import billing_batch_service
from scripts.scheduling_job.scheduling import init_schedule, job_remove, new_oc_billing_schedule, oc_job_remove
from scripts.utils.date_utils import get_today, day_offset, day_diff
from scripts.utils.user_utils import create_owner_account, init_lot_user
from strata.models import AGM, Insurance
from .forms import *
from .models import *
from property.models import OcBudget


# init_lot_user()
class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'base/index.html'

    def get_context_data(self, **kwargs):
        """
        1. filter for specific account number
        2. group by oc_ref_id get max financial year
        3. iterate queryset get total rev by
        :param kwargs:
        :return:
        """
        # Initialise every context variable so the `finally` block can never
        # reference an unbound name if any query above fails part-way.
        total_property = rev = unbill = lot = lot_in_arrea = 0
        insurance = False
        try:
            total_property = Property.objects.count()

            # function change to get summary amount of oc budget
            revenue = OcBudget.objects.filter(Q(acc_code="IS701034") | Q(acc_code="IS701035")).values(
                'oc_ref_id').annotate(max_year=Max('fin_year'))

            # iterate the max fin year and oc id list (dict)
            rev = 0
            for item in revenue:
                oc_id = item ['oc_ref_id']
                fin_year = item ['max_year']
                rev = rev + get_oc_budget_total(oc_id, fin_year)

            unbill = Billing.objects.filter(status="unpaid", is_valid=True).count()

            if unbill is None:
                unbill = 0

            lot = Lot.objects.count()
            insurance = insurance_overdue()
            if insurance == 0:
                insurance = False

            lot_in_arrea = Billing.objects.filter(due_date__lt=get_today(), status="unpaid", is_valid=True).values(
                'lot_ref_id').annotate(
                Sum('billing_amount')).count()


        except Exception as e:
            logging.error(e)
        finally:
            context = {'property': total_property,
                       'rev': rev,
                       'unbill': unbill,
                       'lot': lot,
                       'insurance': insurance,
                       'lot_in_arrea': lot_in_arrea
                       }
            for item in context:
                if context [item] is None:
                    context [item] = 0

            return context


def get_oc_budget_total(oc_id, fin_year):
    revenue = OcBudget.objects.filter(Q(acc_code="IS701034") | Q(acc_code="IS701035")).filter(oc_ref_id=oc_id,
                                                                                              fin_year=fin_year).aggregate(
        total_rev=Sum('amount'))
    return revenue ["total_rev"]


# superuser access, user related data model
class UserListView(LoginRequiredMixin, ListView):
    model = User
    fields = '__all__'
    context_object_name = 'user_list'
    template_name = 'base/user_list.html'
    paginate_by = 30


class UserUpdateView(LoginRequiredMixin, UpdateView, FormMixin):
    model = User
    template_name = 'base/new_user.html'
    form_class = UserUpdateForm

    # get_sucess_url is compulsory for every update,deleteview
    def get_success_url(self):
        return reverse('base:user_list')


# client related data model

class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    template_name = 'base/new_client.html'
    fields = ('client_name', 'ABN', 'TFN', 'Address', 'telephone', 'email', 'IsDeleted', 'post_adr')

    def get_success_url(self):
        return reverse('base:client_list')


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    fields = '__all__'
    context_object_name = 'client_list'
    template_name = 'base/client_list.html'
    paginate_by = 30


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    template_name = 'base/new_client.html'
    fields = ('client_name', 'ABN', 'TFN', 'Address', 'telephone', 'email', 'IsDeleted', 'post_adr')

    def get_success_url(self):
        return reverse('base:client_list')


class DsCreateView(LoginRequiredMixin, CreateView):
    model = DataSource
    template_name = 'base/new_ds.html'
    form_class = DsCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        obj.save()
        return HttpResponseRedirect('/base/ds/')

    def get_success_url(self):
        return reverse('base:ds_list')


class DsListView(LoginRequiredMixin, ListView):
    model = DataSource
    fields = '__all__'
    context_object_name = 'ds_list'
    template_name = 'base/ds_list.html'
    paginate_by = 20


class AltertListView(LoginRequiredMixin, ListView):
    model = Notification
    fields = '__all__'
    context_object_name = 'alert'
    template_name = 'base/alter_list.html'

    paginate_by = 30

    def get_queryset(self):
        result = super(AltertListView, self).get_queryset()
        result = Notification.objects.filter(user_name=self.request.user.username).exclude(read_status='na').order_by(
            '-createtime', '-read_status')
        return result


class DsUpdateView(LoginRequiredMixin, UpdateView):
    model = DataSource
    template_name = 'base/new_ds.html'
    fields = '__all__'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        obj.save()
        return HttpResponseRedirect('/base/ds/')

    def get_success_url(self):
        return reverse('base:ds_list')


def user_login(request):
    if request.method == "GET":
        context = ''
        return render(request, 'base/login.html', {'context': context})

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = auth.authenticate(username=username, password=password)

        if user:
            if user.is_active:
                if user.is_staff:
                    path = '/base/'
                else:
                    path = '/base/owner/'

                auth.login(request, user)
                return HttpResponseRedirect(path)

            else:
                return HttpResponse("Account not active")
        else:

            return HttpResponse("Invalid login details")


@login_required
def user_logout(request):
    auth.logout(request)
    return render(request, 'base/logout.html')


# superuser access
@login_required
def user_create(request):
    if request.method == 'GET':
        form = UserForm()
        return render(request, 'base/new_user.html', {'form': form})

    elif request.method == 'POST':

        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

        else:
            print(user_form.errors)

    return render(request, 'base/index.html')


#### TRUST AUTOMATION
class ImportLogListView(ListView, LoginRequiredMixin):
    template_name = 'base/import.html'
    model = ImportLog
    fields = ('id', 'createtime', 'doc', 'status', 'error_code', 'error_message', 'src_ref')
    context_object_name = 'imports'


class DsRuleListView(LoginRequiredMixin, ListView):
    template_name = 'base/ds_rule_list.html'
    model = DataSourceRule
    fields = '__all__'
    context_object_name = 'ds_rule_list'


class DsRuleCreateView(LoginRequiredMixin, CreateView):
    model = DataSourceRule
    template_name = 'base/new_ds_rule.html'
    fields = ('src_ref', 'src_header', 'map_field', 'ftype', 'is_trans', 'cal_exp', 'reg_exp')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        obj.save()
        return HttpResponseRedirect('/base/ds_rule/')

    def get_success_url(self):
        return reverse('base:ds_rule')


class DsRuleUpdateView(LoginRequiredMixin, UpdateView):
    model = DataSourceRule
    template_name = 'base/new_ds_rule.html'
    fields = ('src_ref', 'src_header', 'map_field', 'ftype', 'is_trans', 'cal_exp', 'reg_exp')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        obj.save()
        return HttpResponseRedirect('/base/ds_rule/')

    def get_success_url(self):
        return reverse('base:ds_rule')


class ImportThread(Thread):
    def __init__(self, group=None, target=None, name=None, args=None, kwargs=None):
        Thread.__init__(self, group=group, target=target, name=name, daemon=True)
        self.args, self.kwargs = args, kwargs
        return

    def run(self):
        logobj = ImportLog.objects.get(pk=self.kwargs ['log_id'])
        logobj.status = '01'
        try:
            importData(self.args)
        except ValueError as ex:
            logobj.status, logobj.error_message = '02', str(ex)
        finally:
            logobj.save()
        return


def run_import(request):
    import_list = ImportLog.objects.all().order_by('-pk')
    form = UploadFileForm()
    context = {'imports': import_list,
               'form': form}
    template_name = 'base/import.html'
    if request.method == 'POST':
        # Start of the data import
        clientcode = int(request.POST.get('client_code'))
        datasource = int(request.POST.get('data_source'))
        property_id = int(request.POST.get('property'))
        oc_id = int(request.POST.get('oc_ref'))
        fin_year = int(request.POST.get('fin_year'))

        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():

            if 'docfile' in request.FILES:
                myfile = request.FILES ['docfile']
                fs = FileSystemStorage()
                filename = fs.save(myfile.name, myfile)
                # check valid and create new record in the import log table
                result = new_importlog(request, clientcode, datasource, filename)
                myfilepath = result [0]
                import_id = result [1]
            importParameters = {'client_ref_id': clientcode,
                                'file_path': myfilepath,
                                'datasource': datasource,
                                'property_ref_id': property_id,
                                'oc_ref_id': oc_id,
                                'fin_year': fin_year,
                                'user': request.user.username
                                }
            for k in request.POST:
                if k not in keyParameters:
                    importParameters [k] = request.POST [k]

            t = ImportThread(args=importParameters, kwargs={'log_id': import_id})
            t.start()
            messages.success(request, f'File uploaded and import task was sent!')

            return redirect('/base/import/')

    return render(request, template_name, context)


def owner_notify(request):
    form = OwnerNotiForm()
    context = {
        'form': form}
    template_name = 'base/owner_notify.html'

    if request.method == 'POST':
        property = int(request.POST.get('property'))
        title = request.POST.get('title')
        body = request.POST.get('body')
        purpose = request.POST.get('purpose')
        form = OwnerNotiForm(request.POST, request.FILES)
        data = {'property_id': property,
                'title': title,
                'body': body,
                'note_type': 'owner',
                'client_id': 1,
                'user': request.user.username,
                'purpose': purpose,
                'cc': request.POST.get('cc')
                }
        if form.is_valid():
            if 'docfile' in request.FILES:
                myfile = request.FILES ['docfile']
                fs = FileSystemStorage()
                filename = fs.save(myfile.name, myfile)
                myfilepath = os.path.join(settings.MEDIA_ROOT, filename)
                data ['attachment'] = myfilepath
            try:
                # use Notify interface
                note = Notify()
                note.init_strategy()
                note.notify(data)

                messages.success(request, 'Owner notification sent')
            except Exception as e:
                messages.warning(request, e)
                logging.exception(e)

    return render(request, template_name, context)


def vendor_notify(request):
    form = VendorNotiForm()
    context = {
        'form': form}
    template_name = 'base/vendor_notify.html'

    if request.method == 'POST':
        vendor = int(request.POST.get('vendor'))
        title = request.POST.get('title')
        body = request.POST.get('body')
        form = VendorNotiForm(request.POST, request.FILES)
        data = {'vendor_id': vendor,
                'title': title,
                'body': body,
                'note_type': 'vendor',
                'client_id': 1,
                'user': request.user.username}
        if form.is_valid():
            if 'docfile' in request.FILES:
                myfile = request.FILES ['docfile']
                fs = FileSystemStorage()
                filename = fs.save(myfile.name, myfile)
                myfilepath = os.path.join(settings.MEDIA_ROOT, filename)
                data ['attachment'] = myfilepath
            try:
                # use Notify interface
                note = Notify()
                note.init_strategy()
                note.notify(data)
                messages.success(request, "success")
            except Exception as e:
                logging.exception(e)

                messages.error(request, str(e))

    return render(request, template_name, context)


# TB class

class TBListView(LoginRequiredMixin, ListView):
    template_name = 'base/TB_list.html'
    model = TB
    fields = '__all__'
    context_object_name = 'TB_list'
    paginate_by = 30


# Scheduling job list

class JobListView(LoginRequiredMixin, ListView):
    template_name = 'base/job_list.html'
    model = DjangoJob
    fields = '__all__'
    context_object_name = 'job'
    paginate_by = 30


def job_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')
        # print (request.POST)
        for item in id_list:
            try:
                job_remove(item)
            except Exception as e:
                logging.exception(e)

    return HttpResponseRedirect('/base/job/')


def ds_rule_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')

        for item in id_list:
            try:
                DataSourceRule.objects.get(id=item).delete()

            except Exception as e:
                logging.exception(e)

    return HttpResponseRedirect('/base/ds_rule/')


# dependent dropdown list
@require_GET
def ajax_get_ds_list(request):
    client = request.GET.get('client_code')
    ds_list = DataSource.objects.filter(client_ref_id=client)
    return render(request, 'base/ajax_get_ds_list.html', {'ds_list': ds_list})


# ajax request for piechart
@require_GET
def get_lotnum_pie(request):
    labels = []
    data = []

    queryset = Property.objects.values('suburb').annotate(total_lot=Sum('lots_num')).order_by('-total_lot') [:10]
    for item in queryset:
        labels.append(item ['suburb'])
        data.append(item ['total_lot'])

    return JsonResponse(data={'labels': labels,
                              'data': data

                              })


@require_GET
def get_revenue(request):
    labels = []
    data = []

    sql_stat = "select date_format(posting_date,'%M %Y') as period,sum(amount) from finance_gl where acc_code in " \
               "('IS701034','IS701035') group by period order by posting_date desc limit 12"
    result = MySQLClass().get_result(sql_stat)

    for item in result:
        labels.append(item [0])
        data.append(float(item [1]))

    return JsonResponse(data={'labels': labels,
                              'data': data

                              })


def insurance_overdue():
    try:
        today = get_today()
        warn_period = settings.INSURANCE_DAY
        over_due_day = day_offset(today, warn_period)
        sql_stat = "select pp.name,max(ins.date_to) from strata_insurance " \
                   "ins left join property_property pp on ins.property_ref_id = pp.id " \
                   "group by pp.name having max(ins.date_to)<='%s'"
        sql_stat = sql_stat % over_due_day
        # Use the project DB connection (Postgres) directly. The legacy
        # MySQLClass transport points at a MySQL port that does not exist on
        # the current database and would stall/fail.
        from django.db import connection
        with connection.cursor() as _cur:
            _cur.execute(sql_stat)
            result = _cur.fetchall()
        warning_msg = ""
        if result is None or len(result) == 0:
            return 0
        else:
            for item in result:
                days = day_diff(item [1], today)
                if days >= 0:
                    warning_msg = warning_msg + "Property [" + item [0] + "] insurance will expire in " + str(
                        days) + " days\n"
                else:
                    warning_msg = warning_msg + "Property [" + item [
                        0] + "] insurance already expired and overdue " + str(
                        abs(days)) + " days\n"

            return warning_msg
    except Exception as e:
        logging.exception(e)
        return 0


# ajax request for user notfication
@require_GET
def get_user_notification(request):
    username = request.user.username
    if Notification.objects.filter(user_name=username, read_status="unread").exists():
        notification = Notification.objects.filter(user_name=username, read_status="unread").order_by("-createtime") [
                       :5]
        notification_num = len(notification)
        if notification_num > 4:
            notification_num = "5+"

    else:
        notification = False
        notification_num = 0

    data = {'notification': notification,
            'notification_num': notification_num

            }
    return render(request, 'partials/_notification.html', data)


@csrf_exempt
def read_alert(request):
    if request.method == "POST":
        try:

            msg_id = int(request.POST.get('msg'))
            msg = Notification.objects.get(pk=msg_id)
            msg.updateby = request.user.username
            if msg.read_status == "unread":
                msg.read_status = "read"
            msg.save()
            messages.success(request, "mark as read successfully")



        except Exception as e:
            logging.exception(e)
    return HttpResponseRedirect('/base/alert/')


# init billing scheduling for all ocs
@csrf_exempt
def oc_billing_init(request):
    if request.method == "POST":
        oc = OCMaster.objects.all()
        try:
            for item in oc:
                oc_job_remove(item.id)
                new_oc_billing_schedule(item.id)
            return JsonResponse({'result': 'success'})
        except Exception as e:
            logging.exception(e)
            return JsonResponse({'result': 'fail',
                                 'error': e})


# start the job scheduling manager
# The APScheduler background scheduler needs a long-lived process and a
# reachable DB jobstore. It cannot run on stateless serverless platforms
# (e.g. Vercel), so allow it to be disabled via the DISABLE_SCHEDULER env var.
if os.environ.get('DISABLE_SCHEDULER', 'False') != 'True':
    init_schedule()


# billing_batch_service()


class OwnerView(LoginRequiredMixin, TemplateView):
    template_name = 'base/owner.html'

    def get_context_data(self, **kwargs):
        """
        1. get lot info
        2. get agm info
        3. get insurance info
        4. get levy history
        5. get general ledger


        """
        context = {}
        user_id = self.request.user.id
        lot = Lot.objects.filter(user_id=user_id).first()
        # get lot info
        if lot:

            total_billing_amt = Billing.objects.filter(lot_ref_id=lot.id, is_valid=1, status="unpaid",
                                                       due_date__lt=get_today()).aggregate(Sum('billing_amount'))
            total_collected = Billing.objects.filter(lot_ref_id=lot.id, is_valid=1, status="unpaid",
                                                     due_date__lt=get_today()).aggregate(Sum('collected_amount'))
            if total_billing_amt ['billing_amount__sum'] is None:
                total_billing_amt ['billing_amount__sum'] = 0.00

            if total_collected ['collected_amount__sum'] is None:
                total_collected ['collected_amount__sum'] = 0.00

            overdue = float(total_billing_amt ['billing_amount__sum']) - float(
                total_collected ['collected_amount__sum'])
            billings = Billing.objects.filter(lot_ref_id=lot.id, special_flag=0, is_valid=1, is_show=1).order_by('-id')
            ledgers = ClientLedger.objects.filter(lot_ref_id=lot.id).order_by('oc_ref_id', '-trans_date', '-id')
            agms = AGM.objects.filter(property_ref_id=lot.property_ref_id).order_by('-fyear')
            insurances = Insurance.objects.filter(property_ref_id=lot.property_ref_id).order_by('-id')

            invoices = Invoice.objects.filter(oc_ref__property_ref_id=lot.property_ref_id).exclude(status='00')

            total_amount_arrear = Billing.objects.filter(oc_ref__property_ref_id=lot.property_ref_id, is_valid=1,
                                                         status="unpaid", due_date__lt=get_today()).aggregate(
                Sum('billing_amount'))
            if total_amount_arrear ['billing_amount__sum'] is None:
                total_amount_arrear ['billing_amount__sum'] = 0.00

            sql_stat = 'select count(distinct (lot_ref_id)) from finance_billing bill left join property_lot pl on bill.lot_ref_id = pl.id where pl.property_ref_id=%s and  bill.status="unpaid"'

            sql_stat = sql_stat % (lot.property_ref_id)
            result = MySQLClass().get_result(sql_stat) [0]
            property = lot.property_ref
            oc_list = OCMaster.objects.filter(property_ref=property)

            fs = FS.objects.filter(createby=self.request.user.username)

            if len(result) > 0:
                total_lot_arrear = result [0]
            else:
                total_lot_arrear = 0
            arrear_billings = Billing.objects.filter(oc_ref__property_ref_id=lot.property_ref_id, is_valid=1,
                                                     status="unpaid", due_date__lt=get_today())

            if get_today().month > 6:
                fyear = get_today().year + 1
            else:
                fyear = get_today().year

            context = {
                'overdue': overdue,
                'lot': lot,
                'billings': billings,
                'ledgers': ledgers,
                'agms': agms,
                'insurances': insurances,
                'all_invoices': invoices,
                'arrear_amount': total_amount_arrear ['billing_amount__sum'],
                'arrear_lot': total_lot_arrear,
                'arrear_billings': arrear_billings,
                'fs': fs,
                'property': property,
                'oc_list': oc_list,
                'fyear': fyear

            }

        return context
