from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import (APIUserSerializer, APIHouseSerializer, APIHouseParamSerializer,
                          APIHouseFullParamSerializer, APICategoryWeightSerializer, APIGradeSerializer)
from .utils import jwt_payload_handler

from RealEstate.apps.core.models import House, Category, Couple, Grade, CategoryWeight, Homebuyer

class APIUserInfoView(APIView):
    """
    API for checking current user information.
    """
    permission_classes = (IsAuthenticated,)
    authentication_classes = (JSONWebTokenAuthentication, )

    def get(self, request, *args, **kwargs):

        serializer = APIUserSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = request.user
            response_data = jwt_payload_handler(user)

            return Response(response_data)
        return Response({'message': serializer.errors['non_field_errors'][0]}, status=status.HTTP_400_BAD_REQUEST)

class APIHouseView(APIView):
    """
    API for listing houses, adding house and getting score of house
    """
    serializer_class = APIHouseSerializer

    def get(self, request, *args, **kwargs):
        hid = self.request.query_params.get('id', None)
        user = self.request.user
        couple = Couple.objects.filter(homebuyer__user=user)
        serializer = APIUserSerializer(data=request.data, context={'request': self.request})

        if not serializer.is_valid():
            return Response({'code': 201, 'message': serializer.errors['non_field_errors'][0]},
                            status=status.HTTP_400_BAD_REQUEST)

        if hid is None:

            house = House.objects.filter(couple=couple)

            if house.count() < 1:
                return Response({'code': 202, 'message': 'No house under current user.'},
                                status=status.HTTP_400_BAD_REQUEST)

            houses = []
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
            paramser = APIHouseParamSerializer(data={'id': hid},
                                               context={'request': self.request})
            if paramser.is_valid():
                d = paramser.val()
                if d is not None:
                    return Response(d, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'code': 300, 'message': 'Format error'}, status=status.HTTP_400_BAD_REQUEST)

            category = Category.objects.filter(couple=couple)

            if category.count() < 1:
                return Response({'code': 204, 'message': 'No such category under the house.'},
                                status=status.HTTP_400_BAD_REQUEST)

            h = House.objects.filter(pk=hid)

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
    def put(self, request, *args, **kwargs):
        hid = self.request.query_params.get('id', None)
        cat = self.request.query_params.get('category', None)
        score = self.request.query_params.get('score', None)

        if hid is None or cat is None or score is None:
            return Response({'code': 300, 'message': 'Format error'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = APIUserSerializer(data=request.data, context={'request': self.request})

        if not serializer.is_valid():
            return Response({'code': 201, 'message': serializer.errors['non_field_errors'][0]})

        paramser = APIHouseFullParamSerializer(data={'id': hid, 'category': cat, 'score': score},
                                               context={'request': self.request})
        if paramser.is_valid():
            d = paramser.val()
            if d is not None:
                return Response(d, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'code': 300, 'message': 'Format error'}, status=status.HTTP_400_BAD_REQUEST)


        house = House.objects.filter(pk=hid)
        category = Category.objects.filter(pk=cat)
        homebuyer = Homebuyer.objects.filter(user=request.user)
        grade = Grade.objects.filter(house=house, category=category, homebuyer=homebuyer)

        data = {
            'house': hid,
            'category': cat,
            'homebuyer': homebuyer[0].pk,
            'score': score
        }

        ser = APIGradeSerializer(instance=grade[0], data=data)

        if ser.is_valid():
            c = ser.save()
            return Response({'code': 101, 'message': 'OK', 'score': c.score})
        else:
            return Response({'code': 205, 'message': ser.errors['non_field_errors'][0]},
                            status=status.HTTP_400_BAD_REQUEST)

    '''
    Add a house
    Add a new house based on the provided nickname and address. The couple of the newly
    created house will be the couple containing the current home buyer.
    '''
    def post(self, request, *args, **kwargs):
        serializer = APIUserSerializer(data=request.data, context={'request': self.request})

        if not serializer.is_valid():
            return Response({'code': 201, 'message': serializer.errors['non_field_errors'][0]},
                            status=status.HTTP_400_BAD_REQUEST)

        couple = Couple.objects.filter(homebuyer__user=request.user)

        data = request.data

        if data['nickname'] is None or data['address'] is None:
            return Response({'code': 300, 'message': 'Format error'}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({'code': 202, 'message': ser.errors['non_field_errors'][0]},
                            status=status.HTTP_400_BAD_REQUEST)

class APICategoryView(APIView):
    """
    API for listing categories and ranking categories
    """
    def get(self, request, *args, **kwargs):
        serializer = APIUserSerializer(data=request.data, context={'request': self.request})

        if not serializer.is_valid():
            return Response({'code': 201, 'message': serializer.errors['non_field_errors'][0]},
                            status=status.HTTP_400_BAD_REQUEST)

        couple = Couple.objects.filter(homebuyer__user=request.user)
        category = Category.objects.filter(couple=couple)

        if category.count() < 1:
                return Response({'code': 202, 'message': 'No such category under the user.'},
                                status=status.HTTP_400_BAD_REQUEST)

        categories = []
        for c in category:
            cweight = CategoryWeight.objects.filter(homebuyer__user=request.user, category=category)
            w = None
            if cweight.count() < 1:
                w = 'NAN'
            else:
                w = cweight[0].weight
            content = {
                'id': c.pk,
                'summary': c.summary,
                'description': c.description,
                'weight': w
            }
            categories.append(content)
        query = {
            'category': categories
        }

        return Response(query)

    def put(self, request, *args, **kwargs):
        serializer = APIUserSerializer(data=request.data, context={'request': self.request})

        if not serializer.is_valid():
            return Response({'code': 201, 'message': serializer.errors['non_field_errors'][0]},
                            status=status.HTTP_400_BAD_REQUEST)

        cid = self.request.query_params.get('id', None)
        w = self.request.query_params.get('weight', None)

        paramser = APIHouseFullParamSerializer(data={'id': int(cid), 'weight': int(w)},
                                               context={'request': self.request})
        if paramser.is_valid():
            d = paramser.val()
            if d is not None:
                return Response(d, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'code': 300, 'message': 'Format error'}, status=status.HTTP_400_BAD_REQUEST)

        cg = Category.objects.filter(pk=cid)
        cgw = CategoryWeight.objects.filter(category=cg, homebuyer__user=request.user)

        if cgw.count() < 1:
                return Response({'code': 202, 'message': 'No category under the user.'},
                                status=status.HTTP_400_BAD_REQUEST)

        hb = Homebuyer.objects.filter(user=request.user)

        data = {
            'homebuyer': int(hb[0].pk),
            'category': cid,
            'weight': int(w)
        }

        ser = APICategoryWeightSerializer(instance=cgw[0], data=data)

        if ser.is_valid(raise_exception=True):
            c = ser.save()
            return Response({'code': 101, 'message': 'OK', 'weight': c.weight})
        else:
            return Response({'code': 203, 'message': ser.errors['non_field_errors'][0]},
                            status=status.HTTP_400_BAD_REQUEST)
