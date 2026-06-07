from property.models import OCMaster, Property
from base.models import Client


def get_property_name(property_id):
    if Property.objects.filter(id=property_id).exists():
        return Property.objects.get(id=property_id).name
    else:
        return None


def get_oc_name(oc_id):
    if OCMaster.objects.filter(id=oc_id).exists():
        return OCMaster.objects.get(id=oc_id).title
    else:
        return None


def get_property_from_oc(oc_id):
    if OCMaster.objects.filter(id=oc_id).exists():
        property_id = OCMaster.objects.get(id=oc_id).property_ref_id
        return Property.objects.get(id=property_id).name
    else:
        return None


def get_property_gst_from_oc(oc_id):
    if OCMaster.objects.filter(id=oc_id).exists():
        property_id = OCMaster.objects.get(id=oc_id).property_ref_id
        return Property.objects.get(id=property_id).GST_register
    else:
        return None


def get_oclist_from_property(property_id):
    OCs = OCMaster.objects.filter(property_ref_id=property_id)
    oc_list = []
    for item in OCs:
        oc_list.append(item.pk)

def get_property_id_from_ocid(oc_id):
    if OCMaster.objects.filter(id=oc_id).exists():
        property_id = OCMaster.objects.get(id=oc_id).property_ref_id
        return property_id
    else:
        return None
