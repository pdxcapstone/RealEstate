from rest_framework import serializers
from django.utils.translation import ugettext as _

from RealEstate.apps.core.models import (House, Homebuyer, Couple, CategoryWeight,
                                         Grade, Category)

class APIUserSerializer(serializers.Serializer):

    def create(self, validated_data):
        # Do nothing
        return None

    def update(self, instance, validated_data):
        # Do nothing
        return None

    def validate(self, attrs):

        user = self.context['request'].user

        homebuyer = Homebuyer.objects.filter(user=user)

        if not homebuyer:
            msg = _('Only home buyers are allowed to use this functionality.')
            raise serializers.ValidationError(msg)
        return user

class APIHouseSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        house = House(**validated_data)
        house.save()
        return house

    class Meta:
        model = House
        field = ('nickname', 'address')

class APICategoryWeightSerializer(serializers.ModelSerializer):

    def update(self, instance, validated_data):
        instance.weight = validated_data.get('weight', instance.weight)
        instance.save()
        return instance

    class Meta:
        model = CategoryWeight

class APIGradeSerializer(serializers.ModelSerializer):

    def update(self, instance, validated_data):
        instance.score = validated_data.get('score', instance.score)
        instance.save()
        return instance

    class Meta:
        model = Grade
        fields = ('score', 'homebuyer', 'house', 'category')

class APIHouseParamSerializer(serializers.Serializer):

    id = serializers.IntegerField(required=True)

    def create(self, validated_data):
        # Do nothing
        return None

    def update(self, instance, validated_data):
        # Do nothing
        return None

    def check(self):
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

    def val(self):
        return self.check()

class APIHouseFullParamSerializer(APIHouseParamSerializer):

    category = serializers.IntegerField(required=True)
    score = serializers.IntegerField(max_value=5, min_value=1, required=True)

    def create(self, validated_data):
        # Do nothing
        return None

    def update(self, instance, validated_data):
        # Do nothing
        return None

    def val(self):
        d = self.check()

        if d is not None:
            return d

        user = self.context['request'].user
        couple = Couple.objects.filter(homebuyer__user=user)

        pcat = self.data['category']
        categ = Category.objects.filter(pk=pcat, couple=couple)

        if categ.count() < 1:
            code = 204
            msg = 'No such category under current user'
            return {'code': code, 'message': msg}
