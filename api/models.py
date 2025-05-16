# api/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    """
    Extends Django’s built-in user to include profile and referral info.
    """
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    cpf = models.CharField(max_length=14, blank=True)  # formatted '123.456.789-00'
    referral_code = models.CharField(max_length=20, unique=True)
    sponsor = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='referrals'
    )

    def save(self, *args, **kwargs):
        # Generate a referral code if not set
        if not self.referral_code:
            self.referral_code = f"HOO-{self.username.upper()}"
        super().save(*args, **kwargs)


class Plan(models.Model):
    """
    Investment plans (FREE, DIAMOND, IMPERIAL, etc.).
    """
    PLAN_TAGS = (
        ('FREE', 'Free'),
        ('DIAMOND', 'Diamond'),
        ('IMPERIAL', 'Imperial'),
    )

    id = models.CharField(max_length=20, primary_key=True, choices=PLAN_TAGS)
    name = models.CharField(max_length=50)
    tag = models.CharField(max_length=20, blank=True)
    description = models.TextField()
    daily_percent = models.DecimalField(max_digits=5, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    cap_percent = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name


class Deposit(models.Model):
    """
    Records user deposits (USDT, PIX).
    """
    METHOD_CHOICES = (
        ('USDT', 'USDT – BEP20'),
        ('PIX', 'PIX'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('FAILED', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    transaction_hash = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} – {self.method} {self.amount}"


class Investment(models.Model):
    """
    User investments into a plan.
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='investments')
    code = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField(default=timezone.now)
    next_release = models.DateField()
    expiration_date = models.DateField()
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')

    def __str__(self):
        return f"{self.code} ({self.user.username})"


class Earning(models.Model):
    """
    Records daily yields, referral commissions, bonuses, cashback, etc.
    """
    EARNING_TYPES = (
        ('YIELD', 'Rendimento'),
        ('REFERRAL', 'Indicação'),
        ('BONUS', 'Bônus'),
        ('CASHBACK', 'Cashback'),
        ('REFUND', 'Estorno'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('CONFIRMED', 'Confirmado'),
        ('CANCELLED', 'Cancelado'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earnings')
    type = models.CharField(max_length=10, choices=EARNING_TYPES)
    origin = models.CharField(max_length=100)  # e.g. plan name or referring user
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_display()} – {self.amount}"


class OnchainTransaction(models.Model):
    """
    Tracks actual blockchain transactions (e.g., via APTUM Explorer).
    """
    TYPE_CHOICES = (
        ('TRANSFER', 'Token transfer'),
        ('CONTRACT', 'Contract call'),
    )
    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onchain_txs')
    tx_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    tx_hash = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=50)   # keep as string to preserve units
    fee = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.tx_hash} ({self.get_status_display()})"
