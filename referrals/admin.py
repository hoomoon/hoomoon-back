"""
Admin interface para sistema de referrals
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count
from django.urls import reverse

from .models import ReferralProgram, ReferralLink, Referral, ReferralEarning


@admin.register(ReferralProgram)
class ReferralProgramAdmin(admin.ModelAdmin):
    """
    Admin para programas de referral
    """
    list_display = [
        'name', 'commission_rate', 'max_levels', 'min_payout',
        'is_default', 'auto_approve', 'is_active_display', 'start_date', 'status'
    ]
    list_filter = [
        'is_default', 'auto_approve', 'status', 'start_date', 'end_date'
    ]
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        (_('Informações Básicas'), {
            'fields': ['name', 'description', 'status']
        }),
        (_('Configurações de Comissão'), {
            'fields': ['commission_rate', 'max_levels', 'level_commissions']
        }),
        (_('Limites e Controles'), {
            'fields': ['min_payout', 'max_monthly_earnings', 'auto_approve']
        }),
        (_('Período de Validade'), {
            'fields': ['start_date', 'end_date']
        }),
        (_('Configurações'), {
            'fields': ['is_default'],
            'classes': ['collapse']
        }),
        (_('Timestamps'), {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def is_active_display(self, obj):
        """Mostra se o programa está ativo com ícone"""
        if obj.is_active():
            return format_html(
                '<span style="color: green;">✓ Ativo</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Inativo</span>'
        )
    is_active_display.short_description = _("Status Ativo")
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            referrals_count=Count('referrals'),
            total_earnings=Sum('referrals__earnings__amount')
        )


@admin.register(ReferralLink)
class ReferralLinkAdmin(admin.ModelAdmin):
    """
    Admin para links de referral
    """
    list_display = [
        'user', 'program', 'code', 'clicks', 'conversions', 
        'conversion_rate_display', 'total_earnings', 'status', 'created_at'
    ]
    list_filter = [
        'program', 'status', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'code'
    ]
    readonly_fields = [
        'uuid', 'clicks', 'conversions', 'total_earnings', 
        'created_at', 'updated_at', 'full_url_display'
    ]
    
    fieldsets = [
        (_('Usuário e Programa'), {
            'fields': ['user', 'program']
        }),
        (_('Identificadores'), {
            'fields': ['code', 'uuid', 'full_url_display']
        }),
        (_('Métricas'), {
            'fields': ['clicks', 'conversions', 'total_earnings'],
            'classes': ['collapse']
        }),
        (_('Configurações'), {
            'fields': ['custom_landing_page', 'notes', 'status']
        }),
        (_('Timestamps'), {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def conversion_rate_display(self, obj):
        """Mostra taxa de conversão formatada"""
        rate = obj.get_conversion_rate()
        if rate > 10:
            color = 'green'
        elif rate > 5:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, rate
        )
    conversion_rate_display.short_description = _("Taxa de Conversão")
    
    def full_url_display(self, obj):
        """Mostra URL completa do link"""
        url = obj.get_full_url()
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            url, url
        )
    full_url_display.short_description = _("URL Completa")


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    """
    Admin para referrals
    """
    list_display = [
        'referrer', 'referred', 'program', 'level', 'referral_status',
        'registered_at', 'first_purchase_at', 'created_at'
    ]
    list_filter = [
        'referral_status', 'level', 'program', 'registered_at', 
        'first_purchase_at', 'created_at'
    ]
    search_fields = [
        'referrer__username', 'referrer__email',
        'referred__username', 'referred__email'
    ]
    readonly_fields = [
        'clicked_at', 'registered_at', 'first_purchase_at',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = [
        (_('Relacionamentos'), {
            'fields': ['referrer', 'referred', 'program', 'referral_link']
        }),
        (_('Status e Nível'), {
            'fields': ['referral_status', 'level']
        }),
        (_('Dados de Rastreamento'), {
            'fields': ['ip_address', 'user_agent', 'referrer_url'],
            'classes': ['collapse']
        }),
        (_('Timeline'), {
            'fields': [
                'clicked_at', 'registered_at', 'first_purchase_at'
            ],
            'classes': ['collapse']
        }),
        (_('Sistema'), {
            'fields': ['status', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    actions = ['mark_as_active', 'mark_as_completed']
    
    def mark_as_active(self, request, queryset):
        """Marca referrals como ativos"""
        count = 0
        for referral in queryset.filter(referral_status='PENDING'):
            referral.mark_as_active()
            count += 1
        
        self.message_user(
            request,
            f"{count} referrals marcados como ativos."
        )
    mark_as_active.short_description = _("Marcar como ativos")
    
    def mark_as_completed(self, request, queryset):
        """Marca referrals como completados"""
        count = 0
        for referral in queryset.filter(referral_status='ACTIVE'):
            referral.mark_first_purchase()
            count += 1
        
        self.message_user(
            request,
            f"{count} referrals marcados como completados."
        )
    mark_as_completed.short_description = _("Marcar como completados")


@admin.register(ReferralEarning)
class ReferralEarningAdmin(admin.ModelAdmin):
    """
    Admin para ganhos de referral
    """
    list_display = [
        'referrer', 'amount', 'commission_rate', 'source_type',
        'earning_status', 'earned_at', 'approved_at', 'paid_at'
    ]
    list_filter = [
        'earning_status', 'source_type', 'earned_at', 
        'approved_at', 'paid_at'
    ]
    search_fields = [
        'referrer__username', 'referrer__email', 'description'
    ]
    readonly_fields = [
        'earned_at', 'approved_at', 'paid_at', 
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'earned_at'
    
    fieldsets = [
        (_('Referral e Usuário'), {
            'fields': ['referral', 'referrer']
        }),
        (_('Origem do Ganho'), {
            'fields': ['source_type', 'source_id', 'description']
        }),
        (_('Valores'), {
            'fields': ['original_amount', 'commission_rate', 'amount']
        }),
        (_('Status e Timeline'), {
            'fields': [
                'earning_status', 'earned_at', 'approved_at', 'paid_at'
            ]
        }),
        (_('Notas Administrativas'), {
            'fields': ['admin_notes'],
            'classes': ['collapse']
        }),
        (_('Sistema'), {
            'fields': ['status', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    actions = ['approve_earnings', 'mark_as_paid', 'cancel_earnings']
    
    def approve_earnings(self, request, queryset):
        """Aprova ganhos pendentes"""
        count = 0
        for earning in queryset.filter(earning_status='PENDING'):
            earning.approve()
            count += 1
        
        self.message_user(
            request,
            f"{count} ganhos aprovados."
        )
    approve_earnings.short_description = _("Aprovar ganhos")
    
    def mark_as_paid(self, request, queryset):
        """Marca ganhos como pagos"""
        count = 0
        for earning in queryset.filter(earning_status='APPROVED'):
            earning.mark_as_paid()
            count += 1
        
        self.message_user(
            request,
            f"{count} ganhos marcados como pagos."
        )
    mark_as_paid.short_description = _("Marcar como pagos")
    
    def cancel_earnings(self, request, queryset):
        """Cancela ganhos"""
        count = 0
        for earning in queryset.exclude(earning_status='CANCELLED'):
            earning.cancel("Cancelado via admin")
            count += 1
        
        self.message_user(
            request,
            f"{count} ganhos cancelados."
        )
    cancel_earnings.short_description = _("Cancelar ganhos")


# Inlines para melhor UX
class ReferralInline(admin.TabularInline):
    """
    Inline para mostrar referrals de um usuário
    """
    model = Referral
    fk_name = 'referrer'
    extra = 0
    readonly_fields = ['referred', 'referral_status', 'level', 'created_at']
    fields = ['referred', 'referral_status', 'level', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


class ReferralEarningInline(admin.TabularInline):
    """
    Inline para mostrar ganhos de referral
    """
    model = ReferralEarning
    extra = 0
    readonly_fields = [
        'amount', 'commission_rate', 'source_type', 
        'earning_status', 'earned_at'
    ]
    fields = [
        'amount', 'commission_rate', 'source_type', 
        'earning_status', 'earned_at'
    ]
    
    def has_add_permission(self, request, obj=None):
        return False
