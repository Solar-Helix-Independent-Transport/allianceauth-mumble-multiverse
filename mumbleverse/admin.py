"""Admin models"""

# Django
from django.contrib import admin  # noqa: F401
from .models import MumbleverseServer, MumbleverseServerUser
# Register your models here.
admin.site.register(MumbleverseServer)
admin.site.register(MumbleverseServerUser)
