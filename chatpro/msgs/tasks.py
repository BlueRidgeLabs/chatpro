from __future__ import unicode_literals

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_message(message_id):
    from .models import Message, STATUS_SENT

    message = Message.objects.select_related('org', 'room', 'sender').get(pk=message_id)

    if message.sender.is_contact():
        raise ValueError("Can't send a message from a contact")

    client = message.org.get_temba_client()
    client.send_message(message.text, groups=[message.room.group_uuid])

    message.status = STATUS_SENT
    message.save(update_fields=('status',))

    logger.info("Sent message from user #%d" % message.sender.user_id)
