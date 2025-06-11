"""
Views para sistema de referrals
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.utils import APIResponseHandler
from core.permissions import IsOwnerOrReadOnly
from .models import ReferralProgram, ReferralLink, Referral, ReferralEarning
from .serializers import (
    ReferralProgramSerializer, ReferralLinkSerializer, ReferralLinkCreateSerializer,
    ReferralSerializer, ReferralEarningSerializer, ReferralDashboardSerializer
)


class ReferralProgramViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para programas de referral (somente leitura)
    """
    queryset = ReferralProgram.objects.filter(status=True).order_by('-is_default', '-created_at')
    serializer_class = ReferralProgramSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Lista programas de referral",
        description="Retorna programas de referral disponíveis"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ReferralLinkViewSet(viewsets.ModelViewSet):
    """
    ViewSet para links de referral
    """
    serializer_class = ReferralLinkSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retorna apenas links do usuário logado"""
        return ReferralLink.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        """Usa serializer específico para criação"""
        if self.action == 'create':
            return ReferralLinkCreateSerializer
        return ReferralLinkSerializer
    
    @extend_schema(
        summary="Lista links de referral do usuário",
        description="Retorna todos os links de referral do usuário autenticado"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Criar novo link de referral",
        description="Cria um novo link de referral para o usuário autenticado"
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            link = serializer.save()
            response_data = ReferralLinkSerializer(link).data
            return APIResponseHandler.success(
                data=response_data,
                message="Link de referral criado com sucesso"
            )
        return APIResponseHandler.error(
            message="Erro na validação",
            errors=serializer.errors
        )


class ReferralViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para referrals (somente leitura)
    """
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retorna referrals do usuário logado (como referrer)"""
        return Referral.objects.filter(referrer=self.request.user).order_by('-created_at')
    
    @extend_schema(
        summary="Lista referrals do usuário",
        description="Retorna todos os referrals feitos pelo usuário autenticado"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ReferralEarningViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ganhos de referral (somente leitura)
    """
    serializer_class = ReferralEarningSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retorna ganhos do usuário logado"""
        return ReferralEarning.objects.filter(referrer=self.request.user).order_by('-earned_at')
    
    @extend_schema(
        summary="Lista ganhos de referral do usuário",
        description="Retorna todos os ganhos de referral do usuário autenticado"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Dashboard de referrals do usuário"""
        user = request.user
        referrals = Referral.objects.filter(referrer=user)
        earnings = self.get_queryset()
        links = ReferralLink.objects.filter(user=user)
        
        # Estatísticas básicas
        total_referrals = referrals.count()
        active_referrals = referrals.filter(referral_status='ACTIVE').count()
        completed_referrals = referrals.filter(referral_status='COMPLETED').count()
        pending_referrals = referrals.filter(referral_status='PENDING').count()
        
        # Performance dos links
        total_clicks = links.aggregate(total=Sum('clicks'))['total'] or 0
        total_conversions = links.aggregate(total=Sum('conversions'))['total'] or 0
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        
        # Ganhos
        total_earnings = earnings.aggregate(total=Sum('amount'))['total'] or 0
        pending_earnings = earnings.filter(earning_status='PENDING').aggregate(total=Sum('amount'))['total'] or 0
        paid_earnings = earnings.filter(earning_status='PAID').aggregate(total=Sum('amount'))['total'] or 0
        
        # Ganhos deste mês
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_earnings = earnings.filter(
            earned_at__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        dashboard_data = {
            'total_referrals': total_referrals,
            'active_referrals': active_referrals,
            'completed_referrals': completed_referrals,
            'pending_referrals': pending_referrals,
            'total_clicks': total_clicks,
            'total_conversions': total_conversions,
            'conversion_rate': round(conversion_rate, 2),
            'total_earnings': total_earnings,
            'pending_earnings': pending_earnings,
            'paid_earnings': paid_earnings,
            'this_month_earnings': this_month_earnings,
            'recent_referrals': ReferralSerializer(referrals[:5], many=True).data,
            'recent_earnings': ReferralEarningSerializer(earnings[:5], many=True).data,
            'active_links': ReferralLinkSerializer(links.filter(status=True), many=True).data,
        }
        
        return APIResponseHandler.success(
            data=dashboard_data,
            message="Dashboard de referrals carregado com sucesso"
        )
