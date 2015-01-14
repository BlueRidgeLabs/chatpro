from __future__ import unicode_literals

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_message(message_id):
    from .models import Message, STATUS_SENT

    message = Message.objects.select_related('org', 'room', 'sender').get(pk=message_id)

    if message.sender.is_contact():  # pragma: no cover
        raise ValueError("Can't send a message from a contact")

    text = "".join([Message.get_prefix(message.sender), message.text])

    client = message.org.get_temba_client()
    client.create_broadcast(text, groups=[message.room.uuid])

    message.status = STATUS_SENT
    message.save(update_fields=('status',))

    logger.info("Sent message from user #%d" % message.sender.user_id)
