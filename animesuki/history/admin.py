"""AnimeSuki History Admin models"""

from django import forms
from django.contrib import admin

from .models import HistoryModel


class HistoryAdminForm(forms.ModelForm):
    comment = forms.CharField(label='Comment / Source', required=False)

    class Meta:
        fields = []


class HistoryAdmin(admin.ModelAdmin):
    form = HistoryAdminForm

    def save_model(self, request, obj, form, change):
        if isinstance(obj, HistoryModel):
            obj.request = request
            if 'comment' in form.cleaned_data:
                obj.comment = form.cleaned_data['comment']
        obj.save()

    def delete_model(self, request, obj):
        if isinstance(obj, HistoryModel):
            obj.request = request
            # Comment field cannot be retrieved here, so set default value
            obj.comment = 'Deleted from admin interface'
        obj.delete()
