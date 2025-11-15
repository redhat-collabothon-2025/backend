from django.apps import AppConfig


class WhitehatAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'whitehat_app'

    def ready(self):
        import whitehat_app.signals  # noqa
