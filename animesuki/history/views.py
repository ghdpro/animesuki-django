"""AnimeSuki History views"""

from django.db import transaction
from django.contrib import messages


class HistoryFormViewMixin:

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.request = self.request
        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.comment = form.cleaned_data['comment']
        response = super().form_valid(form)
        messages.success(self.request, form.instance.get_message())
        return response
