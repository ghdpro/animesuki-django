"""AnimeSuki Media API Viewsets"""

from rest_framework import generics

from ..models import Media, MediaArtwork

from .serializers import MediaSerializer, MediaDetailSerializer, MediaArtworkSerializer


class MediaListAPIView(generics.ListAPIView):
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    permission_classes = ()


class MediaRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Media.objects.all()
    serializer_class = MediaDetailSerializer
    permission_classes = ()


class MediaArtworkListAPIView(generics.ListAPIView):
    queryset = MediaArtwork.objects.all()
    serializer_class = MediaArtworkSerializer
    permission_classes = ()


class MediaArtworkRetrieveAPIView(generics.RetrieveAPIView):
    queryset = MediaArtwork.objects.all()
    serializer_class = MediaArtworkSerializer
    permission_classes = ()
