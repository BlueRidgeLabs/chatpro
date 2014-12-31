from __future__ import unicode_literals

from chatpro.chat.models import Contact, Room, Message
from chatpro.test import ChatProTest
from django.core.urlresolvers import reverse
from mock import patch
from temba.types import Contact as TembaContact, Group as TembaGroup


class TembaHandlerTest(ChatProTest):

    @patch('chatpro.users_ext.TembaClient.get_group')
    @patch('chatpro.users_ext.TembaClient.get_contact')
    def test_new_contact(self, mock_get_contact, mock_get_group):
        url = reverse('api.temba_handler', kwargs=dict(entity='contact', action='new'))

        # GET is not allowed
        response = self.url_get('unicef', '%s?%s' % (url, 'contact=000-007&group=000-001&token=1234567890'))
        self.assertEqual(response.status_code, 405)

        # forbidden response if you don't include secret token
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=001-007&group=000-001'))
        self.assertEqual(response.status_code, 403)

        # bad request if you forget a parameter
        response = self.url_post('unicef', '%s?%s' % (url, 'group=000-001&token=1234567890'))
        self.assertEqual(response.status_code, 400)

        # make a valid request for new contact in an existing group
        mock_get_contact.return_value = TembaContact.deserialize(
            dict(uuid='001-007', name="Jan", urns=['tel:123'], group_uuids=['000-001'], fields=dict(chat_name="jan"),
                 language='eng', modified_on='2014-10-01T06:54:09.817Z')
        )
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=001-007&group=000-001&token=1234567890'))
        self.assertEqual(response.status_code, 200)

        # check new contact created
        contact = Contact.objects.get(uuid='001-007')
        self.assertEqual(contact.full_name, "Jan")
        self.assertEqual(contact.urn, 'tel:123')

        # try with new room/group that must be fetched
        mock_get_contact.return_value = TembaContact.deserialize(
            dict(uuid='001-008', name="Ken", urns=['tel:234'], group_uuids=['000-001'], fields=dict(chat_name="ken"),
                 language='eng', modified_on='2014-10-01T06:54:09.817Z')
        )
        mock_get_group.return_value = TembaGroup.deserialize(
            dict(uuid='001-007', name="New group", size=2)
        )
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=001-008&group=001-007&token=1234567890'))
        self.assertEqual(response.status_code, 200)
        new_room = Room.objects.get(group_uuid='001-007', name="New group")

        # check new contact and room created
        contact = Contact.objects.get(uuid='001-008')
        self.assertEqual(contact.full_name, "Ken")
        self.assertEqual(contact.urn, 'tel:234')
        self.assertEqual(contact.room, new_room)

        # check re-activating an inactive room
        new_room.is_active = False
        new_room.save()

        response = self.url_post('unicef', '%s?%s' % (url, 'contact=001-008&group=001-007&token=1234567890'))
        self.assertEqual(response.status_code, 200)
        Room.objects.get(group_uuid='001-007', name="New group", is_active=True)

        # repeating a request shouldn't create duplicates
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=001-008&group=001-007&token=1234567890'))
        self.assertEqual(response.status_code, 200)

    @patch('chatpro.users_ext.TembaClient.get_group')
    @patch('chatpro.users_ext.TembaClient.get_contact')
    def test_new_message(self, mock_get_contact, mock_get_group):
        url = reverse('api.temba_handler', kwargs=dict(entity='message', action='new'))

        # GET is not allowed
        response = self.url_get('unicef', '%s?%s' % (url, 'contact=000-001&text=Hello%20World&group=000-001&token=1234567890'))
        self.assertEqual(response.status_code, 405)

        # bad request if you forget a parameter
        response = self.url_post('unicef', '%s?%s' % (url, 'text=Hello%20World&group=000-001&token=1234567890'))
        self.assertEqual(response.status_code, 400)

        # make a valid request for new message from an existing contact to an existing group
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=000-001&text=Hello%20World&group=000-001&token=1234567890'))
        self.assertEqual(response.status_code, 200)

        # check new message created
        msg = Message.objects.get(text="Hello World")
        self.assertEqual(msg.contact, self.contact1)
        self.assertEqual(msg.room, self.room1)
        self.assertIsNone(msg.user)

        # try with new room/group that must be fetched
        mock_get_group.return_value = TembaGroup.deserialize(
            dict(uuid='001-007', name="New group", size=2)
        )
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=000-001&text=Hello%20Again&group=001-007&token=1234567890'))
        self.assertEqual(response.status_code, 200)
        new_room = Room.objects.get(group_uuid='001-007', name="New group")

        # check new message created
        msg = Message.objects.get(text="Hello Again")
        self.assertEqual(msg.contact, self.contact1)
        self.assertEqual(msg.room, new_room)
        self.assertIsNone(msg.user)

        # try with new contact and new room/group that must be fetched
        mock_get_group.return_value = TembaGroup.deserialize(
            dict(uuid='001-008', name="Newest group", size=2)
        )
        mock_get_contact.return_value = TembaContact.deserialize(
            dict(uuid='001-007', name="Ken", urns=['tel:234'], group_uuids=['001-108'], fields=dict(chat_name="ken"),
                 language='eng', modified_on='2014-10-01T06:54:09.817Z')
        )
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=001-007&text=Goodbye&group=001-008&token=1234567890'))
        self.assertEqual(response.status_code, 200)
        new_contact = Contact.objects.get(uuid='001-007', full_name="Ken")
        new_room = Room.objects.get(group_uuid='001-008', name="Newest group")

        # check new message created
        msg = Message.objects.get(text="Goodbye")
        self.assertEqual(msg.contact, new_contact)
        self.assertEqual(msg.room, new_room)
        self.assertIsNone(msg.user)
