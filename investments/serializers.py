"""
Serializers para o app de investimentos
"""
from rest_framework import serializers
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.utils import FeatureToggle, BusinessRulesValidator
from .models import Plan, Investment


class PlanSerializer(serializers.ModelSerializer):
    """
    Serializer para planos de investimento
    """
    is_available = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'image_src', 'color', 'min_value', 
            'tag', 'description', 'daily_percent', 'duration_days', 
            'cap_percent', 'withdrawal_policy', 'status', 
            'is_available', 'features', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_is_available(self, obj):
        """Verifica se o plano está disponível baseado nas configurações"""
        return obj.status == 'ACTIVE'
    
    def get_features(self, obj):
        """Retorna features dinâmicas baseadas nas configurações"""
        features = []
        if FeatureToggle.is_enabled('MULTI_CURRENCY'):
            features.append('multi_currency')
        if FeatureToggle.is_enabled('AUTOMATED_YIELDS'):
            features.append('automated_yields')
        return features


class InvestmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de investimentos
    """
    class Meta:
        model = Investment
        fields = ['plan', 'amount', 'deposit_source']
    
    def validate_amount(self, value):
        """Valida se o valor está dentro do mínimo do plano"""
        plan = self.initial_data.get('plan')
        if plan and hasattr(plan, 'min_value'):
            if value < plan.min_value:
                raise serializers.ValidationError(
                    f"Valor mínimo para este plano é {plan.min_value}"
                )
        return value


class InvestmentSerializer(serializers.ModelSerializer):
    """
    Serializer completo para investimentos
    """
    user = serializers.StringRelatedField(read_only=True)
    plan = PlanSerializer(read_only=True)
    deposit_source = serializers.StringRelatedField(read_only=True)  # Simplificado pois está em outro app
    status_display = serializers.CharField(source='get_investment_status_display', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    expected_daily_yield = serializers.SerializerMethodField()
    
    class Meta:
        model = Investment
        fields = [
            'id', 'user', 'plan', 'deposit_source', 'code', 'amount',
            'start_date', 'next_yield_date', 'expiration_date',
            'progress_percent', 'total_yielded', 'investment_status',
            'status_display', 'days_remaining', 'expected_daily_yield',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'code', 'start_date', 'next_yield_date',
            'expiration_date', 'progress_percent', 'total_yielded',
            'created_at', 'updated_at'
        ]
    
    def get_days_remaining(self, obj):
        """Retorna dias restantes do investimento"""
        return obj.get_days_remaining()
    
    def get_expected_daily_yield(self, obj):
        """Retorna rendimento diário esperado"""
        return obj.get_expected_daily_yield()


class InvestmentDashboardSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para dashboard de investimentos
    """
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Investment
        fields = [
            'id', 'code', 'plan_name', 'amount', 'investment_status',
            'progress_percent', 'total_yielded', 'days_remaining',
            'start_date', 'expiration_date'
        ]
    
    def get_days_remaining(self, obj):
        """Retorna dias restantes do investimento"""
        return obj.get_days_remaining() 