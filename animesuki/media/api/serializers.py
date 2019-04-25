"""AnimeSuki Media API Serializers"""

from rest_framework import serializers

from animesuki.core.utils import DatePrecision

from ..models import Media, MediaArtwork


class MediaSerializer(serializers.HyperlinkedModelSerializer):
    site_url = serializers.CharField(source='get_absolute_url')
    media_type = serializers.CharField(source='get_media_type_display')
    sub_type = serializers.CharField(source='get_sub_type_display')
    status = serializers.CharField(source='get_status')
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    season = serializers.CharField(source='get_season_display')

    def get_start_date(self, obj):
        return DatePrecision.get_precision(obj.start_date, obj.start_precision)

    def get_end_date(self, obj):
        return DatePrecision.get_precision(obj.end_date, obj.end_precision)

    class Meta:
        model = Media
        fields = ('url', 'site_url', 'title', 'media_type', 'sub_type', 'status', 'is_adult',
                  'episodes', 'duration', 'volumes', 'chapters', 'start_date', 'end_date',
                  'season_year', 'season', 'description', 'synopsis', 'artwork_active')


class MediaDetailSerializer(MediaSerializer):
    artwork = serializers.HyperlinkedRelatedField(source='mediaartwork_set', many=True, read_only=True, view_name='mediaartwork-detail')

    class Meta:
        model = Media
        fields = MediaSerializer.Meta.fields + ('artwork',)


class MediaArtworkSerializer(serializers.ModelSerializer):
    size = serializers.IntegerField(source='image.size')
    height = serializers.IntegerField(source='image.height')
    width = serializers.IntegerField(source='image.width')
    media = serializers.HyperlinkedRelatedField(read_only=True, view_name='media-detail')

    class Meta:
        model = MediaArtwork
        fields = ('url', 'image', 'size', 'height', 'width', 'media')
