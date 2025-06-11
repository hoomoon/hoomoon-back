"""
Modelos para sistema de indicações/referrals
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

from core.models import TimestampedModel, StatusModelMixin


class ReferralProgram(TimestampedModel, StatusModelMixin):
    """
    Programa de indicação/afiliados
    """
    name = models.CharField(max_length=100, verbose_name=_("Nome do Programa"))
    description = models.TextField(blank=True, verbose_name=_("Descrição"))
    
    # Configurações de comissão
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Percentual de comissão (0-100%)"),
        verbose_name=_("Taxa de Comissão (%)")
    )
    
    # Configurações avançadas
    max_levels = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text=_("Quantos níveis de referência são permitidos"),
        verbose_name=_("Níveis Máximos")
    )
    
    # Comissões por nível (JSON)
    level_commissions = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Comissões específicas por nível {'1': 10.00, '2': 5.00}"),
        verbose_name=_("Comissões por Nível")
    )
    
    # Limites
    min_payout = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('10.00'),
        help_text=_("Valor mínimo para saque"),
        verbose_name=_("Saque Mínimo")
    )
    
    max_monthly_earnings = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Limite máximo de ganhos mensais (opcional)"),
        verbose_name=_("Limite Mensal")
    )
    
    # Configurações de período
    start_date = models.DateTimeField(verbose_name=_("Data de Início"))
    end_date = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Data de Término")
    )
    
    # Flags
    is_default = models.BooleanField(
        default=False, 
        verbose_name=_("Programa Padrão")
    )
    auto_approve = models.BooleanField(
        default=True, 
        verbose_name=_("Aprovação Automática")
    )
    
    class Meta:
        verbose_name = _("Programa de Indicação")
        verbose_name_plural = _("Programas de Indicação")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.commission_rate}%)"
    
    def is_active(self):
        """Verifica se o programa está ativo"""
        now = timezone.now()
        if not self.status:
            return False
        if now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True
    
    def get_commission_for_level(self, level):
        """Retorna a comissão para um nível específico"""
        if level > self.max_levels:
            return Decimal('0.00')
        
        # Comissão específica por nível
        if self.level_commissions:
            level_rate = self.level_commissions.get(str(level))
            if level_rate:
                return Decimal(str(level_rate))
        
        # Comissão padrão
        return self.commission_rate


class ReferralLink(TimestampedModel, StatusModelMixin):
    """
    Links de indicação únicos para cada usuário
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='referral_links',
        verbose_name=_("Usuário")
    )
    program = models.ForeignKey(
        ReferralProgram, 
        on_delete=models.CASCADE, 
        related_name='referral_links',
        verbose_name=_("Programa")
    )
    
    # Identificadores únicos
    code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name=_("Código de Indicação")
    )
    uuid = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        verbose_name=_("UUID")
    )
    
    # Métricas
    clicks = models.PositiveIntegerField(default=0, verbose_name=_("Cliques"))
    conversions = models.PositiveIntegerField(default=0, verbose_name=_("Conversões"))
    total_earnings = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name=_("Ganhos Totais")
    )
    
    # Configurações
    custom_landing_page = models.URLField(
        blank=True, 
        verbose_name=_("Página de Destino Personalizada")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notas"))
    
    class Meta:
        verbose_name = _("Link de Indicação")
        verbose_name_plural = _("Links de Indicação")
        unique_together = ['user', 'program']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.code}"
    
    def get_full_url(self):
        """Retorna URL completa do link de indicação"""
        from django.conf import settings
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return f"{base_url}/register?ref={self.code}"
    
    def track_click(self):
        """Registra um clique no link"""
        self.clicks += 1
        self.save(update_fields=['clicks'])
    
    def track_conversion(self):
        """Registra uma conversão"""
        self.conversions += 1
        self.save(update_fields=['conversions'])
    
    def get_conversion_rate(self):
        """Calcula a taxa de conversão"""
        if self.clicks == 0:
            return 0
        return (self.conversions / self.clicks) * 100


class Referral(TimestampedModel, StatusModelMixin):
    """
    Registro de indicação entre usuários
    """
    STATUS_CHOICES = [
        ('PENDING', _('Pendente')),
        ('ACTIVE', _('Ativo')),
        ('COMPLETED', _('Completado')),
        ('CANCELLED', _('Cancelado'))
    ]
    
    # Relacionamentos
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='referrals_made',
        verbose_name=_("Indicador")
    )
    referred = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='referrals_from',
        verbose_name=_("Indicado")
    )
    program = models.ForeignKey(
        ReferralProgram, 
        on_delete=models.CASCADE, 
        related_name='referrals',
        verbose_name=_("Programa")
    )
    referral_link = models.ForeignKey(
        ReferralLink, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Link Usado")
    )
    
    # Status e nível
    referral_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        verbose_name=_("Status da Indicação")
    )
    level = models.PositiveIntegerField(
        default=1,
        help_text=_("Nível da indicação (1 = direto, 2 = indireto, etc.)"),
        verbose_name=_("Nível")
    )
    
    # Dados de rastreamento
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True, 
        verbose_name=_("IP de Origem")
    )
    user_agent = models.TextField(blank=True, verbose_name=_("User Agent"))
    referrer_url = models.URLField(blank=True, verbose_name=_("URL de Origem"))
    
    # Timestamps importantes
    clicked_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Clicou em")
    )
    registered_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Registrou em")
    )
    first_purchase_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Primeira Compra em")
    )
    
    class Meta:
        verbose_name = _("Indicação")
        verbose_name_plural = _("Indicações")
        unique_together = ['referrer', 'referred']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['referrer', 'referral_status']),
            models.Index(fields=['referred', 'referral_status']),
            models.Index(fields=['program', 'level']),
        ]

    def __str__(self):
        return f"{self.referrer.username} → {self.referred.username}"
    
    def mark_as_active(self):
        """Marca a indicação como ativa"""
        self.referral_status = 'ACTIVE'
        self.registered_at = timezone.now()
        self.save(update_fields=['referral_status', 'registered_at'])
    
    def mark_first_purchase(self):
        """Marca a primeira compra do indicado"""
        if not self.first_purchase_at:
            self.first_purchase_at = timezone.now()
            self.referral_status = 'COMPLETED'
            self.save(update_fields=['first_purchase_at', 'referral_status'])


class ReferralEarning(TimestampedModel, StatusModelMixin):
    """
    Ganhos por indicação
    """
    STATUS_CHOICES = [
        ('PENDING', _('Pendente')),
        ('APPROVED', _('Aprovado')),
        ('PAID', _('Pago')),
        ('CANCELLED', _('Cancelado'))
    ]
    
    # Relacionamentos
    referral = models.ForeignKey(
        Referral, 
        on_delete=models.CASCADE, 
        related_name='earnings',
        verbose_name=_("Indicação")
    )
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='referral_earnings',
        verbose_name=_("Indicador")
    )
    
    # Origem do ganho
    source_type = models.CharField(
        max_length=20,
        choices=[
            ('DEPOSIT', _('Depósito')),
            ('INVESTMENT', _('Investimento')),
            ('EARNING', _('Rendimento')),
            ('SIGNUP_BONUS', _('Bônus de Cadastro')),
            ('MILESTONE', _('Marco Alcançado'))
        ],
        verbose_name=_("Tipo de Origem")
    )
    source_id = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text=_("ID do objeto que gerou o ganho"),
        verbose_name=_("ID da Origem")
    )
    
    # Valores
    original_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text=_("Valor original que gerou a comissão"),
        verbose_name=_("Valor Original")
    )
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text=_("Taxa de comissão aplicada"),
        verbose_name=_("Taxa de Comissão (%)")
    )
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name=_("Valor da Comissão")
    )
    
    # Status
    earning_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        verbose_name=_("Status do Ganho")
    )
    
    # Datas importantes
    earned_at = models.DateTimeField(
        default=timezone.now, 
        verbose_name=_("Ganho em")
    )
    approved_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Aprovado em")
    )
    paid_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Pago em")
    )
    
    # Informações adicionais
    description = models.TextField(blank=True, verbose_name=_("Descrição"))
    admin_notes = models.TextField(blank=True, verbose_name=_("Notas do Admin"))
    
    class Meta:
        verbose_name = _("Ganho por Indicação")
        verbose_name_plural = _("Ganhos por Indicação")
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['referrer', 'earning_status']),
            models.Index(fields=['source_type', 'source_id']),
            models.Index(fields=['earned_at']),
        ]

    def __str__(self):
        return f"{self.referrer.username} - R$ {self.amount} ({self.get_earning_status_display()})"
    
    def approve(self):
        """Aprova o ganho"""
        self.earning_status = 'APPROVED'
        self.approved_at = timezone.now()
        self.save(update_fields=['earning_status', 'approved_at'])
    
    def mark_as_paid(self):
        """Marca como pago"""
        self.earning_status = 'PAID'
        self.paid_at = timezone.now()
        self.save(update_fields=['earning_status', 'paid_at'])
    
    def cancel(self, reason=""):
        """Cancela o ganho"""
        self.earning_status = 'CANCELLED'
        if reason:
            self.admin_notes = reason
        self.save(update_fields=['earning_status', 'admin_notes'])
