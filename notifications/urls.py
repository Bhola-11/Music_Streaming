"""
URL Routing for Notifications & Preference Management.
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('preferences/', views.NotificationPreferencesView.as_view(), name='preferences'),
    path('api/read/<uuid:pk>/', views.MarkNotificationReadAPIView.as_view(), name='api_mark_read'),
    path('api/read-all/', views.MarkAllNotificationsReadAPIView.as_view(), name='api_mark_all_read'),
]
