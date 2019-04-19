"""AnimeSuki URL Configuration"""

from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView, TemplateView
from django.contrib import admin

from allauth.account import views as account

from animesuki.media.views import (MediaDetailView, MediaCreateView, MediaUpdateView, MediaArtworkView)
from animesuki.history.views import (HistoryDetailView, HistoryListView, history_action)


media_patterns = ([
    path('<int:pk>/<slug:slug>', MediaDetailView.as_view(), name='detail'),
    path('<int:pk>/<slug:slug>/edit', MediaUpdateView.as_view(), name='update'),
    path('<int:pk>/<slug:slug>/artwork', MediaArtworkView.as_view(), name='artwork'),
    path('create', MediaCreateView.as_view(), name='create'),
], 'media')

history_patterns = ([
    path('<int:pk>', HistoryDetailView.as_view(), name='detail'),
    path('<int:pk>/action', history_action, name='action'),
    path('browse', HistoryListView.as_view(), name='browse'),
], 'history')

account_patterns = [
    path('signup', account.signup, name='account_signup'),
    path('login', account.login, name='account_login'),
    path('logout', account.logout, name='account_logout'),
    path('password/change', account.password_change, name='account_change_password'),
    path('password/set', account.password_set, name='account_set_password'),
    path('inactive', account.account_inactive, name='account_inactive'),
    path('email', account.email, name='account_email'),
    path('confirm-email', account.email_verification_sent, name='account_email_verification_sent'),
    re_path(r'confirm-email/(?P<key>[-:\w]+)', account.confirm_email, name='account_confirm_email'),
    path('password/reset', account.password_reset, name='account_reset_password'),
    path('password/reset/done', account.password_reset_done, name='account_reset_password_done'),
    re_path(r'password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)', account.password_reset_from_key,
            name='account_reset_password_from_key'),
    path('password/reset/key/done', account.password_reset_from_key_done, name='account_reset_password_from_key_done'),
    # No profile page at the moment
    path('profile', RedirectView.as_view(url='/'), name='account_profile'),
]

urlpatterns = [
    re_path(r'^(?P<mediatype>media|anime|manga|novel)/', include(media_patterns)),
    path('history/', include(history_patterns)),
    path('admin/', admin.site.urls),
    path('account/', include(account_patterns)),
    path('', TemplateView.as_view(template_name='frontpage.html'), name='frontpage')
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))] + \
                   static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
