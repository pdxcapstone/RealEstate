from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django import forms
from .models import House, Homebuyer, Couple


class HomeView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
          couple = Couple.objects.filter(homebuyer__user=request.user)
          house = House.objects.filter(couple=couple)
          return render(request, 'core/homebuyerHome.html', {'couple': couple, 'house': house})
        return HttpResponseRedirect('/login/')
