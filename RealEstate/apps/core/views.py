from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import View
from django import forms

from .models import Homebuyer, Couple, House, Category, Grade


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
                    self.fields[c.summary] = forms.CharField(initial="0" if None else s, widget=forms.HiddenInput())

        context = {'couple': couple, 'house' : house[0], 'grades': graded, "form" : ContactForm() }
        return render(request, 'core/houseEval.html', context)

    def post(self, request, *args, **kwargs):
        homebuyer = Homebuyer.objects.filter(user_id=request.user.id)
        couple = Couple.objects.filter(homebuyer__user=request.user)
        categories = Category.objects.filter(couple=couple)

        # A specific house should be passed into the request, changing next two lines.
        house = House.objects.filter(couple=couple)

        for category in categories:
            value = request.POST.get(category.summary)
            grade, created = Grade.objects.update_or_create(
                homebuyer=homebuyer[0], category=category, house=house[0], defaults={'score': int(value)})

        grades = Grade.objects.filter(house=house[0])

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
                    self.fields[c.summary] = forms.CharField(initial="0" if None else s, widget=forms.HiddenInput())
        
        context = {'couple': couple, 'house' : house[0], 'grades': graded, "form" : ContactForm() }
        return render(request, 'core/houseEval.html', context)
        