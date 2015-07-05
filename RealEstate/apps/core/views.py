from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import View

from .models import Couple, House, Category, Grade


def login(request, *args, **kwargs):
    """
    If the user is already logged in and they navigate to the login URL,
    just redirect them home. Otherwise just delegate to the default
    Django login view.
    """
    if request.user.is_authenticated():
        return redirect(reverse('home'))
    return auth_login(request, *args, **kwargs)


class BaseView(View):
    """
    All subclassed views will redirect to the login view if not logged in.
    """
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BaseView, self).dispatch(request, *args, **kwargs)


class HomeView(BaseView):
    """
    View for the home page, which should render different templates based
    on whether or not the the logged in User is a Realtor or Homebuyer.
    """
    def get(self, request, *args, **kwargs):
        couple = Couple.objects.filter(homebuyer__user=request.user)
        house = House.objects.filter(couple=couple)
        return render(request, 'core/homebuyerHome.html', {'couple': couple, 'house': house})


class EvalView(BaseView):
    """
    View for the Home Evaluation Page. Currently, this page is decoupled 
    from the rest of the app and uses static elements in the database.
    """
    def get(self, request, *args, **kwargs):
        couple = Couple.objects.filter(homebuyer__user=request.user)
        categories = Category.objects.filter(couple=couple)

        # A specific house should be passed into the request, changing next two lines.
        house = House.objects.filter(couple=couple) 
        grades = Grade.objects.filter(house=house[0])

        graded = []
        for category in categories:
            missing = True
            for grade in grades:
                if grade.category.id is category.id:
                    graded.append((category, grade.score))
                    missing = False
                    break
            if missing:
                graded.append((category, None))

        context = {'couple': couple, 'house' : house[0], 'grades': graded }
        return render(request, 'core/houseEval.html', context)
        