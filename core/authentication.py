"""
Sistema de autenticação JWT seguro baseado em cookies para HooMoon
Garante máxima segurança para sistema financeiro
"""
import logging
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)
User = get_user_model()

def _get_token_lifetime_seconds(lifetime: timedelta) -> int:
    """Converte timedelta para segundos"""
    return int(lifetime.total_seconds())

class SecureCookieJWTAuthentication(JWTAuthentication):
    """
    Autenticação JWT segura usando HTTP Cookies
    
    Prioridade de busca do token:
    1. Authorization header (para compatibilidade)
    2. HTTP Cookie 'access_token' (preferencial)
    
    Características de segurança:
    - httpOnly cookies (proteção XSS)
    - Secure em produção (apenas HTTPS)
    - SameSite=Strict (proteção CSRF)
    - Logs de segurança detalhados
    """
    
    def authenticate(self, request):
        """
        Autentica usando token do header ou cookie
        """
        raw_token = None
        token_source = None
        
        # 1. Tentar obter do Authorization header primeiro
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            token_source = "authorization_header"
        
        # 2. Se não encontrou, tentar no cookie
        if raw_token is None:
            raw_token = request.COOKIES.get('access_token')
            token_source = "http_cookie"
        
        # 3. Se não tem token, retornar None (usuário não autenticado)
        if raw_token is None:
            return None
        
        try:
            # Validar o token
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            
            # Log de sucesso para auditoria
            logger.info(
                f"Successful JWT authentication: user={user.username}, "
                f"source={token_source}, ip={request.META.get('REMOTE_ADDR')}"
            )
            
            return (user, validated_token)
            
        except (InvalidToken, TokenError) as e:
            # Log de tentativa com token inválido
            logger.warning(
                f"Invalid JWT token attempt: source={token_source}, "
                f"ip={request.META.get('REMOTE_ADDR')}, error={str(e)}"
            )
            return None
        except Exception as e:
            # Log de erro inesperado
            logger.error(
                f"Unexpected error in JWT authentication: {str(e)}, "
                f"ip={request.META.get('REMOTE_ADDR')}"
            )
            return None

class CookieTokenManager:
    """
    Gerenciador de tokens em cookies com configurações de segurança
    """
    
    @staticmethod
    def set_auth_cookies(response: Response, user: User, request=None) -> Response:
        """
        Define cookies de autenticação seguros na resposta
        
        Args:
            response: Response object do DRF
            user: Usuário autenticado
            request: Request object (para logs)
        
        Returns:
            Response com cookies seguros configurados
        """
        # Gerar tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Configurações de segurança para cookies
        cookie_config = {
            'httponly': True,
            'secure': not settings.DEBUG,  # HTTPS em produção
            'samesite': 'Strict' if not settings.DEBUG else 'Lax',
            'path': '/',
        }
        
        # Cookie do access token (vida curta)
        response.set_cookie(
            'access_token',
            access_token,
            max_age=_get_token_lifetime_seconds(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']),
            **cookie_config
        )
        
        # Cookie do refresh token (vida longa)
        response.set_cookie(
            'refresh_token',
            refresh_token,
            max_age=_get_token_lifetime_seconds(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']),
            **cookie_config
        )
        
        # Log de sucesso
        ip_address = request.META.get('REMOTE_ADDR') if request else 'unknown'
        logger.info(
            f"Auth cookies set for user: {user.username}, "
            f"ip={ip_address}, secure={cookie_config['secure']}"
        )
        
        return response
    
    @staticmethod
    def clear_auth_cookies(response: Response, request=None) -> Response:
        """
        Remove cookies de autenticação
        
        Args:
            response: Response object do DRF
            request: Request object (para logs)
        
        Returns:
            Response com cookies removidos
        """
        cookie_config = {
            'path': '/',
            'samesite': 'Strict' if not settings.DEBUG else 'Lax',
        }
        
        # Remover cookies
        response.delete_cookie('access_token', **cookie_config)
        response.delete_cookie('refresh_token', **cookie_config)
        
        # Log de logout
        ip_address = request.META.get('REMOTE_ADDR') if request else 'unknown'
        logger.info(f"Auth cookies cleared, ip={ip_address}")
        
        return response
    
    @staticmethod
    def refresh_access_token(request) -> tuple:
        """
        Renova o access token usando refresh token do cookie
        
        Args:
            request: Request object
            
        Returns:
            tuple: (success: bool, data: dict)
        """
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            logger.warning(
                f"Refresh token missing in cookies, ip={request.META.get('REMOTE_ADDR')}"
            )
            return False, {'error': 'Refresh token não encontrado'}
        
        try:
            # Validar e usar refresh token
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
            
            logger.info(
                f"Access token refreshed successfully, ip={request.META.get('REMOTE_ADDR')}"
            )
            
            return True, {
                'access_token': new_access_token,
                'token_lifetime': _get_token_lifetime_seconds(
                    settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
                )
            }
            
        except (InvalidToken, TokenError) as e:
            logger.warning(
                f"Invalid refresh token: {str(e)}, ip={request.META.get('REMOTE_ADDR')}"
            )
            return False, {'error': 'Refresh token inválido'}
        except Exception as e:
            logger.error(
                f"Unexpected error refreshing token: {str(e)}, ip={request.META.get('REMOTE_ADDR')}"
            )
            return False, {'error': 'Erro interno do servidor'}

def get_user_from_token(request):
    """
    Utility function para obter usuário do token atual
    """
    auth = SecureCookieJWTAuthentication()
    try:
        result = auth.authenticate(request)
        if result:
            user, token = result
            return user
    except Exception:
        pass
    return None 