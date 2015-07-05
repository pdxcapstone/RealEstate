from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.generic import View

from RealEstate.apps.core.models import User
from RealEstate.apps.core.views import BaseView
from RealEstate.apps.pending.forms import InviteHomebuyerForm
from RealEstate.apps.pending.models import PendingCouple, PendingHomebuyer


class InviteHomebuyerView(BaseView):
    """
    This view supplies a form for sending out email invites to Homebuyers.
    This is temporarily a separate view but we will probably want to integrate
    this into the Realtor home page.
    """
    _USER_TYPES_ALLOWED = User._REALTOR_ONLY
    template_name = 'pending/inviteHomebuyer.html'

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
        messages.success(request,
                         "Email invite sent to {email}".format(email=email))

    def get(self, request, *args, **kwargs):
        context = {'invite_homebuyer_form': InviteHomebuyerForm()}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Populate the form with the submitted data.  If invalid, re-render it
        with the errors displayed.  Otherwise the form is valid; create the
        PendingHomebuyer instances and send out the email invites.
        """
        form = InviteHomebuyerForm(request.POST)
        if form.is_valid():
            first_email = form.cleaned_data.get('first_email')
            second_email = form.cleaned_data.get('second_email')
            with transaction.atomic():
                pending_couple = PendingCouple.objects.create(
                    realtor=request.user.realtor)
                self._invite_homebuyer(request, pending_couple, first_email)
                self._invite_homebuyer(request, pending_couple, second_email)
            return redirect(reverse('invite'))

        context = {'invite_homebuyer_form': form}
        return render(request, self.template_name, context)


class SignupView(View):
    pass
