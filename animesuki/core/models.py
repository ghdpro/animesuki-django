"""AnimeSuki Core models"""

from django.db import models
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator


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


class Language(models.Model):
    # Fixture: fixtures/language.json
    code = models.CharField('code', primary_key=True, max_length=2)
    name = models.CharField('name', max_length=50)
    country_code = models.CharField('country code', max_length=2)

    def __str__(self):
        return self.name
