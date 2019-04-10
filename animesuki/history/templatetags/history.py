"""History Template Tags"""

from django import template
from django.contrib.contenttypes.models import ContentType

from ..models import ChangeRequest

register = template.Library()


@register.inclusion_tag('history/_history.html')
def history_list(obj):
    history = ChangeRequest.objects.filter(object_id=obj.pk, object_type=ContentType.objects.get_for_model(obj),
                                           related_type=None)\
        .select_related('user').order_by('-date_modified', '-date_created')
    return {'history': history}


@register.inclusion_tag('history/_history.html')
def history_list_related(obj, related):
    history = ChangeRequest.objects.filter(object_id=obj.pk, object_type=ContentType.objects.get_for_model(obj),
                                           related_type=ContentType.objects.get_for_model(related))\
        .select_related('user').order_by('-date_modified', '-date_created')
    return {'history': history}
