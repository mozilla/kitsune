from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property

import waffle
from django.conf import settings

from kitsune.products.models import ProductSupportConfig, SupportCoverage, ZendeskConfig
from kitsune.products.utils import get_enterprise_companies
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
class ChatSupport:
    coverage: SupportCoverage | None = None
    reason: str | None = None

    @property
    def eligible(self) -> bool:
        return self.coverage is not None

    @property
    def disabled_site_wide(self) -> bool:
        return self.reason == "chat_is_disabled"


@dataclass(frozen=True)
class SupportAction:
    action: str | None = None
    can_switch: bool = False
    zendesk_config: ZendeskConfig | None = None
    coverage: SupportCoverage | None = None

    @property
    def support_type(self) -> str | None:
        if self.action == ProductSupportConfig.SUPPORT_TYPE_FORUM:
            return ProductSupportConfig.SUPPORT_TYPE_FORUM
        return ProductSupportConfig.SUPPORT_TYPE_ZENDESK if self.action else None


def chat_unavailable_reason() -> str | None:
    """Why the site can't offer chat to anyone, or None when it can."""
    if not waffle.switch_is_active("zendesk-chat"):
        return "chat_is_disabled"
    if not (
        settings.ZENDESK_CHAT_WIDGET_KEY
        and settings.ZENDESK_CHAT_SIGNING_SECRET
        and settings.ZENDESK_CHAT_SIGNING_KEY_ID
    ):
        return "chat_not_configured"
    return None


def resolve_enterprise_support(user, product, companies) -> EnterpriseSupport:
    """Resolve the single effective coverage of the product for the user's single company.

    `companies` holds up to two of the user's enterprise companies; two are ambiguous.
    """
    if not (user and user.is_authenticated):
        return EnterpriseSupport(reason="not_authenticated")
    if not user.is_active:
        return EnterpriseSupport(reason="inactive_user")
    if product.is_archived:
        return EnterpriseSupport(reason="product_unavailable")

    if not companies:
        return EnterpriseSupport(reason="no_company")
    if len(companies) > 1:
        return EnterpriseSupport(reason="ambiguous_company")

    coverages = list(
        SupportCoverage.objects.effective(companies[0])
        .filter(product=product)
        .select_related("contract__company", "zendesk_config")[:2]
    )
    if not coverages:
        return EnterpriseSupport(reason="no_coverage")
    if len(coverages) > 1:
        return EnterpriseSupport(reason="ambiguous_coverage")
    return EnterpriseSupport(coverage=coverages[0])


def resolve_chat(get_enterprise_support: Callable[[], EnterpriseSupport]) -> ChatSupport:
    """Chat needs the site's prerequisites, enterprise support, and its coverage's chat.

    Enterprise support is resolved only when the site can offer chat.
    """
    if reason := chat_unavailable_reason():
        return ChatSupport(reason=reason)
    enterprise_support = get_enterprise_support()
    if not (coverage := enterprise_support.coverage):
        return ChatSupport(reason=enterprise_support.reason)
    if not coverage.includes_chat:
        return ChatSupport(reason="chat_not_included")
    return ChatSupport(coverage=coverage)


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
        return ProductSupport(
            config=config,
            support_type=requested_type or config.default_support_type,
            can_switch=True,
        )

    @cached_property
    def enterprise_support(self) -> EnterpriseSupport:
        return resolve_enterprise_support(
            self.request.user, self.product, get_enterprise_companies(self.request)
        )

    @cached_property
    def chat(self) -> ChatSupport:
        return resolve_chat(lambda: self.enterprise_support)

    @property
    def preferred_ticket(self) -> str | None:
        legs = []
        if self.enterprise_support.eligible:
            legs.append(ENTERPRISE_SUPPORT)
        if self.product_support.has_ticket:
            legs.append(PRODUCT_SUPPORT)
        return max(legs, key=TICKET_WEIGHTS.__getitem__, default=None)

    @cached_property
    def aaq_action(self) -> SupportAction:
        has_forum = self.allows(ProductSupportConfig.SUPPORT_TYPE_FORUM)
        preferred_ticket = self.preferred_ticket
        requested_type = self.request.GET.get("support_type")
        if requested_type == ProductSupportConfig.SUPPORT_TYPE_FORUM and has_forum:
            action: str | None = ProductSupportConfig.SUPPORT_TYPE_FORUM
        elif preferred_ticket == ENTERPRISE_SUPPORT:
            action = ENTERPRISE_SUPPORT
        elif self.product_support.support_type == ProductSupportConfig.SUPPORT_TYPE_FORUM:
            action = ProductSupportConfig.SUPPORT_TYPE_FORUM
        else:
            action = preferred_ticket
        return self.select(action)

    def select(self, action) -> SupportAction:
        """Return the selection for an action this route allows."""
        can_switch = (
            self.allows(ProductSupportConfig.SUPPORT_TYPE_FORUM)
            and self.preferred_ticket is not None
        )
        if action == ENTERPRISE_SUPPORT and (coverage := self.enterprise_support.coverage):
            return SupportAction(
                action, can_switch, zendesk_config=coverage.zendesk_config, coverage=coverage
            )
        if action == PRODUCT_SUPPORT and (config := self.product_support.config):
            return SupportAction(action, can_switch, zendesk_config=config.zendesk_config)
        return SupportAction(action, can_switch)

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
