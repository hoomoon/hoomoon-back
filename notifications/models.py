"""
Modelos para sistema de notificações
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from core.models import TimestampedModel, StatusModelMixin


class NotificationTemplate(TimestampedModel, StatusModelMixin):
    """
    Templates de notificação reutilizáveis
    """
    NOTIFICATION_TYPES = [
        ('DEPOSIT', _('Depósito')),
        ('INVESTMENT', _('Investimento')),
        ('EARNING', _('Ganho')),
        ('WITHDRAWAL', _('Saque')),
        ('REFERRAL', _('Indicação')),
        ('SYSTEM', _('Sistema')),
        ('SECURITY', _('Segurança')),
        ('PROMOTION', _('Promoção')),
        ('WELCOME', _('Bem-vindo')),
        ('KYC', _('Verificação KYC'))
    ]
    
    CHANNEL_TYPES = [
        ('EMAIL', _('Email')),
        ('SMS', _('SMS')),
        ('PUSH', _('Push Notification')),
        ('IN_APP', _('Notificação no App'))
    ]
    
    name = models.CharField(max_length=100, verbose_name=_("Nome do Template"))
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES, 
        verbose_name=_("Tipo de Notificação")
    )
    channel = models.CharField(
        max_length=10, 
        choices=CHANNEL_TYPES, 
        verbose_name=_("Canal de Notificação")
    )
    
    # Conteúdo do template
    subject = models.CharField(max_length=200, verbose_name=_("Assunto/Título"))
    content = models.TextField(verbose_name=_("Conteúdo da Mensagem"))
    html_content = models.TextField(blank=True, verbose_name=_("Conteúdo HTML (para email)"))
    
    # Configurações
    is_default = models.BooleanField(default=False, verbose_name=_("Template Padrão"))
    variables = models.JSONField(
        default=list, 
        blank=True,
        help_text=_("Lista de variáveis disponíveis no template"),
        verbose_name=_("Variáveis")
    )
    
    class Meta:
        verbose_name = _("Template de Notificação")
        verbose_name_plural = _("Templates de Notificação")
        unique_together = ['notification_type', 'channel', 'is_default']
        ordering = ['notification_type', 'channel']

    def __str__(self):
        return f"{self.name} ({self.get_notification_type_display()} - {self.get_channel_display()})"


class Notification(TimestampedModel, StatusModelMixin):
    """
    Notificações enviadas aos usuários
    """
    STATUS_CHOICES = [
        ('PENDING', _('Pendente')),
        ('SENT', _('Enviada')),
        ('DELIVERED', _('Entregue')),
        ('READ', _('Lida')),
        ('FAILED', _('Falhou')),
        ('CANCELLED', _('Cancelada'))
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name=_("Usuário")
    )
    template = models.ForeignKey(
        NotificationTemplate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Template Usado")
    )
    
    # Identificação
    notification_type = models.CharField(
        max_length=20, 
        choices=NotificationTemplate.NOTIFICATION_TYPES, 
        verbose_name=_("Tipo de Notificação")
    )
    channel = models.CharField(
        max_length=10, 
        choices=NotificationTemplate.CHANNEL_TYPES, 
        verbose_name=_("Canal")
    )
    
    # Conteúdo final (após processamento do template)
    subject = models.CharField(max_length=200, verbose_name=_("Assunto/Título"))
    content = models.TextField(verbose_name=_("Conteúdo"))
    html_content = models.TextField(blank=True, verbose_name=_("Conteúdo HTML"))
    
    # Status e timestamps
    notification_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING', 
        verbose_name=_("Status da Notificação")
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Enviada em"))
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Entregue em"))
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Lida em"))
    
    # Dados extras
    recipient_info = models.JSONField(
        default=dict, 
        blank=True,
        help_text=_("Email, telefone, ou dados do destinatário"),
        verbose_name=_("Info do Destinatário")
    )
    variables_used = models.JSONField(
        default=dict, 
        blank=True,
        help_text=_("Variáveis usadas no processamento do template"),
        verbose_name=_("Variáveis Usadas")
    )
    error_message = models.TextField(
        blank=True, 
        verbose_name=_("Mensagem de Erro")
    )
    
    # Para notificações in-app
    action_url = models.URLField(blank=True, verbose_name=_("URL da Ação"))
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Expira em"))
    
    class Meta:
        verbose_name = _("Notificação")
        verbose_name_plural = _("Notificações")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'notification_status']),
            models.Index(fields=['notification_type', 'channel']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()} ({self.get_notification_status_display()})"
    
    def mark_as_read(self):
        """Marca a notificação como lida"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.notification_status = 'READ'
            self.save(update_fields=['read_at', 'notification_status'])
    
    def mark_as_sent(self):
        """Marca a notificação como enviada"""
        self.sent_at = timezone.now()
        self.notification_status = 'SENT'
        self.save(update_fields=['sent_at', 'notification_status'])
    
    def mark_as_delivered(self):
        """Marca a notificação como entregue"""
        self.delivered_at = timezone.now()
        self.notification_status = 'DELIVERED'
        self.save(update_fields=['delivered_at', 'notification_status'])
    
    def mark_as_failed(self, error_message=""):
        """Marca a notificação como falha"""
        self.notification_status = 'FAILED'
        self.error_message = error_message
        self.save(update_fields=['notification_status', 'error_message'])
    
    def is_read(self):
        """Verifica se a notificação foi lida"""
        return self.read_at is not None
    
    def is_expired(self):
        """Verifica se a notificação expirou"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


# Função helper para evitar problemas com default=dict
def get_default_notification_types():
    return {}

def get_default_list():
    return []

def get_default_dict():
    return {}


class NotificationPreference(TimestampedModel):
    """
    Preferências de notificação do usuário
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notification_preferences',
        verbose_name=_("Usuário")
    )
    
    # Preferências por tipo de notificação
    email_enabled = models.BooleanField(default=True, verbose_name=_("Email Habilitado"))
    sms_enabled = models.BooleanField(default=False, verbose_name=_("SMS Habilitado"))
    push_enabled = models.BooleanField(default=True, verbose_name=_("Push Notifications Habilitadas"))
    in_app_enabled = models.BooleanField(default=True, verbose_name=_("Notificações In-App Habilitadas"))
    
    # Preferências específicas por tipo
    notification_types = models.JSONField(
        default=get_default_notification_types,
        blank=True,
        help_text=_("Configurações específicas por tipo de notificação"),
        verbose_name=_("Configurações por Tipo")
    )
    
    # Configurações de horário
    quiet_hours_start = models.TimeField(
        null=True, 
        blank=True,
        help_text=_("Início do período de silêncio"),
        verbose_name=_("Início do Silêncio")
    )
    quiet_hours_end = models.TimeField(
        null=True, 
        blank=True,
        help_text=_("Fim do período de silêncio"),
        verbose_name=_("Fim do Silêncio")
    )
    
    # Frequência
    digest_frequency = models.CharField(
        max_length=10,
        choices=[
            ('IMMEDIATE', _('Imediato')),
            ('HOURLY', _('A cada hora')),
            ('DAILY', _('Diário')),
            ('WEEKLY', _('Semanal')),
            ('NEVER', _('Nunca'))
        ],
        default='IMMEDIATE',
        verbose_name=_("Frequência do Resumo")
    )
    
    class Meta:
        verbose_name = _("Preferência de Notificação")
        verbose_name_plural = _("Preferências de Notificação")

    def __str__(self):
        return f"Preferências de {self.user.username}"
    
    def is_channel_enabled(self, channel):
        """Verifica se um canal está habilitado"""
        channel_map = {
            'EMAIL': self.email_enabled,
            'SMS': self.sms_enabled,
            'PUSH': self.push_enabled,
            'IN_APP': self.in_app_enabled
        }
        return channel_map.get(channel, False)
    
    def is_type_enabled(self, notification_type, channel):
        """Verifica se um tipo específico está habilitado"""
        if not self.is_channel_enabled(channel):
            return False
            
        type_config = self.notification_types.get(notification_type, {})
        return type_config.get(channel.lower(), True)  # Default True se não especificado
