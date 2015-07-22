from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^auth/$', 'rest_framework_jwt.views.obtain_jwt_token'),
    url(r'^refresh/$', 'rest_framework_jwt.views.refresh_jwt_token'),
    url(r'^get-user/$', views.APIUserInfoView.as_view(), name='api_test'),
    url(r'^houses/$', views.APIHouseView.as_view()),
    url(r'^categories/$', views.APICategoryView.as_view())
]
