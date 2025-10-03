"""App URLs"""

# Django
from django.urls import re_path

# AA Example App
from mumbleverse import views

app_name: str = "mumbleverse"

urlpatterns = [
    # Discord Service Control
    re_path(r'deactivate/(?P<server_id>(\d)*)',
            views.deactivate_mumbleverse, name='deactivate'),
    re_path(r'activate/(?P<server_id>(\d)*)',
            views.activate_mumbleverse, name='activate'),
    re_path(r'reset/(?P<server_id>(\d)*)',
            views.reset_mumbleverse, name='reset_password'),
    re_path(r'set/(?P<server_id>(\d)*)',
            views.set_mumbleverse, name='set_password'),
]
