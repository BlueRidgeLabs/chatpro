from __future__ import unicode_literals

from .views import RoomCRUDL

urlpatterns = RoomCRUDL().as_urlpatterns()
