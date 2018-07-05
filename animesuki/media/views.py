"""AnimeSuki Media views"""

from django.views.generic import DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

from animesuki.core.views import AnimeSukiPermissionMixin, ArtworkActiveViewMixin
from animesuki.history.views import HistoryFormViewMixin, HistoryFormsetViewMixin

from .models import Media
from .forms import MediaCreateForm, MediaUpdateForm, MediaArtworkForm, MediaArtworkFormset


class MediaDetailView(DetailView):
    template_name = 'media/detail.html'
    model = Media


class MediaCreateView(LoginRequiredMixin, HistoryFormViewMixin, CreateView):
    template_name = 'media/create.html'
    form_class = MediaCreateForm
    model = Media

    def get_success_url(self):
        return self.object.get_absolute_url('media:update')


class MediaUpdateView(LoginRequiredMixin, HistoryFormViewMixin, UpdateView):
    template_name = 'media/update.html'
    form_class = MediaUpdateForm
    model = Media

    def get_success_url(self):
        return self.object.get_absolute_url('media:update')


class MediaArtworkView(AnimeSukiPermissionMixin, ArtworkActiveViewMixin, HistoryFormsetViewMixin, UpdateView):
    permission_required = 'history.self_approve'
    permission_denied_message = 'To be able to upload artwork you need to be a Contributor'
    template_name = 'media/artwork.html'
    form_class = MediaArtworkForm
    formset_class = MediaArtworkFormset
    model = Media

    def get_success_url(self):
        return self.object.get_absolute_url('media:artwork')
