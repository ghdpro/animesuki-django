"""History models"""

import logging
from collections import OrderedDict

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.fields.related import ManyToManyField
from django.db.models import FileField
from django.forms.models import model_to_dict
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField

from animesuki.core.utils import get_ip_from_request

logger = logging.getLogger(__name__)


def object_to_dict(obj):
    """Converts model instance into a dictionary"""
    raw = model_to_dict(obj)
    data = OrderedDict()
    for field in obj._meta.get_fields():
        # Excluded: primary key; Not supported: ManyToManyField and FileField
        if field.name in raw and field.name != obj._meta.pk.name \
                and not isinstance(field, ManyToManyField) and not isinstance(field, FileField):
            data[field.name] = raw[field.name]
    return data


def object_data_revert(obj):
    """Obtains unaltered data (before save) from database"""
    if obj.pk:
        data = obj.__class__.objects.get(pk=obj.pk)
        return object_to_dict(data)
    return None


def changed_keys(a, b):
    """Compares two dictionaries and returns list of keys where values are different"""
    # Note! This function disregards keys that don't appear in both dictionaries
    keys = []
    if a is not None and b is not None:
        for k, _ in b.items():
            if k in a and a[k] != b[k]:
                keys.append(k)
    return keys


def filter_data(data, keys):
    """Returns a dictionary with only keys found in list"""
    result = OrderedDict()
    for k in keys:
        if k in data:
            result[k] = data[k]
    return result


class ChangeRequest(models.Model):
    class Type:
        ADD = 1
        MODIFY = 2
        DELETE = 3
        RELATED = 4
        choices = (
            (ADD, 'Add'),
            (MODIFY, 'Modify'),
            (DELETE, 'Delete'),
            (RELATED, 'Related')
        )

    class Status:
        PENDING = 1
        APPROVED = 2
        DENIED = 3
        RETRACTED = 4
        choices = (
            (PENDING, 'Pending'),
            (APPROVED, 'Approved'),
            (DENIED, 'Denied'),
            (RETRACTED, 'Retracted'),
        )

    # ChangeRequest does not support non-integer primary keys
    # Change to TextField() to support all types (at performance cost)
    object_type = models.ForeignKey(ContentType, related_name='%(class)s_object', on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object = GenericForeignKey('object_type', 'object_id')
    object_str = models.CharField(max_length=250, blank=True)
    related_type = models.ForeignKey(ContentType, null=True, blank=True, related_name='%(class)s_related',
                                     on_delete=models.PROTECT)
    request_type = models.PositiveSmallIntegerField(choices=Type.choices)
    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.PENDING)
    data_revert = JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    data_changed = JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    comment = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(class)s_user', on_delete=models.PROTECT)
    user_date = models.DateTimeField(auto_now_add=True)
    user_ip = models.GenericIPAddressField(unpack_ipv4=True)
    mod = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(class)s_mod', null=True, blank=True,
                            on_delete=models.PROTECT)
    mod_date = models.DateTimeField(null=True, blank=True)
    mod_ip = models.GenericIPAddressField(unpack_ipv4=True, null=True, blank=True)

    def set_object(self, obj):
        if obj.pk:
            # Existing object
            self.object = obj
            self.object_str = str(obj)
        else:
            # New object
            self.object_type = ContentType.objects.get_for_model(obj)
            self.object_id = None

    def set_request_type(self, request_type=None):
        if request_type is not None:
            self.request_type = request_type
        elif self.related_type is not None:
            self.request_type = ChangeRequest.Type.RELATED
        elif self.object is not None:
            self.request_type = ChangeRequest.Type.MODIFY
        else:
            self.request_type = ChangeRequest.Type.ADD

    def set_user(self, request):
        self.user = request.user
        # user_date is set automatically (field has auto_now_add flag)
        self.user_ip = get_ip_from_request(request)

    def set_mod(self, request):
        self.mod = request.user
        self.mod_date = timezone.now()
        self.mod_ip = get_ip_from_request(request)

    def save(self, *args, **kwargs):
        # Prevent duplicates: when modifying existing entries, do not save if data_revert equals data_changed
        if (self.request_type not in (self.Type.MODIFY, self.Type.RELATED)) or (self.data_revert != self.data_changed):
            super().save(*args, **kwargs)

    class Meta:
        db_table = 'history'
        permissions = (
            ('self_approve', 'Can self-approve add, modify & related requests'),
            ('self_delete', 'Can self-approve delete requests'),
            ('mod_approve', 'Can moderate add, modify & related requests'),
            ('mod_delete', 'Can moderate delete requests'),
        )
        default_permissions = ()


class HistoryModel(models.Model):
    """Base class for models with History support"""
    history_add = models.DateTimeField(auto_now_add=True, blank=True)
    history_modify = models.DateTimeField(auto_now=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cr = None
        self._request = None
        self._comment = ''

    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, request):
        self._request = request

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, comment):
        self._comment = comment

    def create_changerequest(self, request_type=None):
        cr = ChangeRequest()
        cr.set_object(self)
        cr.set_request_type(request_type)
        cr.status = ChangeRequest.Status.PENDING
        cr.data_revert = object_data_revert(self)
        cr.data_changed = object_to_dict(self)
        if cr.request_type == ChangeRequest.Type.MODIFY:
            fields = changed_keys(cr.data_revert, cr.data_changed)
            if len(fields) > 0:  # Leave data_revert & data_changed as-is if there were no changes
                cr.data_revert = filter_data(cr.data_revert, fields)
                cr.data_changed = filter_data(cr.data_changed, fields)
        elif cr.request_type == ChangeRequest.Type.DELETE:
            cr.data_changed = None
        cr.comment = self.comment
        cr.set_user(self.request)
        # Self-approve if user has proper permissions
        if (self.request.user.has_perm('history.self_approve') or
                (cr.request_type == ChangeRequest.Type.DELETE and self.request.user.has_perm('history.self_delete'))):
            cr.set_mod(self.request)
            cr.status = ChangeRequest.Status.APPROVED
        return cr

    def log(self):
        obj = '{}'.format(self._cr.object_type)
        if self._cr.object_str:
            obj += ' "{}"'.format(self._cr.object_str)
        user = '"{}" ({})'.format(self._cr.user.username, self._cr.user.pk)
        mod = ''
        if self._cr.mod is not None:
            mod = ' mod "{}" ({})'.format(self._cr.mod.username, self._cr.mod.pk)
        logger.info('ChangeRequest: [{}] [{}] {} user {}{}'.format(self._cr.get_request_type_display(),
                                                                   self._cr.get_status_display(),
                                                                   obj, user, mod))

    def save(self, *args, **kwargs):
        self._cr = self.create_changerequest()
        self._cr.save()
        # Save actual model instance if: ChangeRequest object was saved -and- the request was (self) approved
        # (ChangeRequest object will not have been saved if data was not altered)
        if self._cr.pk and self._cr.status == ChangeRequest.Status.APPROVED:
            super().save(*args, **kwargs)
            self._cr.set_object(self)
            self._cr.save()
        self.log()

    def delete(self, *args, **kwargs):
        self._cr = self.create_changerequest(request_type=ChangeRequest.Type.DELETE)
        self._cr.save()
        if self._cr.status == ChangeRequest.Status.APPROVED:
            super().delete(*args, **kwargs)
        self.log()

    class Meta:
        abstract = True
