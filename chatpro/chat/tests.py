from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from chatpro.chat.models import Contact, Room
from chatpro.test import ChatProTest
from mock import patch
from temba.types import Contact as TembaContact, Group as TembaGroup


class ContactTest(ChatProTest):
    def test_get_urn(self):
        self.assertEqual(self.contact1.get_urn(), ('tel', '1234'))
        self.assertEqual(self.contact4.get_urn(), ('twitter', 'danny'))

    def test_unicode(self):
        self.assertEqual(unicode(self.contact1), "Ann")
        self.contact1.full_name = None
        self.assertEqual(unicode(self.contact1), "ann")
        self.contact1.chat_name = None
        self.assertEqual(unicode(self.contact1), '1234')


class ContactCRUDLTest(ChatProTest):
    def test_list(self):
        list_url = reverse('chat.contact_list')

        # log in as an administrator
        self.login(self.admin)

        # so should see contacts from all rooms
        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 5)

        # log in as a user of room #1 and #2
        self.login(self.user1)

        # so should see contacts from just those rooms
        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 4)

        # log in as administrator for different org with no contacts
        self.login(self.nic)
        response = self.url_get('nyaruka', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 0)

    def test_read(self):
        # log in as an administrator
        self.login(self.admin)

        # can view any contact from same org
        response = self.url_get('unicef', reverse('chat.contact_read', args=[self.contact1.pk]))
        self.assertEqual(response.status_code, 200)

        # can't view contact from other org
        contact = self.create_contact(self.nyaruka, "Ken", "ken", "tel:6789", self.room4, '000-007')
        response = self.url_get('unicef', reverse('chat.contact_read', args=[contact.pk]))
        self.assertEqual(response.status_code, 404)

        # log in as a user without viewer access to the contact's room
        self.login(self.user2)
        response = self.url_get('unicef', reverse('chat.contact_read', args=[self.contact1.pk]))
        self.assertEqual(response.status_code, 404)

        # log in as a user with viewer access
        self.login(self.user1)
        response = self.url_get('unicef', reverse('chat.contact_read', args=[self.contact1.pk]))
        self.assertEqual(response.status_code, 200)

    def test_update(self):
        # log in as an administrator
        self.login(self.admin)

        # can view update page for any contact from same org
        response = self.url_get('unicef', reverse('chat.contact_update', args=[self.contact1.pk]))
        self.assertEqual(response.status_code, 200)

        # can't view update page for contact from other org
        contact = self.create_contact(self.nyaruka, "Ken", "ken", "tel:6789", self.room4, '000-007')
        response = self.url_get('unicef', reverse('chat.contact_update', args=[contact.pk]))
        self.assertEqual(response.status_code, 404)

        # log in as a user without manage access to the contact's room
        self.login(self.user2)
        response = self.url_get('unicef', reverse('chat.contact_update', args=[self.contact1.pk]))
        self.assertEqual(response.status_code, 404)

        # log in as a user with manage access
        self.login(self.user1)
        response = self.url_get('unicef', reverse('chat.contact_update', args=[self.contact1.pk]))
        self.assertEqual(response.status_code, 200)


class RoomTest(ChatProTest):
    def test_get_all(self):
        self.assertEqual(len(Room.get_all(self.unicef)), 3)
        self.assertEqual(len(Room.get_all(self.nyaruka)), 1)

    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('chatpro.users_ext.TembaClient.get_groups')
    @patch('chatpro.users_ext.TembaClient.get_contacts')
    def test_update_room_groups(self, mock_get_contacts, mock_get_groups):
        mock_get_groups.return_value = TembaGroup.deserialize_list([
            dict(uuid='000-007', name="New group", size=2)
        ])
        mock_get_contacts.return_value = TembaContact.deserialize_list([
            dict(uuid='000-007', name="Jan", urns=['tel:123'], group_uuids=['000-007'], fields=dict(chat_name="jan"), language='eng', modified_on='2014-10-01T06:54:09.817Z'),
            dict(uuid='000-008', name="Ken", urns=['tel:234'], group_uuids=['000-007'], fields=dict(chat_name="ken"), language='eng', modified_on='2014-10-01T06:54:09.817Z')
        ])

        # select one new group
        Room.update_room_groups(self.unicef, ['000-007'])
        self.assertEqual(self.unicef.rooms.filter(is_active=True).count(), 1)
        self.assertEqual(self.unicef.rooms.filter(is_active=False).count(), 3)  # existing de-activated

        new_room = Room.objects.get(group_uuid='000-007')
        self.assertEqual(new_room.name, "New group")
        self.assertTrue(new_room.is_active)

        # check contact changes
        self.assertEqual(self.unicef.contacts.filter(is_active=True).count(), 2)
        self.assertEqual(self.unicef.contacts.filter(is_active=False).count(), 5)  # existing de-activated

        jan = Contact.objects.get(uuid='000-007')
        self.assertEqual(jan.full_name, "Jan")
        self.assertEqual(jan.chat_name, "jan")
        self.assertEqual(jan.urn, 'tel:123')
        self.assertEqual(jan.room, new_room)
        self.assertTrue(jan.is_active)

        # change group and contacts on chatpro side
        Room.objects.filter(name="New group").update(name="Huh?", is_active=False)
        Contact.objects.filter(full_name="Jan").update(full_name="Janet")
        Contact.objects.filter(full_name="Ken").update(is_active=False)

        # re-select new group
        Room.update_room_groups(self.unicef, ['000-007'])

        # local changes should be overwritten
        self.assertEqual(self.unicef.rooms.get(is_active=True).name, 'New group')
        self.assertEqual(self.unicef.contacts.filter(is_active=True).count(), 2)
        Contact.objects.get(full_name="Jan", is_active=True)


class RoomCRUDLTest(ChatProTest):
    def test_list(self):
        list_url = reverse('chat.room_list')

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', list_url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/room/')

        # log in as a non-administrator
        self.login(self.admin)

        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)
