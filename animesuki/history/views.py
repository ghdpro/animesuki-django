"""AnimeSuki History views"""

import bleach

from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.contrib import messages

from animesuki.core.views import AnimeSukiPermissionMixin, ListViewQueryStringMixin

from .forms import HistoryCommentForm
from .models import ChangeRequest


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


class HistoryDetailView(AnimeSukiPermissionMixin, DetailView):
    permission_required = 'history.view_changerequest'
    template_name = 'history/detail.html'
    model = ChangeRequest


class HistoryListView(AnimeSukiPermissionMixin, ListViewQueryStringMixin, ListView):
    permission_required = 'history.view_changerequest'
    template_name = 'history/list.html'
    model = ChangeRequest
    paginate_by = 25
    ALLOWED_ORDER = ['date', '-date']
    ALLOWED_STATUS = ['pending', 'approved', 'denied', 'withdrawn']

    def get_ordering(self):
        order = self.request.GET.get('order', '').strip().lower()
        if order == 'date':
            return 'date_modified', 'date_created'
        else:
            return '-date_modified', '-date_created'

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('object_type', 'related_type', 'user')
        # Status
        status = ChangeRequest.Status.lookup.get(self.request.GET.get('status'), None)
        if status is not None:
            qs = qs.filter(status=status)
        # User
        user = self.request.GET.get('user', '').strip()
        if user:
            qs = qs.filter(user__username__icontains=user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Status
        status = self.request.GET.get('status', '').lower().strip()
        if status in self.ALLOWED_STATUS:
            context['status'] = status
        else:
            context['status'] = 'all'
        return context

    def get_url(self):
        return reverse('history:browse')

    def build_querystring(self, page=None, order=None, status=None):
        q = super().build_querystring(page=page, order=order)
        # Status
        if status is not None:
            # Status can be 'all' (or other non-valid value) to remove it from query string
            if status in self.ALLOWED_STATUS:
                q['status'] = status
                # New status filter should reset page
                if q.get('page', None) is not None:
                    del q['page']
        else:
            s = self.request.GET.get('status', '').lower().strip()
            if s in self.ALLOWED_STATUS:
                q['status'] = s
        # User
        user = bleach.clean(self.request.GET.get('user', ''), tags=[] , strip=True).strip()
        if user:
            q['user'] = user
        return q


def history_action(request, pk):
    cr = get_object_or_404(ChangeRequest, pk=pk)
    action = request.POST.get('action').lower().strip()
    # User action (Withdraw)
    if action == 'withdraw':
        # Check if user matches
        if request.user != cr.user:
            raise PermissionDenied('Only the user who created the change request can withdraw it.')
        cr.withdraw()
        messages.success(request, 'Change request has been withdrawn.')
    # Moderator actions
    else:
        # Moderator permission check
        if not request.user.has_perm('history.mod_approve'):
            raise PermissionDenied('You do not have permission to moderate change requests.')
        # Set moderator
        cr.set_mod(request)
        # Approve
        if action == 'approve':
            # Additional moderator permission check in case of delete
            if cr.request_type == ChangeRequest.Type.DELETE and not request.user.has_perm('history.mod_delete'):
                raise PermissionDenied('You do not have permission to approve deletion requests.')
            cr.approve()
            messages.success(request, 'Change request has been approved.')
        # Deny
        elif action == 'deny':
            cr.deny()
            messages.success(request, 'Change request has been denied.')
        # Revert
        elif action == 'revert':
            cr.revert()
            messages.success(request, 'Change request has been reverted.')
        else:
            raise Exception('Invalid action')
    cr.log()
    return redirect(cr)
