from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'
    verbose_name = 'Sistema de Auditoria'
    
    def ready(self):
        # Importar signals para garantir que sejam registrados
        import audit.signals
        # Registrar models auditados dinamicamente
        audit.signals.register_audited_models()
