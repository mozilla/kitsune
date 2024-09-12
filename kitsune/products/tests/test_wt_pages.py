from django.http import Http404
from django.test import RequestFactory

from wagtail.models import Page
from wagtail.test.utils import WagtailPageTestCase
from wagtail.views import serve as wagtail_serve

from kitsune.products.models import SingleProductIndexPage, SumoPlaceholderPage
from kitsune.products.tests import ProductFactory


class SumoCMSTests(WagtailPageTestCase):
    def test_can_create_dummy_page(self):
        """Test that our page was created"""
        homepage = Page.objects.get(url_path="/")
        product_dummy = SumoPlaceholderPage(title="Product Dummy", slug="products")
        homepage.add_child(instance=product_dummy)

        # See if it is now in the database
        retrieved = Page.objects.get(id=product_dummy.id)
        self.assertEqual(retrieved.title, "Product Dummy")

    def test_can_create_product_index_page(self):
        """Test that we can create a single product index page"""
        homepage = Page.objects.get(url_path="/")
        product_dummy = SumoPlaceholderPage(title="Product Dummy", slug="products")
        homepage.add_child(instance=product_dummy)
        test_product = ProductFactory(
            title="Firefox", slug="firefox", display_order=1, visible=True
        )
        product_index = SingleProductIndexPage(
            title="Firefox WT", slug="firefox", product=test_product
        )
        product_dummy.add_child(instance=product_index)

        # See if it is now in the database
        retrieved = Page.objects.get(id=product_index.id)
        self.assertEqual(retrieved.title, "Firefox WT", "The titles should match")
        self.assertEqual(retrieved.slug, "firefox", "The slugs should match")

    def test_can_serve_wt_product_index(self):
        """Test that we can create a single product index page and serve it"""
        homepage = Page.objects.get(url_path="/")
        product_dummy = SumoPlaceholderPage(title="Product Dummy", slug="products")
        homepage.add_child(instance=product_dummy)
        test_product = ProductFactory(
            title="Firefox", slug="firefox", display_order=1, visible=True
        )
        product_index = SingleProductIndexPage(
            title="Firefox WT", slug="firefox", product=test_product
        )
        product_dummy.add_child(instance=product_index)

        # Serve the page
        response = self.client.get("/en-US/products/firefox", follow=True)
        self.assertEqual(response.status_code, 200, "The page should be served successfully")

    def test_placeholder_returns_404(self):
        """Test that a placeholder page returns a 404"""
        homepage = Page.objects.get(url_path="/")
        product_dummy = SumoPlaceholderPage(title="Product Dummy", slug="products")
        homepage.add_child(instance=product_dummy)

        # Try assertPageIsRenderable
        dummy_page = Page.objects.get(id=product_dummy.id)
        self.assertPageIsRenderable(dummy_page, accept_404=True)

        # Serve the page
        request_factory = RequestFactory()
        request = request_factory.get("/en-US/products/")
        # Can't use test client here because it will follow the
        # redirect and return a 200
        with self.assertRaises(Http404):
            wagtail_serve(request, "/en-US/products/")
