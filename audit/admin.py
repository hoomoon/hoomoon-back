from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.timezone import localtime
from .models import AuditLog, SecurityEvent, DataChangeHistory, AuditSettings

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp_formatted',
        'event_type',
        'severity_colored',
        'user',
        'description_short',
        'module',
        'ip_address'
    ]
    list_filter = [
        'event_type',
        'severity',
        'module',
        'timestamp',
        ('user', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = [
        'description',
        'user__username',
        'user__email',
        'ip_address',
        'module'
    ]
    readonly_fields = [
        'timestamp',
        'event_type',
        'user',
        'session_key',
        'ip_address',
        'user_agent',
        'content_type',
        'object_id',
        'content_object',
        'description',
        'details',
        'old_values',
        'new_values',
        'module',
        'action'
    ]
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def timestamp_formatted(self, obj):
        return localtime(obj.timestamp).strftime('%d/%m/%Y %H:%M:%S')
    timestamp_formatted.short_description = 'Data/Hora'
    timestamp_formatted.admin_order_field = 'timestamp'
    
    def severity_colored(self, obj):
        colors = {
            'LOW': '#28a745',      # verde
            'MEDIUM': '#ffc107',   # amarelo
            'HIGH': '#fd7e14',     # laranja
            'CRITICAL': '#dc3545'  # vermelho
        }
        color = colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_colored.short_description = 'Severidade'
    severity_colored.admin_order_field = 'severity'
    
    def description_short(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_short.short_description = 'Descrição'
    
    fieldsets = (
        ('Informações do Evento', {
            'fields': ('timestamp', 'event_type', 'severity', 'description')
        }),
        ('Usuário e Sessão', {
            'fields': ('user', 'session_key', 'ip_address', 'user_agent')
        }),
        ('Objeto Afetado', {
            'fields': ('content_type', 'object_id', 'content_object')
        }),
        ('Detalhes Técnicos', {
            'fields': ('module', 'action', 'details'),
            'classes': ('collapse',)
        }),
        ('Mudanças de Dados', {
            'fields': ('old_values', 'new_values'),
            'classes': ('collapse',)
        })
    )

@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp_formatted',
        'event_type_colored',
        'ip_address',
        'user',
        'resolved_status',
        'description_short'
    ]
    list_filter = [
        'event_type',
        'resolved',
        'timestamp',
        ('user', admin.RelatedOnlyFieldListFilter),
        ('resolved_by', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = [
        'description',
        'ip_address',
        'user__username',
        'user__email'
    ]
    readonly_fields = [
        'timestamp',
        'event_type',
        'ip_address',
        'user_agent',
        'user',
        'description',
        'additional_data'
    ]
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    list_per_page = 50
    actions = ['mark_as_resolved', 'mark_as_unresolved']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def timestamp_formatted(self, obj):
        return localtime(obj.timestamp).strftime('%d/%m/%Y %H:%M:%S')
    timestamp_formatted.short_description = 'Data/Hora'
    timestamp_formatted.admin_order_field = 'timestamp'
    
    def event_type_colored(self, obj):
        critical_events = ['BRUTE_FORCE', 'DATA_BREACH_ATTEMPT', 'SQL_INJECTION', 'XSS_ATTEMPT']
        warning_events = ['FAILED_LOGIN', 'SUSPICIOUS_ACTIVITY', 'UNAUTHORIZED_ACCESS']
        
        if obj.event_type in critical_events:
            color = '#dc3545'  # vermelho
        elif obj.event_type in warning_events:
            color = '#fd7e14'  # laranja
        else:
            color = '#6c757d'  # cinza
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_event_type_display()
        )
    event_type_colored.short_description = 'Tipo de Evento'
    event_type_colored.admin_order_field = 'event_type'
    
    def resolved_status(self, obj):
        if obj.resolved:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Resolvido</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ Pendente</span>'
            )
    resolved_status.short_description = 'Status'
    resolved_status.admin_order_field = 'resolved'
    
    def description_short(self, obj):
        return obj.description[:80] + '...' if len(obj.description) > 80 else obj.description
    description_short.short_description = 'Descrição'
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            resolved=True,
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} evento(s) marcado(s) como resolvido(s).')
    mark_as_resolved.short_description = 'Marcar como resolvido'
    
    def mark_as_unresolved(self, request, queryset):
        updated = queryset.update(
            resolved=False,
            resolved_by=None,
            resolved_at=None
        )
        self.message_user(request, f'{updated} evento(s) marcado(s) como não resolvido(s).')
    mark_as_unresolved.short_description = 'Marcar como não resolvido'
    
    fieldsets = (
        ('Informações do Evento', {
            'fields': ('timestamp', 'event_type', 'description')
        }),
        ('Origem do Evento', {
            'fields': ('ip_address', 'user_agent', 'user')
        }),
        ('Resolução', {
            'fields': ('resolved', 'resolved_by', 'resolved_at')
        }),
        ('Dados Adicionais', {
            'fields': ('additional_data',),
            'classes': ('collapse',)
        })
    )

@admin.register(DataChangeHistory)
class DataChangeHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp_formatted',
        'content_type',
        'field_name',
        'changed_by',
        'change_summary'
    ]
    list_filter = [
        'content_type',
        'field_name',
        'timestamp',
        ('changed_by', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = [
        'field_name',
        'old_value',
        'new_value',
        'changed_by__username'
    ]
    readonly_fields = [
        'content_type',
        'object_id',
        'content_object', 
        'field_name',
        'old_value',
        'new_value',
        'changed_by',
        'timestamp',
        'audit_log'
    ]
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def timestamp_formatted(self, obj):
        return localtime(obj.timestamp).strftime('%d/%m/%Y %H:%M:%S')
    timestamp_formatted.short_description = 'Data/Hora'
    timestamp_formatted.admin_order_field = 'timestamp'
    
    def change_summary(self, obj):
        old = obj.old_value[:30] + '...' if obj.old_value and len(obj.old_value) > 30 else obj.old_value
        new = obj.new_value[:30] + '...' if obj.new_value and len(obj.new_value) > 30 else obj.new_value
        return f"{old} → {new}"
    change_summary.short_description = 'Mudança'

@admin.register(AuditSettings)
class AuditSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'retention_days',
        'enable_email_alerts',
        'monitor_failed_logins',
        'monitor_high_value_transactions',
        'updated_at'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Configurações de Retenção', {
            'fields': ('retention_days',)
        }),
        ('Configurações de Alertas', {
            'fields': ('enable_email_alerts', 'alert_email')
        }),
        ('Configurações de Monitoramento', {
            'fields': (
                'monitor_failed_logins',
                'max_failed_logins',
                'monitor_high_value_transactions',
                'high_value_threshold'
            )
        }),
        ('Configurações de Logging', {
            'fields': ('log_read_operations', 'log_api_calls')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # Permitir apenas se não existir nenhuma configuração
        return not AuditSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False  # Não permitir deletar configurações
