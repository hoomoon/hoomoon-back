# core/views.py
"""
Views base e utilitárias para o sistema
Estas views fornecem funcionalidades que podem ser reutilizadas por outros apps
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .utils import APIResponseHandler, SystemConfig
from .models import FeatureFlagModel


class SystemConfigView(APIView):
    """
    View para configurações dinâmicas do sistema
    Permite que frontends se adaptem às configurações específicas
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Retorna configurações do sistema para o frontend
        """
        config = SystemConfig.get_system_info()
        config['payment_methods'] = SystemConfig.get_payment_methods()
        
        # Adiciona feature flags do banco de dados
        db_features = {}
        for feature in FeatureFlagModel.objects.filter(is_enabled=True):
            db_features[feature.name] = True
        
        if db_features:
            config['db_features'] = db_features
        
        return APIResponseHandler.success(
            data=config,
            message="Configurações do sistema obtidas com sucesso"
        )


class HealthCheckView(APIView):
    """
    View para verificar a saúde do sistema
    Útil para monitoramento e load balancers
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Retorna status de saúde do sistema
        """
        health_data = {
            "status": "healthy",
            "timestamp": request.timestamp if hasattr(request, 'timestamp') else None,
            "version": SystemConfig.get_system_info().get('version', '1.0.0'),
            "features_enabled": len(SystemConfig.get_system_info().get('features', {}))
        }
        
        return APIResponseHandler.success(
            data=health_data,
            message="Sistema funcionando corretamente"
        )
