from __future__ import unicode_literals

from django.conf.urls import patterns, url
from .views import TembaHandler

urlpatterns = patterns('',
                       url(r'^/(?P<entity>message|contact)/(?P<action>new|del)/', TembaHandler.as_view(), name='api.temba_handler'))