import json
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import View

from RealEstate.apps.core.forms import (AddCategoryForm, EditCategoryForm,
                                        RealtorSignupForm, AddHomeForm,
                                        EditHomeForm, AddCategoryFromEvalForm)

from RealEstate.apps.core.models import (Category, CategoryWeight, Couple,
                                         Grade, Homebuyer, House, Realtor,
                                         User)

from RealEstate.apps.pending.models import PendingCouple, PendingHomebuyer
from RealEstate.apps.pending.forms import (InviteHomebuyerForm,
                                           InviteHomebuyersFormSet)

LOGIN_DELAY = 1.2   # Seconds


@sensitive_post_parameters()
@csrf_protect
@never_cache
def async_login_handler(request, *args, **kwargs):
    """
    Login requests are handled asynchronously from the modal login window.
    These should always be AJAX POST requests.  The login delay is a crude
    method to reduce login attempt spam.  If the login attempt is successful,
    the redirect location is returned (currently just the home page).
    """
    if not (request.is_ajax() and request.method == 'POST'):
        raise PermissionDenied

    time.sleep(LOGIN_DELAY)
    response = {'success': False}
    form = AuthenticationForm(data=request.POST)
    if form.is_valid():
        login(request, form.get_user())
        response = {
            'location': reverse(settings.LOGIN_REDIRECT_URL),
            'success': True,
        }
    return HttpResponse(json.dumps(response), content_type="application/json")


class RealtorSignupView(View):
    """
    This form is the landing page used to sign up realtors.
    """
    template_name = 'registration/signup.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Redirect to home page if already logged in.
        """
        if request.user.is_authenticated():
            return redirect(reverse(settings.LOGIN_REDIRECT_URL))
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
            login(request, user)
            user.send_email_confirmation(request)
            messages.success(request, "Welcome!")
            return redirect(reverse(settings.LOGIN_REDIRECT_URL))
        context = {
            'signup_form': signup_form
        }
        return render(request, self.template_name, context)


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
            id = request.GET['id']
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
        homebuyer = request.user.role_object
        couple = homebuyer.couple

        # ajax calls implement weight and delete category commands.
        if request.is_ajax():
            id = request.POST['id']
            category = Category.objects.get(id=id)

            # Weight a category
            if request.POST['type'] == 'update':
                weight = request.POST['value']
                CategoryWeight.objects.update_or_create(
                    homebuyer=homebuyer, category=category,
                    defaults={'weight': int(weight)})
                return HttpResponse(json.dumps({"id": id}),
                                    content_type="application/json")

            # Delete a category
            elif request.POST['type'] == 'delete':
                name = category.summary
                category.delete()
                return HttpResponse(json.dumps({"id": id, "name": name}),
                                    content_type="application/json")

        # Creates or updates a category
        else:
            summary = request.POST["summary"]
            description = request.POST["description"]

            # Updates a category
            if "id" in request.POST:
                id_category = get_object_or_404(
                    Category, id=request.POST['id'])
                summary_category = Category.objects.filter(
                    couple=couple, summary=summary).first()
                if (id_category and summary_category and
                        id_category.id != summary_category.id):
                    error = (u"Category '{summary}' already exists"
                             .format(summary=summary))
                    messages.error(request, error)
                else:
                    category = id_category
                    category.summary = summary
                    category.description = description
                    category.save()
                    messages.success(
                        request,
                        "Category '{summary}' updated".format(summary=summary))

            # Creates a category
            elif Category.objects.filter(
                    couple=couple, summary=summary).exists():
                error = (u"Category '{summary}' already exists"
                         .format(summary=summary))
                messages.error(request, error)
            else:
                Category.objects.create(couple=couple,
                                        summary=summary,
                                        description=description)
                messages.success(
                    request,
                    u"Category '{summary}' added".format(summary=summary))

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


class DashboardView(BaseView):
    """
    View for the home page, which should render different templates based
    on whether or not the the logged in User is a Realtor or Homebuyer.
    """
    homebuyer_template_name = 'core/homebuyer_dashboard.html'
    realtor_template_name = 'core/realtor_dashboard.html'

    def _build_invite_formset(self):
        return modelformset_factory(PendingHomebuyer,
                                    form=InviteHomebuyerForm,
                                    formset=InviteHomebuyersFormSet,
                                    extra=2,
                                    max_num=2)

    def _homebuyer_get(self, request, homebuyer, *args, **kwargs):
        # Returns summary and description if given category ID
        if request.is_ajax():
            id = request.GET['id']
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
        def _house_exists(couple, nickname):
            exists = House.objects.filter(
                couple=couple, nickname=nickname).exists()
            if exists:
                error = ("House with nickname '{nickname}' already exists"
                         .format(nickname=nickname))
                messages.error(request, error)
            return exists

        # Deletes a home
        if request.is_ajax():
            id = request.POST['id']
            home = House.objects.get(id=id)
            name = home.nickname
            home.delete()
            return HttpResponse(json.dumps({"id": id, "name": name}),
                                content_type="application/json")

        nickname = request.POST["nickname"]
        address = request.POST["address"]
        couple = homebuyer.couple

        # Updates a home
        if "id" in request.POST:
            id_home = get_object_or_404(House, id=request.POST["id"])
            nickname_home = House.objects.filter(
                couple=couple, nickname=nickname).first()
            if (id_home and nickname_home and
                    id_home.id != nickname_home.id):
                error = (u"House '{nickname}' already exists"
                         .format(nickname=nickname))
                messages.error(request, error)
            else:
                home = id_home
                home.nickname = nickname
                home.address = address
                home.save()
                messages.success(
                    request,
                    "House '{nickname}' updated".format(nickname=nickname))

        # Creates new home
        elif House.objects.filter(couple=couple, nickname=nickname).exists():
            error = (u"House '{nickname}' already exists"
                     .format(nickname=nickname))
            messages.error(request, error)
        else:
            House.objects.create(
                couple=couple, nickname=nickname, address=address)
            messages.success(
                request, "House '{nickname}' added".format(nickname=nickname))

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
        hasPending = pendingCouples.exists()
        for couple in couples:
            homebuyer = Homebuyer.objects.filter(couple=couple)
            coupleData.append((couple, homebuyer, not isPending))
        for pendingCouple in pendingCouples:
            pendingHomebuyer = PendingHomebuyer.objects.filter(
                pending_couple=pendingCouple)
            coupleData.append((pendingCouple, pendingHomebuyer, isPending))

        invite_formset = self._build_invite_formset()(
            queryset=PendingHomebuyer.objects.none())
        context = {
            'couples': coupleData,
            'realtor': realtor,
            'hasPending': hasPending,
            'invite_formset': invite_formset,
        }
        return render(request, self.realtor_template_name, context)

    def _realtor_post(self, request, realtor, *args, **kwargs):
        invite_formset = self._build_invite_formset()(request.POST)
        if invite_formset.is_valid():
            pending_homebuyers = [
                form.instance for form in invite_formset.forms]
            with transaction.atomic():
                pending_couple = PendingCouple.objects.create(
                    realtor=request.user.realtor)
                for pending_homebuyer in pending_homebuyers:
                    pending_homebuyer.pending_couple = pending_couple
                    pending_homebuyer.save()

            first_homebuyer, second_homebuyer = pending_homebuyers
            first_homebuyer.send_email_invite(request)
            second_homebuyer.send_email_invite(request)
            success_msg = ("Email invitations sent to '{first}' and '{second}'"
                           .format(first=escape(unicode(first_homebuyer)),
                                   second=escape(unicode(second_homebuyer))))
            messages.success(request, success_msg)
            return redirect(reverse(settings.LOGIN_REDIRECT_URL))

        couples = Couple.objects.filter(realtor=realtor)
        pendingCouples = PendingCouple.objects.filter(realtor=realtor)
        coupleData = []
        isPending = True
        hasPending = pendingCouples.exists()
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
            'hasPending': hasPending,
            'invite_formset': invite_formset,
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


class EmailConfirmationView(BaseView):
    """
    Used to confirm that a Realtor has signed up with a valid email address.
    """
    _USER_TYPES_ALLOWED = User._REALTOR_ONLY

    def get(self, request, *args, **kwargs):
        email_confirmation_token = kwargs.get('email_confirmation_token', None)
        user = request.user
        if (not user.email_confirmed and
                user.email_confirmation_token == email_confirmation_token):
            user.email_confirmed = True
            user.save()
            messages.success(
                request, u"Email confirmed ({email})".format(email=user.email))
        return redirect(reverse(settings.LOGIN_REDIRECT_URL))


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
            'min_weightchoice': min_choice,
            'max_weightchoice': max_choice,
            'default_weight': weight_field.default,
            'js_weight': json.dumps(weight_choices),
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
            'form': AddCategoryFromEvalForm()
        }
        context.update(self._weight_context())
        context.update(self._score_context())
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Depending on what functionality we want, the post may be more of a
        redirect back to the home page. In that case, much of this code will
        leave. In the meantime, it saves new data, recreates the same form and
        posts a success message.
        """
        homebuyer = request.user.role_object

        if request.is_ajax():
            house = get_object_or_404(House, id=kwargs["house_id"])
            id = request.POST['id']
            score = request.POST['value']
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

        else:
            summary = request.POST["summary"]
            description = request.POST["description"]
            couple = homebuyer.couple

            # Creates a category
            if Category.objects.filter(
                    couple=couple, summary=summary).exists():
                error = (u"Category '{summary}' already exists"
                         .format(summary=summary))
                messages.error(request, error)
            else:
                category = Category.objects.create(
                    couple=couple, summary=summary,
                    description=description)
                CategoryWeight.objects.update_or_create(
                    homebuyer=homebuyer, category=category,
                    defaults={'weight': int(request.POST["weight"])})

                messages.success(
                    request,
                    u"Category '{summary}' added".format(summary=summary))

            categories = Category.objects.filter(couple=couple)
            house = get_object_or_404(House, id=kwargs["house_id"])
            grades = Grade.objects.filter(house=house, homebuyer=homebuyer)
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
                'form': AddCategoryFromEvalForm()
            }
            context.update(self._weight_context())
            context.update(self._score_context())
            return render(request, self.template_name, context)


class PasswordChangeDoneView(BaseView):
    """
    This is needed to provide a message to the user that their password change
    was successful.
    """
    def get(self, request, *args, **kwargs):
        messages.success(request,
                         "You have successfully changed your password")
        return redirect(reverse(settings.LOGIN_REDIRECT_URL))


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
