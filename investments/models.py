"""
Modelos de investimento modularizados
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils.crypto import get_random_string

from core.models import TimestampedModel, StatusModelMixin, MoneyFieldMixin


class Plan(TimestampedModel, StatusModelMixin):
    """
    Planos de investimento disponíveis no sistema
    """
    HOO_FREE = "FREE"
    HOO_PANDORA = "PANDORA"
    HOO_TITAN = "TITAN"
    HOO_CALLISTO = "CALLISTO"

    PLAN_IDS = [
        (HOO_FREE, _("Hoo Free")),
        (HOO_PANDORA, _("Hoo Pandora")),
        (HOO_TITAN, _("Hoo Titan")),
        (HOO_CALLISTO, _("Hoo Callisto")),
    ]
    
    id = models.CharField(
        max_length=20, 
        primary_key=True, 
        choices=PLAN_IDS, 
        verbose_name=_("Plan ID")
    )
    name = models.CharField(max_length=100, verbose_name=_("Plan Name"))
    image_src = models.CharField(max_length=255, blank=True, verbose_name=_("Image Source URL"))
    color = models.CharField(max_length=7, default="#FFFFFF", verbose_name=_("Color Hex Code (e.g., #RRGGBB)"))
    min_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name=_("Minimum Investment Value")
    )
    tag = models.CharField(max_length=50, blank=True, verbose_name=_("Tag (e.g., Popular, Premium)"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    daily_percent = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_("Daily Yield Percentage"))
    duration_days = models.PositiveIntegerField(verbose_name=_("Duration in Days"))
    cap_percent = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_("Yield Cap Percentage"))
    withdrawal_policy = models.CharField(
        max_length=100, 
        blank=True,
        help_text=_("Descreva a política de saque. Ex: 'Saques diários', 'Saques semanais', etc."),
        verbose_name=_("Política de Saque")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Investment Plan")
        verbose_name_plural = _("Investment Plans")
        ordering = ['min_value']


class Investment(TimestampedModel, MoneyFieldMixin, StatusModelMixin):
    """
    Investimentos ativos dos usuários
    """
    INVESTMENT_STATUS_CHOICES = (
        ('PENDING_PAYMENT', _('Pending Payment')),
        ('ACTIVE', _('Active')), 
        ('YIELDING', _('Yielding')), 
        ('EXPIRED', _('Expired')), 
        ('CANCELLED', _('Cancelled')),
        ('COMPLETED', _('Completed'))
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='investments', 
        verbose_name=_("User")
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='investments', verbose_name=_("Plan"))
    deposit_source = models.OneToOneField(
        'payments.Deposit', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='activated_investment',
        verbose_name=_("Source Deposit (optional)")
    )
    
    code = models.CharField(max_length=20, unique=True, blank=True, verbose_name=_("Activation Code"))
    # amount herdado de MoneyFieldMixin
    
    start_date = models.DateTimeField(default=timezone.now, verbose_name=_("Start Date/Time"))
    next_yield_date = models.DateField(null=True, blank=True, verbose_name=_("Next Yield Date"))
    expiration_date = models.DateField(verbose_name=_("Expiration Date"))
    
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_("Progress Percentage"))
    total_yielded = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total Yielded Amount"))
    
    # status herdado de StatusModelMixin, mas vamos sobrescrever as choices
    investment_status = models.CharField(
        max_length=20, 
        choices=INVESTMENT_STATUS_CHOICES, 
        default='ACTIVE', 
        verbose_name=_("Investment Status")
    )

    def save(self, *args, **kwargs):
        """
        Gera código de ativação automaticamente e calcula data de expiração
        """
        if not self.code:
            # Gerar código único
            code = None
            while not code or Investment.objects.filter(code=code).exists():
                code = f"INV-{get_random_string(8).upper()}"
            self.code = code
        
        if not self.expiration_date and self.plan:
            # Calcular data de expiração baseada na duração do plano
            from datetime import timedelta
            self.expiration_date = (self.start_date + timedelta(days=self.plan.duration_days)).date()
        
        super().save(*args, **kwargs)

    def get_days_remaining(self):
        """Retorna quantos dias restam até a expiração"""
        if self.expiration_date:
            from datetime import date
            today = date.today()
            if self.expiration_date > today:
                return (self.expiration_date - today).days
        return 0

    def get_expected_daily_yield(self):
        """Retorna o rendimento diário esperado"""
        if self.plan:
            return self.amount * (self.plan.daily_percent / 100)
        return 0

    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'N/A'} - {self.amount}"

    class Meta:
        verbose_name = _("Investment")
        verbose_name_plural = _("Investments")
        ordering = ['-start_date']
