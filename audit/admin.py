"""
Django Admin registration for Audit Trail models.
"""
from django.contrib import admin
from .models import AuditLog, SecurityEvent, APIRequestLog, AdminActionLog, AuditRetentionPolicy


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'action_type', 'actor_email', 'category', 'severity', 'ip_address', 'status_code')
    list_filter = ('category', 'severity', 'request_method', 'timestamp')
    search_fields = ('action_type', 'actor_email', 'description', 'ip_address', 'target_model')
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'event_type', 'severity', 'source_ip', 'country_code', 'is_resolved')
    list_filter = ('severity', 'is_resolved', 'event_type', 'created_at')
    search_fields = ('event_type', 'source_ip', 'city')
    ordering = ('-created_at',)


@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'endpoint', 'method', 'status_code', 'execution_time_ms', 'ip_address')
    list_filter = ('method', 'status_code', 'created_at')
    search_fields = ('endpoint', 'ip_address')
    ordering = ('-created_at',)


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'admin_user', 'action', 'target_entity')
    search_fields = ('action', 'target_entity', 'justification_reason')
    ordering = ('-created_at',)


@admin.register(AuditRetentionPolicy)
class AuditRetentionPolicyAdmin(admin.ModelAdmin):
    list_display = ('category', 'retention_days', 'auto_archive', 'last_cleaned_at')
