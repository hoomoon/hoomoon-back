"""
Admin para models de pagamento
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Deposit, OnchainTransaction


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'method', 'amount', 'status', 'created_at', 'plan')
    list_filter = ('method', 'status', 'created_at')
    search_fields = ('user__username', 'user__email', 'connectpay_transaction_id', 'coinpayments_txn_id')
    readonly_fields = ('created_at', 'updated_at', 'connectpay_transaction_id', 'coinpayments_txn_id')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'plan', 'method', 'amount', 'status')
        }),
        ('CoinPayments', {
            'fields': ('coinpayments_txn_id', 'payment_address', 'qrcode_url', 'status_url'),
            'classes': ('collapse',)
        }),
        ('PIX/ConnectPay', {
            'fields': ('connectpay_transaction_id', 'pix_qr_code_payload', 'pix_qr_code_image_url', 
                      'pix_key', 'pix_key_type', 'pix_beneficiary_name'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'plan')


@admin.register(OnchainTransaction)
class OnchainTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tx_type', 'transaction_status', 'tx_hash_short', 'value', 'timestamp')
    list_filter = ('tx_type', 'transaction_status', 'timestamp')
    search_fields = ('user__username', 'tx_hash', 'value')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'timestamp'
    
    def tx_hash_short(self, obj):
        """Exibe versão encurtada do hash da transação"""
        if obj.tx_hash:
            return f"{obj.tx_hash[:10]}..."
        return "-"
    tx_hash_short.short_description = "Hash"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
