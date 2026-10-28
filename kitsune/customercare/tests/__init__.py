import factory

from kitsune.customercare.models import SupportTicket, accepted_context_for
from kitsune.products.tests import ProductFactory, SupportCoverageFactory
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


class EnterpriseTicketFactory(SupportTicketFactory):
    coverage = factory.SubFactory(SupportCoverageFactory)
    product = factory.SelfAttribute("coverage.product")
    origin = SupportTicket.Origin.ENTERPRISE
    org_group = factory.SelfAttribute("coverage.contract.company")
    accepted_context = factory.LazyAttribute(
        lambda ticket: accepted_context_for(
            ticket.product, ticket.coverage.zendesk_config, ticket.coverage
        )
    )
