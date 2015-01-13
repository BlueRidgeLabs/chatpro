from __future__ import unicode_literals

from chatpro.msgs.models import Message, MESSAGE_MAX_LEN
from chatpro.rooms.models import Room
from dash.orgs.views import OrgPermsMixin
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartTemplateView


class ChatView(OrgPermsMixin, SmartTemplateView):
    """
    Chat homepage
    """
    title = _("Chat")
    template_name = 'home/chat.haml'

    def has_permission(self, request, *args, **kwargs):
        return request.user.is_authenticated()

    def get_context_data(self, **kwargs):
        context = super(ChatView, self).get_context_data(**kwargs)
        rooms = self.request.user.get_rooms(self.request.org)

        if 'room' in self.kwargs:
            initial_room = Room.objects.get(pk=self.kwargs['room'])
        else:
            initial_room = rooms.first()

        msg_text_chars = MESSAGE_MAX_LEN - len(Message.get_prefix(self.request.user.profile))

        context['rooms'] = rooms
        context['initial_room'] = initial_room
        context['msg_text_chars'] = msg_text_chars
        return context


######################### Monkey patching for the OrgCRUDL class #########################


from dash.orgs.views import OrgCRUDL
OrgCRUDL.Edit.success_url = '@home.chat'