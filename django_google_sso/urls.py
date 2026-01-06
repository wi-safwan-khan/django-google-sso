from django_google_sso import conf, views
from django_google_sso.compat import get_url_pattern_function

app_name = "django_google_sso"

url_pattern_func, is_legacy = get_url_pattern_function()

urlpatterns = []

if conf.GOOGLE_SSO_ENABLED:
    if is_legacy:
        # Django 1.8-1.11: Use url() with regex patterns
        urlpatterns += [
            url_pattern_func(r"^login/$", views.start_login, name="oauth_start_login"),
            url_pattern_func(r"^callback/$", views.callback, name="oauth_callback"),
        ]
    else:
        # Django 2.0+: Use path()
        urlpatterns += [
            url_pattern_func("login/", views.start_login, name="oauth_start_login"),
            url_pattern_func("callback/", views.callback, name="oauth_callback"),
        ]
