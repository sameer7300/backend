from django.apps import AppConfig

class UserDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.user_dashboard'
    verbose_name = 'User Dashboard'

    def ready(self):
        try:
            import apps.user_dashboard.signals
        except ImportError:
            pass
