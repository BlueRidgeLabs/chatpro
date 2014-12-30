from __future__ import unicode_literals

from chatpro.chat.models import Message
from chatpro.test import ChatProTest
from django.core.urlresolvers import reverse


class TembaHandlerTest(ChatProTest):
    def test_post(self):
        url = reverse('api.temba_handler', kwargs=dict(entity='message', action='new'))

        # GET is not allowed
        response = self.url_get('unicef', '%s?%s' % (url, 'contact=000-001&text=Hello%20World&group=000-001'))
        self.assertEqual(response.status_code, 405)

        # POST is allowed
        response = self.url_post('unicef', '%s?%s' % (url, 'contact=000-001&text=Hello%20World&group=000-001'))
        self.assertEqual(response.status_code, 200)

        # check new message created
        msg = Message.objects.get()
        self.assertEqual(msg.text, "Hello World")
        self.assertEqual(msg.contact, self.contact1)
        self.assertIsNone(msg.user)

        # TODO check adding new contact or room
