from django.contrib.auth.models import User

from base.models import Notification
from finance.models import Supplier
from property.models import Lot, LotOCMap
from scripts.DB.DBClass import MySQLClass
from scripts.utils.property_utils import get_oc_name, get_property_name


class Notify:

    def init_strategy(self):
        self.sub_class_list = []
        self.sub_class_list.append(OwnerNotify())
        self.sub_class_list.append(BillingNotify())
        self.sub_class_list.append(VendorNotify())
        self.sub_class_list.append(BillingRemind())
        self.sub_class_list.append(AgmOwnerNotify())

    def notify(self, data):

        for item in self.sub_class_list:
            item.support(data)

    def support(self, data):
        pass

    def handler(self):
        pass

    def get_user_list(self, role):
        sql_stat = "select au.username from auth_user_groups gp left join auth_user au on gp.user_id = au.id" \
                   " where gp.id= (select id from auth_group where name='%s')"
        sql_stat = sql_stat % role
        result = MySQLClass().get_result(sql_stat)
        admin_users = User.objects.filter(is_superuser=True)
        user_list = []
        if result [0] is not None:
            for item in result:
                user_list.append(item [0])

        for item in admin_users:
            if item.username not in user_list:
                user_list.append(item.username)

        return user_list


class OwnerNotify(Notify):

    def support(self, data):
        if data ['note_type'] == 'owner':
            self.para = data
            self.handler()

    def handler(self):
        property_id = self.para ['property_id']
        title = self.para ['title']
        body = self.para ['body']
        purpose = self.para ['purpose']

        if 'attachment' in self.para:
            attachment = self.para ['attachment']
        else:
            attachment = None
        owner_list = Lot.objects.filter(property_ref_id=property_id)

        for item in owner_list:
            mail_list = get_mail_list(purpose, item)
            for mail in mail_list:
                self.save_notification(property_id, item.id, mail, title, body, attachment)

    def save_notification(self, property_id, lot_id, email, title, body, attachment=None):
        note = Notification()
        note.user_name = email
        note.msg_subject = title
        note.msg_body = body
        if attachment is not None:
            note.attachment = attachment
        note.read_status = "unread"
        note.email_status = "prepared"
        note.category = "email-note"
        note.property_id = property_id
        note.lot = lot_id
        note.client_ref_id = self.para ['client_id']
        note.createby = self.para ['user']
        note.updateby = self.para ['user']
        if 'cc' in self.para:
            note.cc = self.para ['cc']
        note.save()


class BillingNotify(Notify):

    def support(self, data):
        if data ['note_type'] == 'billing_manager':
            self.para = data
            self.handler()

    def handler(self):
        property_id = self.para ['property_id']
        oc_id = self.para ['oc_id']
        date_from = self.para ['date_from']
        user_list = self.get_user_list("manager")
        oc_name = get_oc_name(oc_id)
        title = oc_name + "billing from" + date_from + " generated"

        for item in user_list:
            self.save_notification(item, property_id, oc_id, title, title)

    # lot_id is the pk of lot so that mail service can use pk to get the email address

    def save_notification(self, username, property_id, oc_id, title, body):
        note = Notification()
        note.user_name = username
        note.msg_subject = title
        note.msg_body = body
        note.read_status = "unread"
        note.email_status = "na"
        note.category = "note"
        note.property_id = property_id
        note.oc_id = oc_id
        note.client_ref_id = self.para ['client_id']
        note.createby = self.para ['user']
        note.updateby = self.para ['user']
        if 'cc' in self.para:
            note.cc = self.para ['cc']
        note.save()


class VendorNotify(Notify):

    def support(self, data):
        if data ['note_type'] == 'vendor':
            self.para = data
            self.handler()

    def handler(self):
        vendor_id = self.para ['vendor_id']
        title = self.para ['title']
        body = self.para ['body']

        if 'attachment' in self.para:
            attachment = self.para ['attachment']
        else:
            attachment = None

        if Supplier.objects.filter(id=vendor_id).exists():
            email = Supplier.objects.get(pk=vendor_id).contact_email
            self.save_notification(email, title, body, attachment)

    def save_notification(self, email, title, body, attachment=None):
        note = Notification()
        note.user_name = email
        note.msg_subject = title
        note.msg_body = body
        if attachment is not None:
            note.attachment = attachment
        note.read_status = "na"
        note.email_status = "prepared"
        note.category = "email"
        note.client_ref_id = self.para ['client_id']
        note.createby = self.para ['user']
        note.updateby = self.para ['user']
        if 'cc' in self.para:
            note.cc = self.para ['cc']
        note.save()


class BillingRemind(Notify):
    def support(self, data):
        if data ['note_type'] == 'remind':
            self.para = data
            self.handler()

    def handler(self):
        title = self.para ['title']
        body = self.para ['body']
        purpose = self.para ['purpose']
        bill = self.para ['bill']
        lot = Lot.objects.get(pk=bill.lot_ref_id)
        if 'attachment' in self.para:
            attachment = self.para ['attachment']
        else:
            attachment = None

        mail_list = get_mail_list(purpose, lot)
        for mail in mail_list:
            self.save_notification(bill, lot, mail, title, body, attachment)

    def save_notification(self, bill, lot, email, title, body, attachment=None):
        note = Notification()
        note.user_name = email
        note.msg_subject = title
        note.msg_body = body
        if attachment is not None:
            note.attachment = attachment
        note.read_status = 'na'
        note.email_status = "prepared"
        note.category = "email"
        note.property_id = bill.get_property_id()
        note.oc_id = bill.oc_ref_id
        note.lot = lot.unit_no
        note.client_ref_id = self.para ['client_id']
        note.createby = self.para ['user']
        note.updateby = self.para ['user']
        if 'cc' in self.para:
            note.cc = self.para ['cc']
        note.save()


class AgmOwnerNotify(Notify):

    def support(self, data):
        if data ['note_type'] == 'agm_owner':
            self.para = data
            self.handler()

    def handler(self):
        property_id = self.para ['property_id']
        oc_id = self.para ['oc_id']
        title = self.para ['title']
        body = self.para ['body']
        purpose = self.para ['purpose']

        if 'attachment' in self.para:
            attachment = self.para ['attachment']
        else:
            attachment = None
        owner_list = []
        map_list = LotOCMap.objects.filter(oc_ref_id=oc_id)
        for item in map_list:
            owner_list.append(item.lot_ref)

        for item in owner_list:
            mail_list = get_mail_list(purpose, item)
            for mail in mail_list:
                self.save_notification(property_id, oc_id, item.id, mail, title, body, attachment)

    def save_notification(self, property_id, oc_id, lot_id, email, title, body, attachment=None):

        note = Notification()
        note.user_name = email
        note.msg_subject = title
        note.msg_body = body
        if attachment is not None:
            note.attachment = attachment
        note.read_status = "unread"
        note.email_status = "prepared"
        note.category = "email-note"
        note.property_id = property_id
        note.oc_id = oc_id
        note.lot = lot_id
        note.client_ref_id = self.para ['client_id']
        note.createby = self.para ['user']
        note.updateby = self.para ['user']
        if 'cc' in self.para:
            note.cc = self.para ['cc']

        note.save()


def get_mail_list(purpose, lot):
    """
    input para: purpose (levy, general,owner)
    levy then go for levy
    15/06/2021 general notice add tenant email address
    """
    mail_list = []
    if purpose == 'owner' or purpose == "agm_owner":
        mail_list = lot.get_owner_mail()
    elif purpose == 'general' and lot.general_mail == 'owner':
        mail_list = lot.get_owner_mail()
        mail_list = mail_list + lot.get_tenant_mail()
    elif purpose == 'general' and lot.general_mail == 'agent':
        mail_list = lot.get_agent_mail()
        mail_list = mail_list + lot.get_tenant_mail()
    elif purpose == 'levy' and lot.prefer_mail == 'owner':
        mail_list = lot.get_owner_mail()
    elif purpose == 'levy' and lot.prefer_mail == 'agent':
        mail_list = lot.get_agent_mail()

    return mail_list
