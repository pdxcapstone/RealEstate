from django import forms
from django.core.exceptions import ValidationError

from RealEstate.apps.core.forms import BaseSignupForm
from RealEstate.apps.core.models import User
from RealEstate.apps.pending.models import PendingHomebuyer


class HomebuyerSignupForm(BaseSignupForm):
    class Meta(BaseSignupForm.Meta):
        fields = ('password', 'password_confirmation', 'first_name',
                  'last_name', 'phone')


class InviteHomebuyerForm(forms.Form):
    """
    This form is used by Realtors to invite potential Homebuyers to the app.
    """
    first_email = forms.EmailField(label="Email")
    second_email = forms.EmailField(label="Email")

    def _confirm_unique(self, cleaned_data, email_fieldname):
        """
        Ensure the email does not match an existing User or PendingHomebuyer.
        If it does, add an error to that email field.
        """
        email = cleaned_data.get(email_fieldname)
        if email:
            for model in (User, PendingHomebuyer):
                if model.objects.filter(email=email).exists():
                    self.add_error(
                        email_fieldname,
                        ValidationError("A user with this email already "
                                        "exists or has been invited."))
        return email

    def clean(self):
        """
        Make sure the two emails are distinct and that the entered emails
        do not already exist in User or PendingHomebuyer instances.
        """
        cleaned_data = super(InviteHomebuyerForm, self).clean()
        first_email = self._confirm_unique(cleaned_data, 'first_email')
        second_email = self._confirm_unique(cleaned_data, 'second_email')
        if first_email and second_email and first_email == second_email:
            self.add_error(None, ValidationError("Emails must be distinct."))
        return cleaned_data
