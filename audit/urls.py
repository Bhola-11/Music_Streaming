"""
URL routing for Audit & Security Trail.
"""
from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('dashboard/', views.AuditDashboardView.as_view(), name='dashboard'),
    path('logs/', views.AuditLogListView.as_view(), name='log_list'),
    path('logs/<uuid:pk>/', views.AuditLogDetailView.as_view(), name='log_detail'),
    path('export/csv/', views.ExportAuditLogsCSVView.as_view(), name='export_csv'),
]
