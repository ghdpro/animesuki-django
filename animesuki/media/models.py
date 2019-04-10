"""AnimeSuki Media models"""

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from animesuki.core.models import ArtworkModel
from animesuki.core.utils import DatePrecision
from animesuki.history.models import HistoryModel


class Media(HistoryModel):
    class Type:
        ANIME = 1
        MANGA = 2
        NOVEL = 3
        choices = (
            (ANIME, 'Anime'),
            (MANGA, 'Manga'),
            (NOVEL, 'Novel'),
        )

    class SubType:
        UNKNOWN = 0
        # Anime
        TV = 1
        OVA = 2
        MOVIE = 3
        WEB = 4
        SPECIAL = 5
        MUSIC = 6
        # Manga
        MANGA = 7
        MANHUA = 8
        MANHWA = 9
        WEB_MANGA = 10
        ONE_SHOT = 11
        DOUJIN = 12
        # Novel
        LIGHT_NOVEL = 13
        WEB_NOVEL = 14
        NOVEL = 15
        choices = (
            (UNKNOWN, 'Unknown'),
            ('Anime', (
                (TV, 'TV'),
                (OVA, 'OVA'),
                (MOVIE, 'Movie'),
                (WEB, 'Web'),
                (SPECIAL, 'Special'),
                (MUSIC, 'Music'),
            )),
            ('Manga', (
                (MANGA, 'Manga'),
                (MANHUA, 'Manhua'),
                (MANHWA, 'Manhwa'),
                (WEB_MANGA, 'Web Manga'),
                (ONE_SHOT, 'One Shot'),
                (DOUJIN, 'Doujin'),
            )),
            ('Novel', (
                (LIGHT_NOVEL, 'Light Novel'),
                (WEB_NOVEL, 'Web Novel'),
                (NOVEL, 'Novel'),
            ))
        )

    class Status:
        AUTO = 1
        HIATUS = 2
        CANCELLED = 3
        choices = (
            (AUTO, 'Automatic'),
            (HIATUS, 'On Hiatus'),
            (CANCELLED, 'Cancelled')
        )

    class Season:
        WINTER = 1
        SPRING = 2
        SUMMER = 3
        FALL = 4
        choices = (
            (WINTER, 'Winter'),
            (SPRING, 'Spring'),
            (SUMMER, 'Summer'),
            (FALL, 'Fall')
        )

    title = models.CharField('title', max_length=250, blank=True)
    media_type = models.PositiveSmallIntegerField('type', choices=Type.choices, default=Type.ANIME)
    sub_type = models.PositiveSmallIntegerField('sub Type', choices=SubType.choices, default=SubType.UNKNOWN)
    status = models.PositiveSmallIntegerField('status', choices=Status.choices, default=Status.AUTO)
    is_adult = models.BooleanField('r-18', default=False)
    episodes = models.IntegerField('episodes', null=True, blank=True)
    duration = models.IntegerField('duration', null=True, blank=True)
    volumes = models.IntegerField('volumes', null=True, blank=True)
    chapters = models.IntegerField('chapters', null=True, blank=True)
    start_date = models.DateField('start date', null=True, blank=True)
    start_precision = models.PositiveSmallIntegerField('precision', choices=DatePrecision.choices,
                                                       default=DatePrecision.FULL)
    end_date = models.DateField('end date', null=True, blank=True)
    end_precision = models.PositiveSmallIntegerField('precision', choices=DatePrecision.choices,
                                                     default=DatePrecision.FULL)
    season_year = models.IntegerField('season year', null=True, blank=True)
    season = models.PositiveSmallIntegerField('season', choices=Season.choices, null=True, blank=True)
    description = models.TextField('description', blank=True)
    synopsis = models.TextField('synopsis', blank=True)
    artwork = models.ForeignKey('MediaArtwork', related_name='media_artwork', on_delete=models.SET_NULL,
                                null=True, blank=True, default=None)

    HISTORY_MODERATE_FIELDS = ('title', 'slug', 'media_type', 'sub_type', 'is_adult')

    def __str__(self):
        return self.title

    def get_status(self):
        if self.status != self.Status.AUTO:
            return self.get_status_display()
        status = {
            self.Type.ANIME: {
                'future': 'Not yet aired',
                'present': 'Currently airing',
                'past': 'Finished'
            },
            self.Type.MANGA: {
                'future': 'Not yet published',
                'present': 'Currently publishing',
                'past': 'Finished'
            },
        }
        status[self.Type.NOVEL] = status[self.Type.MANGA]
        now = timezone.now().date()
        if self.end_date and self.end_date <= now:
            return status[self.media_type]['past']
        elif not self.start_date or self.start_date > now:
            return status[self.media_type]['future']
        else:
            return status[self.media_type]['present']

    def get_absolute_url(self, view='media:detail'):
        return reverse(view, args=[slugify(self.get_media_type_display()), self.pk, slugify(self.title)])

    class Meta:
        db_table = 'media'
        verbose_name_plural = 'media'


class MediaArtwork(ArtworkModel):
    media = models.ForeignKey(Media, on_delete=models.PROTECT)

    ARTWORK_FOLDER = 'media'
    ARTWORK_SIZES = ((75, 75, 't75'), (150, 150, 't150'), (225, 225, 't225'), (450, 450, 't450'),
                     (292, 600, '292w'), (352, 800, '352w'), (438, 1000, '438w'),
                     (528, 1200, '528w'), (584, 1200, '584w'), (704, 1400, '704w'))

    def sub_folder(self):
        return self.media.pk

    class Meta:
        db_table = 'media_artwork'
