from __future__ import absolute_import, unicode_literals

from .views import RoomCRUDL

urlpatterns = RoomCRUDL().as_urlpatterns()
