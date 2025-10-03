"""App Tasks"""

# Standard Library
import logging

# Third Party
from celery import shared_task
from allianceauth.services.tasks import QueueOnce
from .provider import set_groups, deregister_user
logger = logging.getLogger(__name__)


@shared_task(bind=True, base=QueueOnce)
def update_server_groups(self, server_id):
    set_groups(server_id)

@shared_task(bind=True, base=QueueOnce)
def disable_server_user(self, server_id, uid):
    deregister_user(server_id, uid)

