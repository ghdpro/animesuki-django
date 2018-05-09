"""AnimeSuki History Admin models"""

from django import forms
from django.contrib import admin

from .models import HistoryModel


class HistoryAdminForm(forms.ModelForm):
    comment = forms.CharField(label='Comment / Source', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'request') and isinstance(self.instance, HistoryModel):
            self.instance.request = self.request

    class Meta:
        fields = []


class HistoryAdmin(admin.ModelAdmin):
    form = HistoryAdminForm

    def get_form(self, request, obj=None, **kwargs):
        # Pass request to form, necessary to be able to access it during the validation phase
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        return form

    def save_model(self, request, obj, form, change):
        if isinstance(obj, HistoryModel):
            if 'comment' in form.cleaned_data:
                obj.comment = form.cleaned_data['comment']
        obj.save()

    def delete_model(self, request, obj):
        if isinstance(obj, HistoryModel):
            obj.request = request
            # Comment field cannot be retrieved here, so set default value
            obj.comment = 'Deleted from admin interface'
        obj.delete()
