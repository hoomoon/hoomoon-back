# api/models.py

from django.db import models
from django.db.models import Q, UniqueConstraint
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, username, name, password=None, email=None, **extra_fields):
        if not username:
            raise ValueError("O nome de usuário (username) é obrigatório")
        if not name:
            raise ValueError("O nome é obrigatório")
        if email:
            email = self.normalize_email(email)

        user = self.model(username=username, name=name, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, name, password=None, email=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser precisa ter is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser precisa ter is_superuser=True.')
        
        return self.create_user(username, name, password, email, **extra_fields)


class User(AbstractUser):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    referral_code = models.CharField(max_length=20, unique=True)
    sponsor = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Saldo Disponível")

    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name', 'email']

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
    
    def __str__(self):
        return self.username


class Plan(models.Model):
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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Investment Plan")
        verbose_name_plural = _("Investment Plans")


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
