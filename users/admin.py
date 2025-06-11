"""
Configuração do Django Admin para o app de usuários
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from core.utils import FeatureToggle
from .models import User, UserProfile, UserActivity


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin personalizado para o modelo User
    """
    ordering = ('username',)
    list_display = (
        'username', 'email', 'name', 'balance', 'kyc_status', 
        'is_staff', 'is_active', 'date_joined'
    )
    list_filter = (
        'is_staff', 'is_active', 'kyc_status', 'country', 'date_joined'
    )
    search_fields = ('username', 'email', 'name', 'cpf', 'referral_code')
    readonly_fields = ('balance', 'referral_code', 'date_joined', 'last_login')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informações Pessoais'), {
            'fields': ('name', 'email', 'phone', 'country', 'cpf')
        }),
        (_('Sistema de Indicação'), {
            'fields': ('referral_code', 'sponsor'),
            'classes': ('collapse',) if not FeatureToggle.is_enabled('REFERRAL_SYSTEM') else ()
        }),
        (_('Financeiro'), {
            'fields': ('balance',),
            'classes': ('collapse',)
        }),
        (_('KYC'), {
            'fields': ('kyc_status', 'kyc_documents'),
            'classes': ('collapse',) if not FeatureToggle.is_enabled('KYC_VERIFICATION') else ()
        }),
        # As preferências de notificação são gerenciadas pelo app notifications
        (_('Permissões'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Datas Importantes'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'email', 'password1', 'password2'),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions')

    def get_queryset(self, request):
        """Otimizar consultas"""
        return super().get_queryset(request).select_related('sponsor')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin para perfis de usuário
    """
    list_display = ('user', 'birth_date', 'city', 'risk_tolerance', 'investment_experience')
    list_filter = ('gender', 'risk_tolerance', 'investment_experience', 'city', 'state')
    search_fields = ('user__username', 'user__name', 'user__email', 'profession', 'city')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (_('Informações Pessoais'), {
            'fields': ('user', 'birth_date', 'gender', 'profession', 'avatar')
        }),
        (_('Endereço'), {
            'fields': ('address', 'city', 'state', 'postal_code'),
            'classes': ('collapse',)
        }),
        (_('Informações Bancárias'), {
            'fields': ('bank_name', 'bank_account', 'pix_key'),
            'classes': ('collapse',)
        }),
        (_('Perfil de Investimento'), {
            'fields': ('risk_tolerance', 'investment_experience')
        }),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """
    Admin para atividades de usuário
    """
    list_display = ('user', 'action', 'created_at', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'user__name', 'action', 'description')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informações Básicas'), {
            'fields': ('user', 'action', 'description')
        }),
        (_('Dados Técnicos'), {
            'fields': ('ip_address', 'user_agent', 'extra_data'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# O admin para UserNotification foi migrado para o app notifications
# como NotificationAdmin, que é mais completo e modular
