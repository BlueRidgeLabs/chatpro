from __future__ import unicode_literals

from chatpro.rooms.models import Room
from chatpro.profiles.models import Profile
from dash.orgs.models import Org
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class Message(models.Model):
    """
    A message sent to a room. May originate from a RapidPro contact or a ChatPro user
    """
    org = models.ForeignKey(Org, verbose_name=_("Organization"), related_name='messages')

    sender = models.ForeignKey(Profile, null=True, verbose_name=_("Profile"), related_name='messages',
                               help_text=_("The profile that sent this message"))

    text = models.CharField(max_length=640)

    room = models.ForeignKey(Room, verbose_name=_("Room"), related_name='messages',
                             help_text=_("The room which this message was sent to"))

    time = models.DateTimeField(verbose_name=_("Time"), help_text=_("The time when this message was sent"))

    @classmethod
    def create(cls, org, user_or_contact, text, room):
        if not user_or_contact.profile:
            ValueError("Message sender does not have a profile")

        return cls.objects.create(org=org, sender=user_or_contact.profile, text=text, room=room, time=timezone.now())

    def as_json(self):
        return dict(id=self.pk, sender=self.sender.as_json(),
                    text=self.text, room_id=self.room_id, time=self.time)