# api/base_views.py
"""
Views base modulares para reutilização em diferentes sistemas de investimento
Agora utiliza funcionalidades do app core
"""
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework import status
from django.db.models import Q, Sum
from django.conf import settings
from django.utils import timezone
from core.utils import APIResponseHandler, FeatureToggle, SystemConfig, log_api_activity
from .models import User, Plan, Deposit, Investment, Earning
from .serializers import UserSerializer, PlanSerializer, DepositSerializer
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class DynamicPlanViewSet(ReadOnlyModelViewSet):
    """
    ViewSet modular para planos de investimento
    """
    queryset = Plan.objects.all().order_by('min_value')
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):
        """
        Lista planos com informações dinâmicas
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Adiciona informações dinâmicas
        plans_data = serializer.data
        for plan_data in plans_data:
            # Adiciona configurações específicas do sistema
            plan_data['system_currency'] = settings.BUSINESS_RULES.get('DEFAULT_CURRENCY', 'USD')
            plan_data['referral_bonus_enabled'] = FeatureToggle.is_enabled('REFERRAL_SYSTEM')
        
        return APIResponseHandler.success(
            data=plans_data,
            message="Planos de investimento obtidos com sucesso"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Detalha um plano específico
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        plan_data = serializer.data
        plan_data['system_currency'] = settings.BUSINESS_RULES.get('DEFAULT_CURRENCY', 'USD')
        plan_data['payment_methods'] = SystemConfig.get_payment_methods()
        
        return APIResponseHandler.success(
            data=plan_data,
            message="Detalhes do plano obtidos com sucesso"
        )


class DynamicDepositViewSet(ModelViewSet):
    """
    ViewSet modular para depósitos
    """
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtra depósitos do usuário autenticado
        """
        return Deposit.objects.filter(user=self.request.user).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """
        Criação de depósito com validações dinâmicas
        """
        log_api_activity(request.user, "deposit_create_attempt", {"data": request.data})
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return APIResponseHandler.error(
                message="Dados de depósito inválidos",
                details=serializer.errors,
                error_code="VALIDATION_ERROR"
            )
        
        # Validação de método de pagamento
        method = serializer.validated_data.get('method')
        if method == 'PIX' and not FeatureToggle.is_enabled('PIX_PAYMENTS'):
            return APIResponseHandler.error(
                message="Pagamentos via PIX não estão disponíveis",
                error_code="PAYMENT_METHOD_DISABLED"
            )
        
        if method == 'USDT_BEP20' and not FeatureToggle.is_enabled('CRYPTO_PAYMENTS'):
            return APIResponseHandler.error(
                message="Pagamentos via criptomoeda não estão disponíveis",
                error_code="PAYMENT_METHOD_DISABLED"
            )
        
        # Salva o depósito
        deposit = serializer.save(user=request.user)
        
        log_api_activity(request.user, "deposit_created", {"deposit_id": deposit.id, "method": method})
        
        return APIResponseHandler.success(
            data=serializer.data,
            message="Depósito criado com sucesso",
            status_code=status.HTTP_201_CREATED
        )
    
    def list(self, request, *args, **kwargs):
        """
        Lista depósitos do usuário
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return APIResponseHandler.success(
            data=serializer.data,
            message="Depósitos obtidos com sucesso"
        )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Resumo de depósitos do usuário
        """
        queryset = self.get_queryset()
        
        summary_data = {
            'total_deposits': queryset.count(),
            'total_amount': queryset.aggregate(Sum('amount'))['amount__sum'] or 0,
            'pending_count': queryset.filter(status='PENDING').count(),
            'confirmed_count': queryset.filter(status='CONFIRMED').count(),
            'failed_count': queryset.filter(status='FAILED').count(),
        }
        
        return APIResponseHandler.success(
            data=summary_data,
            message="Resumo de depósitos obtido com sucesso"
        )


class UserProfileView(APIView):
    """
    View modular para perfil do usuário
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Retorna perfil do usuário com informações dinâmicas
        """
        serializer = UserSerializer(request.user)
        profile_data = serializer.data
        
        # Adiciona estatísticas dinâmicas baseadas nas features
        if FeatureToggle.is_enabled('REFERRAL_SYSTEM'):
            profile_data['referral_stats'] = {
                'total_referrals': request.user.referrals.count(),
                'referral_link': f"{request.build_absolute_uri('/')}{request.user.referral_code}"
            }
        
        log_api_activity(request.user, "profile_viewed")
        
        return APIResponseHandler.success(
            data=profile_data,
            message="Perfil do usuário obtido com sucesso"
        )


class DashboardView(APIView):
    """
    View modular para dashboard do usuário
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Retorna dados do dashboard adaptados às funcionalidades habilitadas
        """
        user = request.user
        dashboard_data = {
            'user': {
                'name': user.name,
                'username': user.username,
                'balance': float(user.balance),
                'referral_code': user.referral_code if FeatureToggle.is_enabled('REFERRAL_SYSTEM') else None
            },
            'system_info': SystemConfig.get_system_info()
        }
        
        log_api_activity(user, "dashboard_viewed")
        
        return APIResponseHandler.success(
            data=dashboard_data,
            message="Dashboard obtido com sucesso"
        )


class PaymentMethodsView(APIView):
    """
    View para métodos de pagamento disponíveis
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Retorna métodos de pagamento baseado nas features habilitadas
        """
        methods = SystemConfig.get_payment_methods()
        
        return APIResponseHandler.success(
            data=methods,
            message="Métodos de pagamento obtidos com sucesso"
        ) 