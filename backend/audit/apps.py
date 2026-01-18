from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'
    verbose_name = 'Auditoría'

    def ready(self):
        """Importa las señales cuando la app está lista"""
        import audit.signals  # noqa
