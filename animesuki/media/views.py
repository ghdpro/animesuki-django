"""AnimeSuki Media views"""

from django.urls import reverse
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin

from animesuki.history.views import HistoryFormViewMixin

from .models import Media
from .forms import MediaCreateUpdateForm


class MediaCreateView(LoginRequiredMixin, HistoryFormViewMixin, CreateView):
    template_name = 'media/create.html'
    form_class = MediaCreateUpdateForm
    model = Media

    def get_success_url(self):
        return reverse('media:create' , args=['media'])
