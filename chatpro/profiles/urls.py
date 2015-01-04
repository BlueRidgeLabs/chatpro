from __future__ import unicode_literals

from .views import ContactCRUDL, UserCRUDL, ProfileCRUDL

urlpatterns = ContactCRUDL().as_urlpatterns()
urlpatterns += UserCRUDL().as_urlpatterns()
urlpatterns += ProfileCRUDL().as_urlpatterns()
