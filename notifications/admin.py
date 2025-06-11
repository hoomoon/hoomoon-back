"""
Admin interface para sistema de notificações
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count

from .models import NotificationTemplate, Notification, NotificationPreference


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """
    Admin para templates de notificação
    """
    list_display = [
        'name', 'notification_type', 'channel', 'is_default', 
        'status', 'created_at'
    ]
    list_filter = [
        'notification_type', 'channel', 'is_default', 'status', 'created_at'
    ]
    search_fields = ['name', 'subject', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        (_('Informações Básicas'), {
            'fields': ['name', 'notification_type', 'channel', 'is_default', 'status']
        }),
        (_('Conteúdo'), {
            'fields': ['subject', 'content', 'html_content']
        }),
        (_('Configurações'), {
            'fields': ['variables'],
            'classes': ['collapse']
        }),
        (_('Timestamps'), {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            notifications_count=Count('notification')
        )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin para notificações
    """
    list_display = [
        'user', 'notification_type', 'channel', 'notification_status',
        'sent_at', 'read_at', 'created_at'
    ]
    list_filter = [
        'notification_type', 'channel', 'notification_status', 
        'sent_at', 'read_at', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'subject', 'content'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'sent_at', 'delivered_at', 'read_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = [
        (_('Destinatário e Tipo'), {
            'fields': ['user', 'template', 'notification_type', 'channel']
        }),
        (_('Conteúdo'), {
            'fields': ['subject', 'content', 'html_content'],
            'classes': ['collapse']
        }),
        (_('Status e Timestamps'), {
            'fields': [
                'notification_status', 'sent_at', 'delivered_at', 
                'read_at', 'error_message'
            ]
        }),
        (_('Configurações Extras'), {
            'fields': [
                'action_url', 'expires_at', 'recipient_info', 
                'variables_used'
            ],
            'classes': ['collapse']
        }),
        (_('Sistema'), {
            'fields': ['status', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    actions = ['mark_as_read', 'mark_as_sent', 'resend_notification']
    
    def mark_as_read(self, request, queryset):
        """Marca notificações selecionadas como lidas"""
        count = 0
        for notification in queryset:
            if not notification.is_read():
                notification.mark_as_read()
                count += 1
        
        self.message_user(
            request,
            f"{count} notificações marcadas como lidas."
        )
    mark_as_read.short_description = _("Marcar como lidas")
    
    def mark_as_sent(self, request, queryset):
        """Marca notificações selecionadas como enviadas"""
        count = 0
        for notification in queryset.filter(notification_status='PENDING'):
            notification.mark_as_sent()
            count += 1
        
        self.message_user(
            request,
            f"{count} notificações marcadas como enviadas."
        )
    mark_as_sent.short_description = _("Marcar como enviadas")
    
    def resend_notification(self, request, queryset):
        """Reenvia notificações falhadas"""
        count = 0
        for notification in queryset.filter(notification_status='FAILED'):
            # Aqui você implementaria a lógica de reenvio
            notification.notification_status = 'PENDING'
            notification.error_message = ''
            notification.save()
            count += 1
        
        self.message_user(
            request,
            f"{count} notificações marcadas para reenvio."
        )
    resend_notification.short_description = _("Reenviar notificações")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """
    Admin para preferências de notificação
    """
    list_display = [
        'user', 'email_enabled', 'sms_enabled', 'push_enabled', 
        'in_app_enabled', 'digest_frequency', 'created_at'
    ]
    list_filter = [
        'email_enabled', 'sms_enabled', 'push_enabled', 
        'in_app_enabled', 'digest_frequency', 'created_at'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        (_('Usuário'), {
            'fields': ['user']
        }),
        (_('Canais Habilitados'), {
            'fields': [
                'email_enabled', 'sms_enabled', 
                'push_enabled', 'in_app_enabled'
            ]
        }),
        (_('Configurações de Horário'), {
            'fields': ['quiet_hours_start', 'quiet_hours_end'],
            'classes': ['collapse']
        }),
        (_('Frequência e Tipos'), {
            'fields': ['digest_frequency', 'notification_types'],
            'classes': ['collapse']
        }),
        (_('Timestamps'), {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Customizações adicionais para melhor UX no admin
class NotificationInline(admin.TabularInline):
    """
    Inline para mostrar notificações relacionadas a um usuário
    """
    model = Notification
    extra = 0
    readonly_fields = [
        'notification_type', 'channel', 'notification_status', 
        'sent_at', 'read_at'
    ]
    fields = [
        'notification_type', 'channel', 'subject', 
        'notification_status', 'sent_at', 'read_at'
    ]
    
    def has_add_permission(self, request, obj=None):
        return False
