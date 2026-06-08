from datetime import datetime

from django.db import transaction
from django.http import HttpResponse

from base.models import Sequence
from property.models import LotOCMap, Lot


def build_liability_dict(oc_ref_id):
    if type(oc_ref_id).__name__ == 'int':
        liability_dict = {}
        maps = LotOCMap.objects.filter(oc_ref_id=oc_ref_id)
        for item in maps:
            liability_dict [item.lot_ref_id] = round(float(item.liability), 2)

        return liability_dict
    else:
        return False


def allocate_levy(dict_amt, total_amt):
    total_amt = float(total_amt)
    total = 0.00
    lot_levy = {}
    for item in dict_amt:
        if dict_amt [item] > 0:
            total = total + dict_amt [item]

    for item in dict_amt:
        lot_levy [item] = round(dict_amt [item] / total * total_amt, 2)

    return lot_levy


def dist_percent(dict_amt):
    total_record = len(dict_amt)
    count = 0
    total = 0.00
    acc_rate = 0.0000
    dict_percent = {}
    for item in dict_amt:
        if dict_amt [item] > 0:
            total = total + dict_amt [item]

    for item in dict_amt:
        count = count + 1

        if count != total_record:
            dict_percent [item] = round(max(dict_amt [item], 0) / total, 4)
            acc_rate = round(acc_rate + dict_percent [item], 4)
        else:
            dict_percent [item] = round(1.0000 - acc_rate, 4)

    return dict_percent


# distribute the total number to separate element


def amt_distrbute(percentage_dict, total_amount):
    total_record = len(percentage_dict)
    count = 0
    dist_number = 0.00

    dict_amt = {}

    for item in percentage_dict:
        count = count + 1

        if count != total_record:
            dict_amt [item] = round(total_amount * percentage_dict [item], 2)
            dist_number = dist_number + dict_amt [item]
        else:
            dict_amt [item] = round(total_amount - dist_number, 2)

    return dict_amt


@transaction.atomic
def generate_id(code):
    sid1 = transaction.savepoint()

    while True:
        try:
            cur_seq = Sequence.objects.get(seq_code=code)
        except:
            transaction.savepoint_rollback(sid1)
            return HttpResponse('invalid sequence code')
        cur_num = cur_seq.seq_num
        add_zero = cur_seq.seq_char_width - len(str(cur_num)) - len(cur_seq.seq_prefix)
        output_id = cur_seq.seq_prefix + '0' * add_zero + str(cur_num)
        try:
            # optimistic lock
            result = Sequence.objects.filter(seq_code=code, seq_num=cur_num).update(seq_num=cur_num + 1)
        except:
            transaction.savepoint_rollback(sid1)
            return HttpResponse('sequence number generation failed')

        if result == 0:
            continue
        break

    return output_id


def distribute_value(total_value, total_num):
    first_number = round(total_value / total_num, 2)
    distributed_total = 0
    value_list = []
    for i in range(total_num - 1):
        value_list.append(first_number)
        distributed_total = distributed_total + first_number

    value_list.append(total_value - distributed_total)

    return value_list


def transform_lotid_to_lot(input_dict):
    """
    function used for output of build liability dict and allocate levy
    to transfer its key(id of Lot) to lot name
    :param input_dict:
    :return:
    dictionary with the values of original dict but the key is the lot name
    """
    # Fetch all Lot rows in a single query instead of one query per key (N+1)
    lots = {lot.id: lot for lot in Lot.objects.filter(id__in=[int(item) for item in input_dict])}
    output_dict = {}
    for item in input_dict:
        output_dict [lots [int(item)]] = input_dict [item]
    return output_dict
