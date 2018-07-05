"""AnimeSuki History views"""

from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.http import HttpResponseRedirect

from .forms import HistoryCommentForm


class HistoryFormViewMixin:

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.request = self.request
        return form

    @transaction.atomic
    def form_valid(self, form):
        form.instance.comment = form.cleaned_data['comment']
        response = super().form_valid(form)
        form.instance.show_messages()
        return response


class HistoryFormsetViewMixin:
    formset_class = None

    def get_comment_form(self):
        if self.request.method in ('POST', 'PUT'):
            return HistoryCommentForm(prefix=self.get_prefix(), data=self.request.POST, files=self.request.FILES)
        else:
            return HistoryCommentForm(prefix=self.get_prefix())

    def get_context_data(self, **kwargs):
        if 'comment_form' not in kwargs:
            kwargs['comment_form'] = self.get_comment_form()
        return super().get_context_data(**kwargs)

    def get_form(self, form_class=None):
        if self.formset_class is None:
            raise ImproperlyConfigured('HistoryFormsetViewMixin requires formset class to be specified')
        return self.formset_class(**self.get_form_kwargs())

    def form_valid(self, form):
        # ModelFormMixin overwrites self.object with output of form.save(), which is bad because form is a formset here
        self.object.request = self.request
        comment_form = self.get_comment_form()
        if comment_form.is_valid():
            self.object.comment = comment_form.cleaned_data['comment']
        with transaction.atomic():
            self.object.save_related(form)
            self.object.show_messages()
        return HttpResponseRedirect(self.get_success_url())
