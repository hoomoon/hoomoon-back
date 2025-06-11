from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.contenttypes.models import ContentType

from .utils import AuditLogger, audit_login, audit_logout
from .models import AuditEventType, AuditSeverity

# Models críticos que devem ser auditados
# Será preenchido dinamicamente no ready() para evitar imports circulares
AUDITED_MODELS = {}

def register_audited_models():
    """Registra os models que devem ser auditados"""
    global AUDITED_MODELS
    
    try:
        from users.models import User
        AUDITED_MODELS[User] = {
            'sensitive_fields': ['password', 'email', 'is_active', 'is_staff', 'is_superuser'],
            'severity': AuditSeverity.HIGH
        }
    except ImportError:
        pass
    
    try:
        from investments.models import Investment, InvestmentPlan
        AUDITED_MODELS[Investment] = {
            'sensitive_fields': ['amount', 'status', 'plan'],
            'severity': AuditSeverity.HIGH
        }
        AUDITED_MODELS[InvestmentPlan] = {
            'sensitive_fields': ['name', 'min_amount', 'max_amount', 'daily_return_rate', 'is_active'],
            'severity': AuditSeverity.HIGH
        }
    except ImportError:
        pass
    
    try:
        from payments.models import Deposit, Withdrawal
        AUDITED_MODELS[Deposit] = {
            'sensitive_fields': ['amount', 'status', 'method'],
            'severity': AuditSeverity.HIGH
        }
        AUDITED_MODELS[Withdrawal] = {
            'sensitive_fields': ['amount', 'status', 'wallet_address'],
            'severity': AuditSeverity.HIGH
        }
    except ImportError:
        pass
    
    try:
        from financial.models import EarningRecord, PaymentRecord
        AUDITED_MODELS[EarningRecord] = {
            'sensitive_fields': ['amount', 'investment'],
            'severity': AuditSeverity.MEDIUM
        }
        AUDITED_MODELS[PaymentRecord] = {
            'sensitive_fields': ['amount', 'status', 'payment_type'],
            'severity': AuditSeverity.HIGH
        }
    except ImportError:
        pass
    
    try:
        from referrals.models import ReferralBonus
        AUDITED_MODELS[ReferralBonus] = {
            'sensitive_fields': ['amount', 'status'],
            'severity': AuditSeverity.MEDIUM
        }
    except ImportError:
        pass

@receiver(pre_save)
def capture_old_values(sender, instance, **kwargs):
    """Captura valores antigos antes da alteração"""
    if sender not in AUDITED_MODELS:
        return
    
    if instance.pk:  # Só para updates
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_values = {}
            
            sensitive_fields = AUDITED_MODELS[sender]['sensitive_fields']
            for field_name in sensitive_fields:
                if hasattr(old_instance, field_name):
                    instance._old_values[field_name] = getattr(old_instance, field_name)
        except sender.DoesNotExist:
            pass

@receiver(post_save)
def audit_model_save(sender, instance, created, **kwargs):
    """Audita criação e alteração de models críticos"""
    if sender not in AUDITED_MODELS:
        return
    
    config = AUDITED_MODELS[sender]
    event_type = AuditEventType.CREATE if created else AuditEventType.UPDATE
    
    # Descrição do evento
    model_name = sender._meta.verbose_name
    if created:
        description = f"Criação de {model_name}: {instance}"
    else:
        description = f"Atualização de {model_name}: {instance}"
    
    # Valores alterados (apenas para updates)
    old_values = {}
    new_values = {}
    
    if not created and hasattr(instance, '_old_values'):
        sensitive_fields = config['sensitive_fields']
        for field_name in sensitive_fields:
            if hasattr(instance, field_name):
                old_value = instance._old_values.get(field_name)
                new_value = getattr(instance, field_name)
                
                if old_value != new_value:
                    # Mascarar passwords
                    if 'password' in field_name.lower():
                        old_values[field_name] = '***MASKED***'
                        new_values[field_name] = '***MASKED***'
                    else:
                        old_values[field_name] = str(old_value) if old_value is not None else None
                        new_values[field_name] = str(new_value) if new_value is not None else None
    
    # Determinar severidade
    severity = config['severity']
    
    # Aumentar severidade para certas operações
    from users.models import User
    if isinstance(instance, User):
        if not created and 'is_active' in new_values and not new_values['is_active']:
            severity = AuditSeverity.CRITICAL  # Desativação de usuário
        elif not created and 'is_staff' in new_values or 'is_superuser' in new_values:
            severity = AuditSeverity.CRITICAL  # Mudança de privilégios
    
    # Log do evento
    AuditLogger.log_event(
        event_type=event_type,
        description=description,
        content_object=instance,
        severity=severity,
        old_values=old_values,
        new_values=new_values,
        module=sender._meta.app_label,
        action='create' if created else 'update'
    )
    
    # Log específico para transações financeiras de alto valor
    if hasattr(instance, 'amount') and instance.amount:
        amount = float(instance.amount)
        if amount >= 10000:  # Valor alto
            AuditLogger.log_event(
                event_type=AuditEventType.SECURITY_EVENT,
                description=f"Transação de alto valor: {model_name} de {amount}",
                content_object=instance,
                severity=AuditSeverity.HIGH,
                details={'high_value_transaction': True, 'amount': amount},
                module='financial'
            )

@receiver(post_delete)
def audit_model_delete(sender, instance, **kwargs):
    """Audita exclusão de models críticos"""
    if sender not in AUDITED_MODELS:
        return
    
    config = AUDITED_MODELS[sender]
    model_name = sender._meta.verbose_name
    
    description = f"Exclusão de {model_name}: {instance}"
    
    # Capturar dados do objeto deletado
    object_data = {}
    sensitive_fields = config['sensitive_fields']
    for field_name in sensitive_fields:
        if hasattr(instance, field_name):
            value = getattr(instance, field_name)
            if 'password' in field_name.lower():
                object_data[field_name] = '***MASKED***'
            else:
                object_data[field_name] = str(value) if value is not None else None
    
    AuditLogger.log_event(
        event_type=AuditEventType.DELETE,
        description=description,
        content_object=instance,
        severity=AuditSeverity.CRITICAL,  # Deleções são sempre críticas
        details={'deleted_object_data': object_data},
        module=sender._meta.app_label,
        action='delete'
    )

# Signals de autenticação
@receiver(user_logged_in)
def audit_user_login(sender, request, user, **kwargs):
    """Audita login de usuário"""
    audit_login(user, request, success=True)

@receiver(user_logged_out)
def audit_user_logout(sender, request, user, **kwargs):
    """Audita logout de usuário"""
    if user:
        audit_logout(user, request)

@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    """Audita tentativas de login falhadas"""
    username = credentials.get('username', 'unknown')
    
    # Tentar encontrar o usuário
    User = get_user_model()
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = None
    
    audit_login(user, request, success=False)
    
    # Verificar tentativas repetidas (força bruta)
    from .models import SecurityEvent
    from django.utils import timezone
    from datetime import timedelta
    
    # Contar tentativas falhadas na última hora
    one_hour_ago = timezone.now() - timedelta(hours=1)
    ip_address = request.META.get('REMOTE_ADDR')
    
    failed_attempts = SecurityEvent.objects.filter(
        event_type='FAILED_LOGIN',
        ip_address=ip_address,
        timestamp__gte=one_hour_ago
    ).count()
    
    if failed_attempts >= 5:  # Muitas tentativas
        AuditLogger.log_security_event(
            event_type='BRUTE_FORCE',
            description=f'Possível ataque de força bruta: {failed_attempts} tentativas de login falhadas',
            request=request,
            user=user,
            additional_data={
                'failed_attempts': failed_attempts,
                'username': username,
                'time_window': '1 hora'
            }
        )

# Signal personalizado para mudanças de senha
from django.contrib.auth.signals import user_logged_in

def audit_password_change(user, request=None):
    """Função para auditar mudanças de senha"""
    AuditLogger.log_event(
        event_type=AuditEventType.PASSWORD_CHANGE,
        description=f"Alteração de senha para usuário: {user.username}",
        user=user,
        severity=AuditSeverity.HIGH,
        request=request,
        module='authentication'
    )

# Signal personalizado para mudanças de permissão
def audit_permission_change(user, permission_change, changed_by, request=None):
    """Função para auditar mudanças de permissão"""
    AuditLogger.log_event(
        event_type=AuditEventType.PERMISSION_CHANGE,
        description=f"Alteração de permissão para {user.username}: {permission_change}",
        user=changed_by,
        content_object=user,
        severity=AuditSeverity.CRITICAL,
        details={'permission_change': permission_change},
        request=request,
        module='authorization'
    )

# Signal personalizado para transações financeiras
def audit_financial_transaction(transaction_type, user, amount, description, transaction_object=None, request=None, **kwargs):
    """Função para auditar transações financeiras"""
    from .utils import audit_financial_transaction as util_audit_financial
    
    util_audit_financial(
        transaction_type=transaction_type,
        user=user,
        amount=amount,
        description=description,
        request=request,
        **kwargs
    )
    
    if transaction_object:
        # Log adicional com o objeto da transação
        AuditLogger.log_event(
            event_type=transaction_type,
            description=description,
            user=user,
            content_object=transaction_object,
            severity=AuditSeverity.HIGH if amount > 10000 else AuditSeverity.MEDIUM,
            details={
                'amount': float(amount),
                'transaction_type': transaction_type,
                **kwargs
            },
            request=request,
            module='financial'
        ) 