from django.shortcuts import render
from django.core.urlresolvers import reverse
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import APIUserSerializer
from .utils import jwt_payload_handler

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

