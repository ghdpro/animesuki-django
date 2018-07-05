"""AnimeSuki Core models"""

import logging
import subprocess
from hashlib import md5
from pathlib import Path
from urllib.parse import urlencode

from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator

logger = logging.getLogger(__name__)


class AnimeSukiUser(AbstractBaseUser, PermissionsMixin):
    """
    AnimeSuki uses a custom user model for two reasons:
    1) There is no need for "first_name" and "last_name"
    2) Switching to a custom user model later is difficult

    The code below is copied straight from the Django source code
    for "AbstractUser", with first/last name field references removed.
    """
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    slug = models.SlugField(max_length=150, unique=True, allow_unicode=True)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_banned = models.BooleanField(
        _('banned'),
        default=False,
        help_text=_('Designates whether the user is allowed to make modifications to the AnimeSuki database.'),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'core_user'
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def save(self, *args, **kwargs):
        # Set slug if empty
        if not self.slug:
            self.slug = slug = slugify(self.username)
            # Find unique slug
            i = 1
            while AnimeSukiUser.objects.filter(slug=self.slug).exists():
                self.slug = '{}{}'.format(slug, i)
                i += 1
        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def get_gravatar_url(self, size=80, default='identicon'):
        url = 'https://www.gravatar.com/avatar/' + md5(self.email.lower().encode('utf-8')).hexdigest()
        url += '?' + urlencode({'d': default, 's': str(size)})
        return url


class OptionsManager(models.Manager):

    def get_bool(self, code):
        v = str(self.get(code=code).value).strip().lower()
        if len(v) > 0 and v[0] in ('1', 't', 'y'):
            return True
        return False

    def get_int(self, code):
        try:
            return int(self.get(code=code).value)
        except ValueError:
            logger.warning('Options: failed to cast value of "{}" to int'.format(code))
        return 0


class Option(models.Model):
    # Fixture: fixtures/option.json
    EMERGENCY_SHUTDOWN = 'emergency-shutdown'
    HISTORY_THROTTLE_MAX = 'history-throttle-max'
    HISTORY_THROTTLE_MIN = 'history-throttle-min'

    code = models.CharField('code', primary_key=True, max_length=50)
    name = models.CharField('name', max_length=100)
    value = models.CharField('value', max_length=250, null=True, blank=True)
    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(class)s_user',
                                         null=True, blank=True, on_delete=models.PROTECT)
    date_modified = models.DateTimeField(auto_now=True, blank=True)
    objects = OptionsManager()

    def __str__(self):
        return self.code


def artwork_upload_location(instance, filename):
    # Pattern: [artwork_root]/[ARTWORK_FOLDER]/[folder_id()]/[filename].jpg
    return str(Path(slugify(instance.ARTWORK_FOLDER) +'', str(instance.sub_folder()).lower(),
                    slugify(Path(filename).stem[:instance.ARTWORK_NAME_MAX_LENGTH]) +'').with_suffix('.jpg'))


class ArtworkModel(models.Model):
    image = models.ImageField(upload_to=artwork_upload_location)

    ARTWORK_FOLDER = 'artwork'
    ARTWORK_NAME_MAX_LENGTH = 50
    ARTWORK_MAX_SIZE = (2000, 2000)
    ARTWORK_JPEG_QUALITY = 85
    ARTWORK_JPEG_QUALITY_THUMB = 80
    ARTWORK_SIZES = ((1000, 1000, '1000w'),)

    def __str__(self):
        return Path(self.image.path).name

    def sub_folder(self):
        # Child classes should override this function
        return None

    def get_image_path(self, size):
        return str(Path(Path(self.image.path).parent, Path(self.image.path).stem + '-' + str(size) + '.jpg'))

    def get_image_url(self, size):
        return Path(Path(self.image.url).parent, Path(self.image.url).stem + '-' + str(size) + '.jpg')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # The following operations are applied to the image file -every time- the model is saved (so do it only once!)
        # ImageMagick is used here as Pillow uses way too much memory
        # Strip unnecessary meta data and resize uploaded image down where necessary
        cmd = ['convert', self.image.path+'[0]', '-colorspace', 'Lab', '-filter', 'Lanczos',
               '-resize', '{}x{}>'.format(*self.ARTWORK_MAX_SIZE), '-colorspace', 'sRGB',
               '-strip', '-quality', str(self.ARTWORK_JPEG_QUALITY), self.image.path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            logger.info('Artwork: saved file "{}"'.format(self.image.path))
        else:
            logger.error('Artwork: ImageMagick convert returned exit code {}:\n {}'.
                         format(result.returncode, result.stderr.decode('utf-8')))
        # Create alternative sizes
        for size in self.ARTWORK_SIZES:
            file = self.get_image_path(size[2])
            cmd = ['convert', self.image.path+'[0]', '-colorspace', 'Lab', '-filter', 'Lanczos',
                   '-thumbnail', '{}x{}>'.format(size[0], size[1]), '-colorspace', 'sRGB', '-strip']
            if size[0] > 200:
                cmd.extend(['-quality', str(self.ARTWORK_JPEG_QUALITY)])
            else:
                cmd.extend(['-unsharp', '0x.5', '-quality', str(self.ARTWORK_JPEG_QUALITY_THUMB)])
            cmd.append(file)
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                logger.info('Artwork: saved file "{}"'.format(file))
            else:
                logger.error('Artwork: ImageMagick convert returned exit code {}:\n {}'.
                             format(result.returncode, result.stderr.decode('utf-8')))

    def delete(self, *args, **kwargs):
        storage, path = self.image.storage, self.image.path
        super().delete(*args, **kwargs)
        # Delete original image
        try:
            storage.delete(path)
            logger.info('Artwork: deleted file "{}"'.format(path))
        except FileNotFoundError:
            logger.warning('Artwork: attempt to delete file "{}" failed: file not found'.format(path))
        # Delete thumbnails
        for size in self.ARTWORK_SIZES:
            file = self.get_image_path(size[2])
            try:
                storage.delete(file)
                logger.info('Artwork: deleted file "{}"'.format(file))
            except FileNotFoundError:
                logger.warning('Artwork: attempt to delete file "{}" failed: file not found'.format(file))
        # Delete related folders
        sub_folder = Path(path).parent
        artwork_folder = sub_folder.parent
        try:
            sub_folder.rmdir()
            logger.info('Artwork: deleted folder "{}"'.format(sub_folder))
            artwork_folder.rmdir()
            logger.info('Artwork: deleted folder "{}"'.format(artwork_folder))
        except OSError:
            pass

    class Meta:
        abstract = True


class Language(models.Model):
    # Fixture: fixtures/language.json
    code = models.CharField('code', primary_key=True, max_length=2)
    name = models.CharField('name', max_length=50)
    country_code = models.CharField('country code', max_length=2)

    def __str__(self):
        return self.name
