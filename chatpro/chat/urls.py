from __future__ import unicode_literals

from .views import ContactCRUDL, RoomCRUDL, UserCRUDL

urlpatterns = ContactCRUDL().as_urlpatterns()
urlpatterns += RoomCRUDL().as_urlpatterns()
urlpatterns += UserCRUDL().as_urlpatterns()
