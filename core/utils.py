"""
Utilitários para padronização e modularização da API
"""
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class APIResponseHandler:
    """
    Classe para padronizar as respostas da API
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", status_code: int = status.HTTP_200_OK, meta: Dict = None) -> Response:
        """
        Resposta de sucesso padronizada
        """
        response_data = {
            "success": True,
            "message": message,
            "data": data,
            "meta": meta or {}
        }
        
        # Adiciona informações do sistema se disponível
        if hasattr(settings, 'SYSTEM_NAME'):
            response_data["meta"]["system"] = {
                "name": getattr(settings, 'SYSTEM_NAME', 'Investment Platform'),
                "version": getattr(settings, 'SYSTEM_VERSION', '1.0.0')
            }
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message: str = "Error", details: Any = None, status_code: int = status.HTTP_400_BAD_REQUEST, error_code: str = None) -> Response:
        """
        Resposta de erro padronizada
        """
        response_data = {
            "success": False,
            "message": message,
            "error": {
                "code": error_code,
                "details": details
            }
        }
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def paginated(data: Any, page: int, total_pages: int, total_items: int, page_size: int, message: str = "Success") -> Response:
        """
        Resposta paginada padronizada
        """
        meta = {
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }
        
        return APIResponseHandler.success(data, message, meta=meta)

class BusinessRulesValidator:
    """
    Validador de regras de negócio dinâmicas
    """
    
    @staticmethod
    def validate_deposit_amount(amount: float) -> tuple[bool, str]:
        """
        Valida valor de depósito baseado nas regras configuradas
        """
        business_rules = getattr(settings, 'BUSINESS_RULES', {})
        min_amount = business_rules.get('MIN_DEPOSIT_AMOUNT', 10.0)
        max_amount = business_rules.get('MAX_DEPOSIT_AMOUNT', 50000.0)
        
        if amount < min_amount:
            return False, f"Valor mínimo de depósito é {min_amount}"
        
        if amount > max_amount:
            return False, f"Valor máximo de depósito é {max_amount}"
        
        return True, "Valor válido"
    
    @staticmethod
    def validate_withdrawal_amount(amount: float) -> tuple[bool, str]:
        """
        Valida valor de saque baseado nas regras configuradas
        """
        business_rules = getattr(settings, 'BUSINESS_RULES', {})
        min_amount = business_rules.get('MIN_WITHDRAWAL_AMOUNT', 50.0)
        
        if amount < min_amount:
            return False, f"Valor mínimo de saque é {min_amount}"
        
        return True, "Valor válido"
    
    @staticmethod
    def calculate_referral_bonus(amount: float) -> float:
        """
        Calcula bônus de indicação baseado nas regras configuradas
        """
        business_rules = getattr(settings, 'BUSINESS_RULES', {})
        bonus_percent = business_rules.get('REFERRAL_BONUS_PERCENT', 5.0)
        return amount * (bonus_percent / 100)
    
    @staticmethod
    def calculate_withdrawal_fee(amount: float) -> float:
        """
        Calcula taxa de saque baseado nas regras configuradas
        """
        business_rules = getattr(settings, 'BUSINESS_RULES', {})
        fee_percent = business_rules.get('WITHDRAWAL_FEE_PERCENT', 2.0)
        return amount * (fee_percent / 100)

class FeatureToggle:
    """
    Sistema de controle de funcionalidades
    """
    
    @staticmethod
    def is_enabled(feature: str) -> bool:
        """
        Verifica se uma funcionalidade está habilitada
        """
        features = getattr(settings, 'FEATURES', {})
        return features.get(feature, False)
    
    @staticmethod
    def require_feature(feature: str):
        """
        Decorator para exigir que uma funcionalidade esteja habilitada
        """
        def decorator(view_func):
            def wrapper(*args, **kwargs):
                if not FeatureToggle.is_enabled(feature):
                    return APIResponseHandler.error(
                        message="Funcionalidade não disponível",
                        error_code="FEATURE_DISABLED",
                        status_code=status.HTTP_404_NOT_FOUND
                    )
                return view_func(*args, **kwargs)
            return wrapper
        return decorator

class SystemConfig:
    """
    Configurações dinâmicas do sistema
    """
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        Retorna informações básicas do sistema
        """
        return {
            "name": getattr(settings, 'SYSTEM_NAME', 'Investment Platform'),
            "version": getattr(settings, 'SYSTEM_VERSION', '1.0.0'),
            "company": getattr(settings, 'COMPANY_NAME', 'Financial Services Inc.'),
            "theme_color": getattr(settings, 'SYSTEM_THEME_COLOR', '#1e40af'),
            "features": {
                feature: FeatureToggle.is_enabled(feature) 
                for feature in getattr(settings, 'FEATURES', {}).keys()
            },
            "business_rules": {
                "min_deposit": getattr(settings, 'BUSINESS_RULES', {}).get('MIN_DEPOSIT_AMOUNT'),
                "max_deposit": getattr(settings, 'BUSINESS_RULES', {}).get('MAX_DEPOSIT_AMOUNT'),
                "min_withdrawal": getattr(settings, 'BUSINESS_RULES', {}).get('MIN_WITHDRAWAL_AMOUNT'),
                "referral_bonus_percent": getattr(settings, 'BUSINESS_RULES', {}).get('REFERRAL_BONUS_PERCENT'),
                "withdrawal_fee_percent": getattr(settings, 'BUSINESS_RULES', {}).get('WITHDRAWAL_FEE_PERCENT'),
                "default_currency": getattr(settings, 'BUSINESS_RULES', {}).get('DEFAULT_CURRENCY')
            }
        }
    
    @staticmethod
    def get_payment_methods() -> list:
        """
        Retorna métodos de pagamento disponíveis baseado nas features habilitadas
        """
        methods = []
        
        if FeatureToggle.is_enabled('CRYPTO_PAYMENTS'):
            methods.append({
                "id": "USDT_BEP20",
                "name": "USDT (BEP20)",
                "type": "crypto",
                "enabled": True
            })
        
        if FeatureToggle.is_enabled('PIX_PAYMENTS'):
            methods.append({
                "id": "PIX",
                "name": "PIX",
                "type": "bank_transfer",
                "enabled": True
            })
        
        return methods

def log_api_activity(user, action: str, details: Dict = None):
    """
    Função para log de atividades da API
    """
    logger.info(f"API Activity - User: {user.username if user else 'Anonymous'}, Action: {action}, Details: {details}") 