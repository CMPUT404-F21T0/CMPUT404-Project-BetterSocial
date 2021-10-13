import django.contrib.auth.views as auth_views
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views import generic

from .forms import RegistrationForm


class LoginView(auth_views.LoginView):
    template_name = 'users/login.html'


class LogoutView(auth_views.LogoutView):
    template_name = 'users/logout.html'


class RegisterView(SuccessMessageMixin, generic.CreateView):
    template_name = 'users/register.html'
    form_class = RegistrationForm

    success_url = reverse_lazy('users:login')
    success_message = "Account created successfully!"
