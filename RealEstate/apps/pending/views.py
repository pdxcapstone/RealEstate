from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.forms.models import modelformset_factory
from django.shortcuts import redirect, render
from django.utils.html import escape
from django.views.generic import View

from RealEstate.apps.core.models import Couple, Homebuyer, User
from RealEstate.apps.core.views import BaseView
from RealEstate.apps.pending.forms import (HomebuyerSignupForm,
                                           InviteHomebuyerForm,
                                           InviteHomebuyersFormSet)
from RealEstate.apps.pending.models import PendingCouple, PendingHomebuyer


class InviteHomebuyerView(BaseView):
    """
    This view supplies a form for sending out email invites to Homebuyers.
    This is temporarily a separate view but we will probably want to integrate
    this into the Realtor home page.
    """
    _USER_TYPES_ALLOWED = User._REALTOR_ONLY
    template_name = 'pending/inviteHomebuyer.html'

    def _build_formset(self):
        return modelformset_factory(PendingHomebuyer,
                                    form=InviteHomebuyerForm,
                                    formset=InviteHomebuyersFormSet,
                                    extra=2,
                                    max_num=2)

    def get(self, request, *args, **kwargs):
        formset = self._build_formset()
        context = {'formset': formset}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Populate the form with the submitted data.  If invalid, re-render it
        with the errors displayed.  Otherwise the form is valid; create the
        PendingHomebuyer instances and send out the email invites.
        """
        formset = self._build_formset()(request.POST)
        if formset.is_valid():
            pending_homebuyers = [form.instance for form in formset.forms]
            with transaction.atomic():
                pending_couple = PendingCouple.objects.create(
                    realtor=request.user.realtor)
                for pending_homebuyer in pending_homebuyers:
                    pending_homebuyer.pending_couple = pending_couple
                    pending_homebuyer.save()

            for pending_homebuyer in pending_homebuyers:
                pending_homebuyer.send_email_invite(request)
                message = escape(
                    "Email invite sent to {homebuyer}".format(
                        homebuyer=unicode(pending_homebuyer)))
                print message
                messages.success(request, message)
            return redirect('invite')

        context = {'formset': formset}
        return render(request, self.template_name, context)


class HomebuyerSignupView(View):
    """
    This form is used to register homebuyers that have been invited to
    the app by a Realtor.
    """
    template_name = 'pending/homebuyerSignup.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Manages registration of Homebuyers who have been invited.
        For all request methods:
            - If the user is already logged in, redirect home.
            - If the registration token does not correspond to a valid token,
              redirect to the login page with an error.
            - If the registration token corresponds to an already registered
              user, display an info message and redirect to login.
            - Otherwise perform the get or post.
        """
        if request.user.is_authenticated():
            return redirect('home')

        token = kwargs.get('registration_token')
        pending_homebuyer_filter = PendingHomebuyer.objects.filter(
            registration_token=token)
        if not pending_homebuyer_filter.exists():
            messages.error(request, "Invalid Registration Link.")
            return redirect('auth_login')

        pending_homebuyer = pending_homebuyer_filter.first()
        if pending_homebuyer.registered:
            messages.info(request, ("{email} is already registered."
                                    .format(email=pending_homebuyer.email)))
            return redirect('auth_login')
        return super(
            HomebuyerSignupView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        Renders the signup form for registering a homebuyer.
        """
        token = kwargs.get('registration_token')
        pending_homebuyer = PendingHomebuyer.objects.get(
            registration_token=token)
        realtor = pending_homebuyer.pending_couple.realtor
        context = {
            'registration_token': token,
            'signup_form': HomebuyerSignupForm(initial={
                'email': pending_homebuyer.email,
                'first_name': pending_homebuyer.first_name,
                'last_name': pending_homebuyer.last_name,
            }),
        }

        msg = ("Welcome, {name}.<br>You have been invited by {realtor_name} "
               "({realtor_email}).<br>Please fill out the form below to "
               "register for the Real Estate App.".format(
                   name=pending_homebuyer.first_name,
                   realtor_name=realtor.full_name,
                   realtor_email=realtor.email))
        messages.info(request, msg)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Handles the creation of User/Homebuyer/Couple instances when signing
        up a new homebuyer. If the form is not valid, re-render it with errors
        so the user can correct them. Otherwise:
          - Create the User object from the form data.
          - Check to see if there is an existing Couple instance (which
             happens if there partner already registered). If there is,
             create the Homebuyer instance and connect with the existing
             Couple instance.  Otherwise create a brand new instance.
          - Check to see if everyone in the PendingCouple instance has been
            registered.  If so, the PendingCouple/PendingHomebuyer instances
            have been translated into real users and can be deleted.
          - Authenticate/login the newly registered user and direct them to
            the home page.
        """
        token = kwargs.get('registration_token')
        pending_homebuyer = PendingHomebuyer.objects.get(
            registration_token=token)
        realtor = pending_homebuyer.pending_couple.realtor
        form = HomebuyerSignupForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            with transaction.atomic():
                email = pending_homebuyer.email
                password = cleaned_data['password']
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=cleaned_data['first_name'],
                    last_name=cleaned_data['last_name'],
                    phone=cleaned_data['phone'])
                pending_couple = pending_homebuyer.pending_couple
                couple = pending_couple.couple
                if not couple:
                    couple = Couple.objects.create(realtor=realtor)
                Homebuyer.objects.create(user=user, couple=couple)
                if pending_couple.registered:
                    pending_couple.pendinghomebuyer_set.all().delete()
                    pending_couple.delete()
            user = authenticate(email=email, password=password)
            login(request, user)
            return redirect('home')

        context = {
            'registration_token': token,
            'signup_form': form,
        }
        return render(request, self.template_name, context)
