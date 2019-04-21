"""AnimeSuki Media URLs"""

from django.urls import path

from .views import (MediaDetailView, MediaCreateView, MediaUpdateView, MediaArtworkView)


app_name = 'media'
urlpatterns = [
    path('<int:pk>/<slug:slug>', MediaDetailView.as_view(), name='detail'),
    path('<int:pk>/<slug:slug>/edit', MediaUpdateView.as_view(), name='update'),
    path('<int:pk>/<slug:slug>/artwork', MediaArtworkView.as_view(), name='artwork'),
    path('create', MediaCreateView.as_view(), name='create'),
]
