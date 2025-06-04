# api/models.py

from django.db import models
from django.db.models import Q, UniqueConstraint
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.utils.crypto import get_random_string


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email obrigatório")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not extra_fields['is_staff'] or not extra_fields['is_superuser']:
            raise ValueError('Superuser precisa ter is_staff e is_superuser True.')
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractUser):
    username = None
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    cpf = models.CharField(max_length=14, blank=True)
    referral_code = models.CharField(max_length=20, unique=True)
    sponsor = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def save(self, *args, **kwargs):
        if not self.referral_code:
            code = None
            while not code or User.objects.filter(referral_code=code).exists():
                code = f"HOO-{get_random_string(8).upper()}"
            self.referral_code = code
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['cpf'],
                condition=~Q(cpf=''),
                name='unique_non_empty_cpf'
            ),
        ]


class Plan(models.Model):
    PLAN_TAGS = (('FREE', 'Free'), ('DIAMOND', 'Diamond'), ('IMPERIAL', 'Imperial'))
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
    METHOD_CHOICES = (('USDT', 'USDT – BEP20'), ('PIX', 'PIX'))
    STATUS_CHOICES = (('PENDING', 'Pending'), ('PAID', 'Paid'), ('CONFIRMED', 'Confirmed'), ('FAILED', 'Failed'))

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    coinpayments_txn_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    payment_address = models.CharField(max_length=150, blank=True, null=True)
    qrcode_url = models.URLField(blank=True, null=True)
    status_url = models.URLField(blank=True, null=True)
    transaction_hash = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} – {self.method} {self.amount}"


class Investment(models.Model):
    STATUS_CHOICES = (('ACTIVE', 'Active'), ('EXPIRED', 'Expired'), ('CANCELLED', 'Cancelled'))

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
        return f"{self.code} ({self.user.email})"


class Earning(models.Model):
    EARNING_TYPES = (
        ('YIELD', 'Rendimento'), ('REFERRAL', 'Indicação'),
        ('BONUS', 'Bônus'), ('CASHBACK', 'Cashback'),
        ('REFUND', 'Estorno'),
    )
    STATUS_CHOICES = (('PENDING', 'Pendente'), ('CONFIRMED', 'Confirmado'), ('CANCELLED', 'Cancelado'))

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earnings')
    type = models.CharField(max_length=10, choices=EARNING_TYPES)
    origin = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_display()} – {self.amount}"


class OnchainTransaction(models.Model):
    TYPE_CHOICES = (('TRANSFER', 'Token transfer'), ('CONTRACT', 'Contract call'))
    STATUS_CHOICES = (('SUCCESS', 'Success'), ('FAILURE', 'Failure'))

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onchain_txs')
    tx_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    tx_hash = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=50)
    fee = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.tx_hash} ({self.get_status_display()})"
