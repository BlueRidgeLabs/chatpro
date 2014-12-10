from __future__ import unicode_literals

from .views import ContactCRUDL, SupervisorCRUDL

urlpatterns = ContactCRUDL().as_urlpatterns()
urlpatterns += SupervisorCRUDL().as_urlpatterns()
