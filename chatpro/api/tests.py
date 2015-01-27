from __future__ import absolute_import, unicode_literals

from chatpro.msgs.models import Message
from chatpro.profiles.models import Contact
from chatpro.rooms.models import Room
from chatpro.test import ChatProTest
from django.core.urlresolvers import reverse
from django.utils import timezone
from mock import patch
from temba.types import Contact as TembaContact, Group as TembaGroup


class TembaHandlerTest(ChatProTest):

    @patch('dash.orgs.models.TembaClient.get_group')
    @patch('dash.orgs.models.TembaClient.get_contact')
    def test_new_message(self, mock_get_contact, mock_get_group):
        url = reverse('api.temba_handler', kwargs=dict(entity='message', action='new'))

        # GET is not allowed
        response = self.url_get('unicef', '%s?%s' % (url, 'contact=C-001&text=Hello%20World&group=G-001&token=1234567890'))
        self.assertEqual(response.status_code, 405)

        # bad request if you forget a parameter
        response = self.url_post('unicef', '%s?%s' % (url, 'text=Hello%20World&group=G-001&token=1234567890'))
        self.assertEqual(response.status_code, 400)

        # make a valid request for new message from an existing contact to an existing group
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=C-001&text=Hello%20World&group=G-001&token=1234567890'))
        self.assertEqual(response.status_code, 200)

        # check new message created
        msg = Message.objects.get(text="Hello World")
        self.assertEqual(msg.contact, self.contact1)
        self.assertEqual(msg.room, self.room1)

        # try with new room/group that must be fetched
        mock_get_group.return_value = TembaGroup.create(uuid='G-007', name="New group", size=2)

        response = self.url_post('unicef', '%s?%s' % (url, 'contact=C-001&text=Hello%20Again&group=G-007&token=1234567890'))
        self.assertEqual(response.status_code, 200)
        new_room = Room.objects.get(uuid='G-007', name="New group")

        # check new message created
        msg = Message.objects.get(text="Hello Again")
        self.assertEqual(msg.contact, self.contact1)
        self.assertEqual(msg.room, new_room)

        # try with new contact and new room/group that must be fetched
        mock_get_group.return_value = TembaGroup.create(uuid='G-008', name="Newest group", size=2)
        mock_get_contact.return_value = TembaContact.create(uuid='C-007', name="Ken", urns=['tel:234'],
                                                            groups=['G-008'], fields=dict(chat_name="ken"),
                                                            language='eng', modified_on=timezone.now())

        response = self.url_post('unicef', '%s?%s' % (url, 'contact=001-007&text=Goodbye&group=001-008&token=1234567890'))
        self.assertEqual(response.status_code, 200)
        new_contact = Contact.objects.get(uuid='C-007')
        new_room = Room.objects.get(uuid='G-008', name="Newest group")

        # check new message created
        msg = Message.objects.get(text="Goodbye")
        self.assertEqual(msg.contact, new_contact)
        self.assertEqual(msg.room, new_room)

    @patch('dash.orgs.models.TembaClient.get_group')
    @patch('dash.orgs.models.TembaClient.get_contact')
    def test_new_contact(self, mock_get_contact, mock_get_group):
        url = reverse('api.temba_handler', kwargs=dict(entity='contact', action='new'))

        # GET is not allowed
        response = self.url_get('unicef', '%s?%s' % (url, 'contact=C-007&group=G-001&token=1234567890'))
        self.assertEqual(response.status_code, 405)

        # forbidden response if you don't include secret token
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=C-007&group=G-001'))
        self.assertEqual(response.status_code, 403)

        # bad request if you forget a parameter
        response = self.url_post('unicef', '%s?%s' % (url, 'group=G-001&token=1234567890'))
        self.assertEqual(response.status_code, 400)

        # make a valid request for new contact in an existing group
        mock_get_contact.return_value = TembaContact.create(uuid='C-007', name="Jan", urns=['tel:123'],
                                                            groups=['G-001'], fields=dict(chat_name="jan"),
                                                            language='eng', modified_on=timezone.now())

        response = self.url_post('unicef', '%s?%s' % (url, 'contact=C-007&group=G-001&token=1234567890'))
        self.assertEqual(response.status_code, 200)

        # check new contact created
        contact = Contact.objects.get(uuid='C-007')
        self.assertEqual(contact.full_name, "Jan")
        self.assertEqual(contact.chat_name, "jan")
        self.assertEqual(contact.urn, 'tel:123')
        self.assertEqual(contact.room, Room.objects.get(uuid='G-001'))

        # try with new room/group that must be fetched
        mock_get_contact.return_value = TembaContact.create(uuid='C-008', name="Ken", urns=['tel:234'],
                                                            groups=['G-007'], fields=dict(chat_name="ken"),
                                                            language='eng', modified_on=timezone.now())
        mock_get_group.return_value = TembaGroup.create(uuid='G-007', name="New group", size=2)

        response = self.url_post('unicef', '%s?%s' % (url, 'contact=C-008&group=G-007&token=1234567890'))
        self.assertEqual(response.status_code, 200)
        new_room = Room.objects.get(uuid='G-007', name="New group")

        # check new contact and room created
        contact = Contact.objects.get(uuid='C-008')
        self.assertEqual(contact.full_name, "Ken")
        self.assertEqual(contact.chat_name, "ken")
        self.assertEqual(contact.urn, 'tel:234')
        self.assertEqual(contact.room, new_room)

        # check re-activating an inactive room
        new_room.is_active = False
        new_room.save()

        response = self.url_post('unicef', '%s?%s' % (url, 'contact=C-008&group=G-007&token=1234567890'))
        self.assertEqual(response.status_code, 200)
        Room.objects.get(uuid='G-007', name="New group", is_active=True)

        # repeating a request shouldn't create duplicates
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=C-008&group=G-007&token=1234567890'))
        self.assertEqual(response.status_code, 200)

    def test_del_contact(self):
        url = reverse('api.temba_handler', kwargs=dict(entity='contact', action='del'))

        # bad request if you forget the contact parameter
        response = self.url_post('unicef', '%s?%s' % (url, '&token=1234567890'))
        self.assertEqual(response.status_code, 400)

        # make a valid request to delete contact #1
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=C-001&token=1234567890'))
        self.assertEqual(response.status_code, 200)

        contact = Contact.objects.get(pk=self.contact1.pk)
        self.assertFalse(contact.is_active)

        # try to delete a contact in another org
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=C-006&token=1234567890'))
        self.assertEqual(response.status_code, 200)

        contact = Contact.objects.get(pk=self.contact6.pk)
        self.assertTrue(contact.is_active)
