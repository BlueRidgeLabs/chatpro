from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from chatpro.rooms.models import Room
from chatpro.profiles.models import Contact
from chatpro.test import ChatProTest
from mock import patch
from temba.types import Contact as TembaContact, Group as TembaGroup


class RoomTest(ChatProTest):
    def test_get_all(self):
        self.assertEqual(len(Room.get_all(self.unicef)), 3)
        self.assertEqual(len(Room.get_all(self.nyaruka)), 1)

    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('chatpro.profiles.TembaClient.get_groups')
    @patch('chatpro.profiles.TembaClient.get_contacts')
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
        self.assertEqual(jan.profile.full_name, "Jan")
        self.assertEqual(jan.profile.chat_name, "jan")
        self.assertEqual(jan.urn, 'tel:123')
        self.assertEqual(jan.room, new_room)
        self.assertTrue(jan.is_active)

        # change group and contacts on chatpro side
        Room.objects.filter(name="New group").update(name="Huh?", is_active=False)
        jan.profile.full_name = "Janet"
        jan.profile.save()
        Contact.objects.filter(profile__full_name="Ken").update(is_active=False)

        # re-select new group
        Room.update_room_groups(self.unicef, ['000-007'])

        # local changes should be overwritten
        self.assertEqual(self.unicef.rooms.get(is_active=True).name, 'New group')
        self.assertEqual(self.unicef.contacts.filter(is_active=True).count(), 2)
        Contact.objects.get(profile__full_name="Jan", is_active=True)


class RoomCRUDLTest(ChatProTest):
    def test_list(self):
        list_url = reverse('rooms.room_list')

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', list_url)
        self.assertRedirects(response, 'http://unicef.localhost/users/login/?next=/room/')

        # log in as an administrator
        self.login(self.admin)

        response = self.url_get('unicef', list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 3)
