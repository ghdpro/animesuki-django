"""AnimeSuki Core Admin models"""

from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AnimeSukiUser


@admin.register(AnimeSukiUser)
class AnimeSukiUserAdmin(UserAdmin):
    """
    Specific overrides for removing first/last name
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('email',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'is_staff')
    search_fields = ('username', 'email')
