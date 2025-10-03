"""
App Models
Create your models in here
"""

# Django
import random
import logging
from allianceauth.services.hooks import NameFormatter
from django.contrib.auth.models import Group
from passlib.hash import bcrypt_sha256
from typing import ClassVar
import string
from django.db import models
from django.contrib.auth.models import User
from mumbleverse.provider import deregister_user, kick_username, register_user


class General(models.Model):
    """Meta model for app permissions"""

    class Meta:
        """Meta definitions"""

        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access Mumbleverse servers"),
            ("global_access", "Can access all Mumbleverse servers")
        )


logger = logging.getLogger(__name__)


class MumbleverseManager(models.Manager):

    @staticmethod
    def get_display_name(user):
        from mumbleverse.auth_hooks import MumbleverseService
        return NameFormatter(MumbleverseService(), user).format_name()

    @staticmethod
    def get_username(user):
        return user.profile.main_character.character_name  # main character as the user.username may be incorect

    @staticmethod
    def sanitise_username(username):
        return username.replace(" ", "_")

    @staticmethod
    def generate_random_pass():
        return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(16)])

    @staticmethod
    def gen_pwhash(password):
        return bcrypt_sha256.encrypt(password.encode('utf-8'))

    def user_exists(self, username):
        return self.filter(username=username).exists()


class MumbleverseServer(models.Model):
    name = models.CharField(
        max_length=150
    )
    mumble_url = models.CharField(
        max_length=255
    )
    mumble_virtual_server_id = models.IntegerField(
        default=1
    )
    api_url = models.CharField(
        max_length=255
    )
    api_key = models.CharField(
        max_length=255
    )

    active = models.BooleanField(default=True)


class MumbleverseServerUser(models.Model):

    @classmethod
    def user_has_account(cls, server_id, user_id):
        cls.objects.filter(server_id=server_id, user_id=user_id).exists()

    server = models.ForeignKey(
        MumbleverseServer,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    uid = models.CharField(max_length=254, unique=True)
    username = models.CharField(max_length=254, unique=True)
    last_update = models.DateTimeField(
        auto_now=True
    )

    objects: ClassVar[MumbleverseManager] = MumbleverseManager()

    def __str__(self):
        return self.username

    def kick_user(self, reason):
        req = kick_username(self.server, self.username, reason)
        return req

    def update_password(self, password=None):
        init_password = password
        logger.info(f"Updating mumbleverse user {self.server_id} - {self.user_id}({self.uid}) password.")
        if not password:
            password = MumbleverseManager.generate_random_pass()
        if init_password is None:
            self.credentials = {'username': self.username, 'password': password}

    def reset_password(self):
        self.update_password()

    def deregister_user(self):
        return deregister_user(
            self.server,
            self.uid
        )

    def build_username(self):
        return MumbleverseManager.get_display_name(self.user)

    def update_username(self):
        self.username = self.build_username()
        self.save()

    def register_user(self, password: str):
        data = register_user(
            self.server,
            self.username,
            password
        )
        if data:
            self.uid = data["user_id"]
            self.save()
            return True
        return False

    class Meta:
        permissions = (
            ("access_mumbleverse", "Can access the Mumble service"),
            ("view_connection_history", "Can access the connection history of the Mumble service"),
        )
