from __future__ import unicode_literals

from django.conf.urls import patterns, url
from .views import ChatView

urlpatterns = patterns('', url(r'^$', ChatView.as_view(), name='home.chat'))
urlpatterns += patterns('', url(r'^chat/(?P<room>\d+)/$', ChatView.as_view(), name='home.chat_in'))
