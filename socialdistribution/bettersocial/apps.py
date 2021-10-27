from django.apps import AppConfig


class BettersocialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bettersocial'

    def ready(self):
        super().ready()

        # noinspection PyUnresolvedReferences
        # https://docs.djangoproject.com/en/3.2/topics/signals/#django.dispatch.receiver
        from . import signals
