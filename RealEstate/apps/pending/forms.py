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


class InviteHomebuyerForm(forms.Form):
    homebuyer1_first = forms.CharField(max_length=30, label="First Name")
    homebuyer1_last = forms.CharField(max_length=30, label="Last Name")
    homebuyer1_email = forms.EmailField(max_length=254, label="Email")
    homebuyer2_first = forms.CharField(max_length=30, label="First Name")
    homebuyer2_last = forms.CharField(max_length=30, label="Last Name")
    homebuyer2_email = forms.EmailField(max_length=254, label="Email")

    def _clean_email(self, field):
        email = self.cleaned_data.get(field, None)
        if not email:
            return None

        for model in (User, PendingHomebuyer):
            if model.objects.filter(email=email).exists():
                self.add_error(
                    field,
                    ValidationError("A user with this email already "
                                    "exists or has been invited."))
        return email

    def clean_homebuyer1_email(self):
        return self._clean_email('homebuyer1_email')

    def clean_homebuyer2_email(self):
        return self._clean_email('homebuyer2_email')

    def clean(self):
        """
        Ensure password matches password_confirmation.
        """
        cleaned_data = super(InviteHomebuyerForm, self).clean()
        email1 = cleaned_data.get('homebuyer1_email')
        email2 = cleaned_data.get('homebuyer2_email')
        if (email1 and email2 and email1 == email2):
            self.add_error(None, ValidationError("Emails must not match"))
        return cleaned_data
