"""
Admin para o app de investimentos
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Plan, Investment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """
    Admin para planos de investimento
    """
    list_display = [
        'id', 'name', 'min_value', 'daily_percent', 'duration_days', 
        'status', 'colored_tag', 'created_at'
    ]
    list_filter = ['status', 'duration_days', 'created_at']
    search_fields = ['name', 'id', 'description']
    ordering = ['min_value']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'name', 'description', 'tag', 'status')
        }),
        ('Configurações Visuais', {
            'fields': ('image_src', 'color'),
            'classes': ('collapse',)
        }),
        ('Configurações Financeiras', {
            'fields': ('min_value', 'daily_percent', 'duration_days', 'cap_percent')
        }),
        ('Políticas', {
            'fields': ('withdrawal_policy',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def colored_tag(self, obj):
        """Exibe a tag com a cor do plano"""
        if obj.tag:
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
                obj.color,
                obj.tag
            )
        return '-'
    colored_tag.short_description = 'Tag'



@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    """
    Admin para investimentos
    """
    list_display = [
        'code', 'user', 'plan', 'amount', 'investment_status',
        'progress_percent', 'total_yielded', 'expiration_date'
    ]
    list_filter = ['investment_status', 'plan', 'start_date', 'expiration_date']
    search_fields = ['code', 'user__username', 'user__email', 'plan__name']
    ordering = ['-start_date']
    readonly_fields = ['code', 'created_at', 'updated_at', 'investment_link']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'plan', 'deposit_source', 'code', 'amount')
        }),
        ('Status e Progresso', {
            'fields': ('investment_status', 'status', 'progress_percent', 'total_yielded')
        }),
        ('Datas', {
            'fields': ('start_date', 'next_yield_date', 'expiration_date')
        }),
        ('Links', {
            'fields': ('investment_link',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def investment_link(self, obj):
        """Link para visualizar o investimento"""
        if obj.pk:
            url = reverse('admin:investments_investment_change', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">Ver Investimento</a>', url)
        return '-'
    investment_link.short_description = 'Link'
    
    def get_queryset(self, request):
        """Otimiza consultas incluindo relações"""
        return super().get_queryset(request).select_related('user', 'plan', 'deposit_source')


# Configurações adicionais do admin
admin.site.site_header = "HooMoon - Painel Administrativo"
admin.site.site_title = "HooMoon Admin"
admin.site.index_title = "Bem-vindo ao Painel de Administração"
