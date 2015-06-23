"""
URL routing for the core app.
"""
from django.conf.urls import include, url

from RealEstate.apps.core import views


urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home')
]
