# core/models.py
"""
Modelos abstratos base para reutilização em todo o sistema
Estes modelos fornecem funcionalidades comuns que podem ser herdadas por outros apps
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.crypto import get_random_string
from django.conf import settings


class TimestampedModel(models.Model):
    """
    Modelo abstrato que adiciona campos de timestamp a qualquer modelo
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    
    class Meta:
        abstract = True


class StatusModelMixin(models.Model):
    """
    Mixin que adiciona campo de status genérico
    """
    STATUS_CHOICES = (
        ('ACTIVE', _('Active')),
        ('INACTIVE', _('Inactive')),
        ('PENDING', _('Pending')),
        ('CANCELLED', _('Cancelled')),
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE',
        verbose_name=_("Status")
    )
    
    class Meta:
        abstract = True


class MoneyFieldMixin(models.Model):
    """
    Mixin para campos monetários padronizados
    """
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name=_("Amount")
    )
    
    class Meta:
        abstract = True


class FeatureFlagModel(models.Model):
    """
    Modelo para controlar feature flags via banco de dados
    Complementa as configurações via environment variables
    """
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Feature Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    is_enabled = models.BooleanField(default=False, verbose_name=_("Is Enabled"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({'Enabled' if self.is_enabled else 'Disabled'})"
    
    class Meta:
        verbose_name = _("Feature Flag")
        verbose_name_plural = _("Feature Flags")
        ordering = ['name']
