# This module is used to generate fs and return the url
from finance.models import FS
from scripts.utils.date_utils import oc_financial_period
from scripts.PDF_service.pdf import agm_pdf_to_file
from scripts.GL.fs import FinStat


def agm_generate_fs(agm_item):
    """
    1. get oc id, start date and end date
    2. check if fs exists if not then create
    3. generate the pdf and return the path
    :param agm_item:
    :return:
    """
    from_date, to_date = oc_financial_period(agm_item.oc_id, agm_item.fyear, 'date')

    fs = FS.objects.filter(oc_ref_id=agm_item.oc_id, from_date=from_date, to_date=to_date, ).first()

    if not fs:
        fs = FS()
        fs.client_ref_id = 1
        fs.createby = fs.updateby = agm_item.user
        fs.from_date = from_date
        fs.to_date = to_date
        fs.fin_year = agm_item.fyear
        fs.oc_ref_id = agm_item.oc_id
        fs.property_ref_id = agm_item.property_id
        fs.save()
    fs_report = FinStat(fs.id)
    context = fs_report.generate_fs()
    file_name = str(agm_item.id) + 'fs.pdf'
    fs_url = agm_pdf_to_file("fs_template.html", context, file_name, '/css/report.css')
    return fs_url
