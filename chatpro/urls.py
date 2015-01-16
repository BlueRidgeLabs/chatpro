from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'', include('chatpro.home.urls')),
    url(r'', include('chatpro.msgs.urls')),
    url(r'', include('chatpro.profiles.urls')),
    url(r'', include('chatpro.rooms.urls')),
    url(r'^manage/', include('chatpro.orgs_ext.urls')),
    url(r'^users/', include('dash.users.urls')),  # TODO replace forget password views and remove
    url(r'^api/v1', include('chatpro.api.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
)

if settings.DEBUG:  # pragma: no cover
    import debug_toolbar
    urlpatterns = patterns('',
    url(r'^__debug__/', include(debug_toolbar.urls)),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'', include('django.contrib.staticfiles.urls')),
) + urlpatterns
