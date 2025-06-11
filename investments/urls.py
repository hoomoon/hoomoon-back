"""
URLs para o app de investimentos
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, InvestmentViewSet

app_name = 'investments'

router = DefaultRouter()
router.register('plans', PlanViewSet)
router.register('investments', InvestmentViewSet, basename='investment')

urlpatterns = [
    path('', include(router.urls)),
]

"""
Endpoints disponíveis:

Planos de Investimento:
- GET /api/investments/plans/ - Lista todos os planos ativos
- GET /api/investments/plans/{id}/ - Detalhes de um plano específico

Depósitos:
- GET /api/investments/deposits/ - Lista depósitos do usuário
- POST /api/investments/deposits/ - Cria novo depósito
- GET /api/investments/deposits/{id}/ - Detalhes de um depósito
- PUT/PATCH /api/investments/deposits/{id}/ - Atualiza depósito
- DELETE /api/investments/deposits/{id}/ - Remove depósito
- POST /api/investments/deposits/{id}/process_pix/ - Processa pagamento PIX
- POST /api/investments/deposits/{id}/process_crypto/ - Processa pagamento crypto

Investimentos:
- GET /api/investments/investments/ - Lista investimentos do usuário
- POST /api/investments/investments/ - Cria novo investimento
- GET /api/investments/investments/{id}/ - Detalhes de um investimento
- PUT/PATCH /api/investments/investments/{id}/ - Atualiza investimento
- DELETE /api/investments/investments/{id}/ - Remove investimento
- GET /api/investments/investments/dashboard/ - Dashboard de investimentos
- POST /api/investments/investments/{id}/activate/ - Ativa investimento pendente

Rendimentos:
- GET /api/investments/earnings/ - Lista rendimentos do usuário
- GET /api/investments/earnings/{id}/ - Detalhes de um rendimento
- GET /api/investments/earnings/summary/ - Resumo dos rendimentos

Transações:
- GET /api/investments/transactions/ - Lista transações on-chain do usuário
- GET /api/investments/transactions/{id}/ - Detalhes de uma transação
""" 