"""
Views and API Endpoints for User Notifications & Delivery Preference Settings.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, View, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse_lazy

from .models import Notification, NotificationPreference
from .forms import NotificationPreferenceForm
from .services import NotificationService


class NotificationListView(LoginRequiredMixin, ListView):
    """
    Renders user notification inbox with real-time mark-all-as-read functionality.
    """
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 30

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')


class MarkNotificationReadAPIView(LoginRequiredMixin, View):
    """
    Marks a single notification as read via AJAX.
    """
    def post(self, request, pk):
        success = NotificationService.mark_as_read(pk, request.user)
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return JsonResponse({'success': success, 'unread_count': unread_count})


class MarkAllNotificationsReadAPIView(LoginRequiredMixin, View):
    """
    Marks all user notifications as read.
    """
    def post(self, request):
        count = NotificationService.mark_all_as_read(request.user)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'count': count})
        messages.success(request, "All notifications marked as read.")
        return redirect('notifications:list')


class NotificationPreferencesView(LoginRequiredMixin, View):
    """
    Manages user notification preferences.
    """
    template_name = 'notifications/preferences.html'

    def get(self, request):
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        form = NotificationPreferenceForm(instance=prefs)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        form = NotificationPreferenceForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification preferences updated successfully.")
            return redirect('notifications:preferences')
        return render(request, self.template_name, {'form': form})
