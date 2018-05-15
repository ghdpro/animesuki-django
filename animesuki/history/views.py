"""AnimeSuki History views"""

from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.http import HttpResponseRedirect
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


class HistoryFormsetViewMixin:
    formset_class = None

    def get_form(self, form_class=None):
        if self.formset_class is None:
            raise ImproperlyConfigured('HistoryFormsetViewMixin requires formset class to be specified')
        return self.formset_class(**self.get_form_kwargs())

    @transaction.atomic
    def form_valid(self, form):
        # ModelFormMixin overwrites self.object with output of form.save(), which is bad because form is a formset here
        form.save()
        return HttpResponseRedirect(self.get_success_url())
