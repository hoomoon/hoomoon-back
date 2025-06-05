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
        ordering = ['min_value']


class Deposit(models.Model):
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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits', verbose_name=_("User"))
    plan = models.ForeignKey(
        Plan, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='deposits_intended_for',
        verbose_name=_("Intended Plan (optional)")
    )
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, verbose_name=_("Payment Method"))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Amount"))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name=_("Status"))
    
    coinpayments_txn_id = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name=_("CoinPayments TXN ID"))
    payment_address = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("Payment Address (USDT)"))
    qrcode_url = models.URLField(blank=True, null=True, verbose_name=_("QR Code URL (CoinPayments)"))
    status_url = models.URLField(blank=True, null=True, verbose_name=_("Status URL (CoinPayments)"))
    
    pix_qr_code_payload = models.TextField(blank=True, null=True, verbose_name=_("PIX QR Code Payload (Copia e Cola)"))
    pix_qr_code_image_url = models.URLField(blank=True, null=True, verbose_name=_("PIX QR Code Image URL"))
    pix_key = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("PIX Key"))
    pix_key_type = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("PIX Key Type"))
    pix_beneficiary_name = models.CharField(max_length=150, blank=True, null=True, verbose_name=_("PIX Beneficiary Name"))

    transaction_hash = models.CharField(max_length=255, blank=True, verbose_name=_("Transaction Hash/ID"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def __str__(self):
        return f"{self.user.username if self.user else 'N/A'} – {self.get_method_display()} {self.amount} ({self.get_status_display()})"

    class Meta:
        verbose_name = _("Deposit")
        verbose_name_plural = _("Deposits")
        ordering = ['-created_at']


class Investment(models.Model):
    STATUS_CHOICES = (
        ('PENDING_PAYMENT', _('Pending Payment')),
        ('ACTIVE', _('Active')), 
        ('YIELDING', _('Yielding')), 
        ('EXPIRED', _('Expired')), 
        ('CANCELLED', _('Cancelled')),
        ('COMPLETED', _('Completed'))
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments', verbose_name=_("User"))
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='investments', verbose_name=_("Plan"))
    deposit_source = models.OneToOneField(
        Deposit, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='activated_investment',
        verbose_name=_("Source Deposit (optional)")
    )
    
    code = models.CharField(max_length=20, unique=True, blank=True, verbose_name=_("Activation Code"))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Invested Amount"))
    
    start_date = models.DateTimeField(default=timezone.now, verbose_name=_("Start Date/Time"))
    next_yield_date = models.DateField(null=True, blank=True, verbose_name=_("Next Yield Date"))
    expiration_date = models.DateField(verbose_name=_("Expiration Date"))
    
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_("Progress Percentage"))
    total_yielded = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total Yielded Amount"))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name=_("Status"))

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"INV-{get_random_string(10).upper()}"
            while Investment.objects.filter(code=self.code).exists():
                self.code = f"INV-{get_random_string(10).upper()}"
        
        if self.plan and self.start_date:
            if not self.expiration_date:
                self.expiration_date = (self.start_date + timezone.timedelta(days=self.plan.duration_days)).date()
            
            if not self.next_yield_date and self.plan.daily_percent > 0:
                self.next_yield_date = (self.start_date + timezone.timedelta(days=1)).date()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} ({self.user.username if self.user else 'N/A'} - {self.plan.name})"

    class Meta:
        verbose_name = _("Investment")
        verbose_name_plural = _("Investments")
        ordering = ['-start_date']


class Earning(models.Model):
    EARNING_TYPES = (
        ('YIELD', _('Yield')), 
        ('REFERRAL', _('Referral Bonus')),
        ('BONUS', _('Bonus')), 
        ('CASHBACK', _('Cashback')),
        ('REFUND', _('Refund')),
    )
    STATUS_CHOICES = (
        ('PENDING', _('Pending')), 
        ('CONFIRMED', _('Confirmed')),
        ('CANCELLED', _('Cancelled')),
        ('AVAILABLE', _('Available for Withdrawal')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earnings', verbose_name=_("User"))
    investment_source = models.ForeignKey(
        Investment, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='generated_earnings',
        verbose_name=_("Source Investment (optional)")
    )
    type = models.CharField(max_length=20, choices=EARNING_TYPES, verbose_name=_("Earning Type"))
    origin = models.CharField(max_length=100, verbose_name=_("Origin Description"))
    description = models.TextField(blank=True, verbose_name=_("Detailed Description"))
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Amount"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name=_("Status"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    effective_date = models.DateTimeField(default=timezone.now, verbose_name=_("Effective/Credited Date"))

    def __str__(self):
        return f"{self.get_type_display()} – {self.user.username if self.user else 'N/A'} – {self.amount} ({self.get_status_display()})"

    class Meta:
        verbose_name = _("Earning")
        verbose_name_plural = _("Earnings")
        ordering = ['-created_at']


class OnchainTransaction(models.Model):
    TYPE_CHOICES = (
        ('TRANSFER', _('Token transfer')), 
        ('CONTRACT', _('Contract call')),
        ('WITHDRAWAL', _('Withdrawal')),
    )
    STATUS_CHOICES = (
        ('PENDING', _('Pending')),
        ('SUCCESS', _('Success')), 
        ('FAILURE', _('Failure')),
        ('PROCESSING', _('Processing')),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='onchain_txs', verbose_name=_("User"))
    tx_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_("Transaction Type"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name=_("Status"))
    tx_hash = models.CharField(max_length=100, unique=True, verbose_name=_("Transaction Hash"))
    value = models.CharField(max_length=50, verbose_name=_("Value"))
    fee = models.CharField(max_length=50, blank=True, verbose_name=_("Fee"))
    timestamp = models.DateTimeField(default=timezone.now, verbose_name=_("Timestamp"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    def __str__(self):
        return f"{self.tx_hash} ({self.get_status_display()})"
    

    class Meta:
        verbose_name = _("Onchain Transaction")
        verbose_name_plural = _("Onchain Transactions")
        ordering = ['-timestamp']