from django import forms
from django.contrib.auth.forms import UserCreationForm


from RealEstate.apps.core.models import User


class EvaluationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        graded = kwargs.pop('graded', [])
        super(EvaluationForm, self).__init__(*args, **kwargs)
        for c, s in graded:
            self.fields[str(c.id)] = forms.CharField(
                initial=s, widget=forms.HiddenInput())


class UserCreationForm(UserCreationForm):
    """
    Overrides the default admin add form to use email instead of username.
    """
    class Meta:
        model = User
        fields = ('email',)


class addHomeForm(forms.Form):
    """
    Used for adding a home to a users home list
    """
    nickname = forms.CharField(
        label="Nickname",
        required=True
        )
    address = forms.CharField(
        label="Address",
        required=False
        )

class editHomeForm(forms.Form):
    """
    Used for adding a home to a users home list
    """
    edit_nickname = forms.CharField(
        label="Nickname",
        required=True
        )
    edit_address = forms.CharField(
        label="Address",
        required=False
        )
    homeId = forms.CharField(widget=forms.HiddenInput())
