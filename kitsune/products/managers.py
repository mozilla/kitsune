from django.db.models import Manager


class NonArchivedManager(Manager):
    def get_queryset(self):
        # Filter out archived objects by default.
        return super().get_queryset().filter(is_archived=False)


class ProductManager(NonArchivedManager):
    def with_question_forums(self, request, include_products_with_ticketing_support=False):
        qs = self.filter(
            aaq_configs__is_active=True,
            aaq_configs__enabled_locales__locale=request.LANGUAGE_CODE,
        )
        if not include_products_with_ticketing_support:
            qs = qs.filter(codename="")
        return qs.distinct()
