import json
import time
import math

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
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
                                        EditHomeForm, AddCategoryFromEvalForm,
                                        AddRealtorHomeForm)


from RealEstate.apps.core.models import (Category, CategoryWeight, Couple,
                                         Grade, House, Realtor, User)
from RealEstate.apps.core import models

from RealEstate.apps.pending.models import PendingCouple, PendingHomebuyer
from RealEstate.apps.pending.forms import InviteHomebuyerForm

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
            user = User(id=0)
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=cleaned_data['first_name'],
                    last_name=cleaned_data['last_name'],
                    phone=cleaned_data['phone'])
                Realtor.objects.create(user=user)
            email_sent = user.send_email_confirmation(request)
            if not email_sent:
                user.delete()
                messages.error(request, "Failed to send email confirmation")
                return redirect(reverse(settings.LOGIN_URL))
            user = authenticate(email=email, password=password)
            login(request, user)
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
        choices = []
        for key, value in models._CATEGORIES.items():
            choices.append((key, value["summary"]))

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
            if request.POST['type'] == 'category':
                categories = Category.objects.filter(couple=couple)
                return HttpResponse(
                    json.dumps({'category':
                               [category.summary.encode('UTF-8').lower()
                                for category in categories]}),
                    content_type="application/json")

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
            else:
                optNum = len(request.POST.getlist("optional_categories"))
                if optNum > 0:
                    for c in request.POST.getlist("optional_categories"):
                        if Category.objects.filter(
                                couple=couple, summary=summary).exists():
                            continue
                        else:
                            optSum=models._CATEGORIES[c]["summary"]
                            Category.objects.create(
                                couple=couple,
                                summary=optSum,
                                description=models._CATEGORIES[c]["description"])
                            if optNum == 1:
                                messages.success(
                                    request,
                                    u"Category '{summary}' added".format(
                                        summary=optSum))
                    if optNum > 1:
                        messages.success(
                            request,
                            u"{optNum} predefined categories added.".format(
                                optNum=optNum))

                if summary != "":
                    if Category.objects.filter(
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
                            u"Category '{summary}' added".format(
                                summary=summary))

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

    def _homebuyer_get(self, request, homebuyer, *args, **kwargs):
        # Returns summary and description if given category ID
        if request.is_ajax():
            id = request.GET['id']
            house = House.objects.get(id=id)
            response_data = {
                'nickname': house.nickname,
                'address': house.address
            }
            return HttpResponse(json.dumps(response_data),
                                content_type="application/json")

        couple = homebuyer.couple
        houses = couple.house_set.all()
        context = {
            'couple': couple,
            'homebuyer': homebuyer,
            'houses': houses,
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
            house = House.objects.get(id=id)
            name = house.nickname
            house.delete()
            return HttpResponse(json.dumps({"id": id, "name": name}),
                                content_type="application/json")

        nickname = request.POST["nickname"]
        address = request.POST["address"]
        couple = homebuyer.couple

        # Updates a home
        if "id" in request.POST:
            id_house = get_object_or_404(House, id=request.POST["id"])
            nickname_house = House.objects.filter(
                couple=couple, nickname=nickname).first()
            if (id_house and nickname_house and
                    id_house.id != nickname_house.id):
                error = (u"House '{nickname}' already exists"
                         .format(nickname=nickname))
                messages.error(request, error)
            else:
                house = id_house
                house.nickname = nickname
                house.address = address
                house.save()
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

        houses = couple.house_set.all()
        context = {
            'couple': couple,
            'houses': houses,
            'homebuyer': homebuyer,
            'form': AddHomeForm(),
            'editForm': EditHomeForm()
        }
        return render(request, self.homebuyer_template_name, context)

    def _realtor_get(self, request, realtor, *args, **kwargs):
        couples, pending_couples = realtor.get_couples_and_pending_couples()
        invite_form = InviteHomebuyerForm()
        context = {
            'form': AddRealtorHomeForm(),
            'couples': couples,
            'pending_couples': pending_couples,
            'invite_form': invite_form,
            'realtor': realtor,
        }
        return render(request, self.realtor_template_name, context)

    def _realtor_post(self, request, realtor, *args, **kwargs):
        invite_form = InviteHomebuyerForm()

        if "id" in request.POST:
            couple = Couple.objects.get(id=int(request.POST["id"]))
            nickname = request.POST['nickname']
            if House.objects.filter(
                    couple=couple, nickname=nickname).exists():
                error = (u"House '{nickname}' already exists"
                         .format(nickname=nickname))
                messages.error(request, error)
            else:
                House.objects.create(couple=couple, nickname=nickname,
                                     address=request.POST["address"])
                messages.success(
                    request,
                    "House '{nickname}' added".format(nickname=nickname))
        else:
            invite_form = InviteHomebuyerForm(request.POST)
            if invite_form.is_valid():
                cleaned_data = invite_form.cleaned_data
                first_pending_hb = PendingHomebuyer(
                    first_name=cleaned_data['homebuyer1_first'],
                    last_name=cleaned_data['homebuyer1_last'],
                    email=cleaned_data['homebuyer1_email'])
                second_pending_hb = PendingHomebuyer(
                    first_name=cleaned_data['homebuyer2_first'],
                    last_name=cleaned_data['homebuyer2_last'],
                    email=cleaned_data['homebuyer2_email'])
                pending_couple = PendingCouple(realtor=request.user.realtor)

                email_success = all([
                    first_pending_hb.send_email_invite(request),
                    second_pending_hb.send_email_invite(request)
                ])
                if not email_success:
                    messages.error(request, "Failed to send email invitations")
                    return redirect(reverse(settings.LOGIN_REDIRECT_URL))

                with transaction.atomic():
                    pending_couple.save()
                    first_pending_hb.pending_couple = pending_couple
                    second_pending_hb.pending_couple = pending_couple
                    first_pending_hb.save()
                    second_pending_hb.save()

                success_msg = (
                    "Email invitations sent to '{first}' and '{second}'"
                    .format(first=escape(unicode(first_pending_hb)),
                            second=escape(unicode(second_pending_hb))))
                messages.success(request, success_msg)
                return redirect(reverse(settings.LOGIN_REDIRECT_URL))

        couples, pending_couples = realtor.get_couples_and_pending_couples()
        context = {
            'couples': couples,
            'pending_couples': pending_couples,
            'form': AddRealtorHomeForm(),
            'invite_form': invite_form,
            'realtor': realtor,
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
    incomplete_template_name = 'core/incomplete_report.html'

    def _permission_check(self, request, role, *args, **kwargs):
        """
        Homebuyers can only see their own report.  Realtors can see reports
        for any of their Couples
        """
        couple_id = int(kwargs.get('couple_id', 0))
        get_object_or_404(Couple, id=couple_id)
        return role.can_view_report_for_couple(couple_id)

    def get(self, request, *args, **kwargs):
        couple_id = int(kwargs.get('couple_id', 0))
        couple = Couple.objects.get(id=couple_id)
        registered = couple.registered
        categories = couple.category_set.all()
        houses = couple.house_set.all()
        if not all([registered, categories.exists(), houses.exists()]):
            context = {
                'categories': categories,
                'houses': houses,
                'registered': registered,
            }
            return render(request, self.incomplete_template_name, context)

        homebuyers = couple.homebuyer_set.all()
        first = 0
        second = 1
        largestScore = 0.01
        data1 = homebuyers[first].report_data
        data2 = homebuyers[second].report_data
        data3 = homebuyers[first].home_report_data
        data4 = homebuyers[second].home_report_data
        colors = ["#286090", "#9BCE7D", "#639BF1", "#3D3C3A", "#98002F", "#B6A754", "#0193B7",
                  "#5F6024", "#856941", "#ED6639", "#AB3334", "#0FB493", "#262C3A", "#57102C"]

        categoryImportance = []
        for category in data1:
            weight1 = float(data1[category]["weight"]) / homebuyers[first].category_weight_total
            weight2 = float(data2[category]["weight"]) / homebuyers[second].category_weight_total
            categoryImportance.append((category, weight1, weight2))

        weightsAve = []
        weights1 = []
        weights2 = []
        index1 = 0
        index2 = 0
        for category in data1:
            weightAve = (float(data1[category]["weight"]) + float(data2[category]["weight"])) / (homebuyers[first].category_weight_total + homebuyers[second].category_weight_total)
            weight1 = float(data1[category]["weight"]) / homebuyers[first].category_weight_total
            weight2 = float(data2[category]["weight"]) / homebuyers[second].category_weight_total
            weightsAve.append((colors[index1], category, int(weightAve * 100)))
            weights1.append((colors[index1], category, int(weight1 * 100)))
            index1 = (index1 + 1) % len(colors)
            weights2.append((colors[index2], category, int(weight2 * 100)))
            index2 = (index2 + 1) % len(colors)

        categoryData = []
        for category in data1:
            weight1 = float(data1[category]["weight"]) / homebuyers[first].category_weight_total
            weight2 = float(data1[category]["weight"]) / homebuyers[second].category_weight_total
            scores = []
            for house in data1[category]["houses"]:
                score1 = round((data1[category]["houses"][house] * weight1), 2)
                score2 = round((data2[category]["houses"][house] * weight2), 2)
                averageScore = round(((score1 + score2) / 2), 2)
                scores.append((house, averageScore, colors[index1]))
                index1 = (index1 + 1) % len(colors)

            for houses, score, color in scores:
                if score > largestScore:
                    largestScore = score

            categoryData.append((category, scores))

        index3 = 0
        index4 = 0
        weights3 = []
        weights4 = []
        for houses in data3:
            weight3 = float(data3[houses]["weight"]) / homebuyers[first].category_weight_total
            weight4 = float(data4[houses]["weight"]) / homebuyers[second].category_weight_total
            weights3.append((colors[index3], category, int(weight3 * 100)))
            index3 = (index3 + 1) % len(colors)
            weights4.append((colors[index4], category, int(weight4 * 100)))
            index4 = (index4 + 1) % len(colors)

        houseData = []
        for houses in data3:
            weight3 = float(data3[houses]["weight"]) / homebuyers[first].category_weight_total
            weight4 = float(data4[houses]["weight"]) / homebuyers[second].category_weight_total
            scores = []
            for category in data3[houses]["categories"]:
                score3 = round((data3[houses]["categories"][category] * weight3), 2)
                score4 = round((data4[houses]["categories"][category] * weight4), 2)
                averageScore = round(((score3 + score4) / 2), 2)
                scores.append((category, averageScore, colors[index3]))
                index3 = (index3 + 1) % len(colors)

            houseData.append((houses, scores))

        minVal = 5.0
        maxVal = 0.0
        totalScore = {}
        for category, homes in categoryData:
            for home, score, color in homes:
                if(home in totalScore.keys()):
                    totalScore[home] += score
                else:
                    totalScore[home] = score

        for home in totalScore:
            if minVal > totalScore[home]:
                minVal = totalScore[home]
            if maxVal < totalScore[home]:
                maxVal = totalScore[home]


        minVal = minVal - 1
        maxVal = maxVal + 0.5

        if minVal < 0:
            minVal = 0.0

        if maxVal > 5:
            maxVal = 5.0

        houseNum = (int(math.ceil(0.7* len(data1.values()[0].values()[0])))
            if data1 is not None else 0)
        houseWidth = (len(data1.values()[0].values()[0]) * 65 if data1 is
            not None else 0 )

        context = {
            'homebuyer1': homebuyers[0],
            'homebuyer2': homebuyers[1],
            'categoryImportance': categoryImportance,
            'pieAve': weightsAve,
            'categoryData': categoryData,
            'houseData': houseData,
            'totalScore': totalScore,
            'largestScore': largestScore,
            'categoryNum': int(math.ceil(0.7*len(data1))),
            'categoryWidth': len(data1) * 65,
            'houseNum': houseNum,
            'houseWidth': houseWidth,
            'minVal': minVal,
            'maxVal': maxVal
        }
        return render(request, self.template_name, context)
