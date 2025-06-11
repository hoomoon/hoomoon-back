from django.db import models
from django.contrib.auth import get_user_model  
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import json

User = get_user_model()

class AuditEventType(models.TextChoices):
    """Tipos de eventos de auditoria"""
    CREATE = 'CREATE', 'Criação'
    UPDATE = 'UPDATE', 'Atualização'
    DELETE = 'DELETE', 'Exclusão'
    LOGIN = 'LOGIN', 'Login'
    LOGOUT = 'LOGOUT', 'Logout'
    PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'Alteração de Senha'
    PERMISSION_CHANGE = 'PERMISSION_CHANGE', 'Alteração de Permissão'
    DEPOSIT = 'DEPOSIT', 'Depósito'
    WITHDRAWAL = 'WITHDRAWAL', 'Saque'
    INVESTMENT = 'INVESTMENT', 'Investimento'
    PAYMENT = 'PAYMENT', 'Pagamento'
    REFERRAL = 'REFERRAL', 'Indicação'
    NOTIFICATION = 'NOTIFICATION', 'Notificação'
    CONFIG_CHANGE = 'CONFIG_CHANGE', 'Alteração de Configuração'
    SECURITY_EVENT = 'SECURITY_EVENT', 'Evento de Segurança'

class AuditSeverity(models.TextChoices):
    """Níveis de severidade dos eventos"""
    LOW = 'LOW', 'Baixa'
    MEDIUM = 'MEDIUM', 'Média'
    HIGH = 'HIGH', 'Alta'
    CRITICAL = 'CRITICAL', 'Crítica'

class AuditLog(models.Model):
    """Log principal de auditoria"""
    
    # Identificação do evento
    event_type = models.CharField(
        max_length=50,
        choices=AuditEventType.choices,
        verbose_name='Tipo de Evento'
    )
    severity = models.CharField(
        max_length=20,
        choices=AuditSeverity.choices,
        default=AuditSeverity.MEDIUM,
        verbose_name='Severidade'
    )
    
    # Usuário responsável
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Usuário'
    )
    
    # Informações da sessão
    session_key = models.CharField(max_length=40, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # Objeto afetado (usando Generic Foreign Key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Detalhes do evento
    description = models.TextField(verbose_name='Descrição')
    details = models.JSONField(default=dict, blank=True, verbose_name='Detalhes')
    
    # Dados antes e depois (para updates)
    old_values = models.JSONField(default=dict, blank=True, verbose_name='Valores Anteriores')
    new_values = models.JSONField(default=dict, blank=True, verbose_name='Novos Valores')
    
    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now, verbose_name='Data/Hora')
    
    # Metadados adicionais
    module = models.CharField(max_length=100, null=True, blank=True, verbose_name='Módulo')
    action = models.CharField(max_length=100, null=True, blank=True, verbose_name='Ação')
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['event_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.user} - {self.timestamp}"
    
    def save(self, *args, **kwargs):
        # Garantir que detalhes sensíveis não sejam armazenados
        if self.details:
            self.details = self._sanitize_data(self.details)
        if self.old_values:
            self.old_values = self._sanitize_data(self.old_values)
        if self.new_values:
            self.new_values = self._sanitize_data(self.new_values)
        super().save(*args, **kwargs)
    
    def _sanitize_data(self, data):
        """Remove dados sensíveis dos logs"""
        sensitive_fields = ['password', 'token', 'secret', 'key', 'private_key']
        if isinstance(data, dict):
            return {k: '***MASKED***' if any(field in k.lower() for field in sensitive_fields) else v 
                   for k, v in data.items()}
        return data

class SecurityEvent(models.Model):
    """Eventos específicos de segurança"""
    
    SECURITY_EVENT_TYPES = [
        ('FAILED_LOGIN', 'Tentativa de Login Falhou'),
        ('BRUTE_FORCE', 'Tentativa de Força Bruta'),
        ('SUSPICIOUS_ACTIVITY', 'Atividade Suspeita'),
        ('UNAUTHORIZED_ACCESS', 'Acesso não Autorizado'),
        ('DATA_BREACH_ATTEMPT', 'Tentativa de Violação de Dados'),
        ('SQL_INJECTION', 'Tentativa de SQL Injection'),
        ('XSS_ATTEMPT', 'Tentativa de XSS'),
        ('CSRF_ATTACK', 'Ataque CSRF'),
        ('RATE_LIMIT_EXCEEDED', 'Limite de Taxa Excedido'),
        ('IP_BLOCKED', 'IP Bloqueado'),
    ]
    
    event_type = models.CharField(max_length=50, choices=SECURITY_EVENT_TYPES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.TextField()
    additional_data = models.JSONField(default=dict, blank=True)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='resolved_security_events'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Evento de Segurança'
        verbose_name_plural = 'Eventos de Segurança'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.event_type} - {self.ip_address} - {self.timestamp}"

class DataChangeHistory(models.Model):
    """Histórico detalhado de mudanças em dados críticos"""
    
    # Referência genérica ao objeto alterado
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Detalhes da mudança
    field_name = models.CharField(max_length=100, verbose_name='Campo')
    old_value = models.TextField(null=True, blank=True, verbose_name='Valor Anterior')
    new_value = models.TextField(null=True, blank=True, verbose_name='Novo Valor')
    
    # Metadados
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Alterado por')
    timestamp = models.DateTimeField(default=timezone.now, verbose_name='Data/Hora')
    audit_log = models.ForeignKey(
        AuditLog, 
        on_delete=models.CASCADE, 
        related_name='data_changes',
        verbose_name='Log de Auditoria'
    )
    
    class Meta:
        verbose_name = 'Histórico de Mudança de Dados'
        verbose_name_plural = 'Histórico de Mudanças de Dados'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.field_name}: {self.old_value} → {self.new_value}"

class AuditSettings(models.Model):
    """Configurações do sistema de auditoria"""
    
    # Configurações de retenção
    retention_days = models.PositiveIntegerField(
        default=365,
        verbose_name='Dias de Retenção'
    )
    
    # Configurações de alertas
    enable_email_alerts = models.BooleanField(default=True)
    alert_email = models.EmailField(null=True, blank=True)
    
    # Configurações de monitoramento
    monitor_failed_logins = models.BooleanField(default=True)
    max_failed_logins = models.PositiveIntegerField(default=5)
    monitor_high_value_transactions = models.BooleanField(default=True)
    high_value_threshold = models.DecimalField(max_digits=15, decimal_places=2, default=10000)
    
    # Configurações de logging
    log_read_operations = models.BooleanField(default=False)
    log_api_calls = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração de Auditoria'
        verbose_name_plural = 'Configurações de Auditoria'
    
    def save(self, *args, **kwargs):
        # Garantir que existe apenas uma instância de configuração
        if not self.pk and AuditSettings.objects.exists():
            raise ValueError('Só pode existir uma configuração de auditoria')
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Retorna as configurações de auditoria (singleton)"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
