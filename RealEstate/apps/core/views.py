from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django import forms


class HomeView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
          return render(request, 'core/homebuyerHome.html', {})
        return HttpResponseRedirect('/login/')
        

def login_view(request):
    state = (False, "")     # Tuple to store status (True if logged in) and message.
    username = password = ''
    template = "core/auth.html"
    
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                state = (True, "You're successfully logged in!")
                return HttpResponseRedirect('/')
            else:
                state = (False, "Your account is not active, please contact the site admin.")
        else:
            state = (False, "Your username and/or password were incorrect.")

    class LoginForm(forms.Form):
        username = forms.CharField(label='Username', max_length=100)
        password = forms.CharField(label='Password', widget=forms.PasswordInput())
        
    context = {'form' : LoginForm(), 'state':state, 'username': username}
    return render(request, template, context)


def logout_view(request):
    logout(request)
