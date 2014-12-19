from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^manage/', include('dash.orgs.urls')),
    url(r'^users/', include('dash.users.urls')),
    url(r'^api/v1', include('chatpro.api.urls')),
    url(r'', include('chatpro.chat.urls')),
    url(r'', include('chatpro.users_ext.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = patterns('',
    url(r'^__debug__/', include(debug_toolbar.urls)),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'', include('django.contrib.staticfiles.urls')),
) + urlpatterns
