from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('queue/', views.ModerationQueueView.as_view(), name='queue'),
]
