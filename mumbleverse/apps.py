"""App Configuration"""
# Standard Library
import logging

# Django
from django.apps import AppConfig

# AA Mumbleverse
# AA Example App
from mumbleverse import __version__

logger = logging.getLogger(__name__)


class ExampleConfig(AppConfig):
    """App Config"""

    name = "mumbleverse"
    label = "mumbleverse"
    verbose_name = f"Mumbleverse v{__version__}"

    def ready(self):
        # run on startup to sync services!
        from .auth_hooks import add_del_callback  # NOPEP8
        try:
            add_del_callback()
        except Exception as e:
            logger.error("DMV: Failed to Init DMV Server Hook")
            logger.error(e, stack_info=True)

        from . import signals  # noqa: F401
