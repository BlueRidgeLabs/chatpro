from __future__ import unicode_literals

from chatpro.rooms.models import Room
from chatpro.utils import parse_iso8601
from dash.orgs.views import OrgPermsMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from smartmin.users.views import SmartCRUDL, SmartListView
from smartmin.users.views import SmartCreateView
from .models import Message


class MessageCRUDL(SmartCRUDL):
    model = Message
    actions = ('list', 'send')

    class Send(OrgPermsMixin, SmartCreateView):
        def post(self, request, *args, **kwargs):
            org = self.derive_org()
            room = Room.objects.get(pk=request.REQUEST.get('room'))
            text = request.REQUEST.get('text')

            if not (self.request.user.has_profile() and self.request.user.has_room_access(room)):
                raise PermissionDenied()

            msg = Message.create_for_user(org, self.request.user, text, room)
            return JsonResponse(msg.as_json())

    class List(OrgPermsMixin, SmartListView):
        paginate_by = None  # switch off Django pagination
        max_results = 10
        default_order = ('-id',)

        def get_queryset(self, **kwargs):
            org = self.derive_org()
            qs = Message.objects.filter(org=org)

            room_id = self.request.REQUEST.get('room', None)
            ids = self.request.REQUEST.getlist('ids')
            before_id = self.request.REQUEST.get('before_id', None)
            after_id = self.request.REQUEST.get('after_id', None)
            before_time = self.request.REQUEST.get('before_time', None)
            after_time = self.request.REQUEST.get('after_time', None)

            if room_id:
                room = Room.objects.get(pk=room_id)
                if not self.request.user.has_room_access(room):
                    raise PermissionDenied()
                qs = qs.filter(room_id=room.id)
            else:
                qs = qs.filter(room__in=self.request.user.get_rooms(org))

            if ids:
                qs = qs.filter(pk__in=ids)
            if before_id:
                qs = qs.filter(pk__lt=int(before_id))
            if after_id:
                qs = qs.filter(pk__gt=int(after_id))
            if before_time:
                qs = qs.filter(time__lt=parse_iso8601(before_time))
            if after_time:
                qs = qs.filter(time__gt=parse_iso8601(after_time))

            return self.order_queryset(qs)

        def render_to_response(self, context, **response_kwargs):
            total = context['object_list'].count()
            messages = list(context['object_list'][:self.max_results])

            if messages:
                max_id = messages[0].pk
                min_id = messages[-1].pk
                has_older = len(messages) < total
            else:
                max_id = None
                min_id = None
                has_older = False

            results = [msg.as_json() for msg in messages]

            return JsonResponse({'count': len(results),
                                 'max_id': max_id,
                                 'min_id': min_id,
                                 'has_older': has_older,
                                 'results': results})
