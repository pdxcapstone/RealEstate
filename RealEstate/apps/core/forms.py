from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from RealEstate.apps.core.models import User, Category, House
from RealEstate.apps.pending.models import PendingHomebuyer


class AddCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('summary', 'description')


class EditCategoryForm(forms.ModelForm):
    id = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Category
        fields = ('summary', 'description')


class BaseSignupForm(forms.ModelForm):
    """
    Homebuyers/Realtors will use subclasses of this form to sign up.  The view
    that uses this form will then create their User/Homebuyer/Realtor
    instances.
    """
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
        return cleaned_data


class EvaluationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        graded = kwargs.pop('graded', [])
        super(EvaluationForm, self).__init__(*args, **kwargs)
        for c, s in graded:
            self.fields[str(c.id)] = forms.CharField(
                initial=s, widget=forms.HiddenInput())


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


class UserCreationForm(UserCreationForm):
    """
    Overrides the default admin add form to use email instead of username.
    """
    class Meta:
        model = User
        fields = ('email',)


class AddHomeForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ('nickname', 'address')


class EditHomeForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = House
        fields = ('nickname', 'address')
