import factory

from kitsune.postcrash.models import Signature
from kitsune.sumo.tests import FuzzyUnicode
from kitsune.wiki.tests import DocumentFactory


class SignatureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Signature

    document = factory.SubFactory(DocumentFactory)
    signature = FuzzyUnicode()
