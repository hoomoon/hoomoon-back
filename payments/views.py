"""
Views para o app de pagamentos
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, OpenApiParameter

from core.utils import APIResponseHandler, FeatureToggle, BusinessRulesValidator
from core.permissions import IsOwnerOrReadOnly, RequireFeature
from .models import Deposit, OnchainTransaction
from .serializers import (
    DepositSerializer, DepositCreateSerializer,
    OnchainTransactionSerializer, PaymentDashboardSerializer
)
from .connectpay_service import ConnectPayService
from .coinpayments_service import CoinPaymentsService


class DepositViewSet(viewsets.ModelViewSet):
    """
    ViewSet para depósitos
    """
    serializer_class = DepositSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retorna apenas depósitos do usuário logado"""
        return Deposit.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        """Usa serializer específico para criação"""
        if self.action == 'create':
            return DepositCreateSerializer
        return DepositSerializer
    
    def perform_create(self, serializer):
        """Associa o depósito ao usuário logado"""
        serializer.save(user=self.request.user)
    
    @extend_schema(
        summary="Lista depósitos do usuário",
        description="Retorna todos os depósitos do usuário autenticado"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Criar novo depósito",
        description="Cria um novo depósito para o usuário autenticado"
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            deposit = serializer.save(user=request.user)
            
            # Integração com gateways de pagamento baseada no método
            if deposit.method == 'PIX':
                self._process_pix_payment(deposit)
            elif deposit.method == 'USDT_BEP20':
                self._process_crypto_payment(deposit)
            
            response_data = DepositSerializer(deposit).data
            return APIResponseHandler.success(
                data=response_data,
                message="Depósito criado com sucesso"
            )
        return APIResponseHandler.error(
            message="Erro na validação",
            errors=serializer.errors
        )
    
    @action(detail=True, methods=['post'])
    @RequireFeature('PIX_PAYMENTS')
    def process_pix(self, request, pk=None):
        """Processa pagamento PIX para o depósito"""
        deposit = self.get_object()
        
        if deposit.method != 'PIX':
            return APIResponseHandler.error(
                message="Este depósito não é via PIX"
            )
        
        try:
            connectpay_service = ConnectPayService()
            result = connectpay_service.create_pix_payment(deposit)
            
            if result.get('success'):
                # Atualizar depósito com dados do PIX
                deposit.pix_qr_code_payload = result.get('qr_code_payload')
                deposit.pix_qr_code_image_url = result.get('qr_code_image_url')
                deposit.connectpay_transaction_id = result.get('transaction_id')
                deposit.save()
                
                return APIResponseHandler.success(
                    data=DepositSerializer(deposit).data,
                    message="Pagamento PIX processado com sucesso"
                )
            else:
                return APIResponseHandler.error(
                    message="Erro no processamento PIX",
                    errors=result.get('errors')
                )
        except Exception as e:
            return APIResponseHandler.error(
                message="Erro interno no processamento PIX"
            )
    
    @action(detail=True, methods=['post'])
    @RequireFeature('CRYPTO_PAYMENTS')
    def process_crypto(self, request, pk=None):
        """Processa pagamento crypto para o depósito"""
        deposit = self.get_object()
        
        if deposit.method != 'USDT_BEP20':
            return APIResponseHandler.error(
                message="Este depósito não é via crypto"
            )
        
        try:
            coinpayments_service = CoinPaymentsService()
            result = coinpayments_service.create_transaction(deposit)
            
            if result.get('success'):
                # Atualizar depósito com dados crypto
                deposit.payment_address = result.get('address')
                deposit.qrcode_url = result.get('qr_code_url')
                deposit.coinpayments_txn_id = result.get('txn_id')
                deposit.save()
                
                return APIResponseHandler.success(
                    data=DepositSerializer(deposit).data,
                    message="Pagamento crypto processado com sucesso"
                )
            else:
                return APIResponseHandler.error(
                    message="Erro no processamento crypto",
                    errors=result.get('errors')
                )
        except Exception as e:
            return APIResponseHandler.error(
                message="Erro interno no processamento crypto"
            )
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Dashboard de pagamentos do usuário"""
        user = request.user
        deposits = self.get_queryset()
        
        # Estatísticas
        total_deposits = deposits.aggregate(total=Sum('amount'))['total'] or 0
        pending_deposits = deposits.filter(status='PENDING').count()
        confirmed_deposits = deposits.filter(status='CONFIRMED').count()
        
        # Estatísticas por método de pagamento
        payment_methods_stats = {}
        for method, _ in Deposit.METHOD_CHOICES:
            method_deposits = deposits.filter(method=method)
            payment_methods_stats[method] = {
                'count': method_deposits.count(),
                'total_amount': method_deposits.aggregate(total=Sum('amount'))['total'] or 0
            }
        
        dashboard_data = {
            'total_deposits': total_deposits,
            'pending_deposits': pending_deposits,
            'confirmed_deposits': confirmed_deposits,
            'total_onchain_transactions': user.onchain_txs.count(),
            'recent_deposits': DepositSerializer(deposits[:5], many=True).data,
            'payment_methods_stats': payment_methods_stats
        }
        
        return APIResponseHandler.success(
            data=dashboard_data,
            message="Dashboard carregado com sucesso"
        )
    
    def _process_pix_payment(self, deposit):
        """Processa pagamento PIX automaticamente na criação"""
        if FeatureToggle.is_enabled('PIX_PAYMENTS'):
            try:
                connectpay_service = ConnectPayService()
                result = connectpay_service.create_pix_payment(deposit)
                if result.get('success'):
                    deposit.pix_qr_code_payload = result.get('qr_code_payload')
                    deposit.pix_qr_code_image_url = result.get('qr_code_image_url')
                    deposit.connectpay_transaction_id = result.get('transaction_id')
                    deposit.save()
            except Exception:
                pass  # Log error in production
    
    def _process_crypto_payment(self, deposit):
        """Processa pagamento crypto automaticamente na criação"""
        if FeatureToggle.is_enabled('CRYPTO_PAYMENTS'):
            try:
                coinpayments_service = CoinPaymentsService()
                result = coinpayments_service.create_transaction(deposit)
                if result.get('success'):
                    deposit.payment_address = result.get('address')
                    deposit.qrcode_url = result.get('qr_code_url')
                    deposit.coinpayments_txn_id = result.get('txn_id')
                    deposit.save()
            except Exception:
                pass  # Log error in production


class OnchainTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para transações on-chain (somente leitura)
    """
    serializer_class = OnchainTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Retorna apenas transações do usuário logado"""
        return OnchainTransaction.objects.filter(user=self.request.user).order_by('-timestamp')
    
    @extend_schema(
        summary="Lista transações on-chain do usuário",
        description="Retorna todas as transações blockchain do usuário autenticado"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def blockchain_info(self, request, pk=None):
        """Retorna informações detalhadas da blockchain para uma transação"""
        transaction = self.get_object()
        
        # URLs para exploradores de blockchain
        blockchain_explorers = {
            'BSC': f"https://bscscan.com/tx/{transaction.tx_hash}",
            'ETH': f"https://etherscan.io/tx/{transaction.tx_hash}",
            'BTC': f"https://blockchair.com/bitcoin/transaction/{transaction.tx_hash}"
        }
        
        # Por padrão, assumimos BSC para USDT BEP20
        explorer_url = blockchain_explorers.get('BSC', '#')
        
        blockchain_data = {
            'transaction': OnchainTransactionSerializer(transaction).data,
            'explorer_url': explorer_url,
            'blockchain_network': 'BSC',  # Configurável baseado no tipo de transação
            'confirmations_required': 12,  # Configurável por rede
        }
        
        return APIResponseHandler.success(
            data=blockchain_data,
            message="Informações da blockchain carregadas com sucesso"
        )
