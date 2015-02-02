from __future__ import absolute_import, unicode_literals

from chatpro.msgs.models import Message, MESSAGE_MAX_LEN
from chatpro.rooms.models import Room
from dash.orgs.views import OrgPermsMixin
from django.core.exceptions import PermissionDenied
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
        allowed_rooms = self.request.user.get_rooms(self.request.org).order_by('name')

        if 'room' in self.kwargs:
            try:
                initial_room = allowed_rooms.get(pk=self.kwargs['room'])
            except Room.DoesNotExist:
                raise PermissionDenied()
        else:
            initial_room = allowed_rooms.first()

        msg_text_chars = MESSAGE_MAX_LEN - len(Message.get_user_prefix(self.request.user))

        context['rooms'] = allowed_rooms
        context['initial_room'] = initial_room
        context['msg_text_chars'] = msg_text_chars
        return context
