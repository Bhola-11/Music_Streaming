from django.urls import path
from .views import HomeLandingView

urlpatterns = [
    path('', HomeLandingView.as_view(), name='home'),
]
