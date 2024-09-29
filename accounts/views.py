from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView, LogoutView
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import CustomUser
from django.contrib.auth import login
from django.shortcuts import redirect
from django.contrib import messages

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        return reverse_lazy('dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Call the parent method to perform the login
        response = super().form_valid(form)
        messages.success(self.request, "You have successfully logged in.")
        return response

    def form_invalid(self, form):
        # Call the parent method to get the response
        response = super().form_invalid(form)
        messages.error(self.request, "Invalid username or password.")
        return response

class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    success_url = reverse_lazy('login')

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('login')

class ProfileView(TemplateView):
    template_name = 'accounts/profile.html'

class EmailVerificationView(TemplateView):
    template_name = 'accounts/email_verification.html'

class CustomLogoutView(LogoutView):
    # Redirect to 'login' after logout
    next_page = reverse_lazy('dashboard')  # Ensure you use reverse_lazy for URL resolution

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have successfully logged out.")
        return super().dispatch(request, *args, **kwargs)
