"""
function 1, generate agm and agm details
function 2, render AGM notice and Agenda
function 3, return last_agm, insurance, current AGM notice and Agenda

"""
from django.core.files.storage import FileSystemStorage

from base.models import Client
from my_project.agm_config import TITLE_LIST, CONTENT
from property.models import OcBudget, Property
from scripts.utils.date_utils import convert_datetime_format, agm_date_to_str, oc_financial_period, get_today
from strata.models import AGM, Insurance, AgmDetail

class AGMItem():
    def __init__(self):
        self.property_id = None
        self.oc_id = None
        self.meeting_datetime = None
        self.fyear = None
        self.user = None
        self.location = None
        self.last_agm = None
        self.insurance = None
        self.agm = None
        self.meeting_minutes = None
        self.result = "success"
        self.msg = "AGM saved successfully"
        self.is_init = False
        self.update_flag = False

    def set_instance_from_request(self, request):
        if request.POST.get('agm_id'):
            self.id = int(request.POST.get('agm_id'))
            self.agm = AGM.objects.get(pk=self.id)
            self.update_flag = True
        self.property_id = int(request.POST.get('property_ref'))
        self.oc_id = int(request.POST.get('oc_ref'))
        if request.POST.get('dateTimePicker'):
            self.meeting_datetime = convert_datetime_format(request.POST.get('dateTimePicker'))
        self.fyear = int(request.POST.get('fyear'))
        self.user = request.user.username
        self.location = request.POST.get('location')
        self.is_init = (lambda x: True if (x == "on") else False)(request.POST.get('is_init'))
        if 'meeting_minutes' in request.FILES:
            attachment = request.FILES ['meeting_minutes']
            fs = FileSystemStorage()
            filename = fs.save(attachment.name, attachment)
            self.meeting_minutes = filename

    def set_instance_from_agm(self, agm_id, user='sys'):
        agm_item = AGM.objects.get(pk=int(agm_id))
        self.property_id = agm_item.property_ref_id
        self.oc_id = agm_item.oc_ref_id
        self.meeting_datetime = agm_item.meeting_datetime
        self.fyear = agm_item.fyear
        self.location = agm_item.location
        self.is_validate()
        self.id = agm_id
        self.agm = agm_item
        self.user = user

    def handle(self, request=None):
        if request:
            self.set_instance_from_request(request)

        if self.is_validate() and not self.update_flag:
            self._generate_master_agm()
            self._generate_agm_detail()

        if self.update_flag:
            self._generate_master_agm()

        return self.result, self.msg

    def is_validate(self):
        # if agm is for init purpose then don't need to validate
        if self.is_init:
            return True

        # validate 1 check if fy budget exists
        budget = OcBudget.objects.filter(fin_year=self.fyear, oc_ref_id=self.oc_id).first()
        if budget:
            is_budget = True
        else:
            is_budget = False

            self.msg = str(self.fyear) + "budget for the OC selected doesn't exist, please input budget and retry"
        # validation 2 check if insurance exists
        today = get_today()
        insurance = Insurance.objects.filter(date_from__lte=today, date_to__gte=today,
                                             property_ref_id=self.property_id).first()
        if insurance:
            is_insurance = True
            self.insurance = insurance
        else:
            is_insurance = False
            self.msg = "No valid insurance identified for OC, please input insurance info and retry"

        self.last_agm = AGM.objects.filter(fyear=self.fyear - 1, oc_ref_id=self.oc_id).first()
        if self.last_agm and self.last_agm.meeting_minutes.name:

            is_agm = True
        else:
            is_agm = False
            self.msg = "last year AGM doesn't exist or attachment is missing, please retry"

        if is_budget and is_agm and is_insurance:
            return True
        else:
            self.result = 'fail'
            return False

    def _generate_master_agm(self):
        if self.update_flag:
            agm = self.agm
        else:
            agm = AGM()
        agm.property_ref_id = self.property_id
        agm.oc_ref_id = self.oc_id
        if self.meeting_datetime:
            agm.meeting_datetime = self.meeting_datetime
        agm.fyear = self.fyear
        agm.location = self.location
        agm.client_ref_id = 1
        agm.createby = agm.updateby = self.user
        if self.meeting_minutes:
            agm.meeting_minutes = self.meeting_minutes
        agm.is_init = self.is_init
        agm.save()
        if not self.update_flag:
            self.id = agm.id
            self.agm = agm

    def _generate_agm_detail(self):
        input_para = self._build_agm_para_dict()
        self._init_agm_details(input_para)

    def _build_agm_para_dict(self):
        """

        :param last_agm:
        :param fyear: next financial year
        :param client_name:
        :param oc_id:
        :return:
        """
        if self.is_init:
            return {'[LAST_DATE]': '',
                    '[LAST_FIN_START]': '',
                    '[LAST_FIN_END]': '',
                    '[COMPANY]': ''}

        last_agm_date = agm_date_to_str(self.last_agm.meeting_datetime)
        client_name = Client.objects.get(id=1).client_name
        start_date, end_date = oc_financial_period(self.oc_id, self.fyear)
        return {'[LAST_DATE]': last_agm_date,
                '[LAST_FIN_START]': start_date,
                '[LAST_FIN_END]': end_date,
                '[COMPANY]': client_name}

    def _init_agm_details(self, input_para):
        # only execute if this agm is not for init purpose
        if not self.is_init:
            for index, val in enumerate(TITLE_LIST):
                new_agm_item = AgmDetail()
                new_agm_item.createby = new_agm_item.updateby = self.user
                new_agm_item.agm_ref_id = self.id
                new_agm_item.seq_no = index + 1
                new_agm_item.title = agm_dict_replace(val, input_para)
                new_agm_item.content = agm_dict_replace(CONTENT [index], input_para)
                if " Insurance" in val:
                    new_agm_item.is_insurance = True
                new_agm_item.client_ref_id = 1
                new_agm_item.save()

    def update_invite_path(self, path):
        self.agm.meeting_invite = path
        self.agm.save()

    def generate_title(self):
        property = self.agm.property_ref
        return property.plan_num + '-' + property.street + ',' + property.suburb + "- Notice of Annual General Meeting"


def agm_dict_replace(input_str, para_dict) -> object:
    if '[' in input_str:
        for item in para_dict:
            input_str = input_str.replace(item, para_dict [item])
    return input_str
