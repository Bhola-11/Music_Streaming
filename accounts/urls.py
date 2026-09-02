"""
URL routing for Accounts, Authentication & Security.
"""
from django.urls import path
from . import views
from .profile_wizard import OnboardingWizardView

app_name = 'accounts'

urlpatterns = [
    # Auth
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('2fa/verify/', views.TwoFactorVerifyView.as_view(), name='two_factor_verify'),

    # Onboarding Wizard
    path('onboarding/', OnboardingWizardView.as_view(), name='onboarding'),

    # Profile & Preferences
    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('settings/profile/', views.EditProfileView.as_view(), name='edit_profile'),
    path('settings/preferences/', views.PreferencesView.as_view(), name='preferences'),
    path('settings/security/', views.SecuritySettingsView.as_view(), name='security'),

    # 2FA Management
    path('settings/security/2fa/setup/', views.TwoFactorSetupView.as_view(), name='two_factor_setup'),
    path('settings/security/2fa/disable/', views.TwoFactorDisableView.as_view(), name='two_factor_disable'),

    # Session Management
    path('settings/sessions/', views.ActiveSessionsView.as_view(), name='sessions'),
    path('settings/sessions/terminate/<str:session_key>/', views.TerminateSessionView.as_view(), name='terminate_session'),
    path('settings/sessions/terminate-others/', views.TerminateAllOtherSessionsView.as_view(), name='terminate_other_sessions'),

    # Social graph
    path('users/<str:username>/toggle-follow/', views.ToggleFollowUserView.as_view(), name='toggle_follow'),
]
