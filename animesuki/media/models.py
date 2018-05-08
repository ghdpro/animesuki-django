"""AnimeSuki Media models"""

from django.db import models
from django.utils.text import slugify

from animesuki.history.models import HistoryModel
from animesuki.core.utils import DatePrecision


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
        ONE_SHOT = 10
        DOUJIN = 11
        # Novel
        LIGHT_NOVEL = 12
        NOVEL = 13
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
                (ONE_SHOT, 'One Shot'),
                (DOUJIN, 'Doujin'),
            )),
            ('Novel', (
                (LIGHT_NOVEL, 'Light Novel'),
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

    title = models.CharField('Title', max_length=250, blank=True)
    slug = models.SlugField('Slug', max_length=250, unique=True, allow_unicode=True)
    media_type = models.PositiveSmallIntegerField('Type', choices=Type.choices, default=Type.ANIME)
    sub_type = models.PositiveSmallIntegerField('Sub Type', choices=SubType.choices, default=SubType.UNKNOWN)
    status = models.PositiveSmallIntegerField('Status', choices=Status.choices, default=Status.AUTO)
    is_adult = models.BooleanField('Adult?', default=False)
    episodes = models.IntegerField('Episodes', null=True, blank=True)
    duration = models.IntegerField('Duration', null=True, blank=True)
    volumes = models.IntegerField('Volumes', null=True, blank=True)
    chapters = models.IntegerField('Chapters', null=True, blank=True)
    start_date = models.DateField('Start Date', null=True, blank=True)
    start_precision = models.PositiveSmallIntegerField('Precision', choices=DatePrecision.choices,
                                                       default=DatePrecision.FULL)
    end_date = models.DateField('End Date', null=True, blank=True)
    end_precision = models.PositiveSmallIntegerField('Precision', choices=DatePrecision.choices,
                                                     default=DatePrecision.FULL)
    season_year = models.IntegerField('Season Year', null=True, blank=True)
    season = models.PositiveSmallIntegerField('Season', choices=Season.choices, null=True, blank=True)
    description = models.TextField('Description', blank=True)
    synopsis = models.TextField('Synopsis', blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'media'
        verbose_name_plural = 'media'
