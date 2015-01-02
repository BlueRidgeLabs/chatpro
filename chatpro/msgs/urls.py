from __future__ import unicode_literals

from .views import MessageCRUDL

urlpatterns = MessageCRUDL().as_urlpatterns()
