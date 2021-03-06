from __future__ import unicode_literals

import pytz

from chatpro.msgs.models import Message, STATUS_PENDING, STATUS_SENT
from chatpro.test import ChatProTest
from datetime import datetime
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mock import patch
from temba.types import Broadcast as TembaBroadcast
from temba.utils import format_iso8601


class MessageTest(ChatProTest):
    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('dash.orgs.models.TembaClient.create_broadcast')
    def test_create(self, mock_create_broadcast):
        mock_create_broadcast.return_value = TembaBroadcast.create(contacts=[self.contact1.uuid])

        # test from contact
        msg = Message.create_for_contact(self.unicef, self.contact1, "Hello", self.room1)
        self.assertEqual(msg.org, self.unicef)
        self.assertEqual(msg.contact, self.contact1)
        self.assertEqual(msg.user, None)
        self.assertEqual(msg.text, "Hello")
        self.assertEqual(msg.room, self.room1)
        self.assertEqual(msg.status, STATUS_SENT)
        self.assertIsNotNone(msg.time)
        self.assertFalse(msg.is_user_message())

        self.assertEqual(msg.as_json(), dict(id=msg.id, sender=self.contact1.as_participant_json(), text="Hello",
                                             room_id=self.room1.id, time=msg.time, status='S'))

        # test from user
        msg = Message.create_for_user(self.unicef, self.user1, "Goodbye", self.room1)
        self.assertEqual(msg.org, self.unicef)
        self.assertEqual(msg.contact, None)
        self.assertEqual(msg.user, self.user1)
        self.assertEqual(msg.text, "Goodbye")
        self.assertEqual(msg.room, self.room1)
        self.assertEqual(msg.status, STATUS_PENDING)
        self.assertIsNotNone(msg.time)
        self.assertTrue(msg.is_user_message())

        self.assertEqual(msg.as_json(), dict(id=msg.id, sender=self.user1.profile.as_participant_json(), text="Goodbye",
                                             room_id=self.room1.id, time=msg.time, status='P'))

        # async task will have sent the message
        self.assertEqual(Message.objects.get(pk=msg.pk).status, STATUS_SENT)

    def test_get_user_prefix(self):
        self.assertEqual(Message.get_user_prefix(self.superuser), '')
        self.assertEqual(Message.get_user_prefix(self.user1), 'sammy: ')


class MessageCRUDLTest(ChatProTest):
    @override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory')
    @patch('dash.orgs.models.TembaClient.create_broadcast')
    def test_send(self, mock_create_broadcast):
        mock_create_broadcast.return_value = TembaBroadcast.create(contacts=[self.contact1.uuid])

        send_url = reverse('msgs.message_send')

        # try to send as superuser who doesn't have a chat profile
        self.login(self.superuser)
        response = self.url_post('unicef', send_url, dict(room=self.room1.id, text="Hello"))
        self.assertEqual(response.status_code, 403)

        # send as admin user
        self.login(self.admin)
        response = self.url_post('unicef', send_url, dict(room=self.room1.id, text="Hello 1"))
        self.assertEqual(response.status_code, 200)
        mock_create_broadcast.assert_called_with("richard: Hello 1", groups=[self.room1.uuid])

        msg = Message.objects.get(text="Hello 1")
        self.assertEqual(msg.room, self.room1)
        self.assertEqual(msg.user, self.admin)

        # send as regular user
        self.login(self.user1)
        response = self.url_post('unicef', send_url, dict(room=self.room1.id, text="Hello 2"))
        self.assertEqual(response.status_code, 200)
        mock_create_broadcast.assert_called_with("sammy: Hello 2", groups=[self.room1.uuid])

        msg = Message.objects.get(text="Hello 2")
        self.assertEqual(msg.room, self.room1)
        self.assertEqual(msg.user, self.user1)

        # try to send to room that user doesn't have access to
        self.url_post('unicef', send_url, dict(room=self.room3.id, text="Hello 3"))
        self.assertFalse(Message.objects.filter(text="Hello 3").exists())

    def test_list(self):
        def create_message(user, room, num, time):
            return Message.objects.create(org=self.unicef, user=user, text="Msg %d" % num, room=room, time=time)

        msg1 = create_message(self.user1, self.room1, 1, datetime(2014, 1, 1, 1, 0, 0, 0, pytz.UTC))
        msg2 = create_message(self.user1, self.room1, 2, datetime(2014, 1, 1, 2, 0, 0, 0, pytz.UTC))
        msg3 = create_message(self.user2, self.room3, 3, datetime(2014, 1, 1, 3, 0, 0, 0, pytz.UTC))

        # log in as admin who can see messages from all rooms
        self.login(self.admin)

        # by room id
        response = self.url_get('unicef', reverse('msgs.message_list'), {'room': self.room1.pk})
        self.assertContains(response, "Msg 1", status_code=200)
        self.assertContains(response, "Msg 2")
        self.assertNotContains(response, "Msg 3")

        # by ids
        response = self.url_get('unicef', reverse('msgs.message_list'), {'ids': '%d,%d' % (msg1.id, msg3.id)})
        self.assertContains(response, "Msg 1", status_code=200)
        self.assertContains(response, "Msg 3")
        self.assertNotContains(response, "Msg 2")

        # by after_id
        response = self.url_get('unicef', reverse('msgs.message_list'), {'after_id': msg1.id})
        self.assertContains(response, "Msg 2", status_code=200)
        self.assertContains(response, "Msg 3")
        self.assertNotContains(response, "Msg 1")

        # by before_id
        response = self.url_get('unicef', reverse('msgs.message_list'), {'before_id': msg3.id})
        self.assertContains(response, "Msg 1", status_code=200)
        self.assertContains(response, "Msg 2")
        self.assertNotContains(response, "Msg 3")

        # by after_time
        response = self.url_get('unicef', reverse('msgs.message_list'), {'after_time': format_iso8601(msg1.time)})
        self.assertContains(response, "Msg 2", status_code=200)
        self.assertContains(response, "Msg 3")
        self.assertNotContains(response, "Msg 1")

        # by before_time
        response = self.url_get('unicef', reverse('msgs.message_list'), {'before_time': format_iso8601(msg3.time)})
        self.assertContains(response, "Msg 1", status_code=200)
        self.assertContains(response, "Msg 2")
        self.assertNotContains(response, "Msg 3")

        # log in as user who does have access to room #3
        self.login(self.user1)

        # by ids ignores ids not in accessible rooms
        response = self.url_get('unicef', reverse('msgs.message_list'), {'ids': '%d,%d,%d' % (msg1.id, msg2.id, msg3.id)})
        self.assertContains(response, "Msg 1", status_code=200)
        self.assertContains(response, "Msg 2")
        self.assertNotContains(response, "Msg 3")

        # by room gives permission denied
        response = self.url_get('unicef', reverse('msgs.message_list'), {'room': self.room3.pk})
        self.assertEqual(response.status_code, 403)

        # check empty response
        response = self.url_get('unicef', reverse('msgs.message_list'), {'ids': [123]})
        self.assertNotContains(response, "Msg 1", status_code=200)
        self.assertNotContains(response, "Msg 3")
        self.assertNotContains(response, "Msg 2")
