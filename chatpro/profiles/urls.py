from __future__ import absolute_import, unicode_literals

from django.conf.urls import patterns, url
from .views import ContactCRUDL, ManageUserCRUDL, UserCRUDL

urlpatterns = ContactCRUDL().as_urlpatterns()
urlpatterns += UserCRUDL().as_urlpatterns()
urlpatterns += ManageUserCRUDL().as_urlpatterns()

# contact create view can optionally be accessed with an initial room id
urlpatterns += patterns('', url(r'^contact/create/(?P<room>\d+)/$',
                                ContactCRUDL.Create.as_view(),
                                name='profiles.contact_create_in'))
