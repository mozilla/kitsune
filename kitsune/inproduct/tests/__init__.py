import factory

from kitsune.inproduct.models import Redirect


class RedirectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Redirect

    target = "home"
