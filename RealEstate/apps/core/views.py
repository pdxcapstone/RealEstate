from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import View
from django import forms
from django.contrib import messages


from RealEstate.apps.core.models import Category, Couple, Grade, House, Homebuyer, User


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

    def _permission_check(self, request, role, *args, **kwargs):
        """
        Override this in subclassed views if the view needs more granular
        permissions than the simple Homebuyer/Realtor check.
        """
        return True

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        role = request.user.role_object
        if role and role.role_type in self._USER_TYPES_ALLOWED:
            if self._permission_check(request, role, *args, **kwargs):
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


class EvalView(BaseView):
    """
    View for the Home Evaluation Page. Currently, this page is decoupled
    from the rest of the app and uses static elements in the database.
    """
    def _permission_check(self, request, role, *args, **kwargs):
        """
        For a given House instance, only allow the user to view the page if
        its for a related Homebuyer. This prevents users from grading other
        peoples houses.
        """
        if role.role_type == 'Homebuyer':
            house_id = kwargs.get('house_id', None)
            if role.couple.house_set.filter(id=house_id).exists():
                return True
        return False

    def get(self, request, *args, **kwargs):
        homebuyer = request.user.role_object
        couple = Couple.objects.filter(homebuyer__user=request.user)
        categories = Category.objects.filter(couple=couple)
        house = get_object_or_404(House.objects.filter(id=kwargs["house_id"]))
        grades = Grade.objects.filter(house=house, homebuyer=homebuyer)

        # Merging grades and categories to provide object with both information.
        # Data Structure: [(cat1, score1), (cat2, score2), ...]
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

        class ContactForm(forms.Form):
            def __init__(self, *args, **kwargs):
                super(ContactForm, self).__init__(*args, **kwargs)
                for c, s in graded:
                    self.fields[str(c.id)] = forms.CharField(initial="3" if None else s, widget=forms.HiddenInput())

        context = {'couple': couple, 'house' : house, 'grades': graded, "form" : ContactForm() }
        return render(request, 'core/houseEval.html', context)

    def post(self, request, *args, **kwargs):
        """
        Depending on what functionality we want, the post may be more of a redirect back to the home page. In that
        case, much of this code will leave. In the meantime, it saves new data, recreates the same form and posts a
        success message.
        """
        homebuyer = Homebuyer.objects.filter(user_id=request.user.id)
        couple = Couple.objects.filter(homebuyer__user=request.user)
        categories = Category.objects.filter(couple=couple)
        house = get_object_or_404(House.objects.filter(id=kwargs["house_id"]))

        for category in categories:
            value = request.POST.get(str(category.id))
            if not value:
              value = 3
            grade, created = Grade.objects.update_or_create(
                homebuyer=homebuyer.first(), category=category, house=house, defaults={'score': int(value)})

        grades = Grade.objects.filter(house=house, homebuyer=homebuyer)

        # Merging grades and categories to provide object with both information.
        # Data Structure: [(cat1, score1), (cat2, score2), ...]
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

        class ContactForm(forms.Form):
            def __init__(self, *args, **kwargs):
                super(ContactForm, self).__init__(*args, **kwargs)
                for c, s in graded:
                    self.fields[str(c.id)] = forms.CharField(initial="0" if None else s, widget=forms.HiddenInput())

        messages.success(request,"Your evaluation was saved!")

        context = {'couple': couple, 'house' : house, 'grades': graded, "form" : ContactForm() }
        return render(request, 'core/houseEval.html', context)
