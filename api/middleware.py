"""
Middleware para funcionalidades dinâmicas e modularização
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import json


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
            import logging
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