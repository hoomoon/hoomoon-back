"""
Admin para models financeiros
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Earning, FinancialReport


@admin.register(Earning)
class EarningAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'amount', 'earning_status', 'effective_date', 'investment_source')
    list_filter = ('type', 'earning_status', 'effective_date', 'created_at')
    search_fields = ('user__username', 'user__email', 'origin', 'description')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'effective_date'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'investment_source', 'type', 'amount', 'earning_status')
        }),
        ('Detalhes', {
            'fields': ('origin', 'description', 'effective_date')
        }),
        ('Status e Timestamps', {
            'fields': ('is_active', 'status', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'investment_source')


@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'start_date', 'end_date', 'total_deposits', 'total_investments', 
                   'total_earnings', 'active_users', 'created_at')
    list_filter = ('report_type', 'start_date', 'created_at')
    search_fields = ('report_type',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Período do Relatório', {
            'fields': ('report_type', 'start_date', 'end_date')
        }),
        ('Métricas Financeiras', {
            'fields': ('total_deposits', 'total_investments', 'total_earnings')
        }),
        ('Métricas de Usuários', {
            'fields': ('active_users', 'new_users')
        }),
        ('Dados Detalhados', {
            'fields': ('detailed_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def has_delete_permission(self, request, obj=None):
        """Previne deleção acidental de relatórios"""
        return request.user.is_superuser
