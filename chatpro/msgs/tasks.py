from __future__ import unicode_literals

from celery.utils.log import get_task_logger
from djcelery_transactions import task

logger = get_task_logger(__name__)


@task
def send_message(message_id):
    from .models import Message, STATUS_SENT, STATUS_FAILED

    message = Message.objects.select_related('org', 'room', 'user').get(pk=message_id)

    if not message.is_user_message():  # pragma: no cover
        raise ValueError("Can only send user-created messages")

    text = "".join([Message.get_user_prefix(message.user), message.text])

    client = message.org.get_temba_client()

    try:
        client.create_broadcast(text, groups=[message.room.uuid])

        message.status = STATUS_SENT
        message.save(update_fields=('status',))

        logger.info("Sent message %d from user #%d" % (message.pk, message.user.pk))
    except Exception:
        message.status = STATUS_FAILED
        message.save(update_fields=('status',))

        logger.error("Sending message %d failed" % message.pk, exc_info=1)
