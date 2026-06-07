from finance.models import Billing
from scripts.utils.date_utils import get_today
from scripts.utils.fin_utils import get_latest_lot_balance
from decimal import Decimal
from django.db.models import F


# this interface is used to handle cash receipt amount and update corresponding billings' collected amount and change payment status

def handle_payment(oc_id, lot_id, amount, user):
    amount = Decimal(amount)
    balance = Decimal(get_latest_lot_balance(oc_id, lot_id) ['last_bal'])
    if amount >= 0:
        increase_payment(oc_id, lot_id, amount, user)

    elif amount < 0 and balance > 0:
        amount = min(balance + amount, 0)
        reverse_payment(oc_id, lot_id, amount, user)
        # add =0 to below condition to cater for balance is 0
    elif amount < 0 and balance <= 0:
        reverse_payment(oc_id, lot_id, amount, user)

    # This ORM means that collected amount = billing amount to update its status to paid
    Billing.objects.filter(collected_amount=F('billing_amount')).update(status='paid')


def increase_payment(oc_id, lot_id, amount, user):
    billings = Billing.objects.filter(oc_ref_id=oc_id, lot_ref_id=lot_id, status='unpaid', is_valid=True).order_by('id')

    if billings:
        for item in billings:
            if amount >= item.get_payable():
                amount = amount - item.get_payable()
                item.collected_amount = item.billing_amount
                item.status = 'paid'
                item.updateby = user
                item.updatetime = get_today()
                item.save()
            else:
                item.collected_amount = item.collected_amount + amount

                item.updateby = user
                item.updatetime = get_today()
                item.save()
                break


def reverse_payment(oc_id, lot_id, amount, user):
    if amount < 0:
        billings = Billing.objects.filter(collected_amount__gt=0, oc_ref_id=oc_id, lot_ref_id=lot_id,
                                          is_valid=True).order_by('-id')
        amount = Decimal(amount)
        if billings:
            for item in billings:
                if abs(amount) >= item.collected_amount:
                    amount = amount + item.collected_amount
                    item.collected_amount = 0
                    item.status = 'unpaid'
                    item.updateby = user
                    item.updatetime = get_today()
                    item.save()
                else:
                    item.collected_amount = item.collected_amount + amount
                    if item.get_payable() > 0:
                        item.status = "unpaid"
                    else:
                        item.status = 'paid'

                    item.updateby = user
                    item.updatetime = get_today()
                    item.save()
                    break
