from decimal import Decimal

from scripts.utils.date_utils import get_today, str_to_date


def model_instance_maintain(obj, request):
    # this function is used to either create or update a instance

    for attr, value in obj.__dict__.items():
        obj_model = type(obj)

        field_type = obj_model._meta.get_field(attr).get_internal_type

        if 'create' in attr or 'update' in attr or attr == 'id' or 'client' in attr:

            if attr in ('createby', 'updateby'):
                setattr(obj, attr, request.POST.user.username)

            if attr in ('createtime', 'updatetime'):
                setattr(obj, attr, get_today())

            if 'client' in attr:
                obj.client_ref_id = 1


        else:
            # a.model._meta.get_field('g').get_internal_type()
            if field_type == 'DateField':
                setattr(obj, attr, str_to_date(request.POST.get(attr)))
            elif field_type == 'IntegerField':
                setattr(obj, attr, int(request.POST.get(attr)))
            elif field_type == 'DecimalField':
                setattr(obj, attr, Decimal(request.POST.get(attr)))
            else:
                setattr(obj, attr, request.POST.get(attr))

    obj.save()

    return obj.id, obj
