from __future__ import unicode_literals

from .views import AdministratorCRUDL, UserCRUDL

urlpatterns = AdministratorCRUDL().as_urlpatterns()
urlpatterns += UserCRUDL().as_urlpatterns()
