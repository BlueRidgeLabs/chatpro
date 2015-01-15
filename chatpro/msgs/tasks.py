from __future__ import unicode_literals

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_message(message_id):
    from .models import Message, STATUS_SENT

    message = Message.objects.select_related('org', 'room', 'user').get(pk=message_id)

    if not message.is_user_message():  # pragma: no cover
        raise ValueError("Can only send user-created messages")

    text = "".join([Message.get_user_prefix(message.user), message.text])

    client = message.org.get_temba_client()
    client.create_broadcast(text, groups=[message.room.uuid])

    message.status = STATUS_SENT
    message.save(update_fields=('status',))

    logger.info("Sent message from user #%d" % message.user.pk)
