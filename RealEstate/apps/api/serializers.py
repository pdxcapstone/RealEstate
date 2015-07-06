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

class APIHouseSerializer(serializers.ModelSerializer):

    class Meta:
        model = House
        depth = 1
        fields = ('id', 'nickname', 'address')

class APIHouseParamSerializer(serializers.Serializer):

    id = serializers.IntegerField(required=True)
    category = serializers.IntegerField(required=False)
    score = serializers.IntegerField(max_value=5, min_value=1, required=False)


    def val(self):
        user = self.context['request'].user
        pid = self.data['id']
        house = House.objects.filter(pk=pid)

        if house.count() < 1:
            code = 202
            msg = 'House ID invalid'
            return {'code': code, 'message': msg}

        couple = Couple.objects.filter(homebuyer__user=user)
        houses = House.objects.filter(couple=couple, pk=pid)

        if houses.count() < 1:
            code = 203
            msg = 'No such house under current user'
            return {'code': code, 'message': msg}
        return None