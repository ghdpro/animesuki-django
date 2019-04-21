"""AnimeSuki Media API URLs"""

from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from .views import (MediaListAPIView, MediaRetrieveAPIView, MediaArtworkListAPIView, MediaArtworkRetrieveAPIView)


urlpatterns = [
    path('<int:pk>', MediaRetrieveAPIView.as_view(), name='media-detail'),
    path('', MediaListAPIView.as_view()),
    path('artwork/<int:pk>', MediaArtworkRetrieveAPIView.as_view(), name='mediaartwork-detail'),
    path('artwork/', MediaArtworkListAPIView.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
