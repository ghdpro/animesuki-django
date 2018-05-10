"""AnimeSuki Core Admin models"""

from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AnimeSukiUser, Option


@admin.register(AnimeSukiUser)
class AnimeSukiUserAdmin(UserAdmin):
    """
    Specific overrides for removing first/last name
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('email',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_banned', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'is_staff', 'is_banned')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_banned', 'groups')
    search_fields = ('username', 'email')


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    fields = (
        ('code',),
        ('name',),
        ('value',),
        ('last_modified_by',),
        ('date_modified',),
    )
    readonly_fields = ('last_modified_by', 'date_modified')
    list_display = ('code', 'name', 'value', 'last_modified_by', 'date_modified')

    def save_model(self, request, obj, form, change):
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)
