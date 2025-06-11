"""
Serializers para sistema de notificações
"""
from rest_framework import serializers
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import NotificationTemplate, Notification, NotificationPreference


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer para templates de notificação
    """
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )
    channel_display = serializers.CharField(
        source='get_channel_display', 
        read_only=True
    )
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'notification_type', 'notification_type_display',
            'channel', 'channel_display', 'subject', 'content', 
            'html_content', 'is_default', 'variables', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer para notificações
    """
    user = serializers.StringRelatedField(read_only=True)
    template = serializers.StringRelatedField(read_only=True)
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )
    channel_display = serializers.CharField(
        source='get_channel_display', 
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_notification_status_display', 
        read_only=True
    )
    is_read = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    time_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'template', 'notification_type', 
            'notification_type_display', 'channel', 'channel_display',
            'subject', 'content', 'html_content', 'notification_status',
            'status_display', 'sent_at', 'delivered_at', 'read_at',
            'action_url', 'expires_at', 'is_read', 'is_expired',
            'time_since_created', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'template', 'sent_at', 'delivered_at', 
            'read_at', 'created_at', 'updated_at'
        ]
    
    def get_is_read(self, obj):
        """Retorna se a notificação foi lida"""
        return obj.is_read()
    
    def get_is_expired(self, obj):
        """Retorna se a notificação expirou"""
        return obj.is_expired()
    
    def get_time_since_created(self, obj):
        """Retorna tempo desde criação em formato amigável"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} dias atrás"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} horas atrás"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutos atrás"
        else:
            return "Agora mesmo"


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de notificações (admin use)
    """
    class Meta:
        model = Notification
        fields = [
            'user', 'template', 'notification_type', 'channel',
            'subject', 'content', 'html_content', 'action_url',
            'expires_at', 'recipient_info', 'variables_used'
        ]
    
    def validate(self, data):
        """Validações customizadas"""
        if data.get('expires_at') and data['expires_at'] < timezone.now():
            raise serializers.ValidationError(
                "Data de expiração deve ser no futuro"
            )
        return data


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer para preferências de notificação
    """
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'email_enabled', 'sms_enabled', 
            'push_enabled', 'in_app_enabled', 'notification_types',
            'quiet_hours_start', 'quiet_hours_end', 'digest_frequency',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class NotificationSummarySerializer(serializers.Serializer):
    """
    Serializer para resumo de notificações
    """
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    notifications_today = serializers.IntegerField()
    notifications_this_week = serializers.IntegerField()
    
    by_type = serializers.DictField()
    by_channel = serializers.DictField()
    by_status = serializers.DictField()
    
    recent_notifications = NotificationSerializer(many=True)


class NotificationBulkActionSerializer(serializers.Serializer):
    """
    Serializer para ações em lote
    """
    ACTION_CHOICES = [
        ('mark_read', _('Marcar como lida')),
        ('mark_unread', _('Marcar como não lida')),
        ('delete', _('Excluir')),
    ]
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text=_("Lista de IDs das notificações")
    )
    action = serializers.ChoiceField(
        choices=ACTION_CHOICES,
        help_text=_("Ação a ser executada")
    )
    
    def validate_notification_ids(self, value):
        """Valida se as notificações existem"""
        existing_ids = set(
            Notification.objects.filter(id__in=value).values_list('id', flat=True)
        )
        provided_ids = set(value)
        
        if not existing_ids:
            raise serializers.ValidationError(
                "Nenhuma notificação válida foi encontrada"
            )
        
        if provided_ids != existing_ids:
            invalid_ids = provided_ids - existing_ids
            raise serializers.ValidationError(
                f"IDs inválidos: {list(invalid_ids)}"
            )
        
        return value


class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas de notificações
    """
    period = serializers.CharField()
    total_sent = serializers.IntegerField()
    total_delivered = serializers.IntegerField()
    total_read = serializers.IntegerField()
    total_failed = serializers.IntegerField()
    
    delivery_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    read_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    popular_types = serializers.DictField()
    channel_performance = serializers.DictField()
    daily_breakdown = serializers.DictField() 