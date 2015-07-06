from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import View

from RealEstate.apps.core.models import Couple, House, User


def login(request, *args, **kwargs):
    """
    If the user is already logged in and they navigate to the login URL,
    just redirect them home. Otherwise just delegate to the default
    Django login view.
    """
    if request.user.is_authenticated():
        return redirect('home')
    return auth_login(request, *args, **kwargs)


class BaseView(View):
    """
    All subclassed views will redirect to the login view if not logged in.
    By default, both Homebuyers and Realtors are allowed to see all views.
    However this can be overridden by subclassed views to make them
    Homebuyer or Realtor only.
    """
    _USER_TYPES_ALLOWED = User._ALL_TYPES_ALLOWED

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        role = request.user.role_object
        if role and role.role_type in self._USER_TYPES_ALLOWED:
            return super(BaseView, self).dispatch(request, *args, **kwargs)
        raise PermissionDenied


class HomeView(BaseView):
    """
    View for the home page, which should render different templates based
    on whether or not the the logged in User is a Realtor or Homebuyer.
    """
    def get(self, request, *args, **kwargs):
        couple = Couple.objects.filter(homebuyer__user=request.user)
        house = House.objects.filter(couple=couple)
        return render(request, 'core/homebuyerHome.html', {'couple': couple, 'house': house})
