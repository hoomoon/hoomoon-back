"""
Modelos financeiros - Rendimentos e relatórios
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from core.models import TimestampedModel, StatusModelMixin, MoneyFieldMixin


class Earning(TimestampedModel, MoneyFieldMixin, StatusModelMixin):
    """
    Rendimentos e ganhos dos usuários
    """
    EARNING_TYPES = (
        ('YIELD', _('Yield')), 
        ('REFERRAL', _('Referral Bonus')),
        ('BONUS', _('Bonus')), 
        ('CASHBACK', _('Cashback')),
        ('REFUND', _('Refund')),
    )
    EARNING_STATUS_CHOICES = (
        ('PENDING', _('Pending')), 
        ('CONFIRMED', _('Confirmed')),
        ('CANCELLED', _('Cancelled')),
        ('AVAILABLE', _('Available for Withdrawal')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='earnings', 
        verbose_name=_("User")
    )
    investment_source = models.ForeignKey(
        'investments.Investment', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='generated_earnings',
        verbose_name=_("Source Investment (optional)")
    )
    type = models.CharField(max_length=20, choices=EARNING_TYPES, verbose_name=_("Earning Type"))
    origin = models.CharField(max_length=100, verbose_name=_("Origin Description"))
    description = models.TextField(blank=True, verbose_name=_("Detailed Description"))
    # amount herdado de MoneyFieldMixin
    earning_status = models.CharField(
        max_length=20, 
        choices=EARNING_STATUS_CHOICES, 
        default='PENDING', 
        verbose_name=_("Earning Status")
    )
    
    effective_date = models.DateTimeField(default=timezone.now, verbose_name=_("Effective/Credited Date"))

    def __str__(self):
        return f"{self.user.username} - {self.get_type_display()} - {self.amount}"

    class Meta:
        verbose_name = _("Earning")
        verbose_name_plural = _("Earnings")
        ordering = ['-created_at']


class FinancialReport(TimestampedModel):
    """
    Relatórios financeiros do sistema
    """
    REPORT_TYPES = (
        ('DAILY', _('Daily Report')),
        ('WEEKLY', _('Weekly Report')),
        ('MONTHLY', _('Monthly Report')),
        ('CUSTOM', _('Custom Period Report')),
    )
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name=_("Report Type"))
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    
    # Métricas calculadas
    total_deposits = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Total Deposits"))
    total_investments = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Total Investments"))
    total_earnings = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Total Earnings"))
    active_users = models.PositiveIntegerField(default=0, verbose_name=_("Active Users"))
    new_users = models.PositiveIntegerField(default=0, verbose_name=_("New Users"))
    
    # Dados extras em JSON
    detailed_data = models.JSONField(default=dict, blank=True, verbose_name=_("Detailed Data"))
    
    class Meta:
        verbose_name = _("Financial Report")
        verbose_name_plural = _("Financial Reports")
        ordering = ['-created_at']
        unique_together = ['report_type', 'start_date', 'end_date']

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.start_date} to {self.end_date}"
