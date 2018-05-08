"""AnimeSuki Media Admin models"""

from django.contrib import admin

from animesuki.history.admin import HistoryAdmin
from .models import Media


@admin.register(Media)
class MediaAdmin(HistoryAdmin):
    """Media Admin model"""
    fields = (
        ('title',),
        ('slug',),
        ('media_type', 'sub_type'),
        ('status', 'is_adult'),
        ('episodes', 'duration'),
        ('volumes', 'chapters'),
        ('start_date', 'start_precision'),
        ('end_date', 'end_precision'),
        ('season', 'season_year'),
        ('description',),
        ('synopsis',),
        ('comment',),
    )
    list_display = ('pk', 'title', 'media_type', 'sub_type', 'start_date', 'end_date', 'is_adult',)
    list_display_links = ('pk', 'title',)
    list_filter = ('media_type', 'sub_type', 'is_adult',)
    prepopulated_fields = {"slug": ("title",)}
