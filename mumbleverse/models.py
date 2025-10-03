"""
App Models
Create your models in here
"""

# Django
from django.db import models
from django.contrib.auth.models import User

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

import random
import string
from typing import ClassVar
from passlib.hash import bcrypt_sha256

from django.db import models
from django.contrib.auth.models import Group
from allianceauth.services.hooks import NameFormatter
import logging

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

    def update_password(self, password=None):
        init_password = password
        logger.info(f"Updating mumbleverse user {self.server_id} - {self.user_id}({self.uid}) password.")
        if not password:
            password = MumbleverseManager.generate_random_pass()
        # hit api and record success
        self.save()
        if init_password is None:
            self.credentials = {'username': self.username, 'password': password}

    def reset_password(self):
        self.update_password()

    def update_groups(self, groups: Group=None):
        if groups is None:
            groups = self.user.groups.all()
        groups_str = [self.user.profile.state.name]
        for group in groups:
            groups_str.append(str(group.name))
        safe_groups = ','.join({g.replace(' ', '-') for g in groups_str})
        logger.info(f"Updating mumble user {self.user} groups to {safe_groups}")
        self.groups = safe_groups
        self.save()
        return True

    def update_display_name(self):
        logger.info(f"Updating mumble user {self.user} display name")
        self.display_name = MumbleverseManager.get_display_name(self.user)
        self.save()
        return True

    class Meta:
        permissions = (
            ("access_mumbleverse", "Can access the Mumble service"),
            ("view_connection_history", "Can access the connection history of the Mumble service"),
        )
