"""
Modelos de usuário modularizados
"""
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.crypto import get_random_string
from django.db.models import Q, UniqueConstraint
from django.conf import settings
from django.utils import timezone
from core.models import TimestampedModel, StatusModelMixin, MoneyFieldMixin


class User(AbstractUser, TimestampedModel):
    """
    Modelo de usuário estendido para o sistema de investimentos
    """
    name = models.CharField(max_length=150, verbose_name="Nome Completo")
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name="País")
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF")
    referral_code = models.CharField(max_length=20, unique=True, verbose_name="Código de Indicação")
    sponsor = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='referrals',
        verbose_name="Patrocinador"
    )
    
    # Campo de saldo
    balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Saldo Disponível"
    )
    
    # Campos de KYC (Know Your Customer)
    kyc_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pendente'),
            ('APPROVED', 'Aprovado'),
            ('REJECTED', 'Rejeitado'),
            ('REVIEW', 'Em Análise')
        ],
        default='PENDING',
        verbose_name="Status KYC"
    )
    kyc_documents = models.JSONField(default=dict, blank=True, verbose_name="Documentos KYC")
    
    # As preferências de notificação são gerenciadas pelo app notifications
    # através do modelo NotificationPreference com relacionamento OneToOne
    
    objects = UserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name', 'email']
    
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['cpf'],
                condition=~Q(cpf='') & ~Q(cpf__isnull=True),
                name='users_unique_non_empty_cpf'  # Nome único para evitar conflito
            ),
        ]
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """
        Gera código de indicação automaticamente se não existir
        """
        if not self.referral_code:
            prefix = getattr(settings, 'REFERRAL_CODE_PREFIX', 'INV')
            code = None
            while not code or User.objects.filter(referral_code=code).exists():
                code = f"{prefix}-{get_random_string(8).upper()}"
            self.referral_code = code
        super().save(*args, **kwargs)

    def get_full_name(self):
        """Retorna o nome completo do usuário"""
        return self.name

    def get_referral_stats(self):
        """Retorna estatísticas de indicação"""
        return {
            'total_referrals': self.referrals.count(),
            'active_referrals': self.referrals.filter(is_active=True).count(),
            'total_referral_earnings': self.earnings.filter(type='REFERRAL').aggregate(
                total=models.Sum('amount')
            )['total'] or 0
        }
    
    def get_investment_summary(self):
        """Retorna resumo dos investimentos"""
        from investments.models import Investment
        investments = Investment.objects.filter(user=self)
        return {
            'total_investments': investments.count(),
            'active_investments': investments.filter(status='ACTIVE').count(),
            'total_invested': investments.aggregate(total=models.Sum('amount'))['total'] or 0,
            'total_yielded': investments.aggregate(total=models.Sum('total_yielded'))['total'] or 0
        }
    
    def is_kyc_approved(self):
        """Verifica se o KYC está aprovado"""
        return self.kyc_status == 'APPROVED'

    def __str__(self):
        return self.username


class UserProfile(TimestampedModel):
    """
    Perfil estendido do usuário para informações adicionais
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Informações pessoais
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    gender = models.CharField(
        max_length=10,
        choices=[
            ('M', 'Masculino'),
            ('F', 'Feminino'),
            ('O', 'Outro'),
            ('N', 'Prefiro não informar')
        ],
        blank=True,
        verbose_name="Gênero"
    )
    profession = models.CharField(max_length=100, blank=True, verbose_name="Profissão")
    
    # Endereço
    address = models.TextField(blank=True, verbose_name="Endereço")
    city = models.CharField(max_length=100, blank=True, verbose_name="Cidade")
    state = models.CharField(max_length=100, blank=True, verbose_name="Estado")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="CEP")
    
    # Informações bancárias
    bank_name = models.CharField(max_length=100, blank=True, verbose_name="Banco")
    bank_account = models.CharField(max_length=50, blank=True, verbose_name="Conta Bancária")
    pix_key = models.CharField(max_length=255, blank=True, verbose_name="Chave PIX")
    
    # Avatar/Foto
    avatar = models.URLField(blank=True, verbose_name="URL do Avatar")
    
    # Configurações de investimento
    risk_tolerance = models.CharField(
        max_length=20,
        choices=[
            ('LOW', 'Baixo'),
            ('MODERATE', 'Moderado'),
            ('HIGH', 'Alto'),
            ('AGGRESSIVE', 'Agressivo')
        ],
        default='MODERATE',
        verbose_name="Tolerância ao Risco"
    )
    investment_experience = models.CharField(
        max_length=20,
        choices=[
            ('BEGINNER', 'Iniciante'),
            ('INTERMEDIATE', 'Intermediário'),
            ('ADVANCED', 'Avançado'),
            ('EXPERT', 'Especialista')
        ],
        default='BEGINNER',
        verbose_name="Experiência em Investimentos"
    )
    
    class Meta:
        verbose_name = "Perfil do Usuário"
        verbose_name_plural = "Perfis dos Usuários"

    def __str__(self):
        return f"Perfil de {self.user.username}"


class UserActivity(TimestampedModel):
    """
    Log de atividades do usuário
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=100, verbose_name="Ação")
    description = models.TextField(blank=True, verbose_name="Descrição")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Endereço IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="Dados Extras")
    
    class Meta:
        verbose_name = "Atividade do Usuário"
        verbose_name_plural = "Atividades dos Usuários"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.action}"


# O modelo UserNotification foi migrado para o app notifications
# como modelo Notification, que é mais completo e modular
