"""
Views for viewing and exporting Audit Trails and Security Incidents.
"""
import csv
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import AuditLog, SecurityEvent, AdminActionLog, ActionCategory, ActionSeverity
from .services import AuditService


class StaffOrAdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)


class AuditDashboardView(LoginRequiredMixin, StaffOrAdminRequiredMixin, TemplateView):
    template_name = 'audit/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['summary'] = AuditService.get_security_summary()
        context['recent_logs'] = AuditLog.objects.select_related('user')[:15]
        context['recent_security_events'] = SecurityEvent.objects.select_related('user')[:10]
        context['categories'] = ActionCategory.choices
        context['severities'] = ActionSeverity.choices
        return context


class AuditLogListView(LoginRequiredMixin, StaffOrAdminRequiredMixin, ListView):
    model = AuditLog
    template_name = 'audit/log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related('user').all()
        category = self.request.GET.get('category')
        severity = self.request.GET.get('severity')
        search = self.request.GET.get('q')

        if category:
            qs = qs.filter(category=category)
        if severity:
            qs = qs.filter(severity=severity)
        if search:
            qs = qs.filter(action_type__icontains=search) | qs.filter(actor_email__icontains=search) | qs.filter(description__icontains=search)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ActionCategory.choices
        context['severities'] = ActionSeverity.choices
        context['current_category'] = self.request.GET.get('category', '')
        context['current_severity'] = self.request.GET.get('severity', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class AuditLogDetailView(LoginRequiredMixin, StaffOrAdminRequiredMixin, DetailView):
    model = AuditLog
    template_name = 'audit/log_detail.html'
    context_object_name = 'log'


class ExportAuditLogsCSVView(LoginRequiredMixin, StaffOrAdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="musicverse_audit_trail.csv"'

        writer = csv.writer(response)
        writer.writerow(['Timestamp', 'Category', 'Severity', 'Action Type', 'Actor', 'IP Address', 'Target Model', 'Target ID', 'Description'])

        logs = AuditLog.objects.all().order_by('-timestamp')[:1000]
        for log in logs:
            writer.writerow([
                log.timestamp.isoformat(),
                log.category,
                log.severity,
                log.action_type,
                log.actor_email or 'System',
                log.ip_address,
                log.target_model,
                log.target_object_id,
                log.description
            ])

        return response
