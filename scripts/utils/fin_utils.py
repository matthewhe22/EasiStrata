from django.db.models import Q, Max

from finance.models import ClientLedger, GL, Billing, COA, FS
from scripts.GL.fs import FinStat
from scripts.PDF_service.render_pdf_to_file import pdf_to_file
from scripts.utils.date_utils import get_today
from scripts.GL.create_gl import GLGenerator
from scripts.utils.property_utils import get_property_id_from_ocid


def bill_payment_gl(bill, amount, user, recpt_num=None, payment_date=None, reverse=False):
    if payment_date is None:
        payment_date = get_today()
    # payment after billing from

    if payment_date >= bill.billing_from:
        data = {'oc_id': bill.oc_ref_id,
                'client_id': 1,
                'amount': amount,
                'inc_exp': "BS300000",
                'desc': recpt_num + " payment",
                'user': user,
                'posting_date': payment_date
                }

    else:
        """
        payment before billing from date
        1. get today generate advance payment gls, Dr cash Cr pay in advance
        2. on the billing from date, Dr pay in advance Cr AR
        3. 
        """
        # levy in advance
        data = {'oc_id': bill.oc_ref_id,
                'client_id': 1,
                'amount': amount,
                'inc_exp': "BS400004",
                'desc': recpt_num + " payment",
                'user': user,
                'posting_date': payment_date
                }

        # net off payment in advance
        data_net_off = {'oc_id': bill.oc_ref_id,
                        'client_id': 1,
                        'amount': amount,
                        'inc_exp': "BS300003",
                        'desc': recpt_num + " payment",
                        'user': user,
                        'posting_date': bill.billing_from
                        }

        if reverse:
            data_net_off ['reverse'] = True
            data_net_off ['desc'] = bill.billing_num + " reset"

        je = GLGenerator(data_net_off)
        je.generate_je()

    if reverse:
        data ['reverse'] = True
        data ['desc'] = bill.billing_num + " reset"

    je = GLGenerator(data)
    je.generate_je()

    # advance payment


def payment_in_advance(oc_id, amount, user, payment_date, recpt_no, reverse=False):
    data = {'oc_id': oc_id,
            'client_id': 1,
            'amount': amount,
            'inc_exp': "BS400004",
            'desc': recpt_no + " payment",
            'user': user,
            'posting_date': payment_date
            }

    if reverse:
        data ['reverse'] = True
        data ['desc'] = recpt_no + "payment reset"

    je = GLGenerator(data)
    je.generate_je()


# @Feb 15 change parameter from lot_id only to lot_id and oc_id
def get_lot_balance(oc_id, lot_id):
    cur_balance = ClientLedger.objects.filter(oc_ref_id=oc_id, lot_ref_id=lot_id).order_by('-id').first()
    if cur_balance:
        return cur_balance.balance
    else:
        return 0.00


def get_latest_lot_balance(oc_id, lot_id):
    cur_balance = ClientLedger.objects.filter(oc_ref_id=oc_id, lot_ref_id=lot_id).order_by('-id').first()
    if cur_balance:
        result = {'cur_bal': cur_balance.balance,
                  'last_bal': cur_balance.balance + cur_balance.debit_amt}
        return result
    else:
        return {'cur_bal': 0,
                'last_bal': 0}


def get_invoice_lot_balance(lot_id, inv_num):
    cur_balance = ClientLedger.objects.filter(lot_ref_id=lot_id, reference__contains=inv_num).first()
    if cur_balance:
        result = {'cur_bal': cur_balance.balance,
                  'last_bal': cur_balance.balance + cur_balance.debit_amt}
        return result
    else:
        return {'cur_bal': 0,
                'last_bal': 0}


def reverse_cp_entry(keyword, user):
    """
    This function is to be used to reverse cash receipt or billing journal entry, for cash receipt pass in cash receipt no
    for billing pass in billing num

    :param keyword:
    :param user:
    :return:
    """
    entries = GL.objects.filter(Q(description__icontains=keyword), ~Q(description__icontains='reversal'))
    if entries:
        for item in entries:
            reverse_item = item
            reverse_item.id = None
            reverse_item.createby = reverse_item.updateby = user
            reverse_item.createtime = reverse_item.updatetime = reverse_item.posting_date = get_today()
            if reverse_item.dc == 'dr':
                reverse_item.dc = 'cr'
            else:
                reverse_item.dc = 'dr'

            reverse_item.description = reverse_item.description + ' reversal'
            reverse_item.save()


def check_latest_bill(bill):
    """

    :param bill:
    :return: true/false on whether bill passed in is the latest bill in the billing table
    """
    oc_id = bill.oc_ref_id
    lot_id = bill.lot_ref_id
    latest_item = Billing.objects.filter(is_valid=True, oc_ref_id=oc_id, lot_ref_id=lot_id).order_by(
        '-id').first()
    if latest_item:
        return latest_item.id == bill.id

    else:
        return False


def get_account_category(property_budget_item):
    category = COA.objects.get(acc_code=property_budget_item.acc_code).category
    return category


def generate_fs_file(oc_id, from_date, to_date, fyear, user):
    fs = FS.objects.filter(oc_ref_id=oc_id, from_date=from_date, to_date=to_date, ).first()

    if not fs:
        fs = FS()
        fs.client_ref_id = 1
        fs.createby = fs.updateby = user
        fs.from_date = from_date
        fs.to_date = to_date
        fs.fin_year = fyear
        fs.oc_ref_id = oc_id

        fs.property_ref_id = get_property_id_from_ocid(oc_id)
        fs.save()
    fs_report = FinStat(fs.id)
    context = fs_report.generate_fs()
    file_name = str(oc_id) + 'fs.pdf'
    fs_url = pdf_to_file("fs_template.html", context, file_name, '/css/report.css', tmp_folder='/temp_oc/')
    return fs_url


def get_paid_to_date(oc_id, lot_id):
    last_item = Billing.objects.filter(status='paid', lot_ref=lot_id, oc_ref=oc_id, special_flag=False).aggregate(
        Max('billing_to'))
    if last_item:
        return last_item ['billing_to__max']
    else:
        return None


def generate_billing_info(lot, property):
    billing_name2 = ''
    billing_name1 = lot.owner_name1
    if lot.owner_name2 is not None:
        billing_name2 = lot.owner_name2

    if lot.billing_adr is not None:
        billing_address = lot.billing_adr
    else:
        billing_address = 'Unit ' + lot.unit_no + ', ' + property.street + ' ' + property.state + ' ' + property.post_code
    return {'billing_name1': billing_name1,
            'billing_name2': billing_name2,
            'billing_address': billing_address}
