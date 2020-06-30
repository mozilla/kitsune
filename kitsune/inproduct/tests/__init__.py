import factory

from kitsune.inproduct.models import Redirect


class RedirectFactory(factory.DjangoModelFactory):
    class Meta:
        model = Redirect

    target = "home"
