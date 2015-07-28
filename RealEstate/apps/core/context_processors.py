from django.contrib.auth.forms import AuthenticationForm


def async_login_form(request):
    context = {}
    if not request.user.is_authenticated():
        context['login_form'] = AuthenticationForm()
    return context
