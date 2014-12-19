from __future__ import unicode_literals

from chatpro.chat.models import Contact, Message, Room
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View


class TembaHandler(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(TembaHandler, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(('POST',))

    def post(self, request, *args, **kwargs):
        action = kwargs['action'].lower()
        org = request.org

        if action == 'new_message':
            contact_uuid = request.REQUEST.get('contact', None)
            text = request.REQUEST.get('text', None)
            group_uuid = request.REQUEST.get('group', None)

            if not (contact_uuid and text and group_uuid):
                return HttpResponseBadRequest("Missing contact, text or group parameter")

            room = Room.objects.filter(org=org, group_uuid=group_uuid).first()
            if not room:
                temba_group = org.get_temba_client().get_group(group_uuid)
                room = Room.create(org, temba_group.name, temba_group.uuid)

            contact = Contact.objects.filter(org=org, uuid=contact_uuid).first()
            if not contact:
                temba_contact = org.get_temba_client().get_contact(contact_uuid)
                contact = Contact.create(org, temba_contact.name, temba_contact.urns[0], room, temba_contact.uuid)

            Message.create_for_contact(org, contact, text, room)

        return JsonResponse({})