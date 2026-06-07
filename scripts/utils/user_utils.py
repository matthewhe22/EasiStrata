from django.contrib.auth.models import User

from property.models import Lot


def create_owner_account(lot_id):
    if type(lot_id).__name__ == 'int':
        lot = Lot.objects.filter(id=lot_id).first()
        if lot and lot.lot and lot.property_ref.plan_num:
            user_name = lot.property_ref.plan_num.lower() + '-' + lot.lot.lower()

            if User.objects.filter(username=user_name).first() is None and lot.owner_name1:
                # in case plan number
                # Password: Lot No.+ first 3 letters of Owner name 1
                owner = lot.owner_name1.lower().replace(" ", "") [:3]
                password = lot.lot.lower() + owner
                new_user = User()
                new_user.username = user_name
                new_user.first_name = lot.owner_name1
                new_user.set_password(password)
                new_user.is_staff = False
                new_user.save()
                return new_user.id
    else:
        return False


def init_lot_user():
    lots = Lot.objects.filter(user_id__isnull=True)
    for item in lots:
        user_id = create_owner_account(item.id)
        item.user_id = user_id
        item.save()
