"""
Configuração do app de usuários
"""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Configuração para o app de gerenciamento de usuários
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Gerenciamento de Usuários'
    
    def ready(self):
        """
        Configurações executadas quando o app está pronto
        """
        # Importar sinais se necessário
        try:
            import users.signals  # noqa F401
        except ImportError:
            pass
