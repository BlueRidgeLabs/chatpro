from __future__ import unicode_literals

from .views import ContactCRUDL, MessageCRUDL, RoomCRUDL, UserCRUDL

urlpatterns = ContactCRUDL().as_urlpatterns()
urlpatterns += MessageCRUDL().as_urlpatterns()
urlpatterns += RoomCRUDL().as_urlpatterns()
urlpatterns += UserCRUDL().as_urlpatterns()
