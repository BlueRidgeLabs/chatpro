from __future__ import unicode_literals

from django.conf.urls import patterns, url
from .views import ContactCRUDL, MessageCRUDL, RoomCRUDL, HomeView

urlpatterns = ContactCRUDL().as_urlpatterns()
urlpatterns += MessageCRUDL().as_urlpatterns()
urlpatterns += RoomCRUDL().as_urlpatterns()
urlpatterns += patterns('', url(r'^$', HomeView.as_view(), name='chat.home'))
urlpatterns += patterns('', url(r'^room/participants$', HomeView.as_view(), name='chat.home'))
