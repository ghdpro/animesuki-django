"""History Template Tags"""

from django import template
from django.contrib.contenttypes.models import ContentType

from ..models import ChangeRequest

register = template.Library()


@register.inclusion_tag('history/_list.html')
def history_list(obj):
    data = []
    result = ChangeRequest.objects.filter(object_id=obj.pk, object_type=ContentType.objects.get_for_model(obj),
                                          related_type=None)\
        .select_related('user', 'mod').order_by('-date_modified', '-date_created')
    for cr in result:
        row = dict()
        row['related'] = False
        if cr.date_modified:
            row['date'] = cr.date_modified
        else:
            row['date'] = cr.date_created
        row['request_type'] = cr.get_request_type_display()
        row['status'] = cr.get_status_display()
        if cr.request_type != ChangeRequest.Type.ADD:
            row['fields'] = cr.diff()
        else:
            row['fields'] = dict()
        row['user'] = cr.user
        row['mod'] = cr.mod
        row['url'] = cr.get_absolute_url()
        data.append(row)
    return {'history': data}


@register.inclusion_tag('history/_list.html')
def history_list_related(obj, related):
    data = []
    result = ChangeRequest.objects.filter(object_id=obj.pk, object_type=ContentType.objects.get_for_model(obj),
                                          related_type=ContentType.objects.get_for_model(related))\
        .select_related('user', 'mod').order_by('-date_modified', '-date_created')
    for cr in result:
        row = dict()
        row['related'] = True
        if cr.date_modified:
            row['date'] = cr.date_modified
        else:
            row['date'] = cr.date_created
        row['request_type'] = cr.get_request_type_display()
        row['status'] = cr.get_status_display()
        row['fields'] = dict()
        diff = cr.diff_related()
        if len(diff['added']) > 0:
            row['fields']['added'] = len(diff['added'])
        if len(diff['modified']) > 0:
            row['fields']['modified'] = len(diff['modified'])
        if len(diff['deleted']) > 0:
            row['fields']['deleted'] = len(diff['deleted'])
        row['user'] = cr.user
        row['mod'] = cr.mod
        row['url'] = cr.get_absolute_url()
        data.append(row)
    return {'history': data}
