from __future__ import unicode_literals

from .views import ContactCRUDL, RoomCRUDL, SupervisorCRUDL

urlpatterns = ContactCRUDL().as_urlpatterns()
urlpatterns += RoomCRUDL().as_urlpatterns()
urlpatterns += SupervisorCRUDL().as_urlpatterns()
