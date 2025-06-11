# core/admin.py
"""
Configuração do admin para o app core
"""
from django.contrib import admin
from .models import FeatureFlagModel


@admin.register(FeatureFlagModel)
class FeatureFlagAdmin(admin.ModelAdmin):
    """
    Admin para gerenciar feature flags via interface web
    """
    list_display = ('name', 'is_enabled', 'description', 'created_at', 'updated_at')
    list_filter = ('is_enabled', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_enabled',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Status', {
            'fields': ('is_enabled',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        """
        Torna o nome readonly quando editando um objeto existente
        """
        if obj:  # Editando
            return self.readonly_fields + ('name',)
        return self.readonly_fields
