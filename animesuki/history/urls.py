"""AnimeSuki History URLs"""

from django.urls import path

from .views import (HistoryDetailView, HistoryListView, history_action)


app_name = 'history'
urlpatterns = [
    path('<int:pk>', HistoryDetailView.as_view(), name='detail'),
    path('<int:pk>/action', history_action, name='action'),
    path('browse', HistoryListView.as_view(), name='browse'),
]
