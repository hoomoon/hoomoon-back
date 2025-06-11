"""
URLs do app core
Funcionalidades base disponíveis para todos os sistemas
"""
from django.urls import path
from .views import SystemConfigView, HealthCheckView

app_name = 'core'

urlpatterns = [
    # Configurações do sistema
    path('config/', SystemConfigView.as_view(), name='system_config'),
    
    # Health check
    path('health/', HealthCheckView.as_view(), name='health_check'),
] 