"""
Views para o app financeiro
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, Avg
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.utils import APIResponseHandler, FeatureToggle, BusinessRulesValidator
from core.permissions import IsOwnerOrReadOnly, RequireFeature
from .models import Earning, FinancialReport
from .serializers import (
    EarningSerializer, EarningCreateSerializer,
    FinancialReportSerializer, FinancialDashboardSerializer,
    UserBalanceSerializer, EarningSummarySerializer
)


class EarningViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para rendimentos (somente leitura para usuários normais)
    """
    serializer_class = EarningSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retorna apenas rendimentos do usuário logado"""
        return Earning.objects.filter(user=self.request.user).order_by('-created_at')
    
    @extend_schema(
        summary="Lista rendimentos do usuário",
        description="Retorna todos os rendimentos do usuário autenticado",
        parameters=[
            OpenApiParameter(
                name='type',
                description='Filtrar por tipo de rendimento',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='status',
                description='Filtrar por status do rendimento',
                required=False,
                type=str
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Filtros opcionais
        earning_type = request.query_params.get('type')
        earning_status = request.query_params.get('status')
        
        if earning_type:
            queryset = queryset.filter(type=earning_type)
        if earning_status:
            queryset = queryset.filter(earning_status=earning_status)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return APIResponseHandler.success(data=serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Retorna resumo dos rendimentos"""
        user = request.user
        earnings = self.get_queryset()
        
        summary = {
            'total_earnings': earnings.aggregate(total=Sum('amount'))['total'] or 0,
            'pending_earnings': earnings.filter(earning_status='PENDING').aggregate(total=Sum('amount'))['total'] or 0,
            'available_earnings': earnings.filter(earning_status='AVAILABLE').aggregate(total=Sum('amount'))['total'] or 0,
            'confirmed_earnings': earnings.filter(earning_status='CONFIRMED').aggregate(total=Sum('amount'))['total'] or 0,
            'earnings_by_type': {}
        }
        
        # Rendimentos por tipo
        for earning_type, _ in Earning.EARNING_TYPES:
            type_total = earnings.filter(type=earning_type).aggregate(total=Sum('amount'))['total'] or 0
            summary['earnings_by_type'][earning_type] = type_total
        
        return APIResponseHandler.success(data=summary)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Dashboard completo de rendimentos"""
        user = request.user
        earnings = self.get_queryset()
        
        # Cálculos de período
        now = timezone.now()
        current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month = current_month - timedelta(days=1)
        last_month_start = last_month.replace(day=1)
        
        # Métricas básicas
        total_earnings = earnings.aggregate(total=Sum('amount'))['total'] or 0
        this_month_earnings = earnings.filter(
            effective_date__gte=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        last_month_earnings = earnings.filter(
            effective_date__gte=last_month_start,
            effective_date__lt=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Taxa de crescimento
        growth_rate = 0
        if last_month_earnings > 0:
            growth_rate = ((this_month_earnings - last_month_earnings) / last_month_earnings) * 100
        
        # Rendimentos por tipo
        earnings_by_type = {}
        for earning_type, _ in Earning.EARNING_TYPES:
            type_earnings = earnings.filter(type=earning_type)
            earnings_by_type[earning_type] = {
                'total': type_earnings.aggregate(total=Sum('amount'))['total'] or 0,
                'count': type_earnings.count(),
                'this_month': type_earnings.filter(
                    effective_date__gte=current_month
                ).aggregate(total=Sum('amount'))['total'] or 0
            }
        
        # Rendimentos por mês (últimos 6 meses)
        earnings_by_month = {}
        for i in range(6):
            month_start = (current_month - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            month_earnings = earnings.filter(
                effective_date__gte=month_start,
                effective_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            earnings_by_month[month_start.strftime('%Y-%m')] = month_earnings
        
        # Média diária
        days_since_first = (now.date() - user.date_joined.date()).days or 1
        avg_daily_earnings = total_earnings / days_since_first
        
        dashboard_data = {
            'total_earnings': total_earnings,
            'pending_earnings': earnings.filter(earning_status='PENDING').aggregate(total=Sum('amount'))['total'] or 0,
            'available_earnings': earnings.filter(earning_status='AVAILABLE').aggregate(total=Sum('amount'))['total'] or 0,
            'confirmed_earnings': earnings.filter(earning_status='CONFIRMED').aggregate(total=Sum('amount'))['total'] or 0,
            'earnings_by_type': earnings_by_type,
            'earnings_by_month': earnings_by_month,
            'recent_earnings': EarningSerializer(earnings[:5], many=True).data,
            'avg_daily_earnings': round(avg_daily_earnings, 2),
            'growth_rate': round(growth_rate, 2)
        }
        
        return APIResponseHandler.success(
            data=dashboard_data,
            message="Dashboard financeiro carregado com sucesso"
        )
    
    @action(detail=False, methods=['get'])
    def monthly_report(self, request):
        """Relatório mensal de rendimentos"""
        month = request.query_params.get('month')  # Format: YYYY-MM
        
        if not month:
            month = timezone.now().strftime('%Y-%m')
        
        try:
            year, month_num = month.split('-')
            start_date = datetime(int(year), int(month_num), 1).date()
            # Último dia do mês
            if int(month_num) == 12:
                end_date = datetime(int(year) + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(int(year), int(month_num) + 1, 1).date() - timedelta(days=1)
        except (ValueError, IndexError):
            return APIResponseHandler.error(
                message="Formato de mês inválido. Use YYYY-MM"
            )
        
        earnings = self.get_queryset().filter(
            effective_date__gte=start_date,
            effective_date__lte=end_date
        )
        
        report_data = {
            'period': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            'total_amount': earnings.aggregate(total=Sum('amount'))['total'] or 0,
            'count': earnings.count(),
            'avg_amount': earnings.aggregate(avg=Avg('amount'))['avg'] or 0,
            'by_type': {}
        }
        
        # Detalhes por tipo
        for earning_type, _ in Earning.EARNING_TYPES:
            type_earnings = earnings.filter(type=earning_type)
            report_data['by_type'][earning_type] = {
                'total': type_earnings.aggregate(total=Sum('amount'))['total'] or 0,
                'count': type_earnings.count()
            }
        
        return APIResponseHandler.success(
            data=report_data,
            message="Relatório mensal gerado com sucesso"
        )


class FinancialReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para relatórios financeiros (admin only)
    """
    queryset = FinancialReport.objects.all().order_by('-created_at')
    serializer_class = FinancialReportSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @extend_schema(
        summary="Lista relatórios financeiros",
        description="Retorna relatórios financeiros do sistema (admin only)"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Gera um novo relatório financeiro"""
        report_type = request.data.get('report_type', 'DAILY')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        if not start_date or not end_date:
            return APIResponseHandler.error(
                message="start_date e end_date são obrigatórios"
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return APIResponseHandler.error(
                message="Formato de data inválido. Use YYYY-MM-DD"
            )
        
        # Verificar se já existe relatório para este período
        existing_report = FinancialReport.objects.filter(
            report_type=report_type,
            start_date=start_date,
            end_date=end_date
        ).first()
        
        if existing_report:
            return APIResponseHandler.error(
                message="Já existe um relatório para este período"
            )
        
        # Gerar dados do relatório
        report_data = self._generate_report_data(start_date, end_date)
        
        # Criar relatório
        report = FinancialReport.objects.create(
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            **report_data
        )
        
        return APIResponseHandler.success(
            data=FinancialReportSerializer(report).data,
            message="Relatório gerado com sucesso"
        )
    
    def _generate_report_data(self, start_date, end_date):
        """Gera dados agregados para o relatório"""
        from django.contrib.auth import get_user_model
        from payments.models import Deposit
        from investments.models import Investment
        
        User = get_user_model()
        
        # Filtros de data
        deposits = Deposit.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status='CONFIRMED'
        )
        
        investments = Investment.objects.filter(
            start_date__date__gte=start_date,
            start_date__date__lte=end_date
        )
        
        earnings = Earning.objects.filter(
            effective_date__gte=start_date,
            effective_date__lte=end_date
        )
        
        # Usuários ativos no período
        active_users = User.objects.filter(
            Q(deposits__created_at__date__gte=start_date,
              deposits__created_at__date__lte=end_date) |
            Q(investments__start_date__date__gte=start_date,
              investments__start_date__date__lte=end_date) |
            Q(earnings__effective_date__gte=start_date,
              earnings__effective_date__lte=end_date)
        ).distinct().count()
        
        # Novos usuários no período
        new_users = User.objects.filter(
            date_joined__date__gte=start_date,
            date_joined__date__lte=end_date
        ).count()
        
        return {
            'total_deposits': deposits.aggregate(total=Sum('amount'))['total'] or 0,
            'total_investments': investments.aggregate(total=Sum('amount'))['total'] or 0,
            'total_earnings': earnings.aggregate(total=Sum('amount'))['total'] or 0,
            'active_users': active_users,
            'new_users': new_users,
            'detailed_data': {
                'deposits_count': deposits.count(),
                'investments_count': investments.count(),
                'earnings_count': earnings.count(),
                'earnings_by_type': {
                    earning_type: earnings.filter(type=earning_type).aggregate(
                        total=Sum('amount')
                    )['total'] or 0
                    for earning_type, _ in Earning.EARNING_TYPES
                }
            }
        }
