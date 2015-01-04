from __future__ import unicode_literals

from chatpro.rooms.models import Room
from dash.orgs.views import OrgPermsMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartTemplateView


class HomeView(OrgPermsMixin, SmartTemplateView):
    """
    Chat homepage
    """
    title = _("Chat Rooms")
    template_name = 'home/chat.haml'

    def has_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated()

    def pre_process(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('users.user_login'))

        return super(HomeView, self).pre_process(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        rooms = self.request.user.get_rooms(self.request.org)

        if 'initial_room' in self.request.REQUEST:
            initial_room = Room.objects.get(self.request.REQUEST['initial_room'])
        else:
            initial_room = rooms.first()

        context['rooms'] = rooms
        context['initial_room'] = initial_room
        return context


######################### Monkey patching for the OrgCRUDL class #########################


from dash.orgs.views import OrgCRUDL
OrgCRUDL.Edit.success_url = '@home.chat'