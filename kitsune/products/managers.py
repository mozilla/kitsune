from django.db.models import Manager


class NonArchivedManager(Manager):
    def get_queryset(self):
        # Filter out archived objects by default.
        return super().get_queryset().filter(is_archived=False)


class ProductManager(NonArchivedManager):
    def with_question_forums(self, request):
        return self.filter(questions_locales__locale=request.LANGUAGE_CODE).filter(codename="")
