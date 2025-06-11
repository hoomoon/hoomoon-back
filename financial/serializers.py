"""
Serializers para o app financeiro
"""
from rest_framework import serializers
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from core.utils import FeatureToggle, BusinessRulesValidator
from .models import Earning, FinancialReport


class EarningSerializer(serializers.ModelSerializer):
    """
    Serializer para rendimentos
    """
    user = serializers.StringRelatedField(read_only=True)
    investment_source = serializers.StringRelatedField(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_earning_status_display', read_only=True)
    
    class Meta:
        model = Earning
        fields = [
            'id', 'user', 'investment_source', 'type', 'type_display',
            'origin', 'description', 'amount', 'earning_status',
            'status_display', 'effective_date', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'investment_source', 'created_at', 'updated_at'
        ]


class EarningCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de rendimentos (admin use)
    """
    class Meta:
        model = Earning
        fields = [
            'investment_source', 'type', 'origin', 'description',
            'amount', 'earning_status', 'effective_date'
        ]
    
    def validate_amount(self, value):
        """Valida se o valor do rendimento é positivo"""
        if value <= 0:
            raise serializers.ValidationError("Valor deve ser positivo")
        return value


class FinancialReportSerializer(serializers.ModelSerializer):
    """
    Serializer para relatórios financeiros
    """
    period_display = serializers.SerializerMethodField()
    duration_days = serializers.SerializerMethodField()
    
    class Meta:
        model = FinancialReport
        fields = [
            'id', 'report_type', 'start_date', 'end_date', 'period_display',
            'duration_days', 'total_deposits', 'total_investments', 
            'total_earnings', 'active_users', 'new_users',
            'detailed_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_period_display(self, obj):
        """Retorna período em formato legível"""
        return f"{obj.start_date.strftime('%d/%m/%Y')} - {obj.end_date.strftime('%d/%m/%Y')}"
    
    def get_duration_days(self, obj):
        """Retorna duração do período em dias"""
        return (obj.end_date - obj.start_date).days + 1


class FinancialDashboardSerializer(serializers.Serializer):
    """
    Serializer para dashboard financeiro
    """
    total_earnings = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_earnings = serializers.DecimalField(max_digits=15, decimal_places=2)
    available_earnings = serializers.DecimalField(max_digits=15, decimal_places=2)
    confirmed_earnings = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    earnings_by_type = serializers.DictField()
    earnings_by_month = serializers.DictField()
    recent_earnings = EarningSerializer(many=True)
    
    # Métricas de performance
    avg_daily_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    growth_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class UserBalanceSerializer(serializers.Serializer):
    """
    Serializer para saldo detalhado do usuário
    """
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    
    # Saldos
    current_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_invested = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    available_for_withdrawal = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Histórico
    last_earning = EarningSerializer()
    earnings_this_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_withdrawals = serializers.DecimalField(max_digits=12, decimal_places=2)


class EarningSummarySerializer(serializers.Serializer):
    """
    Serializer para resumo de rendimentos
    """
    period = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    count = serializers.IntegerField()
    avg_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    by_type = serializers.DictField() 