from __future__ import absolute_import, unicode_literals

import json

from chatpro.rooms.models import Room
from chatpro.profiles.models import Contact
from chatpro.test import ChatProTest
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils import timezone
from mock import patch
from temba.types import Contact as TembaContact, Group as TembaGroup


class RoomTest(ChatProTest):
    def test_create(self):
        testers = Room.create(self.unicef, "Testers", '000-007')
        jan = Contact.create(self.unicef, self.admin, "Jan", "janet", 'tel:1234', testers, '000-007')
        bob = User.create(self.unicef, "Bob", "bobby", "bob@unicef.org", "pass", False, [testers], [])
        ken = User.create(self.unicef, "Ken", "kenny", "ken@unicef.org", "pass", False, [], [testers])

        self.assertEqual(testers.org, self.unicef)
        self.assertEqual(testers.name, "Testers")
        self.assertEqual(testers.uuid, '000-007')
        self.assertEqual(list(testers.get_contacts()), [jan])
        self.assertEqual(list(testers.get_users().order_by('profile__full_name')), [bob, ken])
        self.assertEqual(list(testers.get_managers()), [ken])

    def test_get_all(self):
        self.assertEqual(len(Room.get_all(self.unicef)), 3)
        self.assertEqual(len(Room.get_all(self.nyaruka)), 1)

    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('chatpro.utils.temba.TembaClient.get_groups')
    @patch('chatpro.utils.temba.TembaClient.get_contacts')
    def test_update_room_groups(self, mock_get_contacts, mock_get_groups):
        mock_get_groups.return_value = [TembaGroup.create(uuid='000-007', name="New group", size=2)]
        mock_get_contacts.return_value = [
            TembaContact.create(uuid='000-007', name="Jan", urns=['tel:123'], groups=['000-007'],
                                fields=dict(chat_name="jan"), language='eng', modified_on=timezone.now()),
            TembaContact.create(uuid='000-008', name="Ken", urns=['tel:234'], groups=['000-007'],
                                fields=dict(chat_name="ken"), language='eng', modified_on=timezone.now())
        ]

        # select one new group
        Room.update_room_groups(self.unicef, ['000-007'])
        self.assertEqual(self.unicef.rooms.filter(is_active=True).count(), 1)
        self.assertEqual(self.unicef.rooms.filter(is_active=False).count(), 3)  # existing de-activated

        new_room = Room.objects.get(uuid='000-007')
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
        jan.full_name = "Janet"
        jan.save()
        Contact.objects.filter(full_name="Ken").update(is_active=False)

        # re-select new group
        Room.update_room_groups(self.unicef, ['000-007'])

        # local changes should be overwritten
        self.assertEqual(self.unicef.rooms.get(is_active=True).name, 'New group')
        self.assertEqual(self.unicef.contacts.filter(is_active=True).count(), 2)
        Contact.objects.get(full_name="Jan", is_active=True)


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

    def test_read(self):
        # log in as a regular user
        self.login(self.user1)

        # view room we have access to
        response = self.url_get('unicef', reverse('rooms.room_read', args=[self.room1.pk]))
        self.assertEqual(response.status_code, 200)

        # try to view room we don't have access to
        response = self.url_get('unicef', reverse('rooms.room_read', args=[self.room3.pk]))
        self.assertEqual(response.status_code, 404)

    def test_participants(self):
        # log in as a regular user
        self.login(self.user1)

        # view room we have access to
        response = self.url_get('unicef', reverse('rooms.room_participants', args=[self.room1.pk]))
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content, dict(count=3, results=[
            dict(id=self.contact1.pk, chat_name="ann", full_name="Ann", type="C"),
            dict(id=self.contact2.pk, chat_name="bob", full_name="Bob", type="C"),
            dict(id=self.user1.pk, chat_name="sammy", full_name="Sam Sims", type="U")
        ]))

        # try to view room we don't have access to
        response = self.url_get('unicef', reverse('rooms.room_participants', args=[self.room3.pk]))
        self.assertEqual(response.status_code, 404)
