from typing import Any

from django.db.models import Manager


class NonArchivedManager(Manager):
    def get_queryset(self):
        # Filter out archived objects by default.
        return super().get_queryset().filter(is_archived=False)


class ProductManager(NonArchivedManager):
    def with_question_forums(self, language_code: str = ""):
        q_kwargs: dict[str, Any] = {
            "aaq_configs__is_active": True,
        }

        if language_code:
            q_kwargs["aaq_configs__enabled_locales__locale"] = language_code

        return self.filter(**q_kwargs).filter(codename="").distinct()


class ProductSupportConfigManager(Manager):
    def locales_list(self):
        """Returns list of locales that have active forum support configurations."""
        return (
            self.filter(forum_config__enabled_locales__locale__isnull=False)
            .values_list("forum_config__enabled_locales__locale", flat=True)
            .distinct()
        )
