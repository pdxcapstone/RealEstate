from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import APIUserSerializer, APIHouseSerializer
from .utils import jwt_payload_handler
from collections import OrderedDict

from RealEstate.apps.core.models import House, Homebuyer, Couple

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
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class APIHouseView(APIView):
    """
    API for listing houses, adding house and getting score of house
    """
    serializer_class = APIHouseSerializer

    def get(self, request, *args, **kwargs):
        id = self.request.query_params.get('id')
        user = self.request.user
        couple = Couple.objects.filter(homebuyer__user=user)
        house = House.objects.filter(couple=couple)
        serializer = APIUserSerializer(data=request.data, context={'request': self.request})

        if not serializer.is_valid():
            return Response({'code': 201, 'message': serializer.errors['non_field_errors'][0]})

        if id is None:
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
            return Response(query)

        return Response({'a': 1})


