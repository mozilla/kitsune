from typing import Any, override

from django.conf import settings
from django.core.cache import cache
from django.db.models import Manager, Q
from django.utils import timezone

from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.config import PINNED_ARTICLE_LIMIT_Q, REDIRECT_HTML

CURATED_BLOCKS_CACHE_KEY = "products:curated-blocks:v1:{topic_id}:{product_id}:{locale}"
CURATED_QUESTIONS_CACHE_KEY = "products:curated-questions:v1:{topic_id}:{product_id}:{locale}"
MIN_ITEMS_SHOWN = 2
MAX_QUESTIONS_SHOWN = 4
# Curated articles are English sources, shown translated or as an English fallback.
CURATED_ARTICLE_Q = PINNED_ARTICLE_LIMIT_Q & Q(locale=settings.WIKI_DEFAULT_LANGUAGE)


class NonArchivedManager(Manager):
    @override
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

    SUPPORT_TYPE_REDIRECT = "redirect_unsubscribed"
    SUPPORT_TYPE_HIDE = "hide_unsubscribed"

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
                - support_type: SUPPORT_TYPE_FORUM, SUPPORT_TYPE_ZENDESK,
                  SUPPORT_TYPE_REDIRECT, SUPPORT_TYPE_HIDE, or None
                - can_switch: whether user can toggle between channels
                - Returns (None, False) if no config exists - view should handle error
        """
        # Avoid cycles: groups.models -> wiki.models -> products.models -> this manager.
        from kitsune.groups.models import GroupProfile
        from kitsune.products.models import ProductSupportConfig

        # Query config for this product
        try:
            support_config = self.get(product=product, is_active=True)
        except self.model.DoesNotExist:
            return (None, False)

        user = request.user

        # Subscription gate: check before any other routing logic
        if support_config.subscription_only:
            is_subscribed = (
                user.is_authenticated and user.profile.products.filter(id=product.id).exists()
            )
            if not is_subscribed:
                if support_config.unsubscribed_redirect_product_id:
                    return (self.SUPPORT_TYPE_REDIRECT, False)
                return (self.SUPPORT_TYPE_HIDE, False)

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

        # Hybrid without organizations: all users can switch
        if not support_config.support_organizations.exists():
            support_type = requested_type or support_config.default_support_type
            return (support_type, True)

        # Hybrid with organizations: check user membership
        user_in_group = (
            user.is_authenticated
            and support_config.support_organizations.filter(
                Q(group_id__in=user.groups.values_list("id", flat=True))
                | Q(group_id__in=GroupProfile.objects.containing(user).values("group_id"))
            ).exists()
        )

        if not user_in_group:
            return (support_config.default_support_type, False)

        # User in group: Can switch, use group default or general default
        default = support_config.group_default_support_type or support_config.default_support_type
        support_type = requested_type or default
        return (support_type, True)


def _question_card(row, locale):
    return {
        "url": reverse("questions.details", kwargs={"question_id": row["id"]}, locale=locale),
        "title": row["title"],
        "solved": row["solution_id"] is not None,
        "replies": row["num_answers"],
    }


class CuratedBlockManager(Manager):
    def for_page(self, product, topic, subtopic, locale):
        """Return the curated blocks of a product topic page as plain dicts.

        Blocks come in the order callout, articles, questions, at most one per kind. On a
        subtopic page the subtopic's own block of a kind wins over the parent topic's.
        Expired blocks, and article and question blocks left with fewer than two items,
        count as absent, so the parent topic's block of that kind shows instead.
        """
        now = timezone.now()
        owners = [subtopic, topic] if subtopic else [topic]
        chosen = {}
        for owner in owners:
            for block in self._for_topic(owner, product, locale):
                kind = block["kind"]
                if kind in chosen or (block["show_until"] and block["show_until"] <= now):
                    continue
                items = block["items"]
                if block["variant"] == self.model.Variant.AUTOMATIC:
                    items = self._popular_questions(owner, product, locale)
                if kind != self.model.Kind.CALLOUT and len(items) < MIN_ITEMS_SHOWN:
                    continue
                chosen[kind] = {
                    "kind": kind,
                    "variant": block["variant"],
                    "message": block["message"],
                    "items": items,
                }
            if len(chosen) == len(self.model.Kind.values):
                break
        return [chosen[kind] for kind in self.model.Kind.values if kind in chosen]

    def _for_topic(self, topic, product, locale):
        """Return the blocks of this topic and product, with items resolved to `locale`.

        `show_until` is left to the caller so the cached result stays valid. The receiver
        in signals.py clears it when a block or its items change.
        """
        cache_key = CURATED_BLOCKS_CACHE_KEY.format(
            topic_id=topic.pk, product_id=product.pk, locale=locale
        )
        resolved = cache.get(cache_key)
        if resolved is not None:
            return resolved

        # Avoid cycles: wiki.models -> products.models -> this manager.
        from kitsune.wiki.models import Document

        blocks = list(self.filter(topic=topic, product=product).prefetch_related("items"))
        items = [item for block in blocks for item in block.items.all()]
        is_default_locale = locale == settings.WIKI_DEFAULT_LANGUAGE

        document_ids = {item.document_id for item in items if item.document_id}
        documents = {}
        translations = {}
        if document_ids:
            documents = {
                document.pk: document
                for document in product.document_set.filter(CURATED_ARTICLE_Q, pk__in=document_ids)
                .select_related("current_revision")
                .only("title", "slug", "locale", "current_revision", "current_revision__summary")
            }
        if documents and not is_default_locale:
            translations = {
                translation.parent_id: translation
                for translation in Document.objects.visible(
                    locale=locale,
                    parent__in=list(documents),
                    is_archived=False,
                    category__in=settings.IA_DEFAULT_CATEGORIES,
                )
                .exclude(html__startswith=REDIRECT_HTML)
                .select_related("current_revision")
                .only(
                    "title",
                    "slug",
                    "locale",
                    "parent",
                    "current_revision",
                    "current_revision__summary",
                )
            }

        question_ids = {item.question_id for item in items if item.question_id}
        questions = {}
        if question_ids:
            questions = {
                row["id"]: row
                for row in product.questions.filter(
                    pk__in=question_ids, locale=locale, is_spam=False, is_archived=False
                ).values("id", "title", "num_answers", "solution_id")
            }

        resolved = []
        for block in blocks:
            cards = []
            for item in block.items.all():
                if block.kind == self.model.Kind.QUESTIONS:
                    if item.question_id in questions:
                        cards.append(_question_card(questions[item.question_id], locale))
                    continue
                document = documents.get(item.document_id)
                if document is None:
                    continue
                translation = translations.get(document.pk)
                shown = translation or document
                url = shown.get_absolute_url()
                is_english_fallback = translation is None and not is_default_locale
                if is_english_fallback:
                    url = url.replace(f"/{settings.WIKI_DEFAULT_LANGUAGE}/", f"/{locale}/", 1)
                cards.append(
                    {
                        "url": url,
                        "title": shown.title,
                        "summary": shown.current_revision.summary,
                        "english": is_english_fallback,
                        "source_id": document.pk,
                    }
                )
            resolved.append(
                {
                    "kind": block.kind,
                    "variant": block.variant,
                    "message": block.message,
                    "show_until": block.show_until,
                    "items": cards,
                }
            )

        cache.set(cache_key, resolved, settings.CACHE_LONG_TIMEOUT)
        return resolved

    def _popular_questions(self, topic, product, locale):
        """Return the top solved questions of the topic (and its subtopics) and product.

        Cached for a short time and never cleared, so a pick can lag behind a question
        becoming spam, locked or archived until the cache expires.
        """
        cache_key = CURATED_QUESTIONS_CACHE_KEY.format(
            topic_id=topic.pk, product_id=product.pk, locale=locale
        )
        cards = cache.get(cache_key)
        if cards is not None:
            return cards

        rows = (
            product.questions.filter(
                Q(topic=topic) | Q(topic__parent=topic),
                locale=locale,
                solution__isnull=False,
                is_spam=False,
                is_archived=False,
                is_locked=False,
            )
            .order_by("-num_votes_past_week", "-id")
            .values("id", "title", "num_answers", "solution_id")[:MAX_QUESTIONS_SHOWN]
        )
        cards = [_question_card(row, locale) for row in rows]
        cache.set(cache_key, cards, settings.CACHE_SHORT_TIMEOUT)
        return cards
