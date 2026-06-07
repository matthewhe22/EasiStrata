import logging
import os

from finance.models import Occertificate
from scripts.PDF_service.render_pdf_to_file import pdf_to_file
from scripts.PDF_service.pdf_generator import merge_pdf_files
from scripts.billing.oc_cert import Certificate
from scripts.utils.date_utils import get_fin_year, oc_financial_period, str_to_date
from property.models import OCMaster
from scripts.utils.fin_utils import generate_fs_file
from scripts.utils.property_utils import get_property_id_from_ocid
from strata.models import AGM, Insurance
from my_project.settings import STATIC_DIR

STATEMENT_URL = os.path.join(STATIC_DIR, "template/Statement_of_advice.pdf")


class OCCert():
    def __init__(self, id):
        # cert is the instance of the oc certificate

        self.fyear = None
        self.oc_id = None
        self.issue_date = None
        self.is_valid = True
        self.is_before_oc = False
        self.attachment_list = None
        self.attachment_url_list = []
        self.error = ''
        self.oc_cert_id = id

    def set_attributes_from_request(self, request, attachment_list):
        self.oc_id = int(request.POST.get('oc_ref'))
        self.issue_date = str_to_date(request.POST.get('issue_date'))
        self.attachment_list = attachment_list
        self.user = request.user.username
        self.request = request

    def _get_oc_rules(self):
        if 'oc_rule' in self.attachment_list:
            self.oc = OCMaster.objects.get(pk=self.oc_id)

            if self.oc.oc_rule.name:
                self.attachment_url_list.append(self.oc.oc_rule.path)
            else:
                self.is_valid = False
                self.error = self.error + "No OC rule identified"

    def _get_agm_minutes(self):
        if 'last_agm' in self.attachment_list:
            self.fyear = get_fin_year(self.oc_id, self.issue_date)
            if self.is_before_oc:
                fyear = self.oc.billing_start_date.year
            else:
                fyear = self.fyear - 1
            agm = AGM.objects.filter(fyear=fyear, oc_ref_id=self.oc_id).first()
            if agm:
                if agm.meeting_minutes.name:
                    self.attachment_url_list.append(agm.meeting_minutes.path)
                else:
                    self.is_valid = False
                    self.error = self.error + "No last year" + str(fyear) + " agm minutes identified"

            else:
                self.is_valid = False
                self.error = self.error + "No last year agm minutes identified"

    def _get_statement(self):
        if 'statement' in self.attachment_list:
            self.attachment_url_list.append(STATEMENT_URL)

    def _get_fs(self):
        if 'fs' in self.attachment_list:
            start_date, end_date = oc_financial_period(self.oc_id, self.fyear, return_type="date",
                                                       end_date=self.issue_date)
            fs_url = generate_fs_file(self.oc_id, start_date, end_date, self.fyear, self.user)
            self.attachment_url_list.append(fs_url)

    def _get_certificate_currency(self):
        # today = get_today()
        if self.is_before_oc:
            issue_date = self.oc.billing_start_date
        else:
            issue_date = self.issue_date

        insurance = Insurance.objects.filter(date_from__lte=issue_date, date_to__gte=issue_date,
                                             property_ref_id=get_property_id_from_ocid(self.oc_id)).first()
        if insurance:
            self.attachment_url_list.append(insurance.currency_cert.path)

        else:
            self.is_valid = False
            self.error = self.error + "no valid certificate currency exists"

    def _generate_oc_cert(self):
        oc_cert = Certificate(self.oc_cert_id)
        context = oc_cert.generate_feed_data()
        file_name = str(self.oc_cert_id) + "oc_cert.pdf"
        oc_cert_url = pdf_to_file("oc_cert.html", context, file_name, '/css/cert.css', tmp_folder='/temp_oc/',
                                  request=self.request)
        self.attachment_url_list.append(oc_cert_url)

    def _combine_pdfs(self):
        filename = str(self.oc_cert_id) + "OC_certificate.pdf"
        return merge_pdf_files(self.attachment_url_list, filename, upload_to='certificate/')

    def _set_before_oc_start_flag(self):
        if self.issue_date < self.oc.billing_start_date:
            self.is_before_oc = True

    def handle(self):

        """
        sequence is as following
        1. generate oc certificate
        2. rules of oc
        3. copy of last year AGM meeting minutes
        4. FS
        5. certificate of currency
        :return:
        """
        try:
            self._generate_oc_cert()
            self._get_oc_rules()
            self._set_before_oc_start_flag()
            self._get_statement()
            self._get_agm_minutes()
            self._get_certificate_currency()
            if not self.is_before_oc:
                # if oc certificate is generated before oc start date then don't need to generate fs
                self._get_fs()

            combined_pdf_url = self._combine_pdfs()
            return self.is_valid, self.error, combined_pdf_url
        except Exception as e:
            logging.exception(e)
            return False, str(e), ''
