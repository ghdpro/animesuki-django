"""AnimeSuki URL Configuration"""

from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView, TemplateView
from django.contrib import admin

from allauth.account import views as account


# URLs for django-allauth/account have been redefined here to remove the ending slash
account_patterns = [
    path('signup', account.signup, name='account_signup'),
    path('login', account.login, name='account_login'),
    path('logout', account.logout, name='account_logout'),
    path('password/change', account.password_change, name='account_change_password'),
    path('password/set', account.password_set, name='account_set_password'),
    path('inactive', account.account_inactive, name='account_inactive'),
    # E-mail
    path('email', account.email, name='account_email'),
    path('confirm-email', account.email_verification_sent, name='account_email_verification_sent'),
    re_path(r'confirm-email/(?P<key>[-:\w]+)', account.confirm_email, name='account_confirm_email'),
    # Password reset
    path('password/reset', account.password_reset, name='account_reset_password'),
    path('password/reset/done', account.password_reset_done, name='account_reset_password_done'),
    re_path(r'password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)', account.password_reset_from_key,
            name='account_reset_password_from_key'),
    path('password/reset/key/done', account.password_reset_from_key_done, name='account_reset_password_from_key_done'),
    # No profile page at the moment
    path('profile', RedirectView.as_view(url='/'), name='account_profile'),
]

urlpatterns = [
    re_path(r'^(?P<mediatype>media|anime|manga|novel)/', include('animesuki.media.urls')),
    path('history/', include('animesuki.history.urls')),
    path('admin/', admin.site.urls),
    path('account/', include(account_patterns)),
    path('', TemplateView.as_view(template_name='frontpage.html'), name='frontpage')
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))] + \
                   static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
