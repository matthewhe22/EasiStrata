import logging

from finance.models import ClientLedger
from scripts.utils.date_utils import get_today


def create_client_ledger(oc_id, lot_id, amount, reference, user, trans_date=None, desc=None):
    if trans_date is None:
        trans_date = get_today()

    new_ledger = ClientLedger()
    new_ledger.createby = new_ledger.updateby = user
    amount = float(amount)
    if amount > 0:
        new_ledger.credit_amt = amount
    else:
        new_ledger.debit_amt = abs(amount)
    new_ledger.trans_date = trans_date
    new_ledger.reference = reference
    new_ledger.lot_ref_id = lot_id
    new_ledger.oc_ref_id = oc_id
    new_ledger.balance = float(get_client_balance(oc_id, lot_id)) + amount
    new_ledger.client_ref_id = 1

    if desc:
        new_ledger.description = desc
    try:
        new_ledger.save()
    except Exception as e:
        logging.exception(e)


def get_client_balance(oc_id, lot_id):
    records = ClientLedger.objects.filter(lot_ref_id=lot_id, oc_ref_id=oc_id).order_by('-id')
    if records:
        latest_record = records [0]
        return latest_record.balance
    else:
        return 0.00
