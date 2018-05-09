"""AnimeSuki Core utilities"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class DatePrecision:
    FULL = 1
    YEAR = 2
    MONTH = 3
    choices = (
        (FULL, 'Full'),
        (YEAR, 'Year'),
        (MONTH, 'Month'),
    )


def get_ip_from_request(request):
    """"Extracts IP address from Request object"""
    # This is a separate function just in case the logic needs to be expanded to account for proxies etc
    return request.META.get('REMOTE_ADDR')


def user_add_permission(model, codename, user):
    """For use in tests. Adds permission to user and returns reloaded user object."""
    content_type = ContentType.objects.get_for_model(model)
    permission = Permission.objects.get(content_type=content_type, codename=codename)
    user.user_permissions.add(permission)
    return get_user_model().objects.get(pk=user.pk)
