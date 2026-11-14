from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import EmailLoginForm, StudentSignUpForm, UserProfileUpdateForm
from .models import User


def role_home(user):
    """Landing URL for a user, based on role."""
    return reverse("dashboard:admin_panel" if user.role == User.Role.ADMIN else "dashboard:home")


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect(role_home(request.user))
    return redirect("accounts:login")


class SignUpView(CreateView):
    form_class = StudentSignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(role_home(request.user))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Account created. Log in to join the Hive.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "We couldn't create your account. Fix the highlighted fields.")
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        return role_home(self.request.user)

    def form_invalid(self, form):
        messages.error(self.request, "Login failed. Check your email and password.")
        return super().form_invalid(form)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileUpdateForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        # Ownership lock: there is no pk in the URL, and only the current user is ever returned.
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Profile not saved. Fix the highlighted fields.")
        return super().form_invalid(form)
