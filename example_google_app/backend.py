import arrow
import httpx
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.backends import ModelBackend
from loguru import logger

# Conditional async imports - only available on Django 3.0+
try:
    from django import VERSION as DJANGO_VERSION
    if DJANGO_VERSION >= (3, 0):
        from asgiref.sync import iscoroutinefunction, sync_to_async
        from django.utils.decorators import sync_and_async_middleware
        try:
            from django.contrib.auth import alogout
        except ImportError:  # Django < 5.0
            alogout = sync_to_async(logout)
        _async_available = True
    else:
        iscoroutinefunction = None
        sync_to_async = None
        sync_and_async_middleware = None
        alogout = None
        _async_available = False
except ImportError:
    iscoroutinefunction = None
    sync_to_async = None
    sync_and_async_middleware = None
    alogout = None
    _async_available = False


class MyBackend(ModelBackend):
    """Simple test for custom authentication backend"""


def pre_login_callback(user, request):
    """Callback function called before user is logged in."""
    messages.info(request, f"Running Pre-Login callback for user: {user}.")

    # Example 1: Add SuperUser status to user
    if not user.is_superuser or not user.is_staff:
        logger.info(f"Adding SuperUser status to email: {user.email}")
        user.is_superuser = True
        user.is_staff = True

    # Example 2: Use Google Info as the unique source of truth
    token = request.session.get("google_sso_access_token")
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
        }
        url = "https://www.googleapis.com/oauth2/v3/userinfo"

        # Use response to update user info
        # Please add the custom scope in settings.GOOGLE_SSO_SCOPES
        # to access this info
        response = httpx.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            logger.debug(f"Updating User Data with Google Info: {user_data}")

            url = "https://people.googleapis.com/v1/people/me?personFields=birthdays"
            response = httpx.get(url, headers=headers, timeout=10)
            people_data = response.json()
            logger.debug(f"Updating User Data with Google People Info: {people_data}")

            user.first_name = user_data["given_name"]
            user.last_name = user_data["family_name"]

    user.save()


def is_user_valid(token):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    url = "https://www.googleapis.com/oauth2/v3/userinfo"
    response = httpx.get(url, headers=headers, timeout=10)

    # Add any check here

    return response.status_code == 200


def google_slo_middleware_example(get_response):
    """Middleware example with async support (Django 3.0+ only)."""
    if _async_available and sync_and_async_middleware and iscoroutinefunction:
        # Django 3.0+: Use async middleware decorator
        @sync_and_async_middleware
        def _middleware(get_response):
            if iscoroutinefunction(get_response):
                async def middleware(request):
                    token = await sync_to_async(request.session.get)("google_sso_access_token")
                    if token and not await sync_to_async(is_user_valid)(token):
                        await alogout(request)
                    response = await get_response(request)
                    return response
            else:
                def middleware(request):
                    token = request.session.get("google_sso_access_token")
                    if token and not is_user_valid(token):
                        logout(request)
                    response = get_response(request)
                    return response
            return middleware
        
        return _middleware(get_response)
    else:
        # Django < 3.0: Sync-only middleware
        def middleware(request):
            token = request.session.get("google_sso_access_token")
            if token and not is_user_valid(token):
                logout(request)
            response = get_response(request)
            return response
        return middleware


def pre_create_callback(google_info, request) -> dict:
    """Callback function called before user is created.

    return: dict content to be passed to User.objects.create() as `defaults` argument.
            If not informed, field `username` is always passed with user email as value.
    """

    user_key = google_info.get("email").split("@")[0]
    user_id = google_info.get("id")

    return {
        "username": f"{user_key}_{user_id}",
        "date_joined": arrow.utcnow().shift(days=-1).datetime,
    }


def pre_validate_callback(google_info, request) -> bool:
    """Callback function called before user is validated.

    Must return a boolean to indicate if user is valid to login.

    params:
        google_info: dict containing user info received from Google.
        request: HttpRequest object.
    """
    messages.info(
        request, f"Running Pre-Validate callback for email: {google_info.get('email')}."
    )
    return True
