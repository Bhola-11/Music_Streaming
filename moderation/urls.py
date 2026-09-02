"""
URL Routing for Content Moderation & Takedowns.
"""
from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('queue/', views.ModerationQueueListView.as_view(), name='queue'),
    path('report/<uuid:pk>/', views.ModerationReportDetailView.as_view(), name='report_detail'),
    path('flag/song/<uuid:song_id>/', views.FileReportView.as_view(), name='file_report'),
    path('dmca/<uuid:song_id>/', views.SubmitTakedownRequestView.as_view(), name='dmca_claim'),
    path('decision/<uuid:pk>/', views.ExecuteModerationDecisionView.as_view(), name='decision'),
]
