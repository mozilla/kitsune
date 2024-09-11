from django.db import models
from django.http import Http404

from kitsune.products.models import Product
from kitsune.wiki.facets import topics_for
from kitsune.wiki.utils import get_featured_articles

from typing import List

from wagtail import blocks
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel
from wagtail.models import Page
from wagtail.snippets.blocks import SnippetChooserBlock


class SumoPlaceholderPage(Page):
    """A page used to allow for child pages to be created
    so we can have a proper Wagtail tree structure"""

    settings_panels = Page.settings_panels + [
        FieldPanel("show_in_menus"),
    ]
    content_panels = [
        FieldPanel("title"),
        FieldPanel("slug"),
    ]

    promote_panels: List[FieldPanel] = []
    preview_modes: List[Page.preview_modes] = []

    is_placeholder = True

    def serve(self, request):
        raise Http404


# Define Blocks for Stream Fields
# Wagtail: This is a StructBlock that allows selection of a Product Snippet
class ProductSnippetBlock(blocks.StructBlock):
    """Block for product snippets"""

    product = SnippetChooserBlock(target_model="products.Product", required=True)

    class Meta:
        template = "products/blocks/product_snippet_block.html"
        icon = "placeholder"
        label = "Product Card"


class SearchBlock(blocks.StructBlock):
    """Block for the search form"""

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        return context

    class Meta:
        template = "products/blocks/search_block.html"
        icon = "search"
        label = "Search Form"


class CTABlock(blocks.StructBlock):
    """Block for the call to action"""

    # Doesn't do much at the moment...#todo

    headline = blocks.CharBlock(required=True, max_length=255)
    details = blocks.RichTextBlock(required=True)
    link = blocks.URLBlock(required=True)
    type = blocks.ChoiceBlock(
        choices=[
            ("Community", "Community"),
            ("Paid", "Paid"),
            ("Other", "Other"),
        ]
    )

    class Meta:
        template = "products/blocks/cta_block.html"
        icon = "plus-inverse"
        label = "Call to Action"


class FeaturedArticlesBlock(blocks.StructBlock):
    """Block for the featured articles"""

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        context["featured"] = get_featured_articles(product=context["product"])
        return context

    class Meta:
        template = "products/blocks/featured_articles_block.html"
        icon = "doc-full-inverse"
        label = "Featured Articles"


class FrequentTopicsBlock(blocks.StructBlock):
    """Block for the frequent topics"""

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        context["topics"] = topics_for(
            user=context["user"], product=context["product"], parent=None
        )
        return context

    class Meta:
        template = "products/blocks/frequent_topics_block.html"
        icon = "doc-full-inverse"
        label = "Frequent Topics"
        max = 1


class SingleProductIndexPage(Page):
    """A page representing a product"""

    template = "products/product_wagtail.html"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="product_index")

    body = StreamField(
        [
            ("search", SearchBlock()),
            ("cta", CTABlock()),
            ("featured_articles", FeaturedArticlesBlock()),
            ("product_snippet", ProductSnippetBlock()),
            ("frequent_topics", FrequentTopicsBlock()),
            ("text", blocks.RichTextBlock()),
        ]
    )

    content_panels = Page.content_panels + [FieldPanel("product"), FieldPanel("body")]

    class Meta:
        verbose_name = "Single Product Index"
        verbose_name_plural = "Single Product Indexes"
