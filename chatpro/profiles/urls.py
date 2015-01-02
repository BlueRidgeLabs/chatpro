from __future__ import unicode_literals

from .views import ProfileCRUDL

urlpatterns = ProfileCRUDL().as_urlpatterns()
