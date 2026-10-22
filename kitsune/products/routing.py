from dataclasses import dataclass
from functools import cached_property

from django.db.models import Q
from django.utils import timezone

from kitsune.customercare.utils import ChatEligibility, resolve_chat_eligibility
from kitsune.groups.models import GroupProfile
from kitsune.products.models import ProductSupportConfig, SupportContract, SupportCoverage
from kitsune.sumo.urlresolvers import reverse

ENTERPRISE_SUPPORT = "enterprise_support"
PRODUCT_SUPPORT = "product_support"
TICKET_WEIGHTS = {ENTERPRISE_SUPPORT: 20, PRODUCT_SUPPORT: 10}


@dataclass(frozen=True)
class ProductSupport:
    config: ProductSupportConfig | None = None
    support_type: str | None = None
    can_switch: bool = False
    redirect_url: str | None = None

    @property
    def has_ticket(self) -> bool:
        return self.support_type == ProductSupportConfig.SUPPORT_TYPE_ZENDESK or self.can_switch


@dataclass(frozen=True)
class EnterpriseSupport:
    coverage: SupportCoverage | None = None
    reason: str | None = None

    @property
    def eligible(self) -> bool:
        return self.coverage is not None


@dataclass(frozen=True)
class SupportForm:
    action: str | None = None
    can_switch: bool = False

    @property
    def support_type(self) -> str | None:
        if self.action == ProductSupportConfig.SUPPORT_TYPE_FORUM:
            return ProductSupportConfig.SUPPORT_TYPE_FORUM
        return ProductSupportConfig.SUPPORT_TYPE_ZENDESK if self.action else None


class SupportRoute:
    def __init__(self, request, product):
        self.request = request
        self.product = product

    @cached_property
    def product_support(self) -> ProductSupport:
        config = ProductSupportConfig.objects.active_for(self.product)
        if not (config and config.has_channel):
            return ProductSupport(config=config)

        if not config.admits(self.request.user):
            if config.unsubscribed_redirect_product_id:
                return ProductSupport(
                    config=config,
                    support_type=ProductSupportConfig.SUPPORT_TYPE_REDIRECT,
                    redirect_url=reverse(
                        "questions.aaq_step2",
                        kwargs={"product_slug": config.unsubscribed_redirect_product.slug},
                    ),
                )
            return ProductSupport(
                config=config, support_type=ProductSupportConfig.SUPPORT_TYPE_HIDE
            )

        if not config.is_hybrid:
            support_type = (
                ProductSupportConfig.SUPPORT_TYPE_FORUM
                if config.enable_forum_support
                else ProductSupportConfig.SUPPORT_TYPE_ZENDESK
            )
            return ProductSupport(config=config, support_type=support_type)

        requested_type = self.request.GET.get("support_type")
        if requested_type not in (
            ProductSupportConfig.SUPPORT_TYPE_FORUM,
            ProductSupportConfig.SUPPORT_TYPE_ZENDESK,
        ):
            requested_type = None

        user = self.request.user
        default = config.default_support_type
        if config.support_organizations.exists():
            # Direct membership counts too: legacy organizations may lack a group profile.
            is_member = (
                user.is_authenticated
                and config.support_organizations.filter(
                    Q(group_id__in=user.groups.values_list("id", flat=True))
                    | Q(group_id__in=GroupProfile.objects.containing(user).values("group_id"))
                ).exists()
            )
            if not is_member:
                return ProductSupport(config=config, support_type=default)
            default = config.group_default_support_type or default

        return ProductSupport(
            config=config, support_type=requested_type or default, can_switch=True
        )

    @cached_property
    def enterprise_support(self) -> EnterpriseSupport:
        user = self.request.user
        if not user.is_authenticated:
            return EnterpriseSupport(reason="not_authenticated")
        if not user.is_active:
            return EnterpriseSupport(reason="inactive_user")
        if self.product.is_archived:
            return EnterpriseSupport(reason="product_unavailable")

        companies = list(GroupProfile.objects.enterprise_companies(user)[:2])
        if not companies:
            return EnterpriseSupport(reason="no_company")
        if len(companies) > 1:
            return EnterpriseSupport(reason="ambiguous_company")

        today = timezone.localdate()
        coverages = list(
            SupportCoverage.objects.filter(
                product=self.product,
                contract__company=companies[0],
                contract__status=SupportContract.Status.ACTIVE,
                contract__starts_on__lte=today,
                contract__ends_on__gte=today,
            ).select_related("contract", "zendesk_config")[:2]
        )
        if not coverages:
            return EnterpriseSupport(reason="no_coverage")
        if len(coverages) > 1:
            return EnterpriseSupport(reason="ambiguous_coverage")
        return EnterpriseSupport(coverage=coverages[0])

    @cached_property
    def chat(self) -> ChatEligibility:
        return resolve_chat_eligibility(self.request.user, self.product)

    @property
    def preferred_ticket(self) -> str | None:
        legs = []
        if self.enterprise_support.eligible:
            legs.append(ENTERPRISE_SUPPORT)
        if self.product_support.has_ticket:
            legs.append(PRODUCT_SUPPORT)
        return max(legs, key=TICKET_WEIGHTS.__getitem__, default=None)

    @cached_property
    def aaq_action(self) -> SupportForm:
        has_forum = self.allows(ProductSupportConfig.SUPPORT_TYPE_FORUM)
        preferred_ticket = self.preferred_ticket
        requested_type = self.request.GET.get("support_type")
        if requested_type == ProductSupportConfig.SUPPORT_TYPE_FORUM and has_forum:
            action: str | None = ProductSupportConfig.SUPPORT_TYPE_FORUM
        elif preferred_ticket and (
            requested_type == ProductSupportConfig.SUPPORT_TYPE_ZENDESK
            or preferred_ticket == ENTERPRISE_SUPPORT
        ):
            action = preferred_ticket
        elif (
            has_forum
            and self.product_support.support_type == ProductSupportConfig.SUPPORT_TYPE_FORUM
        ):
            action = ProductSupportConfig.SUPPORT_TYPE_FORUM
        else:
            action = preferred_ticket
        return SupportForm(
            action=action,
            can_switch=has_forum and preferred_ticket is not None,
        )

    def allows(self, action, coverage_id=None) -> bool:
        if action == ENTERPRISE_SUPPORT:
            coverage = self.enterprise_support.coverage
            return coverage is not None and str(coverage.pk) == coverage_id
        if action == PRODUCT_SUPPORT:
            return self.preferred_ticket == PRODUCT_SUPPORT
        if action == ProductSupportConfig.SUPPORT_TYPE_FORUM:
            return (
                self.product_support.support_type == ProductSupportConfig.SUPPORT_TYPE_FORUM
                or self.product_support.can_switch
            )
        return False


def route_support(request, product) -> SupportRoute:
    if not hasattr(request, "_support_routes"):
        request._support_routes = {}
    if product.pk not in request._support_routes:
        request._support_routes[product.pk] = SupportRoute(request, product)
    return request._support_routes[product.pk]
