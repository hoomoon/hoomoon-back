"""
Middleware para funcionalidades dinâmicas e modularização
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import json
import logging


class DynamicHeadersMiddleware(MiddlewareMixin):
    """
    Adiciona headers dinâmicos baseados na configuração do sistema
    Facilita a integração com diferentes frontends
    """
    
    def process_response(self, request, response):
        # Adiciona headers de configuração do sistema apenas para requests da API
        if request.path.startswith('/api/'):
            # Informações básicas do sistema
            response['X-System-Name'] = getattr(settings, 'SYSTEM_NAME', 'Investment Platform')
            response['X-System-Version'] = getattr(settings, 'SYSTEM_VERSION', '1.0.0')
            response['X-Company-Name'] = getattr(settings, 'COMPANY_NAME', 'Financial Services Inc.')
            
            # Features habilitadas (para que o frontend possa se adaptar)
            if hasattr(settings, 'FEATURES'):
                enabled_features = [
                    feature for feature, enabled in settings.FEATURES.items() 
                    if enabled
                ]
                response['X-Features-Enabled'] = ','.join(enabled_features)
            
            # Moeda padrão
            response['X-Default-Currency'] = settings.BUSINESS_RULES.get('DEFAULT_CURRENCY', 'USD')
            
            # Versão da API
            if '/v1/' in request.path:
                response['X-API-Version'] = 'v1'
            elif '/v2/' in request.path:
                response['X-API-Version'] = 'v2'
            else:
                response['X-API-Version'] = 'v2'  # Padrão
            
            # Headers para facilitar CORS em desenvolvimento
            if settings.DEBUG:
                response['X-Debug-Mode'] = 'true'
        
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware para log de requests da API (opcional, pode ser habilitado/desabilitado)
    """
    
    def process_request(self, request):
        # Log apenas requests da API em modo debug
        if settings.DEBUG and request.path.startswith('/api/'):
            logger = logging.getLogger('api')
            
            # Log básico da requisição
            logger.debug(f"API Request: {request.method} {request.path}")
            
            # Log de headers úteis para debug
            if hasattr(request, 'user') and request.user.is_authenticated:
                logger.debug(f"User: {request.user.username}")
        
        return None


class FeatureToggleMiddleware(MiddlewareMixin):
    """
    Middleware para verificar se endpoints específicos estão habilitados
    """
    
    FEATURE_ENDPOINTS = {
        'REFERRAL_SYSTEM': ['/api/network/', '/api/referrals/'],
        'PIX_PAYMENTS': ['/api/deposits/', '/api/payments/'],
        'CRYPTO_PAYMENTS': ['/api/deposits/', '/api/payments/'],
        'ADMIN_DASHBOARD': ['/api/admin/', '/admin/'],
    }
    
    def process_request(self, request):
        from django.http import JsonResponse
        from .utils import APIResponseHandler
        
        # Verifica se o endpoint requer uma feature específica
        for feature, endpoints in self.FEATURE_ENDPOINTS.items():
            for endpoint in endpoints:
                if request.path.startswith(endpoint):
                    if not settings.FEATURES.get(feature, False):
                        return JsonResponse(
                            APIResponseHandler.error(
                                message="Funcionalidade não disponível neste sistema",
                                error_code="FEATURE_DISABLED"
                            ).data,
                            status=404
                        )
        
        return None 


class SecurityMiddleware:
    """
    Middleware de segurança adicional para sistema financeiro
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Adicionar headers de segurança
        response = self.get_response(request)
        
        # Headers de segurança para sistema financeiro
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Content Security Policy restritiva
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        
        return response


class AuthenticationLoggingMiddleware:
    """
    Middleware para log detalhado de tentativas de autenticação
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('core.security')
    
    def __call__(self, request):
        # Verificar se é uma tentativa de autenticação
        auth_endpoints = ['/auth/login/', '/auth/register/', '/auth/refresh/']
        is_auth_attempt = any(endpoint in request.path for endpoint in auth_endpoints)
        
        if is_auth_attempt:
            # Log da tentativa
            self.logger.info(
                f"Auth attempt: path={request.path}, "
                f"method={request.method}, "
                f"ip={request.META.get('REMOTE_ADDR')}, "
                f"user_agent={request.META.get('HTTP_USER_AGENT', '')[:100]}"
            )
        
        response = self.get_response(request)
        
        # Log do resultado se foi tentativa de auth
        if is_auth_attempt:
            self.logger.info(
                f"Auth result: path={request.path}, "
                f"status={response.status_code}, "
                f"ip={request.META.get('REMOTE_ADDR')}"
            )
        
        return response 