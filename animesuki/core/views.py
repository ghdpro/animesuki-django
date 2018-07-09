"""AnimeSuki Core views"""

from django.core.exceptions import ObjectDoesNotExist
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
                self.object.artwork = form.get_queryset().get(pk=int(artwork_active_form.cleaned_data['active']))
                self.object.save()
                if self.object._cr.pk:
                    messages.success(self.request, 'Changed active artwork for "{}" to "{}"'
                                     .format(self.object, self.object.artwork))
            except ObjectDoesNotExist:
                pass
        # Pick an image to set as active image if not yet set
        try:
            # Reload object in case active artwork was deleted
            obj = self.get_object()
            if obj.artwork is None:
                self.object.artwork = form.get_queryset().all()[0]
                self.object.save()
                if self.object._cr.pk:
                    messages.success(self.request, 'Changed active artwork for "{}" to "{}"'
                                     .format(self.object, self.object.artwork))
        except (ObjectDoesNotExist, IndexError):
            pass
        return result
