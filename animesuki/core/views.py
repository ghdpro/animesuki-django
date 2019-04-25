"""AnimeSuki Core views"""

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponsePermanentRedirect
from django.utils.http import urlencode
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages

from .forms import ArtworkActiveForm


class AnimeSukiPermissionMixin(PermissionRequiredMixin):
    """"
    PermissionRequiredMixin modified to show error message to user.

    By default the PermissionRequiredMixin does not generate an error message, it just redirects to the login page.
    As that can be confusing, this simple mixin makes sure the "permission_denied_message" string is returned to the
    user via the messages framework and also sets a reasonable default value for it.
    """
    permission_denied_message = 'You do not have sufficient permissions to access this page'

    def handle_no_permission(self):
        messages.error(self.request, self.permission_denied_message)
        return super().handle_no_permission()


class ArtworkActiveViewMixin:

    def get_artwork_active_form(self):
        return ArtworkActiveForm(prefix=self.get_prefix(), data=self.request.POST, files=self.request.FILES)

    def form_valid(self, form):
        result = super().form_valid(form)
        artwork_active_form = self.get_artwork_active_form()
        # Set active image
        if artwork_active_form.is_valid():
            try:
                self.object.artwork_active = form.get_queryset().get(pk=int(artwork_active_form.cleaned_data['active']))
                self.object.save()
                if self.object._cr.pk:
                    messages.success(self.request, 'Changed active artwork for "{}" to "{}"'
                                     .format(self.object, self.object.artwork_active))
            except ObjectDoesNotExist:
                pass
        # Pick an image to set as active image if not yet set
        try:
            # Reload object in case active artwork was deleted
            obj = self.get_object()
            if obj.artwork_active is None:
                self.object.artwork_active = form.get_queryset().all()[0]
                self.object.save()
                if self.object._cr.pk:
                    messages.success(self.request, 'Changed active artwork for "{}" to "{}"'
                                     .format(self.object, self.object.artwork_active))
        except (ObjectDoesNotExist, IndexError):
            pass
        return result


class CanonicalDetailViewMixin:

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Redirect to canonical URL if request URL is not the canonical URL
        obj_url = self.object.get_absolute_url()
        if self.request.path != obj_url:
            return HttpResponsePermanentRedirect(obj_url)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class ListViewQueryStringMixin:
    ALLOWED_ORDER = []

    def build_querystring(self, page=None, order=None):
        q = dict()
        # Page
        if page is not None:
            q['page'] = page
        else:
            try:
                p = int(self.request.GET.get('page', 0))
                if p > 0:
                    q['page'] = p
            except ValueError:
                pass
        # Order
        o = self.request.GET.get('order', '').lower().strip()
        if order is not None:
            if o == order:
                q['order'] = order[1:] if order[0] == '-' else '-' + order
            else:  # Also inverse of '-order'
                q['order'] = order
            # New sort order should reset page
            if q.get('page', None) is not None:
                del q['page']
        elif o in self.ALLOWED_ORDER:
            q['order'] = o
        return q

    def get_querystring(self, *args, **kwargs):
        q = self.build_querystring(*args, **kwargs)
        if len(q) > 0:
            return '?' + urlencode(q)
        return ''

    def get_order_direction(self, order):
        # Determines current order direction (up or down) based on what -new- value of "order" will be (=opposite)
        q = self.build_querystring(order=order)
        if q['order'][0] == '-':
            return 'up'
        return 'down'