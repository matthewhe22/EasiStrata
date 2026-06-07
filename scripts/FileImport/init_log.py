from django.contrib import messages
import os
from django.conf import settings
from base.models import ImportLog, Client, DataSource
from django.shortcuts import render, redirect

from django.core.files.storage import FileSystemStorage


def new_importlog(request,clientcode,datasource,filename):
    """

    :param request:
    :param clientcode:
    :param datasource:
    :param filename:
    :return:False means error True means validation passed
    """

    newdoc = ImportLog(status='03',client_ref_id=clientcode)
    if not Client.objects.filter(pk=clientcode).exists():
        newdoc.status, newdoc.error_message = '02', f'Client "{clientcode}" does not exist'
    elif not DataSource.objects.filter(client_ref_id=clientcode, id=datasource).exists():
        newdoc.status, newdoc.error_message = '02', f'Datasource  does not exist'
    if newdoc.status == '02':
        newdoc.save()
        messages.error(request, f'Failed: {newdoc.error_message}')
        raise Exception('Data Import invalid client id / data source id')
    newdoc.src_ref_id = datasource
    newdoc.client_ref_id = clientcode
    newdoc.doc = filename
    newdoc.save()
    import_id: int=newdoc.id
    myfilepath = os.path.join(settings.MEDIA_ROOT, filename)
    return myfilepath,import_id

