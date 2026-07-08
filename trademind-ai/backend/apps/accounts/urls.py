"""
apps/accounts/urls.py
---------------------
Authentication URL patterns — mounted at /api/v1/auth/
"""

from django.urls import path

from .views import (
    ChangePasswordView,
    Confirm2FAView,
    DeleteAccountView,
    Disable2FAView,
    Enable2FAView,
    ForgotPasswordView,
    LoginView,
    LogoutView,
    ProfileView,
    RegisterView,
    ResetPasswordView,
    TokenRefreshView,
    VerifyEmailView,
)

urlpatterns = [
    # Registration & verification
    path("register/",      RegisterView.as_view(),     name="auth-register"),
    path("verify-email/",  VerifyEmailView.as_view(),  name="auth-verify-email"),

    # Login / logout / token
    path("login/",         LoginView.as_view(),         name="auth-login"),
    path("logout/",        LogoutView.as_view(),         name="auth-logout"),
    path("refresh/",       TokenRefreshView.as_view(),  name="auth-refresh"),

    # Password management
    path("forgot-password/",  ForgotPasswordView.as_view(),  name="auth-forgot-password"),
    path("reset-password/",   ResetPasswordView.as_view(),   name="auth-reset-password"),
    path("change-password/",  ChangePasswordView.as_view(),  name="auth-change-password"),

    # 2FA
    path("enable-2fa/",   Enable2FAView.as_view(),   name="auth-enable-2fa"),
    path("confirm-2fa/",  Confirm2FAView.as_view(),  name="auth-confirm-2fa"),
    path("disable-2fa/",  Disable2FAView.as_view(),  name="auth-disable-2fa"),

    # Profile
    path("profile/",   ProfileView.as_view(),       name="auth-profile"),
    path("account/",   DeleteAccountView.as_view(), name="auth-delete-account"),
]
