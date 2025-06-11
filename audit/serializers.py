from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog, SecurityEvent, DataChangeHistory, AuditSettings

User = get_user_model()

class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de auditoria"""
    
    user_display = serializers.CharField(source='user.username', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    content_type_display = serializers.CharField(source='content_type.model', read_only=True)
    timestamp_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'timestamp_formatted', 'event_type', 'event_type_display',
            'severity', 'severity_display', 'user', 'user_display', 'session_key',
            'ip_address', 'user_agent', 'content_type', 'content_type_display',
            'object_id', 'description', 'details', 'old_values', 'new_values',
            'module', 'action'
        ]
        read_only_fields = [
            'id', 'timestamp', 'timestamp_formatted', 'event_type', 'event_type_display',
            'severity', 'severity_display', 'user', 'user_display', 'session_key',
            'ip_address', 'user_agent', 'content_type', 'content_type_display',
            'object_id', 'description', 'details', 'old_values', 'new_values',
            'module', 'action'
        ]
    
    def get_timestamp_formatted(self, obj):
        from django.utils.timezone import localtime
        return localtime(obj.timestamp).strftime('%d/%m/%Y %H:%M:%S')

class AuditLogSummarySerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de logs de auditoria"""
    
    user_display = serializers.CharField(source='user.username', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    timestamp_formatted = serializers.SerializerMethodField()
    description_short = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp', 'timestamp_formatted', 'event_type', 'event_type_display',
            'severity', 'severity_display', 'user_display', 'ip_address',
            'description_short', 'module'
        ]
        read_only_fields = [
            'id', 'timestamp', 'timestamp_formatted', 'event_type', 'event_type_display',
            'severity', 'severity_display', 'user_display', 'ip_address',
            'description_short', 'module'
        ]
    
    def get_timestamp_formatted(self, obj):
        from django.utils.timezone import localtime
        return localtime(obj.timestamp).strftime('%d/%m/%Y %H:%M:%S')
    
    def get_description_short(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description

class SecurityEventSerializer(serializers.ModelSerializer):
    """Serializer para eventos de segurança"""
    
    user_display = serializers.CharField(source='user.username', read_only=True)
    resolved_by_display = serializers.CharField(source='resolved_by.username', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    timestamp_formatted = serializers.SerializerMethodField()
    resolved_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'timestamp', 'timestamp_formatted', 'event_type', 'event_type_display',
            'ip_address', 'user_agent', 'user', 'user_display', 'description',
            'additional_data', 'resolved', 'resolved_by', 'resolved_by_display',
            'resolved_at', 'resolved_at_formatted'
        ]
        read_only_fields = [
            'timestamp', 'event_type', 'ip_address', 'user_agent', 'user',
            'description', 'additional_data'
        ]
    
    def get_timestamp_formatted(self, obj):
        from django.utils.timezone import localtime
        return localtime(obj.timestamp).strftime('%d/%m/%Y %H:%M:%S')
    
    def get_resolved_at_formatted(self, obj):
        if obj.resolved_at:
            from django.utils.timezone import localtime
            return localtime(obj.resolved_at).strftime('%d/%m/%Y %H:%M:%S')
        return None

class DataChangeHistorySerializer(serializers.ModelSerializer):
    """Serializer para histórico de mudanças de dados"""
    
    content_type_display = serializers.CharField(source='content_type.model', read_only=True)
    changed_by_display = serializers.CharField(source='changed_by.username', read_only=True)
    timestamp_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = DataChangeHistory
        fields = [
            'id', 'content_type', 'content_type_display', 'object_id', 'field_name',
            'old_value', 'new_value', 'changed_by', 'changed_by_display',
            'timestamp', 'timestamp_formatted', 'audit_log'
        ]
        read_only_fields = [
            'id', 'content_type', 'content_type_display', 'object_id', 'field_name',
            'old_value', 'new_value', 'changed_by', 'changed_by_display',
            'timestamp', 'timestamp_formatted', 'audit_log'
        ]
    
    def get_timestamp_formatted(self, obj):
        from django.utils.timezone import localtime
        return localtime(obj.timestamp).strftime('%d/%m/%Y %H:%M:%S')

class AuditSettingsSerializer(serializers.ModelSerializer):
    """Serializer para configurações de auditoria"""
    
    class Meta:
        model = AuditSettings
        fields = [
            'id', 'retention_days', 'enable_email_alerts', 'alert_email',
            'monitor_failed_logins', 'max_failed_logins',
            'monitor_high_value_transactions', 'high_value_threshold',
            'log_read_operations', 'log_api_calls', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AuditStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de auditoria"""
    
    total_events = serializers.IntegerField(read_only=True)
    events_today = serializers.IntegerField(read_only=True)
    events_this_week = serializers.IntegerField(read_only=True)
    events_this_month = serializers.IntegerField(read_only=True)
    
    security_events_total = serializers.IntegerField(read_only=True)
    security_events_unresolved = serializers.IntegerField(read_only=True)
    
    events_by_type = serializers.DictField(read_only=True)
    events_by_severity = serializers.DictField(read_only=True)
    events_by_user = serializers.DictField(read_only=True)
    
    top_users = serializers.ListField(read_only=True)
    top_ips = serializers.ListField(read_only=True)
    
    recent_critical_events = AuditLogSummarySerializer(many=True, read_only=True)
    recent_security_events = SecurityEventSerializer(many=True, read_only=True)

class AuditReportSerializer(serializers.Serializer):
    """Serializer para relatórios de auditoria"""
    
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    event_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Tipos de eventos para incluir no relatório"
    )
    users = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="IDs dos usuários para incluir no relatório"
    )
    severity_levels = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Níveis de severidade para incluir no relatório"
    )
    modules = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Módulos para incluir no relatório"
    )
    ip_addresses = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Endereços IP para incluir no relatório"
    )
    include_details = serializers.BooleanField(
        default=False,
        help_text="Incluir detalhes completos dos eventos"
    )
    format = serializers.ChoiceField(
        choices=['json', 'csv', 'pdf'],
        default='json',
        help_text="Formato do relatório"
    )

class UserActivitySummarySerializer(serializers.Serializer):
    """Serializer para resumo de atividade do usuário"""
    
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.CharField()
    
    total_events = serializers.IntegerField()
    last_activity = serializers.DateTimeField()
    last_login = serializers.DateTimeField()
    
    events_by_type = serializers.DictField()
    recent_events = AuditLogSummarySerializer(many=True)
    
    security_events = serializers.IntegerField()
    failed_logins = serializers.IntegerField()
    
    ip_addresses = serializers.ListField(child=serializers.CharField())
    
class SystemHealthSerializer(serializers.Serializer):
    """Serializer para saúde do sistema de auditoria"""
    
    status = serializers.CharField()
    total_logs = serializers.IntegerField()
    logs_today = serializers.IntegerField()
    
    oldest_log = serializers.DateTimeField()
    newest_log = serializers.DateTimeField()
    
    disk_usage_mb = serializers.FloatField()
    retention_policy_active = serializers.BooleanField()
    
    critical_events_last_24h = serializers.IntegerField()
    security_events_last_24h = serializers.IntegerField()
    unresolved_security_events = serializers.IntegerField()
    
    performance_metrics = serializers.DictField()
    
    alerts = serializers.ListField(child=serializers.CharField()) 