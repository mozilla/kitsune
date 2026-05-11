import factory

from kitsune.customercare.models import SupportTicket, SupportTicketReplyOutbox
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


class SupportTicketReplyOutboxFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SupportTicketReplyOutbox

    ticket = factory.SubFactory(SupportTicketFactory)
    author = factory.SelfAttribute("ticket.user")
    body = factory.Faker("paragraph")
