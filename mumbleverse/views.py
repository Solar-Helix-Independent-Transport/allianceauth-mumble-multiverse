import logging

from allianceauth.services.forms import ServicePasswordForm
from allianceauth.services.abstract import BaseCreatePasswordServiceAccountView, BaseDeactivateServiceAccountView, \
    BaseResetPasswordServiceAccountView, BaseSetPasswordServiceAccountView
from django.http import Http404
from django.contrib.auth.decorators import (
    login_required, permission_required, user_passes_test,
)
from django.contrib import messages

from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from allianceauth.services.views import superuser_test

from .models import MumbleverseManager, MumbleverseServer, MumbleverseServerUser

from .provider import deregister_user, get_groups, register_user, kick_username
from .tasks import update_server_groups
logger = logging.getLogger(__name__)


@login_required
def deactivate_mumbleverse(request, server_id):
    logger.debug("deactivate_mumbleverse called by user %s", request.user)
    try:
        _u = MumbleverseServerUser.objects.get(
            server_id=server_id,
            user=request.user
        )
        req = _u.kick_user("Deactivated by Auth")
        if not req:
            messages.warning(request, _('Unable to kick member from mumbleverse server.'))
        req = _u.deregister_user()
        if req:
            _u.delete()
            messages.success(request, _('Deactivated Mumbleverse Account.'))
        else:
            messages.error(
            request, _(
                'An error occurred while deactivating Mumbleverse Account.'
            )
        )
    except MumbleverseServerUser.DoesNotExist:
        messages.error(
            request, _(
                'An error occurred while deactivating Mumbleverse Account.'
            )
        )
    return redirect("services:services")


@login_required
def reset_mumbleverse(request, server_id):
    try:
        _u = MumbleverseServerUser.objects.get(
            server_id=server_id,
            user=request.user
        )
        _u.deregister_user()
        _u.update_username()
        _u.reset_password()
        data = _u.register_user(_u.credentials["password"])
        if data:
            update_server_groups.delay(server_id)
            return render(
                request,
                'services/service_credentials.html',
                context={
                    'credentials': _u.credentials,
                    'service': _u.server.name,
                }
            )
        else: 
            messages.error(
                request, _(
                    'An error occurred while processing your Mumbleverse Account.'
                )
            )
            return redirect("services:services")

    except MumbleverseServerUser.DoesNotExist:
        messages.error(
            request, _(
                'An error occurred while processing your Mumbleverse Account.'
            )
        )
    return redirect("services:services")


@login_required
def set_mumbleverse(request, server_id):
    try:
        if request.method == "POST":
            _password = request.POST.get("password")
            if not _password:
                messages.error(
                    request, _(
                        'An error occurred while processing your Mumbleverse Account.'
                    )
                )
                return redirect("services:services")

            # update user by first deleting the user.
            _u = MumbleverseServerUser.objects.get(
                server_id=server_id,
                user=request.user
            )
            _u.deregister_user()
            _u.update_username()
            updated = _u.register_user(_password)
            if updated:
                update_server_groups.delay(server_id)
                messages.success(
                    request, _(
                        'Set password for Mumbleverse Account.'
                    )
                )
                return redirect("services:services")
            else: 
                messages.error(
                    request, _(
                        'An error occurred while processing your Mumbleverse Account.'
                    )
                )
                return redirect("services:services")
        else:
            form = ServicePasswordForm()
            return render(
                request,
                'services/service_password.html',
                context={
                    "form": form
                }
            )
    except MumbleverseServerUser.DoesNotExist:
        messages.error(
            request, _(
                'An error occurred while processing your Mumbleverse Account.'
            )
        )
    return redirect("services:services")


@login_required
def activate_mumbleverse(request, server_id):
    try:
        _s = MumbleverseServer.objects.get(id=server_id)
        _u = MumbleverseServerUser.objects.create(
            server=_s,
            user=request.user,
            uid=1,
            username="_temp"
        )
        _u.update_username()
        _u.reset_password()
        req = _u.register_user(_u.credentials["password"])
        if not req:
            _u.delete()
            messages.error(
                request, _(
                    'An error occurred while processing your Mumbleverse account.'
                )
            )
            return redirect("services:services")
        update_server_groups.delay(server_id)
        return render(
            request,
            'services/service_credentials.html',
            context={
                'credentials': _u.credentials,
                'service': _u.server.name,
            }
        )
    except MumbleverseServerUser.DoesNotExist:
        messages.error(
            request, _(
                'An error occurred while processing your Mumbleverse account.'
            )
        )
    return redirect("services:services")
