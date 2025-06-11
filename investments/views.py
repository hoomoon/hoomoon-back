"""
Views para o app de investimentos
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.utils import APIResponseHandler, FeatureToggle, BusinessRulesValidator
from core.permissions import IsOwnerOrReadOnly, RequireFeature
from .models import Plan, Investment
from .serializers import (
    PlanSerializer, InvestmentSerializer, InvestmentCreateSerializer,
    InvestmentDashboardSerializer
)


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para planos de investimento (somente leitura)
    """
    queryset = Plan.objects.filter(status='ACTIVE')
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]  # Planos são públicos
    
    def get_queryset(self):
        """Filtra planos baseado nas features habilitadas"""
        queryset = super().get_queryset()
        
        # Adicionar filtros específicos baseados em features se necessário
        if not FeatureToggle.is_enabled('MULTI_CURRENCY'):
            # Se multi-currency estiver desabilitado, pode filtrar planos específicos
            pass
            
        return queryset.order_by('min_value')
    
    @extend_schema(
        summary="Lista planos disponíveis",
        description="Retorna todos os planos de investimento ativos e disponíveis"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Detalhes do plano",
        description="Retorna detalhes completos de um plano específico"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class InvestmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para investimentos
    """
    serializer_class = InvestmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retorna apenas investimentos do usuário logado"""
        return Investment.objects.filter(user=self.request.user).order_by('-start_date')
    
    def get_serializer_class(self):
        """Usa serializer específico para criação"""
        if self.action == 'create':
            return InvestmentCreateSerializer
        return InvestmentSerializer
    
    def perform_create(self, serializer):
        """Associa o investimento ao usuário logado"""
        serializer.save(user=self.request.user)
    
    @extend_schema(
        summary="Lista investimentos do usuário",
        description="Retorna todos os investimentos do usuário autenticado"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Criar novo investimento",
        description="Cria um novo investimento para o usuário autenticado"
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Validações adicionais de negócio
            validator = BusinessRulesValidator()
            
            # Verificar se o usuário tem saldo ou depósito confirmado
            # Esta lógica seria mais complexa em produção
            
            investment = serializer.save(user=request.user)
            response_data = InvestmentSerializer(investment).data
            
            return APIResponseHandler.success(
                data=response_data,
                message="Investimento criado com sucesso"
            )
        return APIResponseHandler.error(
            message="Erro na validação",
            errors=serializer.errors
        )
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Retorna dashboard de investimentos do usuário"""
        user = request.user
        investments = self.get_queryset()
        
        # Calcular estatísticas
        total_invested = investments.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_yielded = investments.aggregate(
            total=Sum('total_yielded')
        )['total'] or 0
        
        active_investments = investments.filter(
            investment_status='ACTIVE'
        ).count()
        
        dashboard_data = {
            'total_invested': total_invested,
            'total_yielded': total_yielded,
            'active_investments': active_investments,
            'investments': InvestmentDashboardSerializer(
                investments[:5], many=True
            ).data
        }
        
        return APIResponseHandler.success(
            data=dashboard_data,
            message="Dashboard carregado com sucesso"
        )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Ativa um investimento pendente"""
        investment = self.get_object()
        
        if investment.investment_status != 'PENDING_PAYMENT':
            return APIResponseHandler.error(
                message="Investimento não pode ser ativado"
            )
        
        # Verificar se há depósito confirmado ou saldo suficiente
        # Esta lógica seria implementada baseada nas regras de negócio
        
        investment.investment_status = 'ACTIVE'
        investment.save()
        
        return APIResponseHandler.success(
            data=InvestmentSerializer(investment).data,
            message="Investimento ativado com sucesso"
        )
