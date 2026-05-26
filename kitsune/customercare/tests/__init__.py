import factory

from kitsune.customercare.models import SupportTicket, SupportTicketPendingChange
from kitsune.products.tests import ProductFactory
from kitsune.users.tests import UserFactory


class SupportTicketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SupportTicket

    subject = factory.Sequence(lambda n: f"Test ticket {n}")
    description = factory.Faker("paragraph")
    category = "other"
    product = factory.SubFactory(ProductFactory)
    user = factory.SubFactory(UserFactory)
    email = factory.LazyAttribute(lambda obj: obj.user.email if obj.user else "test@example.com")
    submission_status = SupportTicket.STATUS_SENT


class SupportTicketPendingChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SupportTicketPendingChange

    ticket = factory.SubFactory(SupportTicketFactory)
    kind = SupportTicketPendingChange.KIND_COMMENT
    payload = "hello"
    status = SupportTicketPendingChange.STATUS_SENDING
