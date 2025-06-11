"""
Serializers para o app de pagamentos
"""
from rest_framework import serializers
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.utils import FeatureToggle, BusinessRulesValidator
from .models import Deposit, OnchainTransaction


class DepositCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de depósitos
    """
    class Meta:
        model = Deposit
        fields = [
            'plan', 'method', 'amount'
        ]
    
    def validate_amount(self, value):
        """Valida o valor do depósito baseado nas regras de negócio"""
        validator = BusinessRulesValidator()
        
        if not validator.validate_deposit_amount(value):
            min_amount = getattr(settings, 'BUSINESS_RULES', {}).get('MIN_DEPOSIT_AMOUNT', 10)
            max_amount = getattr(settings, 'BUSINESS_RULES', {}).get('MAX_DEPOSIT_AMOUNT', 50000)
            raise serializers.ValidationError(
                f"Valor deve estar entre {min_amount} e {max_amount}"
            )
        return value
    
    def validate_method(self, value):
        """Valida se o método de pagamento está habilitado"""
        if value == 'PIX' and not FeatureToggle.is_enabled('PIX_PAYMENTS'):
            raise serializers.ValidationError("Pagamentos PIX não estão habilitados")
        if value == 'USDT_BEP20' and not FeatureToggle.is_enabled('CRYPTO_PAYMENTS'):
            raise serializers.ValidationError("Pagamentos crypto não estão habilitados")
        return value


class DepositSerializer(serializers.ModelSerializer):
    """
    Serializer completo para depósitos
    """
    user = serializers.StringRelatedField(read_only=True)
    plan = serializers.StringRelatedField(read_only=True)
    method_display = serializers.CharField(source='get_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Deposit
        fields = [
            'id', 'user', 'plan', 'method', 'method_display', 
            'amount', 'status', 'status_display',
            'connectpay_transaction_id', 'coinpayments_txn_id',
            'payment_address', 'qrcode_url', 'status_url',
            'pix_qr_code_payload', 'pix_qr_code_image_url',
            'pix_key', 'pix_key_type', 'pix_beneficiary_name',
            'transaction_hash', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'connectpay_transaction_id', 
            'coinpayments_txn_id', 'payment_address', 'qrcode_url', 
            'status_url', 'pix_qr_code_payload', 'pix_qr_code_image_url',
            'pix_key', 'pix_key_type', 'pix_beneficiary_name',
            'transaction_hash', 'created_at', 'updated_at'
        ]


class OnchainTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer para transações on-chain
    """
    user = serializers.StringRelatedField(read_only=True)
    type_display = serializers.CharField(source='get_tx_type_display', read_only=True)
    status_display = serializers.CharField(source='get_transaction_status_display', read_only=True)
    tx_hash_short = serializers.SerializerMethodField()
    
    class Meta:
        model = OnchainTransaction
        fields = [
            'id', 'user', 'tx_type', 'type_display', 'transaction_status',
            'status_display', 'tx_hash', 'tx_hash_short', 'value', 'fee', 'timestamp',
            'notes', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at'
        ]
    
    def get_tx_hash_short(self, obj):
        """Retorna versão encurtada do hash"""
        if obj.tx_hash:
            return f"{obj.tx_hash[:10]}...{obj.tx_hash[-6:]}"
        return "-"


class PaymentDashboardSerializer(serializers.Serializer):
    """
    Serializer para dashboard de pagamentos
    """
    total_deposits = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_deposits = serializers.IntegerField()
    confirmed_deposits = serializers.IntegerField()
    total_onchain_transactions = serializers.IntegerField()
    recent_deposits = DepositSerializer(many=True)
    payment_methods_stats = serializers.DictField() 