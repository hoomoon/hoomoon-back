# core/apps.py
"""
Configuração do app core
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuração do app core - funcionalidades base do sistema
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core System'
    
    def ready(self):
        """
        Código executado quando o app está pronto
        """
        # Importa signals se houver
        try:
            from . import signals  # noqa
        except ImportError:
            pass
