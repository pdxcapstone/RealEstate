from django import forms
from django.contrib.auth.forms import UserCreationForm

from crispy_forms.helper import FormHelper

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
    def __init__(self, *args, **kwargs):
        super(addHomeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'addHomeForm'
        self.helper.form_class = 'addHome'
        self.helper.form_method = 'save'
        self.helper.form_action = 'add_to_homelist'

        self.helper.add_input(Submit('save', 'cancel'))
