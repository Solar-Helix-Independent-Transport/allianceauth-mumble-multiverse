"""App Tasks"""

# Standard Library
import logging

# Third Party
from celery import shared_task
from httpx import HTTPError

# Alliance Auth
from allianceauth.services.tasks import QueueOnce

# AA Mumbleverse
from mumbleverse.models import MumbleverseServer, MumbleverseServerUser

from .provider import set_groups

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=QueueOnce)
def update_server_groups(self, server_id):
    set_groups(MumbleverseServer.objects.get(id=server_id))


@shared_task(bind=True, base=QueueOnce)
def disable_server_user(self, server_id: int, user_id: int):
    try:
        _u = MumbleverseServerUser.objects.get(
            server_id=server_id,
            user_id=user_id
        )
        _u.kick_user("Deactivated by Auth")
        req = _u.deregister_user()
        if req:
            _u.delete()
    except MumbleverseServerUser.DoesNotExist:
        logger.error("Unable to delete user? none exists?")
    except HTTPError as error:
        logger.error(f"Failed to delete user from mumble server api - {server_id} - {user_id}")
        logger.error(f"{error.request} - {error.args}")
        self.retry(countdown=60)


@shared_task(bind=True, base=QueueOnce)
def check_all_users_in_server(self, server_id):
    server = MumbleverseServer.objects.get(id=server_id)
    users = server.mumbleverseserveruser_set.all()
    for u in users:
        if not MumbleverseServer.user_can_access_server(u.user, server):
            disable_server_user.delay(server.id, u.user.id)
        # else:
        #     print(f"pass {u}")


@shared_task(bind=True, base=QueueOnce)
def check_users_in_all_server(self):
    servers = MumbleverseServer.objects.all()
    for server in servers:
        check_all_users_in_server.delay(server.id)
