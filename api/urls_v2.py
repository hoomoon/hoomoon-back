# api/urls_v2.py
"""
URLs modulares e dinâmicas para API v2
Essas URLs são mais genéricas e podem ser adaptadas para diferentes sistemas
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import SystemConfigView
from .base_views import (
    DynamicPlanViewSet, DynamicDepositViewSet, 
    UserProfileView, DashboardView, PaymentMethodsView
)
from .views import (
    # Mantemos algumas views específicas que não foram modularizadas ainda
    MyNetworkView, CoinPaymentsIPNView, ConnectPayWebhookView,
    check_email_exists, check_cpf_exists, sponsor_by_code, check_username_exists,
    FreePlanActivateView, InitiateDepositView, FreePlanStatusView, update_cpf, AdminLoginView,
    CookieTokenObtainPairView, CookieTokenRefreshView, LogoutView, RegisterView
)

# Router para ViewSets modulares
router = DefaultRouter()
router.register(r'plans', DynamicPlanViewSet, basename='plan')
router.register(r'deposits', DynamicDepositViewSet, basename='deposit')

urlpatterns = [
    # URLs dos ViewSets
    path('', include(router.urls)),
    
    # Configurações do Sistema - Endpoint dinâmico para frontends
    path('system/config/', SystemConfigView.as_view(), name='system_config'),
    path('system/payment-methods/', PaymentMethodsView.as_view(), name='payment_methods'),
    
    # Autenticação - URLs modulares
    path('auth/login/', CookieTokenObtainPairView.as_view(), name='auth_login'),
    path('auth/refresh/', CookieTokenRefreshView.as_view(), name='auth_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    
    # Perfil do Usuário - Modular
    path('user/profile/', UserProfileView.as_view(), name='user_profile'),
    path('user/dashboard/', DashboardView.as_view(), name='user_dashboard'),
    
    # Rede de Referência - Específico (mantido por compatibilidade)
    path('network/', MyNetworkView.as_view(), name='network'),
    
    # Webhooks - Específicos (mantidos por compatibilidade)
    path('webhooks/coinpayments/', CoinPaymentsIPNView.as_view(), name='coinpayments_webhook'),
    path('webhooks/connectpay/', ConnectPayWebhookView.as_view(), name='connectpay_webhook'),

    # Admin - Específico (mantido por compatibilidade)
    path('admin/login/', AdminLoginView.as_view(), name='admin_login'),

    # Investimentos - Específicos (mantidos por compatibilidade)
    path('investments/free-plan/activate/', FreePlanActivateView.as_view(), name='free_plan_activate'),
    path('investments/free-plan/status/', FreePlanStatusView.as_view(), name='free_plan_status'),
    path('investments/deposits/initiate/', InitiateDepositView.as_view(), name='initiate_deposit'),
    
    # Validações - Específicas (mantidas por compatibilidade)
    path('validators/sponsor/<str:code>/', sponsor_by_code, name='validate_sponsor'),
    path('validators/email/', check_email_exists, name='validate_email'),
    path('validators/cpf/', check_cpf_exists, name='validate_cpf'),
    path('validators/username/', check_username_exists, name='validate_username'),
    path('user/update-cpf/', update_cpf, name='update_cpf'),
] 