# api/urls.py
from django.urls import path, include # type: ignore
from rest_framework.routers import DefaultRouter # type: ignore
from .views import PlanViewSet, DepositViewSet, MyNetworkView, CoinPaymentsIPNView # type: ignore
from .views import check_email_exists, check_cpf_exists, sponsor_by_code, check_username_exists # type: ignore

router = DefaultRouter()
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'deposits', DepositViewSet, basename='deposit')

urlpatterns = [
    path('', include(router.urls)),
    path('minha-rede/', MyNetworkView.as_view(), name='minha-rede'),
    path('coinpayments-ipn/', CoinPaymentsIPNView.as_view(), name='coinpayments-ipn'),
    
    # checkers
    path('sponsor/<str:code>/', sponsor_by_code, name='sponsor-by-code'),
    path('check-email/', check_email_exists, name='check-email'),
    path('check-cpf/', check_cpf_exists, name='check-cpf'),
    path('check-username/', check_username_exists, name='check-username')
]
