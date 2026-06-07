import csv, io
import xlwt, os, logging
from my_project.settings import MEDIA_ROOT
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView
from my_project.weasy_compat import WeasyTemplateResponseMixin

from scripts.oc_cert.oc_cert import OCCert
from scripts.scheduling_job.mail_template import REMIND_TITLE
from scripts.notification.Notify import Notify
from scripts.utils.date_utils import convert_date_format, get_today
from scripts.scheduling_job.billing_mail_job import get_sign, get_subject
import my_project.settings as settings
from base.models import Client
from base.views import TemplateView, messages, FileSystemStorage
from scripts.GL.create_gl import GLGenerator
from scripts.billing.billing_invoice import BillingInv
from scripts.billing.oc_cert import Certificate
from scripts.GL.fs import FinStat
from scripts.utils.cal_utils import generate_id, build_liability_dict, allocate_levy
from scripts.utils.fin_utils import bill_payment_gl, reverse_cp_entry, get_lot_balance, check_latest_bill, \
    generate_billing_info
from scripts.bank.bank_interface import Bank
from scripts.utils.date_utils import day_offset, str_to_date, date_to_str
from .filters import *
from .forms import *
from .models import *
from django_filters.views import FilterView
from scripts.GL.client_ledger import create_client_ledger
from scripts.billing.payment_interface import handle_payment
from scripts.GL.payment_gl import PaymentGL


# This is finance views
class COACreateView(LoginRequiredMixin, CreateView):
    model = COA
    template_name = 'finance/new_coa.html'
    form_class = COACreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        return super(COACreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:coa_list')


class COAUpdateView(LoginRequiredMixin, UpdateView):
    model = COA
    template_name = 'finance/new_coa.html'
    form_class = COACreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        return super(COAUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:coa_list')


class COAListView(LoginRequiredMixin, ListView):

    def get_initial(self):
        return {
            'acc_num': self.request.GET.get('acc_num'),
            'acc_name': self.request.GET.get('acc_name')}

    def get_queryset(self):
        result = super(COAListView, self).get_queryset()

        q_acc_num = self.request.GET.get('acc_num')
        q_acc_name = self.request.GET.get('acc_name')

        if q_acc_num or q_acc_name:
            result = result.filter(Q(acc_code__icontains=q_acc_num), Q(acc_name__icontains=q_acc_name))

        return result

    model = COA
    fields = ('acc_code', 'acc_name', 'category', 'account_level1', 'account_level1', 'account_level2')
    context_object_name = 'coa'
    template_name = 'finance/coa_list.html'
    paginate_by = 30


@require_POST
def coa_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')

        for item in id_list:
            del_item = get_object_or_404(COA, pk=int(item))
            del_item.delete()

    return HttpResponseRedirect('/finance/coa/')


# section for income expense definition


class IncCreateView(LoginRequiredMixin, CreateView):
    model = IncomeExp
    template_name = 'finance/new_income.html'
    form_class = IncCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref_id = 1
        return super(IncCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:inc_list')


class IncUpdateView(LoginRequiredMixin, UpdateView):
    model = IncomeExp
    template_name = 'finance/new_income.html'
    form_class = IncCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        return super(IncUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:inc_list')


class IncListView(LoginRequiredMixin, ListView):

    def get_initial(self):
        return {
            'inc_code': self.request.GET.get('inc_code'),
            'inc_name': self.request.GET.get('inc_name')}

    def get_queryset(self):
        result = super(IncListView, self).get_queryset()

        q_inc_code = self.request.GET.get('inc_code')
        q_inc_name = self.request.GET.get('inc_name')

        if q_inc_code or q_inc_name:
            result = result.filter(Q(income_expense_code__icontains=q_inc_code), Q(name__icontains=q_inc_name))

        return result

    model = IncomeExp
    fields = ('name', 'income_expense_code', 'category', 'debit_acc', 'credit_acc', 'is_gst_output')
    context_object_name = 'inc'
    template_name = 'finance/inc_list.html'
    paginate_by = 30


# sample delete view
@require_POST
def inc_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')

        for item in id_list:
            del_item = get_object_or_404(IncomeExp, pk=int(item))
            del_item.delete()

    return HttpResponseRedirect('/finance/inc/')


# section for supplier

class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    template_name = 'finance/new_supply.html'
    form_class = SupplierCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        return super(SupplierCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:supply_list')


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    template_name = 'finance/new_supply.html'
    form_class = SupplierCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        return super(SupplierUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:supply_list')


class SupplierListView(LoginRequiredMixin, FilterView):
    fields = ('name', 'type_supply', 'from_date', 'to_date', 'review_date')
    context_object_name = 'supply'
    template_name = 'finance/supply_list.html'
    paginate_by = 30
    filterset_class = VendorFilter


# sample delete view
@require_POST
def supply_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')

        for item in id_list:
            del_item = get_object_or_404(Supplier, pk=int(item))
            del_item.delete()

    return HttpResponseRedirect('/finance/supply/')


# section for inovice


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    template_name = 'finance/new_invoice.html'
    form_class = InvoiceCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref_id = 1
        obj.save()

        try:
            data = {'oc_id': obj.oc_ref_id,
                    'client_id': 1,
                    'amount': obj.amount,
                    'input_gst_amt': obj.input_gst,
                    'inc_exp': obj.exp_ref.income_expense_code,
                    'desc': 'vendor invoice No.' + obj.inv_num + ' AP',
                    'user': self.request.user.username,
                    'defer_from': obj.defer_from,
                    'defer_periods': obj.defer_periods,
                    'posting_date': obj.inv_date

                    }

            je = GLGenerator(data)
            je.generate_je()
        except Exception as e:
            logging.exception(e)

        return super(InvoiceCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:invoice_list')


class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    template_name = 'finance/new_invoice.html'
    form_class = InvoiceCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        obj.save()
        return super(InvoiceUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:invoice_list')


class InvoiceListView(LoginRequiredMixin, FilterView):
    filterset_class = InvFilter
    fields = ('inv_date', 'inv_num', 'supplier_ref', 'due_date', "amount", 'status', 'last_approved')
    template_name = 'finance/invoice_list.html'
    paginate_by = 30


class CashRecpListView(LoginRequiredMixin, FilterView):
    filterset_class = CashFilter
    fields = ('recpt_no', 'recpt_date', 'amount', 'reference', "amount", 'reference', 'description', 'is_valid')
    template_name = 'finance/cash_receipt_list.html'
    paginate_by = 30


class ClientLedgerListView(LoginRequiredMixin, FilterView):
    filterset_class = ClientLedgerFilter
    fields = ('trans_date', 'debit_amt', 'credit_amt', 'balance', 'reference', 'description')
    template_name = 'finance/client_ledger_list.html'
    paginate_by = 30


# sample delete view
@require_POST
def invoice_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')

        for item in id_list:
            del_item = get_object_or_404(Invoice, pk=int(item))
            del_item.delete()

    return HttpResponseRedirect('/finance/invoice/')


# section for Billing


class BillingCreateView(LoginRequiredMixin, CreateView):
    model = Billing
    template_name = 'finance/new_billing.html'
    form_class = BillingCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        obj.billing_num = generate_id('BILLING')
        obj.due_date = day_offset(obj.billing_date, 28)
        obj.mail_status = 'draft'

        bal = get_lot_balance(obj.oc_ref_id, obj.lot_ref_id)

        if bal >= obj.billing_amount - obj.collected_amount:
            obj.status = "paid"

        if bal > 0:
            obj.collected_amount = min(obj.billing_amount, bal + obj.collected_amount)

        inc_exp_id = int(form.data ['income_ref'])
        inc_exp_code = IncomeExp.objects.get(pk=inc_exp_id).income_expense_code
        if not obj.desc:
            obj.desc = OCMaster.objects.get(id=obj.oc_ref_id).frequency + "Fee from" + str(
                obj.billing_from) + " to " + str(obj.billing_to)
        try:
            create_client_ledger(obj.oc_ref_id, obj.lot_ref_id, float(obj.billing_amount) * (-1), obj.billing_num,
                                 obj.createby,
                                 obj.billing_date)
            data = {'oc_id': obj.oc_ref_id,
                    'client_id': 1,
                    'amount': float(obj.billing_amount),
                    'inc_exp': inc_exp_code,
                    'desc': "Billing Generation" + obj.billing_num,
                    'user': self.request.user.username,
                    'posting_date': obj.billing_from
                    }
            je = GLGenerator(data)
            je.generate_je()

        except Exception as e:
            logging.exception(e)

        return super(BillingCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:billing_list')


class BillingUpdateView(LoginRequiredMixin, UpdateView):
    model = Billing
    template_name = 'finance/new_billing.html'
    form_class = BillingCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        obj.client_ref_id = 1

        return super(BillingUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:billing_list')


class BillingListView(LoginRequiredMixin, FilterView):
    fields = ('billing_num', 'lot_ref', 'billing_amount', 'collected_amount', 'billing_from',
              'billing_to', 'due_date', 'billing_date', 'status')
    template_name = 'finance/billing_list.html'
    paginate_by = 30
    filterset_class = BillFilter
    ordering_fields = ['-billing_num', ]


# sample delete view
@require_POST
def billing_delete(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('chkgroup')
        # print (request.POST)
        for item in id_list:
            del_item = get_object_or_404(Billing, pk=int(item))
            del_item.delete()

    return HttpResponseRedirect('/finance/billing/')


@require_POST
@csrf_exempt
def billing_reset(request, id=None):
    if request.method == "POST":

        id_list = request.POST.getlist('names[]')

        for item in id_list:
            reset_item = get_object_or_404(Billing, pk=int(item))
            # desc = reset_item.billing_num + "  payment"
            # take delete strategy
            GL.objects.filter(
                Q(description__icontains=reset_item.billing_num) & Q(description__icontains="payment")).delete()
            reset_item.updateby = request.user.username
            reset_item.collected_amount = 0
            reset_item.status = 'unpaid'
            reset_item.save()

    return HttpResponseRedirect('/finance/billing/')


@csrf_exempt
def billing_pay(request, *args, **kwargs):
    if request.method == "POST":
        try:

            id_list = request.POST.getlist('names[]')

            for item in id_list:
                confirm_item = Billing.objects.get(pk=int(item))
                # print(confirm_item)
                if confirm_item.status == 'unpaid':
                    confirm_item.status = 'paid'
                    payment_amt = confirm_item.billing_amount - confirm_item.collected_amount
                    confirm_item.collected_amount = confirm_item.billing_amount
                    confirm_item.updateby = request.user.username
                    # @0910 new logic for advance payment to generate GLs
                    bill_payment_gl(confirm_item, float(payment_amt), request.user.username)
                    confirm_item.save()
        except Exception as e:
            logging.exception(e)
    return HttpResponseRedirect('/finance/billing/')


@csrf_exempt
def cash_cancel(request, *args, **kwargs):
    if request.method == "POST":
        try:

            id_list = request.POST.getlist('names[]')
            count = 0
            for item in id_list:
                cancel_item = CashReceipt.objects.get(pk=int(item))
                bank_transaction = cancel_item.bank_ref
                if cancel_item.is_valid:
                    cancel_item.is_valid = False
                    cancel_item.updateby = request.user.username
                    # udpate clientledger
                    create_client_ledger(cancel_item.bank_ref.oc_ref_id, cancel_item.lot_ref_id,
                                         0.00 - float(cancel_item.amount),
                                         cancel_item.recpt_no + "cancellation", request.user.username)
                    # decrease billing collect amount
                    handle_payment(cancel_item.bank_ref.oc_ref_id, cancel_item.lot_ref_id,
                                   0.00 - float(cancel_item.amount), request.user.username)

                    cancel_item.save()
                    # add back amount to bank transaction
                    bank_transaction.updateby = request.user.username
                    bank_transaction.recpt_amt = max(0, bank_transaction.recpt_amt - cancel_item.amount)
                    if bank_transaction.recpt_amt == 0:
                        bank_transaction.process_result = "No lot matched. Please manually create cash receipt"
                    else:
                        bank_transaction.process_result = bank_transaction.process_result + cancel_item.recpt_no + 'cancel'
                    bank_transaction.save()

                    # Update GL
                    reverse_cp_entry(cancel_item.recpt_no, request.user.username)

                    count += 1
            return JsonResponse({'result': 'success', 'msg': str(count) + "items have been cancelled"})
        except Exception as e:
            logging.exception(e)
            return JsonResponse({'result': 'fail', 'msg': str(e)})


@csrf_exempt
def billing_remind(request, *args, **kwargs):
    """
    1. get list of billings that need to send reminder and the body from post request
    2. build the data(get the title, body, sign) combine sign and body as body
    3. based on the bill, create notifiction in the table
    note: sending of notification was taken care by scheduling job

    :param request: request contains a list of billls that need to send to reminder
    :param args:
    :param kwargs:
    :return:
    """
    if request.method == "POST":
        try:

            id_list = request.POST.getlist('billList[]')
            body = request.POST.get('body')
            body = body + get_sign(1)

            for item in id_list:
                remind_item = Billing.objects.get(pk=int(item))
                title = REMIND_TITLE + get_subject(remind_item) [0]

                # build the input para for notification
                data = {
                    'title': title,
                    'body': body,
                    'note_type': 'remind',
                    'client_id': 1,
                    'user': request.user.username,
                    'attachment': remind_item.attachment,
                    'purpose': 'levy',
                    'bill': remind_item
                }
                note = Notify()
                note.init_strategy()
                note.notify(data)
            return JsonResponse({'result': 'success', 'msg': 'reminder sent successfully'})


        except Exception as e:
            logging.exception(e)
            return JsonResponse({'result': 'fail', 'msg': str(e)})


@csrf_exempt
def billing_resend(request, *args, **kwargs):
    if request.method == "POST":
        try:

            id_list = request.POST.getlist('names[]')

            for item in id_list:
                confirm_item = Billing.objects.get(pk=int(item))
                # print(confirm_item)
                confirm_item.mail_status = "prepared"
                confirm_item.save()
        except Exception as e:
            logging.exception(e)
    return JsonResponse({'result': 'success'})


@csrf_exempt
def cancel_invoice(request, *args, **kwargs):
    if request.method == "POST":
        try:

            id_list = request.POST.getlist('names[]')

            for item in id_list:
                confirm_item = Invoice.objects.get(pk=int(item))
                if confirm_item.amount_paid == 0:
                    confirm_item.status = '00'
                    confirm_item.updateby = request.user.username
                    # add logic to generate GLs
                    data = {'oc_id': confirm_item.oc_ref_id,
                            'client_id': 1,
                            'amount': confirm_item.amount,
                            'inc_exp': confirm_item.exp_ref.income_expense_code,
                            'desc': 'cancel invoice No.' + confirm_item.inv_num,
                            'input_gst_amt': confirm_item.input_gst,
                            'user': request.user.username,
                            'reverse': True
                            }
                    je = GLGenerator(data)
                    je.generate_je()
                    confirm_item.save()
        except Exception as e:
            logging.exception(e)
    return HttpResponseRedirect('/finance/invoice/')


@csrf_exempt
def gl_recon(request):
    if request.method == "POST":
        try:

            id_list = request.POST.getlist('names[]')
            request_type = request.POST.get('type')

            for item in id_list:
                gl = GL.objects.get(pk=item)
                if request_type == 'recon':
                    gl.unpresent_flag = False
                    gl.recon_amt = gl.amount
                elif request_type == 'present' and gl.recon_amt == 0:
                    gl.unpresent_flag = True
                gl.updateby = request.user.username
                gl.save()
            return JsonResponse({'result': 'success'})
        except Exception as e:
            logging.exception(e)
            return JsonResponse({'result': 'fail',
                                 'error': e})


@csrf_exempt
def bank_recon(request):
    if request.method == "POST":
        try:

            id_list = request.POST.getlist('names[]')
            request_type = request.POST.get('type')

            for item in id_list:
                bank = BankTrans.objects.get(pk=item)
                if request_type == 'recon':
                    bank.unpresent_flag = False
                    bank.recon_amt = bank.amount
                elif request_type == 'present' and bank.recon_amt == 0:
                    bank.unpresent_flag = True
                bank.updateby = request.user.username
                bank.save()
            return JsonResponse({'result': 'success'})
        except Exception as e:
            logging.exception(e)
            return JsonResponse({'result': 'fail',
                                 'error': e})


@csrf_exempt
def bank_upload(request):
    if request.method == "POST":
        try:
            if 'docfile' in request.FILES:
                trans_file = request.FILES ['docfile']
                if not trans_file.name.endswith('.csv'):
                    return JsonResponse({'result': 'fail',
                                         'msg': 'THIS IS NOT A CSV FILE'})

                data_set = trans_file.read().decode('UTF-8')
                io_string = io.StringIO(data_set)
                next(io_string)
                for row in csv.reader(io_string, delimiter=','):
                    trans_item = Bank(row, request.user.username)
                    trans_item.handle()
            return JsonResponse({'result': 'success'})
        except Exception as e:
            logging.exception(e)
            return JsonResponse({'result': 'fail',
                                 'msg': 'import failed' + str(e)})


@csrf_exempt
def pay_invoice(request, *args, **kwargs):
    if request.method == "POST":
        try:
            id_list = request.POST.getlist('names[]')
            for item in id_list:
                confirm_item = Invoice.objects.get(pk=int(item))
                if abs(confirm_item.amount_paid) < abs(
                        confirm_item.amount) and confirm_item.payment_status == 'unpaid' and confirm_item.status != '00':
                    confirm_item.updateby = request.user.username
                    payment_amt = confirm_item.amount + confirm_item.input_gst - confirm_item.amount_paid
                    # add logic to generate GLs
                    data = {'oc_id': confirm_item.oc_ref_id,
                            'client_id': 1,
                            'amount': payment_amt,
                            'inc_exp': "BS400002",
                            'desc': 'vendor invoice No.' + confirm_item.inv_num + 'bank payment',
                            'user': request.user.username,
                            }
                    je = GLGenerator(data)
                    je.generate_je()
                    # set payment status and amount_paid
                    confirm_item.payment_status = "paid"
                    confirm_item.amount_paid = confirm_item.amount
                    confirm_item.save()
        except Exception as e:
            logging.exception(e)
    return HttpResponseRedirect('/finance/invoice/')


class GetInoviceData(TemplateView):
    template_name = settings.INVOICE_TEMPLATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:

            pk = int(self.kwargs ['pk'])
            billing = BillingInv(pk)
            context = billing.generate_feed_data()
            return context
        except Exception as e:
            messages.warning(self.request, e)
            return {}


class GetCashReceiptData(TemplateView):
    template_name = settings.RECEIPT_TEMPLATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:

            pk = int(self.kwargs ['pk'])
            cash_receipt = CashReceipt.objects.get(id=pk)
            property = cash_receipt.get_property()
            oc = cash_receipt.get_oc()
            lot = cash_receipt.get_lot_instance()
            billing_info = generate_billing_info(lot, property)
            context = {
                'item': cash_receipt,
                'property': property,
                'oc': oc,
                'lot': lot,
                'billing_info': billing_info,
                'client': Client.objects.get(id=1)
            }
            return context
        except Exception as e:
            messages.warning(self.request, e)
            return {}


class GetLastestInoviceData(TemplateView):
    template_name = settings.INVOICE_TEMPLATE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:

            pk = int(self.kwargs ['pk'])
            billing = BillingInv(pk, hist_flag=False)
            context = billing.generate_feed_data()
            return context
        except Exception as e:
            messages.warning(self.request, e)
            return {}


class GetOcData(TemplateView):
    template_name = "oc_cert.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs ['pk']
        oc = Certificate(pk)
        try:
            context = oc.generate_feed_data()
            return context
        except Exception as e:
            logging.exception(e)
            messages.add_message(self.request, messages.ERROR, e)
            context ['error'] = e
            return context


class GetfsData(TemplateView):
    template_name = "fs_template.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs ['pk']
        fs = FinStat(pk)
        try:
            context = fs.generate_fs()
            return context
        except Exception as e:
            logging.exception(e)
            messages.warning(self.request, e)
            return HttpResponseRedirect("/finance/fs/")


class Invoice2Pdf(GetInoviceData, WeasyTemplateResponseMixin):
    pdf_stylesheets = [
        settings.STATIC_DIR + '/css/invoice.css',
    ]
    # show pdf in-line (default: True, show download dialog)
    pdf_attachment = False
    # suggested filename (is required for attachment!)
    pdf_filename = 'invoice.pdf'


class LastestInvoice2Pdf(GetLastestInoviceData, WeasyTemplateResponseMixin):
    pdf_stylesheets = [
        settings.STATIC_DIR + '/css/invoice.css',
    ]
    # show pdf in-line (default: True, show download dialog)
    pdf_attachment = False
    # suggested filename (is required for attachment!)
    pdf_filename = 'invoice.pdf'


class CashReceipt2Pdf(GetCashReceiptData, WeasyTemplateResponseMixin):
    pdf_stylesheets = [
        settings.STATIC_DIR + '/css/invoice.css',
    ]
    # show pdf in-line (default: True, show download dialog)
    pdf_attachment = False
    # suggested filename (is required for attachment!)
    pdf_filename = 'cash_receipt.pdf'


class Oc2Pdf(GetOcData, WeasyTemplateResponseMixin):
    pdf_stylesheets = [
        settings.STATIC_DIR + '/css/cert.css',
    ]
    # show pdf in-line (default: True, show download dialog)
    pdf_attachment = False
    # suggested filename (is required for attachment!)
    pdf_filename = 'oc_certificate.pdf'


class Fs2Pdf(GetfsData, WeasyTemplateResponseMixin):
    pdf_stylesheets = [
        settings.STATIC_DIR + '/css/report.css',
    ]
    # show pdf in-line (default: True, show download dialog)
    pdf_attachment = False
    # suggested filename (is required for attachment!)
    pdf_filename = 'fs.pdf'
    presentational_hints = True


# start of oc certificate
def oc_cert_create(request):
    template_name = 'finance/new_oc_cert.html'
    form = OcCreateForm()
    context = {'form': form}
    is_valid = True
    if request.method == "POST":
        form = OcCreateForm(request.POST)
        if form.is_valid() and is_valid:
            obj = form.save(commit=False)
            obj.createby = request.user.username
            obj.updateby = request.user.username
            obj.client_ref = Client.objects.get(id=1)
            obj.issue_date = request.POST.get('issue_date')
            attachment_list = request.POST.getlist('attachment_list')
            obj.save()
            oc_cert = OCCert(obj.id)
            oc_cert.set_attributes_from_request(request, attachment_list)
            is_valid, error_msg, final_url = oc_cert.handle()
            if is_valid and final_url:
                obj.attachment = final_url
                obj.save()
                messages.success(request, "OC Certificate created successfully")
            else:
                messages.error(request, error_msg)
        else:
            messages.error(request, "something doesn't look right")
            return render(request, template_name, {'form': form})
        return HttpResponseRedirect(reverse('finance:oc_cert_list'))

    return render(request, template_name, context)


class OcCertCreateView(LoginRequiredMixin, CreateView):
    model = Occertificate
    template_name = 'finance/new_oc_cert.html'
    form_class = OcCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        obj.issue_date = self.request.POST.get('issue_date')

        attachment_list = self.request.POST.getlist('attachment_list')
        messages.success(self.request, 'error')

        return super(OcCertCreateView, self).form_valid(form)

    def get_success_url(self):
        # messages.success(self.request, 'success')
        return reverse('finance:oc_cert_list')

    def form_submit(self, request):
        valid_flag = False
        if request.method == "POST":
            form = OcCreateForm(request.POST)
            if form.is_valid() and valid_flag:
                form.save()
                # messages.success(self.request, 'success')

            else:
                # messages.error(self.request,'failed')
                pass
            return HttpResponseRedirect(reverse('oc_cert_create'))


class OcCertUpdateView(LoginRequiredMixin, UpdateView):
    model = Occertificate
    template_name = 'finance/new_oc_cert.html'
    form_class = OcCreateForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)

        return super(OcCertUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:oc_cert_list')


class OcCertListView(LoginRequiredMixin, FilterView):
    fields = ('oc_ref', 'lot_ref', 'issue_date',)
    template_name = 'finance/oc_cert_list.html'
    paginate_by = 30
    filterset_class = OcCertFilter


class GLsListView(LoginRequiredMixin, FilterView):
    paginate_by = 30
    fields = ('acc_code', 'posting_date', 'document_date', 'dc', 'period', 'description',
              'amount', 'oc_ref')
    template_name = 'finance/gl_list.html'
    filterset_class = GLFilter


class GLsReconListView(LoginRequiredMixin, FilterView):
    paginate_by = 30

    # def get_queryset(self):
    #     result = super(GLsReconListView, self).get_queryset()
    #     result = GL.objects.filter(acc_code="BS300000")
    #     # result=Paginator(result,30)
    #
    #     return result

    fields = ('doc_num', 'posting_date', 'document_date', 'dc', 'period', 'description',
              'amount', 'recon_amt', 'unpresent_flag')
    filterset_class = GLReconFilter
    template_name = 'finance/gl_recon_list.html'


# FS views


class FSCreateView(LoginRequiredMixin, CreateView):
    model = FS
    template_name = 'finance/new_oc_cert.html'
    form_class = FsForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.createby = self.request.user.username
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)
        return super(FSCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:fs_list')


class FSUpdateView(LoginRequiredMixin, UpdateView):
    model = FS
    template_name = 'finance/new_oc_cert.html'
    form_class = FsForm

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updateby = self.request.user.username
        obj.client_ref = Client.objects.get(id=1)

        return super(FSUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('finance:fs_list')


class FSListView(LoginRequiredMixin, FilterView):
    fields = ('property_ref', 'oc_ref', 'to_date', 'fin_year')
    template_name = 'finance/fs_list.html'
    paginate_by = 30
    filterset_class = FsFilter


# gl related functions

def generate_gl(request):
    if request.method == 'POST':
        form = GLForm(request.POST)
        data = request.POST
        oc_id = int(data ['oc_ref'])
        amount = float(data ['amount'])
        input_gst_amt = float(data ['input_gst  _amt'])
        inc_exp = int(data ['inc_exp'])
        inc_exp_code = IncomeExp.objects.get(pk=inc_exp).income_expense_code
        desc = data ['desc']
        posting_date = data ['posting_date']

        if form.is_valid():
            try:
                data = {'oc_id': oc_id,
                        'client_id': 1,
                        'amount': amount,
                        'inc_exp': inc_exp_code,
                        'desc': desc,
                        'input_gst_amt': input_gst_amt,
                        'user': request.user.username,
                        'posting_date': posting_date,
                        }

                gl = GLGenerator(data)
                gl.generate_je()
                messages.success(request, f'Manual GL posted successfully')
            except Exception as e:
                logging.exception(e)


    else:
        form = GLForm()
    return render(request, 'finance/gl.html', {'form': form})


@csrf_exempt
def part_pay_invoice(request):
    if request.method == 'POST':
        data = request.POST
        try:
            payment_amt = Decimal(data ['payment_amt'])
            id = int(data ['invoice_id'])
            invoice = Invoice.objects.get(pk=id)
            if abs(payment_amt) <= abs(invoice.amount + invoice.input_gst) - abs(invoice.amount_paid):
                invoice.amount_paid = invoice.amount_paid + payment_amt
                invoice.updateby = request.user.username
                if payment_amt == invoice.amount + invoice.input_gst - invoice.amount_paid:
                    invoice.payment_status = "paid"
                data = {'oc_id': invoice.oc_ref_id,
                        'client_id': 1,
                        'amount': payment_amt,
                        'inc_exp': "BS400002",
                        'desc': 'vendor invoice No.' + invoice.inv_num + 'bank payment',
                        'user': request.user.username,
                        }
                je = GLGenerator(data)
                je.generate_je()
                invoice.save()
            else:
                raise Exception("payment amount is greater than balance amount")
        except Exception as e:
            logging.exception(e)
        return JsonResponse({'invoice_id': id,
                             'payment_amt': payment_amt})

    else:

        invoice_id = request.GET.get('invoice_id')
        invoice = Invoice.objects.get(pk=invoice_id)
        bal = invoice.input_gst + invoice.amount - invoice.amount_paid
        invoice_num = invoice.inv_num
        init_context = {'bal_amount': bal,
                        'invoice': invoice_num,
                        'invoice_id': invoice_id,
                        }

        return JsonResponse(init_context)


def get_defer_ind(request):
    if request.method == "GET":
        income_id = request.GET.get('income_id')
        if type(income_id).__name__ == 'str' and len(income_id) > 0:
            income_obj = get_object_or_404(IncomeExp, pk=int(income_id))
            return JsonResponse({'ind': income_obj.is_deferred})
        else:
            return JsonResponse({'ind': False})


@csrf_exempt
def part_pay_bill(request):
    if request.method == 'POST':
        data = request.POST
        try:
            payment_amt = Decimal(data ['payment_amt'])
            id = int(data ['invoice_id'])
            invoice = Billing.objects.get(pk=id)
            invoice.updateby = request.user.username
            # if payment >= billling_amount-collected_amount then paid
            if payment_amt >= invoice.billing_amount - invoice.collected_amount:
                invoice.collected_amount = invoice.billing_amount
                invoice.status = "paid"
            else:
                invoice.collected_amount = invoice.collected_amount + payment_amt
            bill_payment_gl(invoice, float(payment_amt), request.user.username)
            invoice.save()

        except Exception as e:
            logging.exception(e)
        return JsonResponse({'invoice_id': id,
                             'payment_amt': payment_amt})

    else:

        invoice_id = request.GET.get('invoice_id')
        invoice = Billing.objects.get(pk=invoice_id)
        bal = invoice.billing_amount - invoice.collected_amount
        invoice_num = invoice.billing_num
        init_context = {'bal_amount': bal,
                        'invoice': invoice_num,
                        'invoice_id': invoice_id,
                        }

        return JsonResponse(init_context)


class BankListView(LoginRequiredMixin, FilterView):
    filterset_class = BankFilter
    fields = ('acc_num', 'acc_name', 'trans_date', 'narrative', 'ref_num', 'amount', 'balance', 'cateogry', 'recon_amt',
              'unpresent_flag')
    template_name = 'finance/bank_list.html'
    paginate_by = 30


def special_levy(request):
    form = specialLevyForm()
    context = {
        'form': form}
    template_name = 'finance/special_levy.html'

    if request.method == 'POST':
        """
        1. get parameter
        2. get the liability dict of lot and get property id gst
        3. locate the budget
        4. generate the billing
        """
        try:
            property_id = int(request.POST.get('property_ref'))
            oc_id = int(request.POST.get('oc_ref'))
            total_budget = round(float(request.POST.get('total_budget')), 2)
            billing_date = request.POST.get('billing_date')
            desc = request.POST.get('desc')
            rev_type = request.POST.get('rev_type')
            if rev_type == 'special':
                income_exp_code = 'IS100040'
                special_desc = 'Special Levy'
                flag = True

            elif rev_type == 'operating':
                income_exp_code = 'IS100001'
                special_desc = ''
                flag = False
            elif rev_type == 'maintenance':
                income_exp_code = 'IS100002'
                special_desc = ''
                flag = False

            gst_flag = Property.objects.get(id=property_id).GST_register
            if gst_flag:
                gst = 1.1
            else:
                gst = 1

            total_budget = total_budget * gst
            liability_dict = build_liability_dict(oc_id)
            levy_dict = allocate_levy(liability_dict, total_budget)

            for item in levy_dict:
                billing = Billing()
                billing.lot_ref_id = int(item)
                # add logic for scenario if client has prepayment
                bal = get_lot_balance(oc_id, int(item))

                billing.createby = request.user.username
                billing.updateby = request.user.username
                billing.client_ref_id = 1
                billing.oc_ref_id = oc_id
                billing.billing_num = generate_id('BILLING')
                billing.billing_date = billing_date
                billing.billing_from = billing_date
                billing.billing_to = billing_date
                billing.due_date = day_offset(billing.billing_date, 28)
                billing.desc = desc
                billing.mail_status = 'draft'
                billing.billing_amount = levy_dict [item]
                # 16 May add logic for lots with prepayments
                if bal > 0:
                    billing.collected_amount = min(billing.billing_amount, bal)
                    if bal >= billing.billing_amount:
                        billing.status = "paid"
                billing.special_flag = flag
                billing.save()
                # create client ledger
                create_client_ledger(oc_id, int(item), 0 - float(billing.billing_amount), billing.billing_num,
                                     request.user.username, billing_date, desc)
                # generate entry
                data = {'oc_id': oc_id,
                        'client_id': 1,
                        'amount': float(billing.billing_amount),
                        'inc_exp': income_exp_code,
                        'desc': special_desc + billing.billing_num,
                        'user': request.user.username,
                        'posting_date': billing_date
                        }

                je = GLGenerator(data)
                je.generate_je()
            messages.success(request, "success")
        except Exception as e:
            logging.exception(e)
            messages.error(request, str(e))

        finally:
            return render(request, template_name, context)
    return render(request, template_name, context)


@csrf_exempt
def gl_export(request):
    oc_id = request.POST.get('ocID')
    start_date = request.POST.get('startDate')
    to_date = request.POST.get('toDate')

    kwargs = {}
    if oc_id != '':
        kwargs ['oc_ref_id'] = int(oc_id)
    if start_date != '':
        kwargs ['posting_date__gt'] = convert_date_format(start_date)
    if to_date != '':
        kwargs ['posting_date__lt'] = convert_date_format(to_date)

    nowTime = datetime.now().strftime('%Y-%m-%d-%H')
    filename = "GL" + str(nowTime) + ".xls"
    filepath = os.path.join(MEDIA_ROOT, filename)
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('GL')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['OC', 'Account Code', 'Posting Date', 'Document Date', 'Debit/Credit', 'Period', 'Description', 'Amount']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns [col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    rows = GL.objects.filter(**kwargs).values_list('oc_ref', 'acc_code', 'posting_date', 'document_date', 'dc',
                                                   'period',
                                                   'description', 'amount')

    # rows = GL.objects.all()

    for item in rows:
        row = list(item)
        row [0] = OCMaster.objects.get(pk=int(row [0])).title
        row [2] = date_to_str(row [2])
        row [3] = date_to_str(row [3])
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row [col_num], font_style)

    wb.save(filepath)

    return JsonResponse({'filename': "/media/" + filename})


@csrf_exempt
def create_cash_recpt(request):
    # this is for vendor invoice not for the billing
    if request.method == 'POST':
        data = request.POST
        try:
            payment_amt = Decimal(data ['payment_amt'])
            id = int(data ['invoice_id'])
            invoice = Invoice.objects.get(pk=id)
            if abs(payment_amt) <= abs(invoice.amount + invoice.input_gst) - abs(invoice.amount_paid):
                invoice.amount_paid = invoice.amount_paid + payment_amt
                invoice.updateby = request.user.username
                if payment_amt == invoice.amount + invoice.input_gst - invoice.amount_paid:
                    invoice.payment_status = "paid"
                data = {'oc_id': invoice.oc_ref_id,
                        'client_id': 1,
                        'amount': payment_amt,
                        'inc_exp': "BS400002",
                        'desc': 'vendor invoice No.' + invoice.inv_num + 'bank payment',
                        'user': request.user.username,
                        }
                je = GLGenerator(data)
                je.generate_je()
                invoice.save()
            else:
                raise Exception("payment amount is greater than balance amount")
        except Exception as e:
            logging.exception(e)
        return JsonResponse({'invoice_id': id,
                             'payment_amt': payment_amt})

    else:

        invoice_id = request.GET.get('invoice_id')
        invoice = Invoice.objects.get(pk=invoice_id)
        bal = invoice.input_gst + invoice.amount - invoice.amount_paid
        invoice_num = invoice.inv_num
        init_context = {'bal_amount': bal,
                        'invoice': invoice_num,
                        'invoice_id': invoice_id,
                        }

        return JsonResponse(init_context)


def get_bank_trans_detail(request):
    if request.method == "GET":
        bank_trans_id = request.GET.get('cashID')
        bank_item = BankTrans.objects.get(id=int(bank_trans_id))
        context = {
            'balance': bank_item.amount - bank_item.recpt_amt
        }
        return JsonResponse(context)


@csrf_exempt
def allocate_cash(request):
    if request.method == "POST":
        try:
            lot_id = int(request.POST.get('lot_id'))
            amount = float(request.POST.get('amount'))
            desc = request.POST.get('desc')
            ref = request.POST.get('ref')
            bank_id = int(request.POST.get('bank_id'))
            receipt = CashReceipt()
            transaction = BankTrans.objects.get(pk=bank_id)
            oc_id = transaction.oc_ref_id
            balance = get_lot_balance(oc_id, lot_id)

            # create new cash receipt
            receipt.createby = receipt.updateby = request.user.username
            receipt.recpt_date = transaction.trans_date
            receipt.lot_ref_id = lot_id
            receipt.amount = amount
            receipt.reference = ref
            receipt.description = desc
            receipt.bank_ref_id = transaction.id
            receipt.recpt_no = generate_id('RCP')
            receipt.client_ref_id = 1
            receipt.save()
            # generate client ledger
            create_client_ledger(oc_id, lot_id, amount, ref, request.user.username, receipt.recpt_date, desc)
            # update bank transaction itself
            transaction.recpt_amt = transaction.recpt_amt + Decimal(amount)
            transaction.updateby = request.user.username

            if 'lot matched' in transaction.process_result:
                transaction.process_result = receipt.recpt_no + ' created'
            else:
                transaction.process_result = transaction.process_result + receipt.recpt_no + ' created'
            transaction.save()

            # generate gl needs to perform before handle payment
            PaymentGL(oc_id, lot_id, receipt.recpt_no, amount,
                      transaction.trans_date, request.user.username, balance)
            # update billing collected amount
            handle_payment(oc_id, lot_id, amount, request.user.username)

            result = 'success'
            msg = "cash receipt has been successfully created"

            return JsonResponse({'result': result, 'msg': msg})

        except Exception as e:
            logging.exception(e)
            result = 'fail'
            msg = str(e)
            return JsonResponse({'result': result, 'msg': msg})


@csrf_exempt
def billing_cancel(request):
    if request.method == 'POST':
        billing_id = request.POST.get('bill_id')
        bill = Billing.objects.get(pk=billing_id)

        # check if bill could be reversed
        """
        1. is_valid=true and status == "unpaid"
        2. is the latest bill in the client ledger get cancel list if any cash receipt found later than this bill 
        if 1 and 2 yes then good to cancel
        
        3. reverse the JE found for this bill and delete client ledger
        4. reverse the cash receipt ahead of this bill if any- exclude
        5. post reverse amount to client ledger
               
        """
        if bill.is_valid and check_latest_bill(bill) and bill.collected_amount == 0:
            # reverse the JE of the bill
            reverse_cp_entry(bill.billing_num, request.user.username)
            # post reverse amount
            create_client_ledger(bill.oc_ref_id, bill.lot_ref_id, bill.billing_amount, 'reverse' + bill.billing_num,
                                 request.user.username, desc='reverse' + bill.billing_num)
            # set bill status
            bill.is_valid = False
            bill.save()
            return JsonResponse({'status': 'success', 'msg': bill.billing_num + 'reversed successfully'})
        else:

            return JsonResponse({'status': 'failed', 'msg': 'cannot reverse the bill selected'})


@csrf_exempt
def oc_cert_handle(request):
    try:
        if request.method == "POST":
            attachment_list = request.POST.getlist('attachment_list')
            print(attachment_list)
            item = OCCert()
            item.set_instance_from_request(request)
            return JsonResponse({'status': 'success', 'msg': 'success'})


    except Exception as e:
        logging.exception(e)
        return JsonResponse({'status': 'failed', 'msg': 'failed due to ' + str(e)})


@csrf_exempt
def fs_del(request):
    try:
        if request.method == "POST":
            id = request.POST.get('id')
            item = FS.objects.get(id=int(id))
            item.delete()
            return JsonResponse({'msg': 'delete successfully'})



    except Exception as e:
        logging.exception(str(e))
        return JsonResponse({'msg': 'failed' + str(e)})


@csrf_exempt
def fs_owner(request):
    try:
        if request.method == "POST":
            item = FS()
            item.createby = item.updateby = request.user.username
            item.client_ref_id = 1
            item.fin_year = request.POST.get('fyear')
            item.oc_ref_id = request.POST.get('oc_ref')
            item.property_ref_id = request.POST.get('property_id')
            item.from_date = request.POST.get('start_date')
            item.to_date = request.POST.get('end_date')
            item.save()
            return JsonResponse({'msg': "save successfully"})




    except Exception as e:
        logging.exception(str(e))
        return JsonResponse({'msg': 'failed' + str(e)})
