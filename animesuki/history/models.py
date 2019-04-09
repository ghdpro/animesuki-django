"""History models"""

import logging
from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.fields.related import ManyToManyField
from django.db.models import Field, FileField
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.contrib import messages

from animesuki.core.utils import get_ip_from_request
from animesuki.core.models import Option

logger = logging.getLogger(__name__)


def object_to_dict(obj, exclude_pk=True):
    """Converts model instance into a dictionary"""
    raw = model_to_dict(obj)
    data = OrderedDict()
    for field in obj._meta.get_fields():
        # ManyToManyField are not supported
        if field.name in raw and not isinstance(field, ManyToManyField):
            # Exclude primary key
            if not exclude_pk or field.name != obj._meta.pk.name:
                if isinstance(field, FileField):
                    data[field.name] = str(raw[field.name])
                else:
                    data[field.name] = raw[field.name]
    return data


def object_data_revert(obj):
    """Obtains unaltered data (before save) from database"""
    if obj.pk:
        data = obj.__class__.objects.get(pk=obj.pk)
        return object_to_dict(data)
    return None


def formset_data_revert(formset):
    """Obtains unaltered data for a formset from database"""
    return [object_to_dict(obj, exclude_pk=False) for obj in formset.get_queryset().all()]


def formset_data_changed(formset):
    """Builds a list of (potentially altered and/or new) object instances from the formset"""
    result = []
    forms_to_delete = formset.deleted_forms
    for form in formset.initial_forms:
        if form.instance.pk and not form in forms_to_delete:
            result.append(object_to_dict(form.instance, exclude_pk=False))
    for form in formset.extra_forms:
        if form.has_changed() and not (formset.can_delete and formset._should_delete_form(form)):
            result.append(object_to_dict(form.instance, exclude_pk=False))
    return result


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


def format_object_str(object_type, object_str, object_id):
    result = '{}'.format(object_type)
    if object_str:
        result += ' "{}"'.format(object_str)
    if object_id:
        result += ' ({})'.format(object_id)
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
        WITHDRAWN = 4
        choices = (
            (PENDING, 'Pending'),
            (APPROVED, 'Approved'),
            (DENIED, 'Denied'),
            (WITHDRAWN, 'Withdrawn'),
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
    user_ip = models.GenericIPAddressField(unpack_ipv4=True)
    mod = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(class)s_mod', null=True, blank=True,
                            on_delete=models.PROTECT)
    mod_ip = models.GenericIPAddressField(unpack_ipv4=True, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, blank=True)
    date_modified = models.DateTimeField(auto_now=True, blank=True)

    _class_cache = dict()

    def __str__(self):
        return format_object_str(self.object_type, self.object_str, self.object_id)

    def set_object(self, obj):
        if obj.pk:
            # Existing object
            self.object = obj
        else:
            # New object
            self.object_type = ContentType.objects.get_for_model(obj)
            self.object_id = None
        self.object_str = str(obj)

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
        self.user_ip = get_ip_from_request(request)

    def set_mod(self, request):
        self.mod = request.user
        self.mod_ip = get_ip_from_request(request)

    def save(self, *args, **kwargs):
        # Prevent duplicates: when modifying existing entries, do not save if data_revert equals data_changed
        if (self.request_type not in (self.Type.MODIFY, self.Type.RELATED)) or (self.data_revert != self.data_changed):
            super().save(*args, **kwargs)

    def diff(self):
        if self.object_type_id not in self._class_cache:
            self._class_cache[self.object_type_id] = self.object_type.model_class()
        def order(data):
            r = dict()
            for field in self._class_cache[self.object_type_id]._meta.get_fields():
                if field.name in data:
                    r[field.verbose_name] = data[field.name]
            return data
        # ADD
        if self.data_revert is None:
            return order(self.data_changed)
        # DELETE
        if self.data_changed is None:
            return order(self.data_revert)
        # MODIFY
        result = dict()
        for k, v in self.data_changed.items():
            if k not in self.data_revert or self.data_revert[k] != v:
                result[k] = v
        return order(result)

    def diff_related(self):
        if self.related_type_id not in self._class_cache:
            self._class_cache[self.related_type_id] = self.related_type.model_class()
        result = dict()
        # Primary Key
        result['pk'] = pk = self._class_cache[self.related_type_id]._meta.pk.name
        # Fields
        result['fields'] = []
        for field in self._class_cache[self.related_type_id]._meta.get_fields():
            # ManyToManyField are not supported
            if isinstance(field, Field) and not isinstance(field, ManyToManyField):
                result['fields'].append(field.verbose_name)
        # Get list of old Primary Key values in data_revert; used to check for new rows
        pks_revert = []
        if self.data_revert is not None:
            for item in self.data_revert:
                if pk in item and item[pk]:
                    pks_revert.append(item[pk])
        # Build list of added rows and dictionary for data_changed; used for comparison against data_revert
        result['added'] = []
        result['added_str'] = []
        changed = dict()
        if self.data_changed is not None:
            for item in self.data_changed:
                # Check if Primary Key is set and in pks_revert
                if pk in item and item[pk] and item[pk] in pks_revert:
                    # Existing row
                    changed[item[pk]] = item
                else:
                    # New row
                    result['added'].append(item)
                    result['added_str'].append(self._class_cache[self.related_type_id].to_str(item))
        # Build list of existing, modified and deleted rows
        result['existing'] = dict()
        result['modified'] = dict()
        result['modified_str'] = []
        result['deleted'] = []
        result['deleted_str'] = []
        if self.data_revert is not None:
            for item in self.data_revert:
                row = item
                if item[pk] in changed:
                    diff = changed_keys(item, changed[item[pk]])
                    if len(diff) > 0:
                        result['modified'][item[pk]] = diff
                        result['modified_str'].append(self._class_cache[self.related_type_id].to_str(changed[item[pk]]))
                        row = changed[item[pk]]
                else:
                    result['deleted'].append(item[pk])
                    result['deleted_str'].append(self._class_cache[self.related_type_id].to_str(item))
                result['existing'][item[pk]] = row
        return result

    def get_absolute_url(self, view='history:detail'):
        return reverse(view, args=[self.pk])

    class Meta:
        db_table = 'history'
        permissions = (
            ('self_approve', 'Can self-approve add, modify & related requests'),
            ('self_delete', 'Can self-approve delete requests'),
            ('throttle_min', 'Subject to more lenient throttling'),
            ('throttle_off', 'Not subject to any throttling'),
            ('mod_approve', 'Can moderate add, modify & related requests'),
            ('mod_delete', 'Can moderate delete requests'),
        )
        default_permissions = ()


class HistoryModel(models.Model):
    """Base class for models with History support"""
    date_created = models.DateTimeField(auto_now_add=True, blank=True)
    date_modified = models.DateTimeField(auto_now=True, blank=True)

    HISTORY_APPROVE_ACTIONS = (ChangeRequest.Type.MODIFY, ChangeRequest.Type.RELATED)
    HISTORY_MODERATE_FIELDS = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cr = None
        self._request = None
        self._comment = ''
        self._messages = []

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

    @cached_property
    def has_pending(self):
        """Returns a pending change request for this object or None if not found."""
        if self.pk:
            try:
                cr = ChangeRequest.objects.filter(object_type=ContentType.objects.get_for_model(self),
                                                  object_id=self.id,
                                                  status=ChangeRequest.Status.PENDING)[:1].get()
                logger.info('ChangeRequest: pending change request blocked attempted change of {} by user "{}" ({})'
                            .format(cr, self.request.user.username, self.request.user.pk))
                return cr
            except ChangeRequest.DoesNotExist:
                return None
        return None

    @cached_property
    def user_throttled(self):
        """Returns True if user has exceeded maximum number of allowed edits."""
        if not self.request.user.has_perm('history.throttle_off'):
            day = timezone.now() - timezone.timedelta(days=1)
            count = ChangeRequest.objects.filter(user=self.request.user, date_created__gte=day).count()
            # Contributor
            if self.request.user.has_perm('history.throttle_min'):
                if count >= Option.objects.get_int(Option.HISTORY_THROTTLE_MIN):
                    logger.info('ChangeRequest: user "{}" ({}) hit throttle limit ({}) [min]'
                                .format(self.request.user.username, self.request.user.pk, count))
                    return True
            # User
            elif count >= Option.objects.get_int(Option.HISTORY_THROTTLE_MAX):
                logger.info('ChangeRequest: user "{}" ({}) hit throttle limit ({}) [max]'
                            .format(self.request.user.username, self.request.user.pk, count))
                return True
        return False

    @cached_property
    def sanity_checks(self):
        """Checks conditions that will disallow any changes from being processed at all."""
        # If first run outside clean() this function may cause a fatal error (raises exceptions in wrong places)
        if not self.request.user.is_authenticated:
            # Reaching this point should be impossible: changerequest.set_user() assumes user is AnimeSukiUser instance
            # Therefore an unauthenticated (anonymous) user will get a fatal error before this code is run
            raise ValidationError('You need to be logged in to perform this action.', code='user-not-authenticated')
        if not self.request.user.is_active:
            raise ValidationError('Your user account is not active.', code='user-not-active')
        if self.request.user.is_banned:
            raise ValidationError('You are permanently banned from making changes to the database.',
                                  code='user-banned')
        if Option.objects.get_bool(Option.EMERGENCY_SHUTDOWN):
            raise ValidationError('Making any changes to the database is currently disabled.',
                                  code='emergency-shutdown')
        return True

    @cached_property
    def sanity_checks_extra(self):
        """Checks additional conditions that will disallow any changes from being processed at all."""
        # If first run outside clean() this function may cause a fatal error (raises exceptions in wrong places)
        if self.has_pending is not None:
            raise ValidationError('Object has existing pending change request. '
                                  'Please wait for a moderator to process this request.',
                                  code='has-pending')
        if self.user_throttled:
            raise ValidationError('You have exceeded the maximum number of changes you can make in 24 hours. '
                                  'Please wait or contact site staff to have you privileges expanded.',
                                  code='user-throttled')
        return True

    @cached_property
    def self_approve(self):
        """Checks conditions that would allow a change (add, modify or delete) to be approved immediately."""
        week = timezone.now() - timezone.timedelta(days=7)
        if self._cr.request_type == ChangeRequest.Type.DELETE and self.request.user.has_perm('history.self_delete'):
            # Always approve if action is DELETE and user has self_delete permission
            return True
        elif self._cr.request_type != ChangeRequest.Type.DELETE and self.request.user.has_perm('history.self_approve'):
            # Always approve if action is ADD/MODIFY/RELATED and user has self_approve permission
            return True
        elif self.request.user.date_joined >= week:
            # Never approve if user account is less than one week old
            return False
        elif self._cr.request_type in self.HISTORY_APPROVE_ACTIONS:
            # Approve if action is in HISTORY_APPROVE_ACTIONS...
            if self._cr.data_changed is not None:
                # ...unless a field was changed that is in HISTORY_MODERATE_FIELDS
                if any(field in self._cr.data_changed.keys() for field in self.HISTORY_MODERATE_FIELDS):
                    return False
            return True
        else:
            return False

    def create_changerequest(self, request_type=None):
        cr = ChangeRequest()
        cr.set_object(self)
        cr.set_request_type(request_type)
        cr.status = ChangeRequest.Status.PENDING
        if cr.request_type != ChangeRequest.Type.RELATED:
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
        return cr

    def log(self, action=None, obj=None):
        action = self._cr.get_request_type_display() if action is None else action
        obj = format_object_str(self._cr.object_type, self._cr.object_str, self._cr.object_id) if obj is None else obj
        user = '"{}" ({})'.format(self._cr.user.username, self._cr.user.pk)
        mod = ''
        if self._cr.mod is not None:
            mod = ' mod "{}" ({})'.format(self._cr.mod.username, self._cr.mod.pk)
        logger.info('ChangeRequest: [{}] [{}] {} user {}{}'
                    .format(action, self._cr.get_status_display(), obj, user, mod))

    def clean(self):
        self.sanity_checks
        # Caution: the following might cause issues in a ModelForm where the action executed isn't simply save()
        self.sanity_checks_extra

    def save(self, *args, **kwargs):
        self._cr = self.create_changerequest()
        if self.self_approve and self.sanity_checks and self.sanity_checks_extra:
            # Approve immediately if right conditions are met
            self._cr.status = ChangeRequest.Status.APPROVED
        self._cr.save()
        # Save actual model instance if: ChangeRequest object was saved -and- the request was self-approved
        # (ChangeRequest object will not have been saved if data was not altered)
        if self._cr.pk:
            self.log()
            if self._cr.status == ChangeRequest.Status.APPROVED:
                super().save(*args, **kwargs)
                self._cr.set_object(self)
                self._cr.save()
                # Generate message
                verb = {ChangeRequest.Type.ADD: 'Added',
                        ChangeRequest.Type.MODIFY: 'Updated'}  # DELETE or RELATED requests shouldn't be handled by save()
                self.add_message(messages.SUCCESS, verb[self._cr.request_type], self._cr.object_type, self._cr.object_str)
            elif self._cr.status == ChangeRequest.Status.PENDING:
                self.add_message_pending()
        # Reset cached property
        if hasattr(self, 'has_pending'):
            delattr(self, 'has_pending')

    def save_related(self, formset):
        self._cr = self.create_changerequest(request_type=ChangeRequest.Type.RELATED)
        self._cr.related_type = ContentType.objects.get_for_model(formset.model)
        self._cr.data_revert = formset_data_revert(formset)
        self._cr.data_changed = formset_data_changed(formset)
        if self.self_approve and self.sanity_checks and self.sanity_checks_extra:
            # Approve immediately if right conditions are met
            self._cr.status = ChangeRequest.Status.APPROVED
        self._cr.save()
        # Save formset if: ChangeRequest object was saved -and- the request was self-approved
        # (ChangeRequest object will not have been saved if data was not altered)
        if self._cr.pk:
            self.log()
            if self._cr.status == ChangeRequest.Status.APPROVED:
                formset.save()
                # Generate message(s)
                for obj in formset.new_objects:
                    self.add_message(messages.SUCCESS, 'Added', self._cr.related_type, obj)
                    self.log('Add', format_object_str(self._cr.related_type, obj, obj.pk))
                for obj in formset.changed_objects:
                    self.add_message(messages.SUCCESS, 'Updated', self._cr.related_type, obj)
                    self.log('Modify', format_object_str(self._cr.related_type, obj, obj.pk))
                for obj in formset.deleted_objects:
                    self.add_message(messages.SUCCESS, 'Deleted', self._cr.related_type, obj)
                    self.log('Delete', format_object_str(self._cr.related_type, obj, obj.pk))
                # Refresh data_changed: any new instances should now have a pk set
                self._cr.data_changed = formset_data_revert(formset)
                self._cr.save()
            elif self._cr.status == ChangeRequest.Status.PENDING:
                self.add_message_pending()
        # Reset cached property
        if hasattr(self, 'has_pending'):
            delattr(self, 'has_pending')

    def delete(self, *args, **kwargs):
        self._cr = self.create_changerequest(request_type=ChangeRequest.Type.DELETE)
        if self.self_approve and self.sanity_checks:
            # Approve immediately if right conditions are met
            self._cr.status = ChangeRequest.Status.APPROVED
            self._cr.save()
            super().delete(*args, **kwargs)
            self.add_message(messages.SUCCESS, 'Deleted', self._cr.object_type, self._cr.object_str)
        else:
            self._cr.save()
        if self._cr.status == ChangeRequest.Status.PENDING:
            self.add_message_pending()
        self.log()
        # Reset cached property
        if hasattr(self, 'has_pending'):
            delattr(self, 'has_pending')

    def add_message(self, level, verb, obj_type, obj_str):
        self._messages.append({'level': level,
                               'message': '{} {} "{}"'.format(verb, str(obj_type), str(obj_str))})

    def add_message_pending(self):
        self._messages.append({'level': messages.WARNING,
                               'message': 'Change request for {} "{}" is pending moderator approval'.format(
                                   str(self._cr.object_type), str(self._cr.object_str))})

    def show_messages(self):
        for msg in self._messages:
            messages.add_message(self.request, msg['level'], msg['message'])

    class Meta:
        abstract = True
