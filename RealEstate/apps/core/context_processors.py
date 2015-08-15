from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm


def app_name(request):
    return {'app_name': settings.APP_NAME}


def async_login_form(request):
    context = {}
    if not request.user.is_authenticated():
        context['login_form'] = AuthenticationForm()
    return context


def navbar(request):
    navbar = {}
    user = request.user
    if user.is_authenticated():
        role = user.role_object
        if role and role.role_type == 'Homebuyer':
            navbar['categories'] = True
    return {'navbar': navbar}
