"""
Compatibility utilities for supporting older Python and Django versions.
"""
import sys

try:
    from django import VERSION as DJANGO_VERSION
except ImportError:
    DJANGO_VERSION = (0, 0, 0)

try:
    from django.contrib.auth import get_user_model
except ImportError:
    get_user_model = None


def get_django_version():
    """Get Django version as a tuple."""
    return DJANGO_VERSION


def django_version_ge(major, minor=0, patch=0):
    """Check if Django version is greater than or equal to the specified version."""
    return DJANGO_VERSION >= (major, minor, patch)


def get_email_field_name(user_model):
    """
    Get the email field name for a user model.
    
    Compatible with Django 1.8+ (uses get_email_field_name() if available,
    otherwise falls back to checking EMAIL_FIELD attribute or defaults to 'email').
    
    Args:
        user_model: The user model class
        
    Returns:
        str: The name of the email field
    """
    # Django 3.1+ has get_email_field_name() method
    if django_version_ge(3, 1) and hasattr(user_model, 'get_email_field_name'):
        try:
            return user_model.get_email_field_name()
        except (AttributeError, TypeError):
            pass
    
    # Django 1.8-3.0: Check EMAIL_FIELD attribute (available in Django 1.8+)
    if hasattr(user_model, 'EMAIL_FIELD'):
        email_field = getattr(user_model, 'EMAIL_FIELD', None)
        if email_field:
            return email_field
    
    # Fallback: check if 'email' field exists in model fields
    if hasattr(user_model, '_meta'):
        try:
            # Try get_fields() first (Django 1.8+)
            fields = user_model._meta.get_fields()
            for field in fields:
                if hasattr(field, 'name') and field.name == 'email':
                    return 'email'
        except (AttributeError, TypeError):
            # Fallback to get_all_field_names() for very old Django versions
            try:
                if hasattr(user_model._meta, 'get_all_field_names'):
                    if 'email' in user_model._meta.get_all_field_names():
                        return 'email'
            except (AttributeError, TypeError):
                pass
    
    # Ultimate fallback
    return 'email'


def has_async_support():
    """
    Check if async support is available.
    
    Returns:
        bool: True if async support is available (Django 3.0+), False otherwise
    """
    return django_version_ge(3, 0)


def get_url_pattern_function():
    """
    Get the appropriate URL pattern function based on Django version.
    
    Returns:
        tuple: (path_function, is_legacy) where path_function is the function
               to use and is_legacy indicates if using legacy url() patterns
    """
    if django_version_ge(2, 0):
        try:
            from django.urls import path
            return path, False
        except ImportError:
            pass
    
    # Django 1.8-1.11: Use url() from django.conf.urls
    try:
        from django.conf.urls import url
        return url, True
    except ImportError:
        # Fallback: try django.urls.url (Django 1.11+)
        try:
            from django.urls import url
            return url, True
        except ImportError:
            raise ImportError("Could not import URL pattern function")


def is_python_36():
    """Check if running Python 3.6."""
    return sys.version_info[:2] == (3, 6)

