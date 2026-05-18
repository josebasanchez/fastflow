from django.apps import AppConfig


class RestauranteConfig(AppConfig):
    name = 'restaurante'

    def ready(self):
        # Ensure signal handlers are registered.
        from . import signals  # noqa: F401
