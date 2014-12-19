from __future__ import unicode_literals

from .views import UserCRUDL

urlpatterns = UserCRUDL().as_urlpatterns()
