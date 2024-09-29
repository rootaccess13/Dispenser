from django.urls import path
from .views import RegisterView, CustomLoginView, CustomLogoutView, CustomPasswordResetView, CustomPasswordResetConfirmView, ProfileView, EmailVerificationView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('email-verification/', EmailVerificationView.as_view(), name='email_verification'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

]
