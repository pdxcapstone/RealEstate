from rest_framework import serializers
from django.utils.translation import ugettext as _

from RealEstate.apps.core.models import House, Homebuyer, Couple

class APIUserSerializer(serializers.Serializer):

    def validate(self, attrs):

        user = self.context['request'].user

        homebuyer = Homebuyer.objects.filter(user=user)

        if not homebuyer:
            msg = _('Only home buyers are allowed to use this functionality.')
            raise serializers.ValidationError(msg)
        return user