"""
Modelos de pagamento e transações
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from core.models import TimestampedModel, StatusModelMixin, MoneyFieldMixin


class Deposit(TimestampedModel, MoneyFieldMixin):
    """
    Depósitos realizados pelos usuários
    """
    METHOD_CHOICES = (
        ('USDT_BEP20', _('USDT (BEP20)')),
        ('PIX', _('PIX')),
    )
    STATUS_CHOICES = (
        ('PENDING', _('Pending')), 
        ('PAID', _('Paid')), 
        ('CONFIRMED', _('Confirmed')), 
        ('FAILED', _('Failed')),
        ('EXPIRED', _('Expired')),
    )
    
    connectpay_transaction_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        unique=True,
        verbose_name=_("ConnectPay Transaction ID")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='deposits', 
        verbose_name=_("User")
    )
    plan = models.ForeignKey(
        'investments.Plan', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='deposits_intended_for',
        verbose_name=_("Intended Plan (optional)")
    )
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, verbose_name=_("Payment Method"))
    # amount herdado de MoneyFieldMixin
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name=_("Status"))
    
    # Campos específicos para CoinPayments
    coinpayments_txn_id = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name=_("CoinPayments TXN ID"))
    payment_address = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Payment Address (USDT)"))
    qrcode_url = models.URLField(blank=True, null=True, verbose_name=_("QR Code URL (CoinPayments)"))
    status_url = models.URLField(blank=True, null=True, verbose_name=_("Status URL (CoinPayments)"))
    
    # Campos específicos para PIX
    pix_qr_code_payload = models.TextField(blank=True, null=True, verbose_name=_("PIX QR Code Payload (Copia e Cola)"))
    pix_qr_code_image_url = models.URLField(blank=True, null=True, verbose_name=_("PIX QR Code Image URL"))
    pix_key = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("PIX Key"))
    pix_key_type = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("PIX Key Type"))
    pix_beneficiary_name = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("PIX Beneficiary Name"))

    transaction_hash = models.CharField(max_length=255, blank=True, verbose_name=_("Transaction Hash/ID"))

    def __str__(self):
        return f"{self.user.username if self.user else 'N/A'} – {self.get_method_display()} {self.amount} ({self.get_status_display()})"

    class Meta:
        verbose_name = _("Deposit")
        verbose_name_plural = _("Deposits")
        ordering = ['-created_at']


class OnchainTransaction(TimestampedModel, StatusModelMixin):
    """
    Transações on-chain (blockchain)
    """
    TYPE_CHOICES = (
        ('TRANSFER', _('Token transfer')), 
        ('CONTRACT', _('Contract call')),
        ('WITHDRAWAL', _('Withdrawal')),
    )
    TRANSACTION_STATUS_CHOICES = (
        ('PENDING', _('Pending')),
        ('SUCCESS', _('Success')), 
        ('FAILURE', _('Failure')),
        ('PROCESSING', _('Processing')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='onchain_txs', 
        verbose_name=_("User")
    )
    tx_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_("Transaction Type"))
    transaction_status = models.CharField(
        max_length=20, 
        choices=TRANSACTION_STATUS_CHOICES, 
        default='PENDING', 
        verbose_name=_("Transaction Status")
    )
    tx_hash = models.CharField(max_length=100, unique=True, verbose_name=_("Transaction Hash"))
    value = models.CharField(max_length=50, verbose_name=_("Value"))
    fee = models.CharField(max_length=50, blank=True, verbose_name=_("Fee"))
    timestamp = models.DateTimeField(default=timezone.now, verbose_name=_("Timestamp"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    def __str__(self):
        return f"{self.user.username} - {self.get_tx_type_display()} - {self.tx_hash[:10]}..."

    class Meta:
        verbose_name = _("Onchain Transaction")
        verbose_name_plural = _("Onchain Transactions")
        ordering = ['-timestamp']
