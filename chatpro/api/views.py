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
        entity = kwargs['entity'].lower()
        action = kwargs['action'].lower()
        org = request.org

        if entity == 'message' and action == 'new':
            contact_uuid = request.REQUEST.get('contact', None)
            text = request.REQUEST.get('text', None)
            group_uuid = request.REQUEST.get('group', None)

            if not (contact_uuid and text and group_uuid):
                return HttpResponseBadRequest("Missing contact, text or group parameter")

            room = self._get_or_create_room(org, group_uuid)
            contact = self._get_or_create_contact(org, room, contact_uuid)

            Message.create_for_contact(org, contact, text, room)

        elif entity == 'contact' and action == 'new':
            contact_uuid = request.REQUEST.get('contact', None)
            group_uuid = request.REQUEST.get('group', None)

            if not (contact_uuid and group_uuid):
                return HttpResponseBadRequest("Missing contact or group parameter")

            room = self._get_or_create_room(org, group_uuid)
            self._get_or_create_contact(org, room, contact_uuid)

        return JsonResponse({})

    def _get_or_create_room(self, org, group_uuid):
        """
        Gets a room by group UUID, or creates it by fetching from Temba instance
        """
        room = Room.objects.filter(org=org, group_uuid=group_uuid).first()
        if room:
            if not room.is_active:
                room.is_active = True
                room.save(update_fields=('is_active',))
        else:
            temba_group = org.get_temba_client().get_group(group_uuid)
            room = Room.create(org, temba_group.name, temba_group.uuid)

        return room

    def _get_or_create_contact(self, org, room, contact_uuid):
        """
        Gets a contact by UUID, or creates it by fetching from Temba instance
        """
        contact = Contact.objects.filter(org=org, uuid=contact_uuid).first()
        if contact:
            if not contact.is_active or contact.room_id != room.pk:
                contact.is_active = True
                contact.room = room
                contact.save(update_fields=('is_active', 'room'))
        else:
            temba_contact = org.get_temba_client().get_contact(contact_uuid)
            contact = Contact.create(org, temba_contact.name, temba_contact.urns[0], room, temba_contact.uuid)

        return contact
