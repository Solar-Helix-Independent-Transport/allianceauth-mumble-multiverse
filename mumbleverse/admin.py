"""Admin models"""

# Django
from django.contrib import admin  # noqa: F401
from .models import MumbleverseServer, MumbleverseServerUser
# Register your models here.
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

admin.site.register(MumbleverseServer, MumbleverseServerAdmin)
admin.site.register(MumbleverseServerUser)
