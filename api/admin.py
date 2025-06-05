# app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, Plan, Deposit, Investment, Earning, OnchainTransaction


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('username',)
    list_display = ('username', 'email', 'name', 'balance', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'country')
    search_fields = ('username', 'email', 'name')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal Info'), {'fields': ('name', 'email', 'phone', 'country', 'cpf', 'balance', 'referral_code', 'sponsor')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important Dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'email', 'password', 'password2', 'is_staff', 'is_active'),
        }),
    )
    readonly_fields = ('balance', 'last_login', 'date_joined', 'referral_code')
    filter_horizontal = ('groups', 'user_permissions')

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'method', 'status', 'created_at', 'coinpayments_txn_id')
    list_filter = ('status', 'method', 'created_at')
    search_fields = ('user__email', 'payment_address', 'coinpayments_txn_id', 'transaction_hash')
    readonly_fields = ('user', 'created_at', 'coinpayments_txn_id', 'payment_address', 'qrcode_url', 'status_url', 'transaction_hash')
    
    fieldsets = (
        ('Informações Principais', {
            'fields': ('user', 'amount', 'method', 'status', 'created_at')
        }),
        ('Dados do Gateway de Pagamento (CoinPayments)', {
            'fields': ('coinpayments_txn_id', 'payment_address', 'qrcode_url', 'status_url', 'transaction_hash')
        }),
    )


admin.site.register((Plan, Investment, Earning, OnchainTransaction))
