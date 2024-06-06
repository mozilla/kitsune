from django.apps import AppConfig


class ProductsConfig(AppConfig):
    name = "kitsune.products"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from kitsune.products import signals  # noqa
