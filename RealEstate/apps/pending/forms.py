from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import BaseModelFormSet

from RealEstate.apps.core.forms import BaseSignupForm
from RealEstate.apps.core.models import User
from RealEstate.apps.pending.models import PendingHomebuyer


class HomebuyerSignupForm(BaseSignupForm):
    class Meta(BaseSignupForm.Meta):
        fields = ('first_name', 'last_name', 'phone', 'password',
                  'password_confirmation')


class InviteHomebuyerForm(forms.ModelForm):
    def clean_email(self):
        """
        Ensure the email does not match an existing User or PendingHomebuyer.
        """
        email = self.cleaned_data.get('email', None)
        if not email:
            return None

        for model in (User, PendingHomebuyer):
            if model.objects.filter(email=email).exists():
                self.add_error(
                    'email',
                    ValidationError("A user with this email already "
                                    "exists or has been invited."))
        return email

    class Meta:
        model = PendingHomebuyer
        fields = ('email', 'first_name', 'last_name')


class InviteHomebuyersFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        """
        Disallow empty forms.
        """
        super(InviteHomebuyersFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False
        return
