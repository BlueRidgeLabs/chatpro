from __future__ import unicode_literals

from django.conf.urls import patterns, url
from .views import HomeView

urlpatterns = patterns('', url(r'^$', HomeView.as_view(), name='home.chat'))
urlpatterns += patterns('', url(r'^chat/(?P<room>\d+)/$', HomeView.as_view(), name='home.chat_in'))
