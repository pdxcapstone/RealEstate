"""RealEstate URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

from RealEstate.apps.core import views as CoreViews
from RealEstate.apps.pending import views as PendingViews


urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('RealEstate.apps.api.urls')),

    url(r'^login/$', CoreViews.login, name='auth_login'),
    url(r'^logout/$',
        'django.contrib.auth.views.logout_then_login', name='auth_logout'),
    url(r'^change-password/$', 'django.contrib.auth.views.password_change',
        {'post_change_redirect': 'home'}, name='password_change'),

    url(r'^invite/$',
        PendingViews.InviteHomebuyerView.as_view(), name='invite'),
    url(r'^signup/(?P<registration_token>[0-9a-f]{64})/$',
        PendingViews.SignupView.as_view(), name='signup'),
    url(r'^eval/(?P<house_id>[\d]+)/$',
        CoreViews.EvalView.as_view(), name='eval'),
    url(r'^report/(?P<couple_id>[\d]+)/$',
        CoreViews.ReportView.as_view(), name='report'),
    url(r'^$', CoreViews.HomeView.as_view(), name='home'),
    url(r'^categories/$', CoreViews.CategoryView.as_view(), name='categories'),
]
