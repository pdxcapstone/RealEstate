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


class SignupForm(forms.ModelForm):
    """
    Potential homebuyers will use this form to sign up.  The view that uses
    this form will then create their User/Homebuyer instances.
    """
    registration_token = forms.CharField(min_length=64, max_length=64,
                                         widget=forms.widgets.HiddenInput)

    class Meta:
        model = User
        fields = ('registration_token',
                  'email', 'first_name', 'last_name', 'phone')

    def clean_email(self):
        """
        Ensure a User with this email does not already exist.
        """
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            error = ValidationError("User with this email already exists.")
            self.add_error('email', error)
        return email

    def clean_registration_token(self):
        """
        Ensure this token actually corresponding to a PendingHomebuyer
        instance.  If it does, store that instance instead in the cleaned_data
        strucutre so the view does not need to repeat the query.
        """
        token = self.cleaned_data.get('registration_token')
        homebuyer = PendingHomebuyer.objects.filter(registration_token=token)
        if not homebuyer.exists():
            self.add_error('registration_token',
                           ValidationError("Invalid Registration Token."))
        return homebuyer.first()
