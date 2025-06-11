"""
Serializers para sistema de referrals
"""
from rest_framework import serializers
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from .models import ReferralProgram, ReferralLink, Referral, ReferralEarning


class ReferralProgramSerializer(serializers.ModelSerializer):
    """
    Serializer para programas de referral
    """
    is_active = serializers.SerializerMethodField()
    commission_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ReferralProgram
        fields = [
            'id', 'name', 'description', 'commission_rate', 
            'commission_display', 'max_levels', 'level_commissions',
            'min_payout', 'max_monthly_earnings', 'start_date', 
            'end_date', 'is_default', 'auto_approve', 'is_active',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_active(self, obj):
        """Retorna se o programa está ativo"""
        return obj.is_active()
    
    def get_commission_display(self, obj):
        """Retorna comissão formatada"""
        return f"{obj.commission_rate}%"


class ReferralLinkSerializer(serializers.ModelSerializer):
    """
    Serializer para links de referral
    """
    user = serializers.StringRelatedField(read_only=True)
    program = ReferralProgramSerializer(read_only=True)
    full_url = serializers.SerializerMethodField()
    conversion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ReferralLink
        fields = [
            'id', 'user', 'program', 'code', 'uuid', 'full_url',
            'clicks', 'conversions', 'conversion_rate', 'total_earnings',
            'custom_landing_page', 'notes', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'uuid', 'clicks', 'conversions', 
            'total_earnings', 'created_at', 'updated_at'
        ]
    
    def get_full_url(self, obj):
        """Retorna URL completa do link"""
        return obj.get_full_url()
    
    def get_conversion_rate(self, obj):
        """Retorna taxa de conversão"""
        return round(obj.get_conversion_rate(), 2)


class ReferralLinkCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de links de referral
    """
    program_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ReferralLink
        fields = ['program_id', 'code', 'custom_landing_page', 'notes']
    
    def validate_program_id(self, value):
        """Valida se o programa existe e está ativo"""
        try:
            program = ReferralProgram.objects.get(id=value)
            if not program.is_active():
                raise serializers.ValidationError(
                    "Programa não está ativo"
                )
            return value
        except ReferralProgram.DoesNotExist:
            raise serializers.ValidationError(
                "Programa não encontrado"
            )
    
    def validate_code(self, value):
        """Valida se o código é único"""
        if ReferralLink.objects.filter(code=value).exists():
            raise serializers.ValidationError(
                "Este código já está em uso"
            )
        return value
    
    def create(self, validated_data):
        """Cria link de referral associado ao usuário"""
        program_id = validated_data.pop('program_id')
        program = ReferralProgram.objects.get(id=program_id)
        
        return ReferralLink.objects.create(
            user=self.context['request'].user,
            program=program,
            **validated_data
        )


class ReferralSerializer(serializers.ModelSerializer):
    """
    Serializer para referrals
    """
    referrer = serializers.StringRelatedField(read_only=True)
    referred = serializers.StringRelatedField(read_only=True)
    program = ReferralProgramSerializer(read_only=True)
    referral_link = ReferralLinkSerializer(read_only=True)
    status_display = serializers.CharField(
        source='get_referral_status_display', 
        read_only=True
    )
    
    class Meta:
        model = Referral
        fields = [
            'id', 'referrer', 'referred', 'program', 'referral_link',
            'referral_status', 'status_display', 'level', 'ip_address',
            'clicked_at', 'registered_at', 'first_purchase_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'referrer', 'referred', 'clicked_at', 'registered_at',
            'first_purchase_at', 'created_at', 'updated_at'
        ]


class ReferralEarningSerializer(serializers.ModelSerializer):
    """
    Serializer para ganhos de referral
    """
    referral = ReferralSerializer(read_only=True)
    referrer = serializers.StringRelatedField(read_only=True)
    source_type_display = serializers.CharField(
        source='get_source_type_display', 
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_earning_status_display', 
        read_only=True
    )
    
    class Meta:
        model = ReferralEarning
        fields = [
            'id', 'referral', 'referrer', 'source_type', 
            'source_type_display', 'source_id', 'original_amount',
            'commission_rate', 'amount', 'earning_status', 
            'status_display', 'description', 'earned_at',
            'approved_at', 'paid_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'referral', 'referrer', 'earned_at', 'approved_at',
            'paid_at', 'created_at', 'updated_at'
        ]


class ReferralDashboardSerializer(serializers.Serializer):
    """
    Serializer para dashboard de referrals
    """
    # Estatísticas básicas
    total_referrals = serializers.IntegerField()
    active_referrals = serializers.IntegerField()
    completed_referrals = serializers.IntegerField()
    pending_referrals = serializers.IntegerField()
    
    # Link performance
    total_clicks = serializers.IntegerField()
    total_conversions = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Ganhos
    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    this_month_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Breakdown
    earnings_by_source = serializers.DictField()
    referrals_by_level = serializers.DictField()
    monthly_performance = serializers.DictField()
    
    # Dados recentes
    recent_referrals = ReferralSerializer(many=True)
    recent_earnings = ReferralEarningSerializer(many=True)
    
    # Links ativos
    active_links = ReferralLinkSerializer(many=True)


class ReferralStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas detalhadas de referrals
    """
    period = serializers.CharField()
    total_referrals_made = serializers.IntegerField()
    successful_conversions = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_earning_per_referral = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    by_level = serializers.DictField()
    by_source_type = serializers.DictField()
    daily_breakdown = serializers.DictField()


class ReferralPayoutSerializer(serializers.Serializer):
    """
    Serializer para solicitação de saque de comissões
    """
    amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=Decimal('1.00')
    )
    payment_method = serializers.ChoiceField(
        choices=[
            ('PIX', _('PIX')),
            ('BANK_TRANSFER', _('Transferência Bancária')),
            ('CRYPTO', _('Criptomoeda')),
        ]
    )
    payment_details = serializers.JSONField(
        help_text=_("Detalhes do método de pagamento (chave PIX, dados bancários, etc.)")
    )
    
    def validate_amount(self, value):
        """Valida se o valor está disponível para saque"""
        user = self.context['request'].user
        
        # Verificar saldo disponível
        available_earnings = ReferralEarning.objects.filter(
            referrer=user,
            earning_status='APPROVED'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        if value > available_earnings:
            raise serializers.ValidationError(
                f"Valor solicitado excede saldo disponível: R$ {available_earnings}"
            )
        
        # Verificar valor mínimo
        default_program = ReferralProgram.objects.filter(
            is_default=True,
            status=True
        ).first()
        
        if default_program and value < default_program.min_payout:
            raise serializers.ValidationError(
                f"Valor mínimo para saque: R$ {default_program.min_payout}"
            )
        
        return value 