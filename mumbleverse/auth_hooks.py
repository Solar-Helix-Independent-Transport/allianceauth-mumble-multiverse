import logging
import urllib

from django.conf import settings
from django.template.loader import render_to_string
from allianceauth.notifications import notify
from django.db.models.signals import post_delete, post_save

from allianceauth import hooks
from allianceauth.services.hooks import NameFormatter, ServicesHook, UrlHook

from .tasks import update_server_groups, disable_server_user
from .models import MumbleverseServer, MumbleverseServerUser
from . import urls

logger = logging.getLogger(__name__)


class MumbleverseService(ServicesHook):
    """Service for managing many Mumble servers with a Single Auth"""
    def __init_subclass__(cls, sid, server_name=None):
        super().__init_subclass__()
        cls.sid = sid
        cls.server_name = server_name

    def __init__(self):
        ServicesHook.__init__(self)
        if hasattr(self, "sid"):
            self.name = f'mmv:{self.server_name if self.server_name else self.sid}'
        else:
            self.name = f'mmv'
        self.access_perm = 'mumbleverse.basic_access'
        self.service_ctrl_template = 'mumbleverse/mumbleverse_service_ctrl.html'
        self.name_format = '[{corp_ticker}] {character_name}'

    def delete_user(self, user, notify_user=False):
        logging.debug(f"Deleting user {user} {self.name} account")
        # delete remotely

        # try:
        #     if user.mumble.delete():
        #         if notify_user:
        #             notify(user, 'Mumble Account Disabled', level='danger')
        #         return True
        #     return False
        # except MumbleverseServerUser.DoesNotExist:
        #     logging.debug("User does not have a mumble account")

    def update_groups(self, user):
        # logger.debug(f"Updating {self.name} groups for {user}")
        update_server_groups.delay(self.sid)

    def sync_nickname(self, user):
        # this requires a new password be provided or can i update it?
        pass

    def validate_user(self, user):
        if MumbleverseServerUser.user_has_account(self.sid, user.id) and not self.service_active_for_user(user):
            self.delete_user(user, notify_user=True)

    def update_all_groups(self):
        logger.debug("Updating all %s groups" % self.name)
        update_server_groups.delay(self.sid)

    def service_active_for_user(self, user):
        return user.has_perm(self.access_perm)

    def render_services_ctrl(self, request):
        username = ''
        service_url = ''
        connect_url = ''
        try:
            _u = MumbleverseServerUser.objects.get(
                server_id=self.sid,
                user=request.user
            )
            username = _u.username
            service_url = _u.server.mumble_url
            connect_url = urllib.parse.quote(username, safe="") + '@' + service_url if username else service_url
        except MumbleverseServerUser.DoesNotExist:
            pass
        return render_to_string(self.service_ctrl_template, {
            'service_name': self.server_name,
            'service_url': service_url,
            'connect_url': connect_url,
            'username': username,
            "sid": self.sid
        }, request=request)


def add_del_callback(*args, **kwargs):
    """
        This works great at startup of auth, however has a bug where changes
        made during operation are only captured on a single thread.
        TLDR restart auth after adding a new server
    """
    # Get a list of all guild ID's to check in our hook list
    server_add = list(
        MumbleverseServer.objects.all(
        ).values_list(
            "id",
            flat=True
        )
    )
    # Spit out the ID's for troubleshooting
    logger.info(f"Processing Servers {server_add}")

    # Loop all services and look for our specific hook classes
    for h in hooks._hooks.get("services_hook", []):
        if isinstance(h(), MumbleverseServer):
            # This is our hook
            # h is an instanced MultiDiscordService hook with a guild_id
            if h.sid in server_add:
                # this is a known discord ID so remove it from our list of knowns
                server_add.remove(h.guild_id)
            else:
                # This one was deleted remove the hook.
                del (h)

    # Loop to setup what is mising ( or everyhting on first boot )
    for sid in server_add:
        # What guild_id
        logger.info(f"Adding Server ID {sid}")
        server = MumbleverseServer.objects.get(id=sid)
        # This is the magic to instance the hook class with a new Class Name
        # this way there are no conflicts at runtime
        Server_class = type(
            f"MumbleverseService{sid}",  # New class name
            (MumbleverseService,), {},  # Super class
            sid=server.id,  # set the guild_id
            server_name=server.name  # and server name
        )
        # This adds the hook to the services_hook group to be loaded when needed.
        hooks.register("services_hook", Server_class)


post_save.connect(add_del_callback, sender=MumbleverseServer)
post_delete.connect(add_del_callback, sender=MumbleverseServer)


# @hooks.register('services_hook')
# def register_mumble_service():
#     return MumbleService()

@hooks.register("url_hook")
def register_urls():
    return UrlHook(urls, "mumbleverse", r"^mumbleverse/")
