# Django
from django.db.models.signals import m2m_changed

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Mumbleverse
from mumbleverse.tasks import check_all_users_in_server

from .models import MumbleverseServer

logger = get_extension_logger(__name__)


def perms_change(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
        Perms have chagned CHECK EVERYONE!
    """
    if action in ["post_remove"]:
        check_all_users_in_server.delay(
            instance.id
        )


# all the m2m's
m2m_changed.connect(perms_change, sender=MumbleverseServer.state_access.through)
m2m_changed.connect(perms_change, sender=MumbleverseServer.group_access.through)
m2m_changed.connect(perms_change, sender=MumbleverseServer.character_access.through)
m2m_changed.connect(perms_change, sender=MumbleverseServer.corporation_access.through)
m2m_changed.connect(perms_change, sender=MumbleverseServer.alliance_access.through)
m2m_changed.connect(perms_change, sender=MumbleverseServer.faction_access.through)
