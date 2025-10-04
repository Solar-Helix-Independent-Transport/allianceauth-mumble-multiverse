# Standard Library
import logging
from functools import wraps

# Third Party
from httpx import ConnectError, delete, get, post

logger = logging.getLogger(__name__)


def api_error_wrapper(func):
    @wraps(func)
    def _api_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectError as error:
            logger.error("Failed to connect to mumble server api")
            logger.error(f"{error.request} - {error.args}")
            return False
    return _api_wrapper


@api_error_wrapper
def get_groups(server):
    out = get(
        server.api_url + "/api/auth/groups",
        params={
            "server_id": server.mumble_virtual_server_id,
        },
        headers={
            "key": server.api_key
        }
    )
    if out.status_code == 200:
        return out.json()
    else:
        # out.raise_for_status()
        return False


@api_error_wrapper
def set_groups(server):
    all_users = server.mumbleverseserveruser_set.all()
    output = {}
    for u in all_users:
        all_groups = u.user.groups.all()
        for g in all_groups:
            if g.name not in output:
                output[g.name] = {
                    "name": g.name,
                    "users": []
                }
            output[g.name]["users"].append(u.uid)
    out = post(
        server.api_url + "/api/auth/groups",
        params={
            "server_id": server.mumble_virtual_server_id,
        },
        headers={
            "key": server.api_key
        },
        json=list(output.values())

    )
    if out.status_code == 200:
        return out.json()
    else:
        # out.raise_for_status()
        return False


@api_error_wrapper
def register_user(server, username, password):
    out = post(
        server.api_url + "/api/auth/user",
        data={
            "user_name": username,
            "user_pass": password
        },
        params={
            "server_id": server.mumble_virtual_server_id,
        },
        headers={
            "key": server.api_key
        },
    )
    if out.status_code == 200:
        return out.json()
    else:
        # out.raise_for_status()
        return False


@api_error_wrapper
def deregister_user(server, user_id: int):
    out = delete(
        server.api_url + "/api/auth/users/delete",
        params={
            "server_id": server.mumble_virtual_server_id,
            "user_id": user_id,
        },
        headers={
            "key": server.api_key
        },
    )
    if out.status_code == 200:
        return out.json()
    else:
        # out.raise_for_status()
        return False


@api_error_wrapper
def kick_username(server, user_name, reason="Auth Revoked Access"):
    out = delete(
        server.api_url + "/api/auth/users/kick",
        params={
            "server_id": server.mumble_virtual_server_id,
            "user_name": user_name,
            "reason": reason,
        },
        headers={
            "key": server.api_key
        },
    )
    if out.status_code == 200:
        return out.json()
    return False
