import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import View, FormView
from django.http import HttpResponse
from django.views.generic import UpdateView, ListView
from django.template.loader import render_to_string


from RealEstate.apps.core.models import (Category, Couple, Grade, House,
                                         Homebuyer, User)
from RealEstate.apps.core.forms import addHomeForm, editHomeForm


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
        # Returns summary and description if given category ID
        if request.is_ajax():
            id = request.GET['home']
            home = House.objects.get(id=id)
            response_data = {
                'nickname': home.nickname,
                'address': home.address
            }
            return HttpResponse(json.dumps(response_data),
                                content_type="application/json")
        
        couple = Couple.objects.filter(homebuyer__user=request.user)
        house = House.objects.filter(couple=couple)
        context =   {
                        'couple'  : couple,
                        'house'   : house,
                        'form'    : addHomeForm(),
                        'editForm': editHomeForm()
                    }
        return render(request, 'core/homebuyerHome.html', context)

    def post(self, request, *args, **kwargs):
        # Deletes a home
        if request.is_ajax():
            id = request.POST['home']
            home = House.objects.get(id=id)
            home.delete()
            return HttpResponse(json.dumps({"id" : id}),
                                content_type="application/json")
        
        # Updates a home
        if "homeId" in request.POST:
            nickname = request.POST["edit_nickname"]
            address = request.POST["edit_address"]
            home = get_object_or_404(House.objects.filter(id=request.POST["homeId"]))
            home.nickname = nickname
            home.address = address
            home.save()
        
        # Creates new home
        else:
            nickname = request.POST["nickname"]
            address = request.POST["address"]
            couple = Couple.objects.filter(homebuyer__user=request.user)
            home, created = House.objects.update_or_create(
                couple=couple.first(), nickname=nickname,
                defaults={'address': address})
        
        couple = Couple.objects.filter(homebuyer__user=request.user)
        house = House.objects.filter(couple=couple)
        context =   {
                        'couple'  : couple,
                        'house'   : house,
                        'form'    : addHomeForm(),
                        'editForm': editHomeForm()
                    }
        return render(request, 'core/homebuyerHome.html', context)


class EvalView(BaseView):
    """
    View for the Home Evaluation Page. Currently, this page is decoupled
    from the rest of the app and uses static elements in the database.
    """
    template_name = 'core/houseEval.html'

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

    def _score_context(self):
        score_field = Grade._meta.get_field('score')
        score_choices = dict(score_field.choices)
        min_score = min(score for score in score_choices)
        max_score = max(score for score in score_choices)
        min_choice = score_choices[min_score]
        max_choice = score_choices[max_score]
        return {
            'min_score': min_score,
            'max_score': max_score,
            'min_choice': min_choice,
            'max_choice': max_choice,
            'default_score': score_field.default,
            'js_scores': json.dumps(score_choices),
        }

    def get(self, request, *args, **kwargs):
        homebuyer = request.user.role_object
        couple = Couple.objects.filter(homebuyer__user=request.user)
        categories = Category.objects.filter(couple=couple)
        house = get_object_or_404(House.objects.filter(id=kwargs["house_id"]))
        grades = Grade.objects.filter(house=house, homebuyer=homebuyer)

        # Merging grades and categories to provide object with both
        # information. Data Structure: [(cat1, score1), (cat2, score2), ...]
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

        context = {
            'couple': couple,
            'house': house,
            'grades': graded,
        }
        context.update(self._score_context())
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Depending on what functionality we want, the post may be more of a
        redirect back to the home page. In that case, much of this code will
        leave. In the meantime, it saves new data, recreates the same form and
        posts a success message.
        """
        if not request.is_ajax():
            raise PermissionDenied

        homebuyer = Homebuyer.objects.filter(user_id=request.user.id)
        house = get_object_or_404(House.objects.filter(id=kwargs["house_id"]))
        id = request.POST['category']
        score = request.POST['score']
        category = Category.objects.get(id=id)
        grade, created = Grade.objects.update_or_create(
            homebuyer=homebuyer.first(), category=category, house=house,
            defaults={'score': int(score)})
        response_data = {
            'id': str(id),
            'score': str(score)
        }
        return HttpResponse(json.dumps(response_data),
                            content_type="application/json")


class ReportView(BaseView):
    """
    This view will take into account the category weights and scores for each
    Homebuyer that is part of the Couple instance, and display the results.
    """
    template_name = 'core/report.html'

    def _permission_check(self, request, role, *args, **kwargs):
        """
        Homebuyers can only see their own report.  Realtors can see reports
        for any of their Couples
        """
        couple_id = int(kwargs.get('couple_id', 0))
        get_object_or_404(Couple, id=couple_id)
        return role.can_view_report_for_couple(couple_id)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})
