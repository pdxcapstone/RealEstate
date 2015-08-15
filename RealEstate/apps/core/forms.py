from collections import OrderedDict

from django import forms
from django.conf import settings
from django.contrib.auth.forms import (PasswordChangeForm, UserChangeForm,
                                       UserCreationForm)
from django.core.exceptions import ValidationError

from passwords.fields import PasswordField

from RealEstate.apps.core.models import Category, House, User
from RealEstate.apps.pending.models import PendingHomebuyer


class AddCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('summary', 'description')


class AddCategoryFromEvalForm(forms.ModelForm):
    weight = forms.CharField(widget=forms.HiddenInput(), initial=3)

    class Meta:
        model = Category
        fields = ('summary', 'description')


class EditCategoryForm(forms.ModelForm):
    id = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Category
        fields = ('summary', 'description')


class AddHomeForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ('nickname', 'address')


class EditHomeForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = House
        fields = ('nickname', 'address')


class EditHomeForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = House
        fields = ('nickname', 'address')
class BaseSignupForm(forms.ModelForm):
    """
    Homebuyers/Realtors will use subclasses of this form to sign up.  The view
    that uses this form will then create their User/Homebuyer/Realtor
    instances.
    """
    password = PasswordField(label="Password")
    password_confirmation = forms.CharField(label="Password Confirmation",
                                            widget=forms.PasswordInput)

    class Meta:
        fields = ()
        model = User
        widgets = {
            'password': forms.PasswordInput,
        }

    def clean(self):
        """
        Ensure password matches password_confirmation.
        """
        cleaned_data = super(BaseSignupForm, self).clean()
        password = cleaned_data.get('password')
        password_confirmation = cleaned_data.get('password_confirmation')
        if (password and password_confirmation and
                password != password_confirmation):
            self.add_error('password_confirmation',
                           ValidationError("Passwords do not match."))
        if 'password' in self.errors:
            self.errors['password'] = [settings.PASSWORD_ERROR_MESSAGE]
        return cleaned_data


class EvaluationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        graded = kwargs.pop('graded', [])
        super(EvaluationForm, self).__init__(*args, **kwargs)
        for c, s in graded:
            self.fields[str(c.id)] = forms.CharField(
                initial=s, widget=forms.HiddenInput())


class PasswordChangeForm(PasswordChangeForm):
    new_password1 = PasswordField(label="New password")

    def clean(self):
        cleaned_data = super(PasswordChangeForm, self).clean()
        new_password = cleaned_data.get('new_password1')
        if 'new_password1' in self.errors:
            self.errors['new_password1'] = [settings.PASSWORD_ERROR_MESSAGE]
        return cleaned_data

PasswordChangeForm.base_fields = OrderedDict(
    (k, PasswordChangeForm.base_fields[k])
    for k in ['old_password', 'new_password1', 'new_password2']
)



class RealtorSignupForm(BaseSignupForm):
    def clean_email(self):
        """
        Disallow duplicate emails when validation form.
        """
        email = self.cleaned_data.get('email')
        if email:
            for model in (User, PendingHomebuyer):
                if model.objects.filter(email=email).exists():
                    raise ValidationError(
                        "A user with this email already exists.")
        return email

    class Meta(BaseSignupForm.Meta):
        fields = ('email', 'first_name', 'last_name', 'phone', 'password',
                  'password_confirmation')


class UserChangeForm(UserChangeForm):
    """
    Uses core.User instead of django.contrib.auth.User
    """
    class Meta:
        model = User
        fields = '__all__'


class UserCreationForm(UserCreationForm):
    """
    Overrides the default admin add form to use email instead of username.
    """
    class Meta:
        model = User
        fields = ('email',)


class AddRealtorHomeForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = House
        fields = ('nickname', 'address')
