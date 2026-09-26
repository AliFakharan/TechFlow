from django.apps import AppConfig


class AuditAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "audit_app"
    label = "audit"
    verbose_name = "Log audit (log of changes)"
