from django.apps import AppConfig


class PlataformaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plataforma'
    icon = 'fa fa-user'

    def ready(self):
        import plataforma.signals
