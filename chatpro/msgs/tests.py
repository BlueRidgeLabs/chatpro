from __future__ import unicode_literals

import pytz

from chatpro.test import ChatProTest
from chatpro.msgs.models import Message
from datetime import datetime
from django.core.urlresolvers import reverse
from .utils import format_iso8601


class MessageTest(ChatProTest):
    def test_create(self):
        # test from contact
        msg = Message.create(self.unicef, self.contact1, "Hello", self.room1)
        self.assertEqual(msg.org, self.unicef)
        self.assertEqual(msg.sender, self.contact1.profile)
        self.assertEqual(msg.text, "Hello")
        self.assertEqual(msg.room, self.room1)

        # test from user
        msg = Message.create(self.unicef, self.user1, "Hello", self.room1)
        self.assertEqual(msg.org, self.unicef)
        self.assertEqual(msg.sender, self.user1.profile)
        self.assertEqual(msg.text, "Hello")
        self.assertEqual(msg.room, self.room1)

    def test_as_json(self):
        msg = Message.create(self.unicef, self.contact1, "Hello", self.room1)
        self.assertEqual(msg.as_json(), dict(id=msg.id, sender=self.contact1.profile.as_json(),
                                             text="Hello", room_id=self.room1.id, time=msg.time))


class MessageCRUDLTest(ChatProTest):
    def test_send(self):
        send_url = reverse('msgs.message_send')

        # send as admin user
        self.login(self.admin)
        response = self.url_post('unicef', send_url, dict(room=self.room1.id, text="Hello 1"))
        self.assertEqual(response.status_code, 200)

        msg = Message.objects.get(text="Hello 1")
        self.assertEqual(msg.room, self.room1)
        self.assertEqual(msg.sender, self.admin.profile)

        # send as regular user
        self.login(self.user1)
        response = self.url_post('unicef', send_url, dict(room=self.room1.id, text="Hello 2"))
        self.assertEqual(response.status_code, 200)

        msg = Message.objects.get(text="Hello 2")
        self.assertEqual(msg.room, self.room1)
        self.assertEqual(msg.sender, self.user1.profile)

        # try to send to room that user doesn't have access to
        response = self.url_post('unicef', send_url, dict(room=self.room3.id, text="Hello 3"))
        self.assertFalse(Message.objects.filter(text="Hello 3").exists())

    def test_list(self):
        def create_message(user, room, num, time):
            return Message.objects.create(org=self.unicef, sender=user.profile, text="Msg %d" % num, room=room, time=time)

        msg1 = create_message(self.user1, self.room1, 1, datetime(2014, 1, 1, 1, 0, 0, 0, pytz.UTC))
        msg2 = create_message(self.user1, self.room1, 2, datetime(2014, 1, 1, 2, 0, 0, 0, pytz.UTC))
        msg3 = create_message(self.user1, self.room1, 3, datetime(2014, 1, 1, 3, 0, 0, 0, pytz.UTC))

        # after_id as admin user
        self.login(self.admin)
        response = self.url_get('unicef', reverse('msgs.message_list'), {'after_id': msg1.id})
        self.assertContains(response, "Msg 2", status_code=200)
        self.assertContains(response, "Msg 3")

        # before_id as regular user
        self.login(self.user1)
        response = self.url_get('unicef', reverse('msgs.message_list'), {'before_id': msg3.id})
        self.assertContains(response, "Msg 1", status_code=200)
        self.assertContains(response, "Msg 2")

        # after_time
        response = self.url_get('unicef', reverse('msgs.message_list'), {'after_time': format_iso8601(msg1.time)})
        self.assertContains(response, "Msg 2", status_code=200)
        self.assertContains(response, "Msg 3")

        # before_time
        response = self.url_get('unicef', reverse('msgs.message_list'), {'before_time': format_iso8601(msg3.time)})
        self.assertContains(response, "Msg 1", status_code=200)
        self.assertContains(response, "Msg 2")
