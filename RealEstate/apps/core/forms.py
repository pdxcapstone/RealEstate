from django.contrib.auth.forms import UserCreationForm

from RealEstate.apps.core.models import User


class UserCreationForm(UserCreationForm):
    """
    Overrides the default admin add form to use email instead of username.
    """
    class Meta:
        model = User
        fields = ('email',)
