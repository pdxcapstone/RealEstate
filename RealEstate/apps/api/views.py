from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (APIUserSerializer, APIHouseSerializer, APIHouseParamSerializer,
                          APIHouseFullParamSerializer)
from .utils import jwt_payload_handler

from RealEstate.apps.core.models import House, Category, Couple, Grade

class APIUserInfoView(APIView):
    """
    API for checking current user information.
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, )

    def get(self, request):

        serializer = APIUserSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = request.user
            response_data = jwt_payload_handler(user)

            return Response(response_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class APIHouseView(APIView):
    """
    API for listing houses, adding house and getting score of house
    """
    serializer_class = APIHouseSerializer

    def get(self, request):
        hid = self.request.query_params.get('id', None)
        user = self.request.user
        couple = Couple.objects.filter(homebuyer__user=user)
        serializer = APIUserSerializer(data=request.data, context={'request': self.request})

        if not serializer.is_valid():
            return Response({'code': 201, 'message': serializer.errors['non_field_errors'][0]})

        if hid is None:
            houses = []

            house = House.objects.filter(couple=couple)

            for h in house:
                content = {
                    'id': h.pk,
                    'nickname': h.nickname,
                    'address': h.address
                }
                houses.append(content)

            query = {
                'house': houses
            }
        else:
            paramser = APIHouseParamSerializer(data={'id': int(hid)},
                                               context={'request': self.request})
            if paramser.is_valid():
                d = paramser.val()
                if d is not None:
                    return Response(d)
            else:
                return Response({'code': 300, 'message': 'Format error'})

            h = House.objects.filter(pk=hid)
            category = Category.objects.filter(couple=couple)
            categories = []
            for c in category:
                grade = Grade.objects.filter(category=c, house=h, homebuyer__user=user)
                if grade.count() > 0:
                    content = {
                        'id': c.pk,
                        'summary': c.summary,
                        'score': grade[0].score
                    }
                    categories.append(content)
            query = {
                'category': categories
            }
        return Response(query)


    '''
    Grade a house
    This API will get the house and the category information from the request,
    then update the grade of the category provided. If the house doesn't have
    the category, an error will be returned.
    '''
    def put(self, request):
        hid = self.request.query_params.get('id', None)
        cat = self.request.query_params.get('category', None)
        score = self.request.query_params.get('score', None)

        if hid is None or cat is None or score is None:
            return Response({'code': 300, 'message': 'Format error'})

        paramser = APIHouseFullParamSerializer(data={'id': int(hid), 'category': int(cat),
                                        'score': int(score)},context={'request': self.request})
        if paramser.is_valid():
            d = paramser.val()
            if d is not None:
                return Response(d)
        else:
            return Response({'code': 300, 'message': 'Format error'})

        serializer = APIUserSerializer(data=request.data, context={'request': self.request})

        if not serializer.is_valid():
            return Response({'code': 201, 'message': serializer.errors['non_field_errors'][0]})

        # Waiting for the bug to be fixed and the new version to be released

        return Response('Waiting for updates')

    '''
    Add a house
    Add a new house based on the provided nickname and address. The couple of the newly
    created house will be the couple containing the current home buyer.
    '''
    def post(self, request):
        serializer = APIUserSerializer(data=request.data, context={'request': self.request})

        if not serializer.is_valid():
            return Response({'code': 201, 'message': serializer.errors['non_field_errors'][0]})

        couple = Couple.objects.filter(homebuyer__user=request.user)

        data = request.data
        data['couple'] = couple[0].pk

        ser = APIHouseSerializer(data=data)

        if ser.is_valid(raise_exception=True):
            ser.save()
            ret = ser.validated_data
            content = {
                'nickname': ret['nickname'],
                'address': ret['address']
            }
            return Response(content)
        else:
            # Will be replaced by serializer error
            return Response({'error': 'Format error'})

