from django.apps import AppConfig

class PortfolioChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.portfolio_chat'
    verbose_name = 'Portfolio Chat System'

    def ready(self):
        import apps.portfolio_chat.signals  # noqa
