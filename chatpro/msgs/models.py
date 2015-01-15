from __future__ import unicode_literals

from chatpro.rooms.models import Room
from chatpro.profiles.models import Contact
from dash.orgs.models import Org
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from .tasks import send_message

MESSAGE_MAX_LEN = 140

STATUS_PENDING = 'P'
STATUS_SENT = 'S'

STATUS_CHOICES = ((STATUS_PENDING, _("Pending")),
                  (STATUS_SENT, _("Sent")))


class Message(models.Model):
    """
    A message sent to a room. May originate from a RapidPro contact or a ChatPro user
    """
    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='messages')

    user = models.ForeignKey(User, null=True, verbose_name=_("User"), related_name='messages',
                             help_text=_("The user that sent this message"))

    contact = models.ForeignKey(Contact, null=True, verbose_name=_("Contact"), related_name='messages',
                                help_text=_("The contact that sent this message"))

    text = models.CharField(max_length=640)

    room = models.ForeignKey(Room, verbose_name=_("Room"), related_name='messages',
                             help_text=_("The room which this message was sent to"))

    time = models.DateTimeField(verbose_name=_("Time"), help_text=_("The time when this message was sent"))

    status = models.CharField(max_length=1, verbose_name=_("Status"), choices=STATUS_CHOICES,
                              help_text=_("Current status of this message"))

    @classmethod
    def create_for_contact(cls, org, contact, text, room):
        return cls.objects.create(org=org, contact=contact, text=text, room=room,
                                  time=timezone.now(), status=STATUS_SENT)

    @classmethod
    def create_for_user(cls, org, user, text, room):
        if not user.profile:  # pragma: no cover
            raise ValueError("User does not have a chat profile")

        msg = cls.objects.create(org=org, user=user, text=text, room=room,
                                 time=timezone.now(), status=STATUS_PENDING)

        send_message.delay(msg.pk)
        return msg

    def is_user_message(self):
        return bool(self.user_id)

    @classmethod
    def get_user_prefix(cls, user):
        return '%s: ' % user.profile.chat_name

    def as_json(self):
        participant = self.user.profile if self.is_user_message() else self.contact

        return dict(id=self.pk, sender=participant.as_participant_json(), text=self.text, room_id=self.room_id,
                    time=self.time, status=self.status)