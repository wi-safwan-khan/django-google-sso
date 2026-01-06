import asyncio
from typing import Any, Callable, Coroutine, Union

from django.contrib import messages
from loguru import logger

from django_google_sso import conf
from django_google_sso.compat import has_async_support
from django_google_sso.templatetags.show_form import define_show_form
from django_google_sso.templatetags.sso_tags import define_sso_providers

# Conditional async imports - only available on Django 3.0+
_async_available = has_async_support()
sync_to_async = None

if _async_available:
    try:
        from asgiref.sync import sync_to_async
    except ImportError:
        _async_available = False
        sync_to_async = None


def send_message(request, message, level: str = "error"):
    getattr(logger, level.lower())(message)
    enable_messages = conf.GOOGLE_SSO_ENABLE_MESSAGES
    if callable(enable_messages):
        enable_messages = enable_messages(request)
    if enable_messages:
        messages.add_message(request, getattr(messages, level.upper()), message)


def show_credential(credential):
    credential = str(credential)
    return f"{credential[:5]}...{credential[-5:]}"


def async_(
    func: Callable,
) -> Union[Callable[..., Any], Callable[[Any, Any], Coroutine[Any, Any, Any]]]:
    """Returns a coroutine function."""
    if not _async_available or sync_to_async is None:
        raise RuntimeError(
            "Async support is not available. Requires Django 3.0+ and asgiref."
        )
    return func if asyncio.iscoroutinefunction(func) else sync_to_async(func)


# Only define async functions if async support is available
if _async_available and sync_to_async is not None:
    async def adefine_sso_providers(request):
        context = {"request": request}
        return await async_(define_sso_providers)(context)

    async def adefine_show_form(request):
        context = {"request": request}
        return await async_(define_show_form)(context)
else:
    # Define no-op functions for older Django versions
    def adefine_sso_providers(request):
        raise RuntimeError(
            "Async support is not available. Requires Django 3.0+ and asgiref."
        )

    def adefine_show_form(request):
        raise RuntimeError(
            "Async support is not available. Requires Django 3.0+ and asgiref."
        )
