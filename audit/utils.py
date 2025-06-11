from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from .models import AuditLog, SecurityEvent, DataChangeHistory, AuditEventType, AuditSeverity
import logging
import json

User = get_user_model()
logger = logging.getLogger(__name__)

class AuditLogger:
    """Classe principal para registrar eventos de auditoria"""
    
    @staticmethod
    def log_event(
        event_type: str,
        description: str,
        user=None,
        severity: str = AuditSeverity.MEDIUM,
        content_object=None,
        details: dict = None,
        old_values: dict = None,
        new_values: dict = None,
        request=None,
        module: str = None,
        action: str = None
    ):
        """
        Registra um evento de auditoria
        
        Args:
            event_type: Tipo do evento (usar AuditEventType)
            description: Descrição do evento
            user: Usuário responsável pelo evento
            severity: Severidade do evento
            content_object: Objeto afetado
            details: Detalhes adicionais
            old_values: Valores anteriores (para updates)
            new_values: Novos valores (para updates)
            request: Request HTTP (para extrair IP, user-agent, etc.)
            module: Módulo onde ocorreu o evento
            action: Ação específica
        """
        try:
            # Extrair informações do request se disponível
            ip_address = None
            user_agent = None
            session_key = None
            
            if request:
                ip_address = AuditLogger._get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limitar tamanho
                session_key = request.session.session_key
                
                # Se usuário não foi passado, tentar extrair do request
                if not user and hasattr(request, 'user') and request.user.is_authenticated:
                    user = request.user
            
            # Preparar dados do content_object
            content_type = None
            object_id = None
            if content_object:
                content_type = ContentType.objects.get_for_model(content_object)
                object_id = content_object.pk
            
            # Criar o log de auditoria
            audit_log = AuditLog.objects.create(
                event_type=event_type,
                severity=severity,
                user=user,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                content_type=content_type,
                object_id=object_id,
                description=description,
                details=details or {},
                old_values=old_values or {},
                new_values=new_values or {},
                module=module,
                action=action
            )
            
            # Se houver mudanças detalhadas de campos, criar registros de DataChangeHistory
            if old_values and new_values and content_object:
                AuditLogger._create_field_changes(audit_log, old_values, new_values, user)
            
            # Log para sistema de logging do Django também
            logger.info(f"Audit Event: {event_type} - {description} - User: {user}")
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Erro ao registrar evento de auditoria: {e}")
            return None
    
    @staticmethod
    def log_security_event(
        event_type: str,
        description: str,
        ip_address: str = None,
        user_agent: str = None,
        user=None,
        additional_data: dict = None,
        request=None
    ):
        """Registra um evento de segurança"""
        try:
            if request and not ip_address:
                ip_address = AuditLogger._get_client_ip(request)
            if request and not user_agent:
                user_agent = request.META.get('HTTP_USER_AGENT', '')
            if request and not user and hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
                
            security_event = SecurityEvent.objects.create(
                event_type=event_type,
                ip_address=ip_address or '0.0.0.0',
                user_agent=user_agent[:500] if user_agent else None,
                user=user,
                description=description,
                additional_data=additional_data or {}
            )
            
            # Também criar um log de auditoria regular
            AuditLogger.log_event(
                event_type=AuditEventType.SECURITY_EVENT,
                description=f"Evento de Segurança: {description}",
                user=user,
                severity=AuditSeverity.HIGH,
                details={
                    'security_event_type': event_type,
                    'ip_address': ip_address,
                    'additional_data': additional_data or {}
                },
                request=request,
                module='security'
            )
            
            logger.warning(f"Security Event: {event_type} - {description} - IP: {ip_address}")
            
            return security_event
            
        except Exception as e:
            logger.error(f"Erro ao registrar evento de segurança: {e}")
            return None
    
    @staticmethod
    def log_model_change(sender, instance, created=False, raw=False, using=None, **kwargs):
        """
        Signal handler para mudanças em models
        Deve ser conectado aos signals post_save e post_delete
        """
        if raw:  # Pular se for um raw save (fixtures, etc.)
            return
            
        try:
            event_type = AuditEventType.CREATE if created else AuditEventType.UPDATE
            description = f"{'Criação' if created else 'Atualização'} de {sender._meta.verbose_name}: {instance}"
            
            # Tentar encontrar o usuário atual (isso requer middleware personalizado)
            user = AuditLogger._get_current_user()
            
            AuditLogger.log_event(
                event_type=event_type,
                description=description,
                user=user,
                content_object=instance,
                module=sender._meta.app_label,
                action='create' if created else 'update'
            )
            
        except Exception as e:
            logger.error(f"Erro ao registrar mudança de model: {e}")
    
    @staticmethod
    def log_model_delete(sender, instance, using=None, **kwargs):
        """Signal handler para deleções de models"""
        try:
            description = f"Exclusão de {sender._meta.verbose_name}: {instance}"
            user = AuditLogger._get_current_user()
            
            AuditLogger.log_event(
                event_type=AuditEventType.DELETE,
                description=description,
                user=user,
                content_object=instance,
                severity=AuditSeverity.HIGH,
                module=sender._meta.app_label,
                action='delete'
            )
            
        except Exception as e:
            logger.error(f"Erro ao registrar deleção de model: {e}")
    
    @staticmethod
    def _create_field_changes(audit_log, old_values, new_values, user):
        """Cria registros detalhados de mudanças de campos"""
        for field_name in set(old_values.keys()) | set(new_values.keys()):
            old_value = old_values.get(field_name)
            new_value = new_values.get(field_name)
            
            if old_value != new_value:
                DataChangeHistory.objects.create(
                    content_type=audit_log.content_type,
                    object_id=audit_log.object_id,
                    field_name=field_name,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(new_value) if new_value is not None else None,
                    changed_by=user,
                    audit_log=audit_log
                )
    
    @staticmethod
    def _get_client_ip(request):
        """Extrai o IP real do cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def _get_current_user():
        """
        Obtém o usuário atual através do thread local
        Requer middleware personalizado para funcionar
        """
        try:
            from .middleware import get_current_user
            return get_current_user()
        except ImportError:
            return None

class ModelAuditMixin:
    """
    Mixin para models que devem ser auditados automaticamente
    
    Usage:
        class MyModel(ModelAuditMixin, models.Model):
            # ... fields ...
            
            class Meta:
                audit_fields = ['field1', 'field2']  # Campos específicos para auditar
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Armazenar valores originais para comparação
        self._original_values = {}
        if self.pk:
            self._store_original_values()
    
    def _store_original_values(self):
        """Armazena valores originais dos campos auditados"""
        audit_fields = getattr(self._meta, 'audit_fields', None)
        if audit_fields:
            for field_name in audit_fields:
                if hasattr(self, field_name):
                    self._original_values[field_name] = getattr(self, field_name)
        else:
            # Se não especificado, auditar todos os campos não relacionais
            for field in self._meta.fields:
                if not isinstance(field, (models.ForeignKey, models.ManyToManyField)):
                    self._original_values[field.name] = getattr(self, field.name)
    
    def save(self, *args, **kwargs):
        # Determinar se é criação ou atualização
        is_new = self._state.adding
        
        # Se é atualização, comparar valores
        old_values = {}
        new_values = {}
        
        if not is_new:
            audit_fields = getattr(self._meta, 'audit_fields', None)
            fields_to_check = audit_fields if audit_fields else [f.name for f in self._meta.fields 
                                                               if not isinstance(f, (models.ForeignKey, models.ManyToManyField))]
            
            for field_name in fields_to_check:
                old_value = self._original_values.get(field_name)
                new_value = getattr(self, field_name)
                
                if old_value != new_value:
                    old_values[field_name] = old_value
                    new_values[field_name] = new_value
        
        # Salvar o objeto
        super().save(*args, **kwargs)
        
        # Registrar no log de auditoria
        if is_new or old_values:
            event_type = AuditEventType.CREATE if is_new else AuditEventType.UPDATE
            description = f"{'Criação' if is_new else 'Atualização'} de {self._meta.verbose_name}: {self}"
            
            AuditLogger.log_event(
                event_type=event_type,
                description=description,
                content_object=self,
                old_values=old_values,
                new_values=new_values,
                module=self._meta.app_label
            )
        
        # Atualizar valores originais
        self._store_original_values()

def audit_login(user, request, success=True):
    """Registra tentativas de login"""
    if success:
        AuditLogger.log_event(
            event_type=AuditEventType.LOGIN,
            description=f"Login realizado com sucesso: {user.username}",
            user=user,
            severity=AuditSeverity.LOW,
            request=request,
            module='authentication'
        )
    else:
        AuditLogger.log_security_event(
            event_type='FAILED_LOGIN',
            description=f"Tentativa de login falhada para: {user.username if user else 'usuário desconhecido'}",
            request=request,
            user=user,
            additional_data={'username': getattr(user, 'username', 'unknown')}
        )

def audit_logout(user, request):
    """Registra logout"""
    AuditLogger.log_event(
        event_type=AuditEventType.LOGOUT,
        description=f"Logout realizado: {user.username}",
        user=user,
        severity=AuditSeverity.LOW,
        request=request,
        module='authentication'
    )

def audit_financial_transaction(transaction_type, user, amount, description, request=None, **kwargs):
    """Registra transações financeiras"""
    severity = AuditSeverity.HIGH if amount > 10000 else AuditSeverity.MEDIUM
    
    AuditLogger.log_event(
        event_type=transaction_type,
        description=f"{description} - Valor: {amount}",
        user=user,
        severity=severity,
        details={
            'amount': float(amount),
            'transaction_type': transaction_type,
            **kwargs
        },
        request=request,
        module='financial'
    ) 