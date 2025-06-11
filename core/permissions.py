"""
Permissões customizadas reutilizáveis em todo o sistema
"""
from rest_framework.permissions import BasePermission
from .utils import FeatureToggle


class IsOwnerOrReadOnly(BasePermission):
    """
    Permissão que permite leitura para todos, mas escrita apenas para o dono
    """
    
    def has_object_permission(self, request, view, obj):
        # Permissões de leitura para qualquer request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Permissões de escrita apenas para o dono do objeto
        return obj.user == request.user


class RequireFeaturePermission(BasePermission):
    """
    Permissão que exige que uma feature específica esteja habilitada
    """
    
    def __init__(self, feature_name):
        self.feature_name = feature_name
    
    def has_permission(self, request, view):
        return FeatureToggle.is_enabled(self.feature_name)


def RequireFeature(feature_name):
    """
    Decorator para métodos/actions que exigem uma feature específica
    """
    def decorator(func):
        from functools import wraps
        from rest_framework.response import Response
        from rest_framework import status
        from .utils import APIResponseHandler
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Verificar se a feature está habilitada
            if not FeatureToggle.is_enabled(feature_name):
                return APIResponseHandler.error(
                    message="Funcionalidade não disponível",
                    error_code="FEATURE_DISABLED",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


class IsAdminOrOwner(BasePermission):
    """
    Permissão que permite acesso para admins ou donos do objeto
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin tem acesso total
        if request.user.is_staff:
            return True
        
        # Usuário comum só acessa seus próprios objetos
        return hasattr(obj, 'user') and obj.user == request.user


class IsAuthenticatedOrReadOnlyForPublic(BasePermission):
    """
    Permissão que permite leitura pública para alguns endpoints
    mas exige autenticação para escrita
    """
    
    def has_permission(self, request, view):
        # Métodos de leitura são públicos
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Métodos de escrita exigem autenticação
        return request.user and request.user.is_authenticated


class HasValidReferralCode(BasePermission):
    """
    Permissão que verifica se o usuário tem um código de indicação válido
    Útil para sistemas com sistema de referência obrigatório
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verifica se o sistema de referência está habilitado
        if not FeatureToggle.is_enabled('REFERRAL_SYSTEM'):
            return True  # Se não está habilitado, permite acesso
        
        # Verifica se o usuário tem código de indicação
        return bool(getattr(request.user, 'referral_code', None))


class IsKYCVerified(BasePermission):
    """
    Permissão que verifica se o usuário passou pela verificação KYC
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Se KYC não está habilitado, permite acesso
        if not FeatureToggle.is_enabled('KYC_VERIFICATION'):
            return True
        
        # Verifica se o usuário tem KYC verificado
        # Isso pode ser expandido com campos específicos no modelo de usuário
        return getattr(request.user, 'kyc_verified', False)


def require_feature(feature_name):
    """
    Decorator para views que exigem uma feature específica
    """
    def decorator(view_class):
        original_permission_classes = getattr(view_class, 'permission_classes', [])
        
        class FeaturePermission(BasePermission):
            def has_permission(self, request, view):
                return FeatureToggle.is_enabled(feature_name)
        
        view_class.permission_classes = [FeaturePermission] + list(original_permission_classes)
        return view_class
    
    return decorator 