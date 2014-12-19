from __future__ import unicode_literals

from django.conf.urls import patterns, url
from .views import TembaHandler

urlpatterns = patterns('',
                       url(r'^/temba/(?P<action>new_message|new_contact)/', TembaHandler.as_view(), name='api.temba_handler'))