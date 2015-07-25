import json

from django.contrib.auth import authenticate, login as _login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as auth_login
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.http import HttpResponse

from RealEstate.apps.core.forms import (AddCategoryForm, EditCategoryForm,
                                        RealtorSignupForm, AddHomeForm,
                                        EditHomeForm)

from RealEstate.apps.core.models import (Category, CategoryWeight, Couple,
                                         Grade, Homebuyer, House, Realtor,
                                         User)

from RealEstate.apps.pending.models import PendingCouple, PendingHomebuyer
from RealEstate.apps.pending.forms import InviteHomebuyerForm


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
    homebuyer_template_name = 'core/homebuyerHome.html'
    realtor_template_name = 'core/realtorHome.html'

    def _invite_homebuyer(self, request, pending_couple, email):
        """
        Create the PendingHomebuyer instance and attach it to the
        PendingCouple.  Then send out the email invite and flash a message
        to the user that the invite has been sent.
        """
        homebuyer = PendingHomebuyer.objects.create(
            email=email,
            pending_couple=pending_couple)
        homebuyer.send_email_invite(request)

    def _homebuyer_get(self, request, homebuyer, *args, **kwargs):
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

        couple = homebuyer.couple
        house = House.objects.filter(couple=couple)
        context = {
            'couple': couple,
            'house': house,
            'form': AddHomeForm(),
            'editForm': EditHomeForm()
        }
        return render(request, self.homebuyer_template_name, context)

    def _homebuyer_post(self, request, homebuyer, *args, **kwargs):
        # Deletes a home
        if request.is_ajax():
            id = request.POST['home']
            home = House.objects.get(id=id)
            home.delete()
            return HttpResponse(json.dumps({"id": id}),
                                content_type="application/json")

        nickname = request.POST["nickname"]
        address = request.POST["address"]
        # Updates a home
        if "homeId" in request.POST:
            home = get_object_or_404(House.objects.filter
                                     (id=request.POST["homeId"]))
            home.nickname = nickname
            home.address = address
            home.save()

        # Creates new home
        else:
            couple = homebuyer.couple
            home, created = House.objects.update_or_create(
                couple=couple, nickname=nickname,
                defaults={'address': address})

        couple = homebuyer.couple
        house = House.objects.filter(couple=couple)
        context = {
            'couple': couple,
            'house': house,
            'form': AddHomeForm(),
            'editForm': EditHomeForm()
        }
        return render(request, self.homebuyer_template_name, context)

    def _realtor_get(self, request, realtor, *args, **kwargs):
        couples = Couple.objects.filter(realtor=realtor)
        pendingCouples = PendingCouple.objects.filter(realtor=realtor)
        # Couple data is a list of touples [(couple1, homebuyers, isPending),
        # (couple2, homebuyers, isPending)] There may be a better way to get
        # homebuyers straight from couples, but I didn't see it in the model.
        coupleData = []
        isPending = True
        hasPending = True if (len(pendingCouples) > 0) else False
        for couple in couples:
            homebuyer = Homebuyer.objects.filter(couple=couple)
            coupleData.append((couple, homebuyer, not isPending))
        for pendingCouple in pendingCouples:
            pendingHomebuyer = PendingHomebuyer.objects.filter(
                pending_couple=pendingCouple)
            coupleData.append((pendingCouple, pendingHomebuyer, isPending))
        context = {
            'couples': coupleData,
            'realtor': realtor,
            'form': InviteHomebuyerForm(),
            'hasPending': hasPending
        }
        return render(request, self.realtor_template_name, context)

    def _realtor_post(self, request, realtor, *args, **kwargs):
        couples = Couple.objects.filter(realtor=realtor)
        pendingCouples = PendingCouple.objects.filter(realtor=realtor)
        form = InviteHomebuyerForm(request.POST)
        if form.is_valid():
            first_email = form.cleaned_data.get('first_email')
            second_email = form.cleaned_data.get('second_email')
            with transaction.atomic():
                pending_couple = PendingCouple.objects.create(
                    realtor=request.user.realtor)
                self._invite_homebuyer(request, pending_couple, first_email)
                self._invite_homebuyer(request, pending_couple, second_email)

        coupleData = []
        isPending = True
        hasPending = True if (len(pendingCouples) > 0) else False
        for couple in couples:
            homebuyer = Homebuyer.objects.filter(couple=couple)
            coupleData.append((couple, homebuyer, not isPending))
        for pendingCouple in pendingCouples:
            pendingHomebuyer = PendingHomebuyer.objects.filter(
                pending_couple=pendingCouple)
            coupleData.append((pendingCouple, pendingHomebuyer, isPending))
        context = {
            'couples': coupleData,
            'realtor': realtor,
            'form': InviteHomebuyerForm(),
            'hasPending': hasPending
        }
        return render(request, self.realtor_template_name, context)

    def get(self, request, *args, **kwargs):
        role = request.user.role_object
        handlers = {
            'Homebuyer': self._homebuyer_get,
            'Realtor': self._realtor_get,
        }
        return handlers[role.role_type](request, role, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        role = request.user.role_object
        handlers = {
            'Homebuyer': self._homebuyer_post,
            'Realtor': self._realtor_post,
        }
        return handlers[role.role_type](request, role, *args, **kwargs)


class EvalView(BaseView):
    """
    View for the Home Evaluation Page. Currently, this page is decoupled
    from the rest of the app and uses static elements in the database.
    """
    _USER_TYPES_ALLOWED = User._HOMEBUYER_ONLY
    template_name = 'core/houseEval.html'

    def _permission_check(self, request, role, *args, **kwargs):
        """
        For a given House instance, only allow the user to view the page if
        its for a related Homebuyer. This prevents users from grading other
        peoples houses.
        """
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
        couple = homebuyer.couple
        categories = Category.objects.filter(couple=couple)
        house = get_object_or_404(House, id=kwargs["house_id"])
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

        homebuyer = request.user.role_object
        house = get_object_or_404(House, id=kwargs["house_id"])
        id = request.POST['category']
        score = request.POST['score']
        category = Category.objects.get(id=id)
        grade, created = Grade.objects.update_or_create(
            homebuyer=homebuyer, category=category, house=house,
            defaults={'score': int(score)})
        response_data = {
            'id': str(id),
            'score': str(score)
        }
        return HttpResponse(json.dumps(response_data),
                            content_type="application/json")


class RealtorSignupView(View):
    """
    This form is used to register realtors.
    """
    template_name = 'core/realtorSignup.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('home')
        return super(
            RealtorSignupView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        Renders the signup form for registering a realtor.
        """
        context = {
            'signup_form': RealtorSignupForm()
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Handles the creation of User/Realtor instances when signing up a new
        realtor. If the form is not valid, re-render it with errors
        so the user can correct them. If valid, create the User/Realtor.
        """
        signup_form = RealtorSignupForm(request.POST)
        if signup_form.is_valid():
            cleaned_data = signup_form.cleaned_data
            email = cleaned_data['email']
            password = cleaned_data['password']
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=cleaned_data['first_name'],
                    last_name=cleaned_data['last_name'],
                    phone=cleaned_data['phone'])
                Realtor.objects.create(user=user)
            user = authenticate(email=email, password=password)
            _login(request, user)
            return redirect('home')
        context = {
            'signup_form': signup_form
        }
        return render(request, self.template_name, context)


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


class CategoryView(BaseView):
    """
    View for the Category Ranking Page.
    """
    _USER_TYPES_ALLOWED = User._HOMEBUYER_ONLY
    template_name = 'core/categories.html'

    def _permission_check(self, request, role, *args, **kwargs):
        return True

    def _weight_context(self):
        weight_field = CategoryWeight._meta.get_field('weight')
        weight_choices = dict(weight_field.choices)
        min_weight = min(weight for weight in weight_choices)
        max_weight = max(weight for weight in weight_choices)
        min_choice = weight_choices[min_weight]
        max_choice = weight_choices[max_weight]
        return {
            'min_weight': min_weight,
            'max_weight': max_weight,
            'min_choice': min_choice,
            'max_choice': max_choice,
            'default_weight': weight_field.default,
            'js_weight': json.dumps(weight_choices),
        }

    def get(self, request, *args, **kwargs):
        # Returns summary and description if given category ID
        if request.is_ajax():
            id = request.GET['category']
            category = Category.objects.get(id=id)
            response_data = {
                'summary': category.summary,
                'description': category.description
            }
            return HttpResponse(json.dumps(response_data),
                                content_type="application/json")

        # Renders standard category page
        homebuyer = request.user.role_object
        couple = homebuyer.couple
        categories = Category.objects.filter(couple=couple)
        weights = CategoryWeight.objects.filter(homebuyer=homebuyer)

        weighted = []
        for category in categories:
            missing = True
            for weight in weights:
                if weight.category.id is category.id:
                    weighted.append((category, weight.weight))
                    missing = False
                    break
            if missing:
                weighted.append((category, None))

        context = {
            'weights': weighted,
            'form': AddCategoryForm(),
            'editForm': EditCategoryForm()
        }
        context.update(self._weight_context())
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Depending on what functionality we want, the post may be more of a
        redirect back to the home page. In that case, much of this code will
        leave. In the meantime, it saves new data, recreates the same form and
        posts a success message.
        """
        # ajax calls implement weight and delete category commands.
        if request.is_ajax():
            id = request.POST['category']
            category = Category.objects.get(id=id)

            # Weight a category
            if request.POST['type'] == 'update':
                homebuyer = request.user.role_object
                weight = request.POST['weight']
                grade, created = CategoryWeight.objects.update_or_create(
                    homebuyer=homebuyer, category=category,
                    defaults={'weight': int(weight)})
                return HttpResponse(json.dumps({"id": id}),
                                    content_type="application/json")

            # Delete a category
            elif request.POST['type'] == 'delete':
                category.delete()
                return HttpResponse(json.dumps({"id": id}),
                                    content_type="application/json")

        # Creates or updates a category
        else:
            homebuyer = request.user.role_object
            couple = homebuyer.couple
            summary = request.POST["summary"]
            description = request.POST["description"]

            # Updates a category
            if "catID" in request.POST:
                category = get_object_or_404(Category,
                                             id=request.POST['catID'])
                category.summary = summary
                category.description = description
                category.save()

            # Creates a category
            else:
                grade, created = Category.objects.update_or_create(
                    couple=couple, summary=summary,
                    defaults={'description': str(description)})

            weights = CategoryWeight.objects.filter(homebuyer=homebuyer)
            categories = Category.objects.filter(couple=couple)

            weighted = []
            for category in categories:
                missing = True
                for weight in weights:
                    if weight.category.id is category.id:
                        weighted.append((category, weight.weight))
                        missing = False
                        break
                if missing:
                    weighted.append((category, None))

            context = {
                'weights': weighted,
                'form': AddCategoryForm(),
                'editForm': EditCategoryForm()
            }
            context.update(self._weight_context())
            return render(request, self.template_name, context)
