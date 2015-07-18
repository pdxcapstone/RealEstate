from django import forms
from django.core.exceptions import ValidationError

from RealEstate.apps.core.models import User
from RealEstate.apps.pending.models import PendingHomebuyer


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


class HomebuyerSignupForm(forms.ModelForm):
    """
    Potential homebuyers will use this form to sign up.  The view that uses
    this form will then create their User/Homebuyer instances.
    """
    password_confirmation = forms.CharField(label="Password Confirmation",
                                            widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('password', 'password_confirmation', 'first_name',
                  'last_name', 'phone')
        widgets = {
            'password': forms.PasswordInput,
        }

    def __init__(self, *args, **kwargs):
        super(HomebuyerSignupForm, self).__init__(*args, **kwargs)

    def clean(self):
        """
        Ensure password matches password_confirmation.
        """
        cleaned_data = super(HomebuyerSignupForm, self).clean()
        password = cleaned_data.get('password')
        password_confirmation = cleaned_data.get('password_confirmation')
        if (password and password_confirmation and
                password != password_confirmation):
            self.add_error('password_confirmation',
                           ValidationError("Passwords do not match."))
        return cleaned_data
