from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, UpdateView, View
from .forms import StudentRegistrationForm, CustomAuthenticationForm, UserProfileForm
from .models import CustomUser

class CustomLoginView(FormView):
    """
    Handles user login using email and custom remember me logic.
    """
    template_name = 'accounts/login.html'
    form_class = CustomAuthenticationForm

    def get_success_url(self):
        return reverse_lazy('dashboard:dashboard_redirect')

    def dispatch(self, request, *args, **kwargs):
        # Redirect authenticated users immediately to dashboard redirection
        if request.user.is_authenticated:
            return redirect('dashboard:dashboard_redirect')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        auth_login(self.request, user)
        
        # Configure session expiry based on "Remember Me" checkbox
        remember_me = form.cleaned_data.get('remember_me')
        if remember_me:
            # Keep user logged in for 2 weeks
            self.request.session.set_expiry(1209600)
        else:
            # Expire session when the user closes their browser
            self.request.session.set_expiry(0)
            
        messages.success(self.request, f"Welcome back, {user.full_name}!")
        return super().form_valid(form)


class RegisterView(FormView):
    """
    Handles student registration.
    """
    template_name = 'accounts/register.html'
    form_class = StudentRegistrationForm
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:dashboard_redirect')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your registration was successful! You can now log in.")
        return super().form_valid(form)


class CustomLogoutView(View):
    """
    Handles logging out the user. Supports both GET and POST requests.
    """
    def get(self, request, *args, **kwargs):
        auth_logout(request)
        messages.info(request, "You have been successfully logged out.")
        return redirect('login')

    def post(self, request, *args, **kwargs):
        auth_logout(request)
        messages.info(request, "You have been successfully logged out.")
        return redirect('login')


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    Allows the authenticated user to view and update their profile.
    """
    model = CustomUser
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile has been updated successfully!")
        return super().form_valid(form)
