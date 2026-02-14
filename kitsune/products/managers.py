from typing import Any

from django.db.models import Manager


class NonArchivedManager(Manager):
    def get_queryset(self):
        # Filter out archived objects by default.
        return super().get_queryset().filter(is_archived=False)


class ProductManager(NonArchivedManager):
    def with_question_forums(self, language_code: str = ""):
        q_kwargs: dict[str, Any] = {
            "support_configs__is_active": True,
            "support_configs__forum_config__enabled_locales__isnull": False,
        }

        if language_code:
            q_kwargs["support_configs__forum_config__enabled_locales__locale"] = language_code

        return self.filter(**q_kwargs).distinct()


class ProductSupportConfigManager(Manager):
    def locales_list(self):
        """Returns list of locales that have active forum support configurations."""
        return (
            self.filter(forum_config__enabled_locales__locale__isnull=False)
            .values_list("forum_config__enabled_locales__locale", flat=True)
            .distinct()
        )

    def route_support_request(self, request, product):
        """
        Determines which support channel to route a request to (forum or Zendesk).

        Handles group-based access control for hybrid products and honors user
        preferences via query parameters when permitted.

        Args:
            request: HttpRequest object
            product: Product instance

        Returns:
            tuple: (support_type, can_switch)
                - support_type: SUPPORT_TYPE_FORUM, SUPPORT_TYPE_ZENDESK, or None
                - can_switch: whether user can toggle between channels
                - Returns (None, False) if no config exists - view should handle error
        """
        from kitsune.products.models import ProductSupportConfig

        # Query config for this product
        try:
            support_config = self.get(product=product, is_active=True)
        except self.model.DoesNotExist:
            return (None, False)

        user = request.user
        requested_type = request.GET.get("support_type")

        # Validate requested_type
        if requested_type and requested_type not in [
            ProductSupportConfig.SUPPORT_TYPE_FORUM,
            ProductSupportConfig.SUPPORT_TYPE_ZENDESK,
        ]:
            requested_type = None

        # Non-hybrid: Only one support type available, no switching
        if not support_config.is_hybrid:
            if support_config.enable_forum_support:
                return (ProductSupportConfig.SUPPORT_TYPE_FORUM, False)
            elif support_config.enable_zendesk_support:
                return (ProductSupportConfig.SUPPORT_TYPE_ZENDESK, False)
            else:
                raise ValueError(f"No support channels enabled for product {product.slug}")

        # Hybrid without groups: All users can switch
        if not support_config.hybrid_support_groups.exists():
            support_type = requested_type or support_config.default_support_type
            return (support_type, True)

        # Hybrid with groups: Check user membership
        user_in_group = (
            user.is_authenticated
            and support_config.hybrid_support_groups.filter(
                id__in=user.groups.values_list("id", flat=True)
            ).exists()
        )

        if not user_in_group:
            return (support_config.default_support_type, False)

        # User in group: Can switch, use group default or general default
        default = support_config.group_default_support_type or support_config.default_support_type
        support_type = requested_type or default
        return (support_type, True)
