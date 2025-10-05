"""Admin models"""

# Django
from django.contrib import admin

from .models import MumbleverseServer, MumbleverseServerUser


# Register your models here.
@admin.register(MumbleverseServer)
class MumbleverseServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'mumble_url', 'api_url']
    filter_horizontal = [
        "faction_access",
        "alliance_access",
        "corporation_access",
        "character_access",
        "group_access",
        "state_access",
    ]


@admin.register(MumbleverseServerUser)
class MumbleverseServerUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'uid', 'server', 'user', 'last_update']
    raw_id_fields = ['server', 'user']
